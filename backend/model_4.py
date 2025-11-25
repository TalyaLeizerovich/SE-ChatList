#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single-file pipeline:
- Reads messages from a JSON file named `messages.json`
  (array of objects with fields: content, date (YYYY-MM-DD) or timestamp, time (HH:MM:SS), group_name, sender_name)
- Cleans text
- Filters messages from today (00:00 to now)
- Detects numeric quantities & units (basic English+Hebrew)
- Classifies actionable vs non-actionable using HF zero-shot
- Stores results to SQLite 'task_pipeline.db' (table messages_labeled)
- Prints a short summary
"""
import re
import json
import sqlite3
from datetime import datetime, timezone, date
from dateutil import parser as dateparser
from transformers import pipeline
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# -------------------------
# Requirements: run once
# -------------------------
# pip install -r requirements.txt
# and (first run) in python:
# import nltk; nltk.download('punkt'); nltk.download('stopwords')

# -------------------------
# Helpers - preprocessing
# -------------------------
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
EN_STOP = set(stopwords.words("english"))
# small Hebrew stoplist (expand as needed)
HE_STOP = {"של", "את", "עם", "על", "מה", "הוא", "היא", "יש", "זה", "למחר", "מחר", "להביא", "תודה"}

def normalize_text(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"http\S+|www\.\S+", "", t)                # remove urls
    t = re.sub(r"[\U00010000-\U0010ffff]", "", t)         # remove most emojis
    t = t.lower()
    t = re.sub(r"[^\w\s\u0590-\u05FF]", " ", t)           # keep Hebrew letters, words, digits
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def tokenize_and_remove_stopwords(text: str):
    t = normalize_text(text)
    tokens = word_tokenize(t)
    tokens = [tok for tok in tokens if tok not in EN_STOP and tok not in HE_STOP]
    return " ".join(tokens)

# -------------------------
# Quantity/units extraction
# -------------------------
UNITS_MAP = {
    # English
    "bottle":"bottles","bottles":"bottles","pack":"packs","packs":"packs",
    "kg":"kilograms","g":"grams","gram":"grams","grams":"grams","liter":"liters","liters":"liters","l":"liters",
    "shirt":"shirts","shirts":"shirts","ticket":"tickets","tickets":"tickets",
    # Hebrew
    "בקבוק":"bottles","בקבוקים":"bottles","חבילה":"packs","חבילות":"packs",
    "קילוגרם":"kilograms","קג":"kilograms","גרם":"grams","גרמים":"grams",
    "ליטר":"liters","חולצה":"shirts","חולצות":"shirts","כרטיס":"tickets","כרטיסים":"tickets"
}
# small word numbers map (eng + heb)
WORD_NUM = {
    "one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,
    "אחד":1,"שניים":2,"שתיים":2,"שלוש":3,"ארבע":4,"חמש":5,"שש":6,"שבע":7,"שמונה":8,"תשע":9,"עשר":10
}

num_regex = re.compile(r"\b(\d+)\b")
wordnum_regex = re.compile(r"\b(" + "|".join(re.escape(w) for w in WORD_NUM.keys()) + r")\b", re.IGNORECASE)
unit_regex = re.compile(r"\b(" + "|".join(re.escape(u) for u in UNITS_MAP.keys()) + r")\b", re.IGNORECASE)

def extract_quantities(text: str):
    found = []
    t = normalize_text(text)
    nums = [int(n) for n in num_regex.findall(t)]
    wordnums = [WORD_NUM.get(w.lower()) for w in wordnum_regex.findall(t)]
    # flatten
    all_nums = nums + [n for n in wordnums if n]
    units = unit_regex.findall(t)
    # normalize units
    units_norm = [UNITS_MAP.get(u, u) for u in units]
    # pair sequentially (best-effort)
    for i in range(min(len(all_nums), len(units_norm))):
        found.append({"quantity": all_nums[i], "unit": units_norm[i]})
    return found

# -------------------------
# Zero-shot classifier (no fine-tune)
# -------------------------
# we'll use NLI/zero-shot to check if text "is a request/task"
# label set: actionable / non-actionable
zs_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

CANDIDATE_LABELS = ["actionable", "non-actionable"]

def is_actionable_zero_shot(text: str, threshold=0.6):
    cleaned = tokenize_and_remove_stopwords(text)
    if not cleaned:
        return False, 0.0
    res = zs_classifier(cleaned, CANDIDATE_LABELS, multi_label=False)
    # res: {'labels':[...],'scores':[...],...}
    label = res['labels'][0]  # top label
    score = float(res['scores'][0])
    return (label == "actionable" and score >= threshold), score

# -------------------------
# Storage (SQLite)
# -------------------------
DB_PATH = "task_pipeline.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS messages_labeled (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      content TEXT,
      date TEXT,
      time TEXT,
      group_name TEXT,
      sender_name TEXT,
      is_actionable INTEGER,
      score REAL,
      quantities TEXT,
      ingested_at TEXT
    )
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_date ON messages_labeled(date);')
    cur.commit = conn.commit
    conn.commit()
    conn.close()

def save_labeled_message(rec):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
      INSERT INTO messages_labeled
      (content, date, time, group_name, sender_name, is_actionable, score, quantities, ingested_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (rec['content'], rec.get('date'), rec.get('time'), rec.get('group_name'),
          rec.get('sender_name'), rec.get('is_actionable'), rec.get('score'),
          json.dumps(rec.get('quantities', []), ensure_ascii=False), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

# -------------------------
# Main processing flow
# -------------------------
def load_messages_json(path="messages.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def message_is_today(msg):
    # Accept msg with 'timestamp' (ISO) or date/time fields or 'date' only.
    try:
        if 'timestamp' in msg and msg['timestamp']:
            dt = dateparser.parse(msg['timestamp'])
        elif msg.get('date') and msg.get('time'):
            dt = dateparser.parse(f"{msg['date']}T{msg['time']}")
        elif msg.get('date'):
            dt = dateparser.parse(msg['date'])
        else:
            return False
        # compare date in local system timezone to today
        return dt.date() == date.today()
    except Exception:
        return False

def process_messages(path="messages.json", threshold=0.6):
    msgs = load_messages_json(path)
    init_db()
    processed_count = 0
    actionable_count = 0
    for m in msgs:
        if not message_is_today(m):
            continue  # skip older messages
        content = m.get('content','').strip()
        if not content:
            continue
        quantities = extract_quantities(content)
        actionable, score = is_actionable_zero_shot(content, threshold=threshold)
        rec = {
            "content": content,
            "date": m.get('date'),
            "time": m.get('time'),
            "group_name": m.get('group_name'),
            "sender_name": m.get('sender_name'),
            "is_actionable": 1 if actionable else 0,
            "score": score,
            "quantities": quantities
        }
        save_labeled_message(rec)
        processed_count += 1
        if actionable:
            actionable_count += 1
    print(f"Processed today messages: {processed_count}, actionable: {actionable_count}")

# -------------------------
# Run as script
# -------------------------
if __name__ == "__main__":
    # expects a file messages.json in the same folder (not python file)
    # example messages.json schema:
    # [{"content":"Please bring 2 bottles of water","date":"2025-11-24","time":"10:10:00","group_name":"Class A","sender_name":"Rachel"}, ...]
    process_messages("messages.json", threshold=0.6)
