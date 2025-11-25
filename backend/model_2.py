import json
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from transformers import pipeline

# --- DOWNLOAD NLTK RESOURCES (first run only) ---
nltk.download("punkt")
nltk.download("stopwords")

# --- LOAD HUGGING FACE MODEL (pretrained sentiment classifier) ---
classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")

# --- CLEANING FUNCTION: remove emojis, punctuation & normalize text ---
def clean_text(text):
    text = text.lower()
    # Remove emojis
    text = re.sub(r"[^\w\s]", "", text)
    # Tokenize
    tokens = word_tokenize(text)
    # Remove stopwords
    stop_words = set(stopwords.words("english"))
    filtered = [t for t in tokens if t not in stop_words]
    return " ".join(filtered)

# --- RULE‑BASED IRRELEVANT DETECTION ---
irrelevant_keywords = [
    "thanks", "thank you", "thx", "ok", "okay", "great", "cool",
    "good morning", "good night", "gm", "gn", "lol", "haha", "nice",
    "מדהים", "תודה", "סבבה", "בכיף", "חח", "לילה טוב", "בוקר טוב"
]

def rule_based_irrelevant(message):
    msg = message.lower()
    return any(kw in msg for kw in irrelevant_keywords)

# --- MODEL‑BASED DECISION ---
def classify_relevance(message):
    cleaned = clean_text(message)
    result = classifier(cleaned)[0]
    return "relevant" if result["label"] == "POSITIVE" else "irrelevant"

# --- PROCESS JSON FILE (simulate your chat file json.py) ---
with open("json.py", "r", encoding="utf-8") as f:
    messages = json.load(f)

filtered_output = []

for msg in messages:
    content = msg["content"]

    # Rule-based detection first
    if rule_based_irrelevant(content):
        msg["classification"] = "irrelevant"
    else:
        # AI classification second
        relevance = classify_relevance(content)
        msg["classification"] = relevance

    if msg["classification"] == "relevant":
        filtered_output.append(msg)

# --- SAVE RESULT FILE (messages that remain after filtering) ---
with open("filtered_messages.json", "w", encoding="utf-8") as output:
    json.dump(filtered_output, output, indent=2, ensure_ascii=False)

print("Filtering complete! Relevant messages saved to filtered_messages.json")
