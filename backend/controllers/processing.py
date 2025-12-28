import json
import re
import requests
import os
from typing import Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# ==================== CONFIG ====================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral:7b-instruct"
MAX_WORKERS = 1

# ==================== PROMPTS ====================

TASK_PROMPT = """
You are a task extraction engine.

Given a chat message:
1. Decide if it contains a task.
2. If yes, rewrite it as a short, clear task in imperative form.
3. Categorize the task into one of these: [Work, Personal, Shopping, Studies, Urgent, Home, General].

Return ONLY valid JSON in this format:
{{ 
  "task": "<task_description>",
  "category": "<category_name>"
}} 
OR if no task exists:
{{ "task": null, "category": null }}

Message:
"{message}"
"""

# ==================== OLLAMA CALL ====================

def ollama_generate(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )
    response.raise_for_status()
    return response.json().get("response", "").strip()

# ==================== TASK DETECTION ====================

def detect_task_with_llm(text: str) -> Optional[Dict[str, str]]:
    prompt = TASK_PROMPT.format(message=text)
    try:
        raw = ollama_generate(prompt)
        matches = re.findall(r"\{[^{}]*\}", raw, re.DOTALL)
        if not matches:
            return None

        for match in matches:
            try:
                data = json.loads(match.strip())
                task = data.get("task")
                category = data.get("category", "General")
                
                if task and task != "null" and isinstance(task, str) and len(task.strip()) >= 3:
                    return {
                        "task": task.strip(),
                        "category": category if category else "General"
                    }
            except json.JSONDecodeError:
                continue
    except Exception as e:
        print(f"[ERROR] LLM parsing failed: {e}")
    return None

# ==================== MESSAGE PROCESSING ====================

def process_message(msg_obj: dict) -> Optional[dict]:
    try:
        content = msg_obj.get("content", "").strip()
        if not content:
            return None

        llm_result = detect_task_with_llm(content)
        if not llm_result:
            return None
        
        time_value = msg_obj.get("time", "")
        if isinstance(time_value, str) and len(time_value) == 5:
            time_value += ":00"

        return {
            "content": llm_result["task"],
            "category": llm_result["category"],
            "date": msg_obj.get("date"),
            "time": time_value,
            "from": msg_obj.get("from"),
            "group": msg_obj.get("group")
        }
    except Exception as e:
        print(f"[ERROR] Failed to process message: {e}")
        return None

# ==================== FILE PROCESSING ====================

def process_json_file(input_file: str, output_file: str):
    try:
        if not os.path.exists(input_file):
            print(f"[ERROR] Input file not found: {input_file}")
            return

        with open(input_file, "r", encoding="utf-8") as f:
            messages = json.load(f)
        
        print(f"\n[1/2] Extracting tasks and categories from {len(messages)} messages...")
        start_time = time.time()
        
        final_tasks = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_msg = {executor.submit(process_message, msg): i for i, msg in enumerate(messages)}
            
            for future in as_completed(future_to_msg):
                result = future.result()
                if result:
                    final_tasks.append(result)
        
        print(f"[2/2] Saving {len(final_tasks)} tasks to {output_file}...")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_tasks, f, indent=2, ensure_ascii=False)

        print(f"✓ Process complete in {time.time() - start_time:.1f}s")
    
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

# ==================== MAIN ====================

if __name__ == "__main__":
    process_json_file(
        r"C:\softwareEngineer\ChatList\backend\controllers\raw_messages.json",
        "processed_messages.json"
    )