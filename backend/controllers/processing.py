import json
import re
import requests
import os

# ------------------------------------------------------
# הרצת מודל Llama3 ב–Ollama (ללא שינוי!)
# ------------------------------------------------------
def ollama_generate(prompt: str):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        data = response.json()
        result = data.get("response", "")

        if not result:
            return ""

        return result.strip()
    except Exception as e:
        raise RuntimeError(f"Ollama error: {str(e)}")

# ------------------------------------------------------
# לוגיקה — ללא שינוי!
# ------------------------------------------------------
CANDIDATE_LABELS = ["task", "not_task"]


def is_actionable(text: str, threshold=0.6) -> bool:
    prompt = f"""
Classify the following message as either "task" or "not_task".
Return ONLY one word: task / not_task.

Message: "{text}"
"""
    label = ollama_generate(prompt).lower().strip()
    return "task" in label


def extract_task_from_text(text: str) -> str:
    prompt = f"""
Extract the actionable task from this message.
Return ONLY the task itself. No explanations.

Message: {text}
"""
    return ollama_generate(prompt).strip()


def heuristic_fix(task_text: str, original_text: str) -> str:
    if re.match(r"i('m| will)", task_text.lower()):
        match = re.search(
            r"(bring|send|upload|prepare|finish|review|update|schedule).+",
            original_text,
            re.IGNORECASE
        )
        if match:
            return match.group(0)
    return task_text


def process_message(msg_obj: dict):
    content = msg_obj.get("content", "").strip()
    if not content:
        return None

    if not is_actionable(content):
        return None

    task_text = extract_task_from_text(content)
    task_text = heuristic_fix(task_text, content)

    if not task_text:
        return None

    return {
        "content": task_text,
        "date": msg_obj.get("date"),
        "time": msg_obj.get("time") + ":00" if len(msg_obj.get("time", "")) == 5 else msg_obj.get("time"),
        "from": msg_obj.get("from"),
        "group": msg_obj.get("group")
    }


# ------------------------------------------------------
# 🔥 הפתרון היחיד הדרוש — בלי לגעת בלוגיקה 🔥
# ------------------------------------------------------
def process_json_file(input_file: str, output_file: str):

    # יצירת תיקיית controllers במידת הצורך
    input_dir = os.path.dirname(input_file)
    if input_dir and not os.path.exists(input_dir):
        print(f"[INFO] Creating missing directory: {input_dir}")
        os.makedirs(input_dir, exist_ok=True)

    # אם קובץ raw_messages.json לא קיים → ניצור קובץ ריק
    if not os.path.exists(input_file):
        print(f"[INFO] Creating missing file: {input_file}")
        with open(input_file, "w", encoding="utf-8") as f:
            json.dump([], f)

    # עכשיו הקריאה תעבוד בטוח
    with open(input_file, "r", encoding="utf-8") as f:
        messages = json.load(f)

    # עיבוד = ללא שינוי
    results = []
    for msg in messages:
        processed = process_message(msg)
        if processed:
            results.append(processed)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Processed {len(results)} tasks → saved to {output_file}")


if __name__ == "__main__":
    process_json_file(
        r"C:\softwareEngineer\ChatList\backend\controllers\raw_messages.json",
        "processed_messages.json"
    )

