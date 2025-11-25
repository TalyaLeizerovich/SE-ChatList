import json
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from transformers import pipeline

# --- DOWNLOAD NLTK RESOURCES (only first run) ---
nltk.download('punkt')
nltk.download('stopwords')

# --- LOAD HUGGING FACE CLASSIFICATION MODEL ---
classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")

# --- TEXT CLEANING FUNCTION ---
def clean_text(text):
    text = text.lower()
    tokens = word_tokenize(text)
    tokens = [t for t in tokens if t.isalnum()]
    stop_words = set(stopwords.words("english"))
    filtered = [t for t in tokens if t not in stop_words]
    return " ".join(filtered)

# --- CLASSIFY IF MESSAGE IS TASK / NOT TASK ---
def classify_message(message):
    cleaned = clean_text(message)
    result = classifier(cleaned)[0]
    return "actionable" if result["label"] == "POSITIVE" else "non-actionable"

# --- LOAD JSON DATA (messages) ---
with open("json.py", "r", encoding="utf-8") as f:
    messages = json.load(f)

# --- PROCESS AND LABEL ---
results = []
for msg in messages:
    label = classify_message(msg["content"])
    msg["classification"] = label
    results.append(msg)

# --- SAVE LABELED RESULTS ---
with open("classified_messages.json", "w", encoding="utf-8") as output:
    json.dump(results, output, indent=2, ensure_ascii=False)

print("Done! All messages analyzed and saved into classified_messages.json")
