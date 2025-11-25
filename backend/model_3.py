import json
import re
from datetime import datetime
from transformers import pipeline

# --- IMPORT A PIPELINE FOR GENERAL TEXT UNDERSTANDING (NO TRAINING) ---
nlp = pipeline("token-classification", model="Davlan/bert-base-multilingual-cased-ner-hrl", aggregation_strategy="simple")

# --- DICTIONARY OF UNITS (HEBREW + ENGLISH) ---
UNITS_MAP = {
    "bottle": "bottles",
    "bottles": "bottles",
    "ml": "milliliters",
    "liter": "liters",
    "liters": "liters",
    "kg": "kilograms",
    "gram": "grams",
    "grams": "grams",
    "shirt": "shirts",
    "shirts": "shirts",
    "pack": "packs",
    "packs": "packs",

    # HEBREW
    "בקבוק": "bottles",
    "בקבוקים": "bottles",
    "חולצה": "shirts",
    "חולצות": "shirts",
    "גרם": "grams",
    "גרמים": "grams",
    "ליטר": "liters",
    "חבילה": "packs",
    "חבילות": "packs"
}

# --- FUNCTION TO EXTRACT NUMBERS & UNITS ---
def extract_quantities(text):
    found = []

    # find numbers (digits and written words)
    number_pattern = r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|אחד|שתיים|שלוש|ארבע|חמש|שש|שבע|שמונה|תשע|עשר)\b"
    unit_pattern = r"\b(" + "|".join(UNITS_MAP.keys()) + r")\b"

    numbers = re.findall(number_pattern, text, flags=re.IGNORECASE)
    units = re.findall(unit_pattern, text, flags=re.IGNORECASE)

    # convert word numbers → digits
    word_to_digit = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "אחד": 1, "שתיים": 2, "שלוש": 3, "ארבע": 4,
        "חמש": 5, "שש": 6, "שבע": 7, "שמונה": 8, "תשע": 9, "עשר": 10
    }

    normalized_numbers = []
    for n in numbers:
        if n.isdigit():
            normalized_numbers.append(int(n))
        else:
            normalized_numbers.append(word_to_digit.get(n.lower(), n))

    normalized_units = [UNITS_MAP.get(u.lower(), u) for u in units]

    for i in range(min(len(normalized_numbers), len(normalized_units))):
        found.append({"quantity": normalized_numbers[i], "unit": normalized_units[i]})

    return found

# --- LOAD JSON (MESSAGES) FOR PROCESSING ---
with open("json.py", "r", encoding="utf-8") as file:
    messages = json.load(file)

# --- FILTER BY TODAY FROM 00:00 ---
today = datetime.now().strftime("%Y-%m-%d")
messages = [m for m in messages if m.get("date") == today]

# --- PROCESS MESSAGES ---
processed = []
for msg in messages:
    quantities = extract_quantities(msg["content"])
    msg["quantities_detected"] = quantities
    processed.append(msg)

# --- SAVE OUTPUT FILE ---
with open("quantities_extracted.json", "w", encoding="utf-8") as output:
    json.dump(processed, output, indent=2, ensure_ascii=False)

print("Done! quantities_extracted.json created successfully 🎉")
