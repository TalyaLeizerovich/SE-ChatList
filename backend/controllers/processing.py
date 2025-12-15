# import json
# import re
# import requests
# import os

# #llama3 
# def ollama_generate(prompt: str):
#     try:
#         response = requests.post(
#             "http://localhost:11434/api/generate",
#             json={
#                 "model": "llama3",
#                 "prompt": prompt,
#                 "stream": False
#             }
#         )
#         response.raise_for_status()
#         data = response.json()
#         result = data.get("response", "")

#         if not result:
#             return ""

#         return result.strip()
#     except Exception as e:
#         raise RuntimeError(f"Ollama error: {str(e)}")


# CANDIDATE_LABELS = ["task", "not_task"]


# def is_actionable(text: str, threshold=0.6) -> bool:
#     prompt = f"""
# Classify the following message as either "task" or "not_task".
# Return ONLY one word: task / not_task.

# Message: "{text}"
# """
#     label = ollama_generate(prompt).lower().strip()
#     return "task" in label


# def extract_task_from_text(text: str) -> str:
#     prompt = f"""
# Extract the actionable task from this message.
# Return ONLY the task itself. No explanations.

# Message: {text}
# """
#     return ollama_generate(prompt).strip()


# def heuristic_fix(task_text: str, original_text: str) -> str:
#     if re.match(r"i('m| will)", task_text.lower()):
#         match = re.search(
#             r"(bring|send|upload|prepare|finish|review|update|schedule).+",
#             original_text,
#             re.IGNORECASE
#         )
#         if match:
#             return match.group(0)
#     return task_text


# def process_message(msg_obj: dict):
#     content = msg_obj.get("content", "").strip()
#     if not content:
#         return None

#     if not is_actionable(content):
#         return None

#     task_text = extract_task_from_text(content)
#     task_text = heuristic_fix(task_text, content)

#     if not task_text:
#         return None

#     return {
#         "content": task_text,
#         "date": msg_obj.get("date"),
#         "time": msg_obj.get("time") + ":00" if len(msg_obj.get("time", "")) == 5 else msg_obj.get("time"),
#         "from": msg_obj.get("from"),
#         "group": msg_obj.get("group")
#     }



# def process_json_file(input_file: str, output_file: str):

    
#     input_dir = os.path.dirname(input_file)
#     if input_dir and not os.path.exists(input_dir):
#         print(f"[INFO] Creating missing directory: {input_dir}")
#         os.makedirs(input_dir, exist_ok=True)

    
#     if not os.path.exists(input_file):
#         print(f"[INFO] Creating missing file: {input_file}")
#         with open(input_file, "w", encoding="utf-8") as f:
#             json.dump([], f)

    
#     with open(input_file, "r", encoding="utf-8") as f:
#         messages = json.load(f)

    
#     results = []
#     for msg in messages:
#         processed = process_message(msg)
#         if processed:
#             results.append(processed)

#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(results, f, indent=2, ensure_ascii=False)

#     print(f"Processed {len(results)} tasks → saved to {output_file}")


# if __name__ == "__main__":
#     process_json_file(
#         r"C:\softwareEngineer\ChatList\backend\controllers\raw_messages.json",
#         "processed_messages.json"
#     )

import json
import re
import os
from typing import List, Dict, Optional, Set
from difflib import SequenceMatcher
from datetime import datetime


# Rule-based task detection - NO AI NEEDED
def detect_task_with_rules(text: str) -> Optional[str]:
    """Detect if text contains a task using regex patterns and rules."""
    text_lower = text.lower().strip()
    
    # Hebrew task indicators
    hebrew_patterns = [
        r'תביא[ו]?\s+(.+)',  # תביא/תביאו
        r'קנ[הו]\s+(.+)',     # קנה/קנו
        r'אל\s+תשכח[ו]?\s+(.+)',  # אל תשכח/תשכחו
        r'תזכור[ו]?\s+(.+)',  # תזכור/תזכורו
        r'צריך[ים]?\s+(.+)',  # צריך/צריכים
        r'חייב[ים]?\s+(.+)',  # חייב/חייבים
        r'תכין[ו]?\s+(.+)',   # תכין/תכינו
        r'תעש[הו]\s+(.+)',    # תעשה/תעשו
        r'תשלח[ו]?\s+(.+)',   # תשלח/תשלחו
        r'תסדר[ו]?\s+(.+)',   # תסדר/תסדרו
        r'תבדוק[ו]?\s+(.+)',  # תבדוק/תבדקו
        r'תארגן[ו]?\s+(.+)',  # תארגן/תארגנו
        r'תטפל[ו]?\s+(.+)',   # תטפל/תטפלו
    ]
    
    # English task indicators
    english_patterns = [
        r'bring\s+(.+)',
        r'buy\s+(.+)',
        r'don\'?t\s+forget\s+(.+)',
        r'remember\s+to\s+(.+)',
        r'need\s+to\s+(.+)',
        r'have\s+to\s+(.+)',
        r'must\s+(.+)',
        r'please\s+(.+)',
        r'can\s+you\s+(.+)',
        r'could\s+you\s+(.+)',
        r'prepare\s+(.+)',
        r'get\s+(.+)',
        r'make\s+(.+)',
        r'send\s+(.+)',
        r'check\s+(.+)',
        r'organize\s+(.+)',
    ]
    
    # Combined patterns
    all_patterns = hebrew_patterns + english_patterns
    
    # Check each pattern
    for pattern in all_patterns:
        match = re.search(pattern, text_lower)
        if match:
            # Extract the task part
            task = match.group(1) if match.groups() else text
            # Clean and return
            return clean_task_text(text, task)
    
    # Check for modal verbs + action verbs
    modal_action_patterns = [
        r'(need|must|should|have to|got to)\s+(bring|buy|get|make|send|prepare|check)',
        r'(צריך|חייב)\s+(להביא|לקנות|לעשות|לשלוח|להכין|לבדוק|לסדר)',
    ]
    
    for pattern in modal_action_patterns:
        if re.search(pattern, text_lower):
            return clean_task_text(text, text)
    
    # Check for imperative sentences with objects
    imperative_with_object = [
        r'(bring|get|buy|take|send|make)\s+(\w+\s+){1,4}(milk|bread|water|food|document|file|report|email)',
        r'(הביא|קנה|קח|שלח|עשה)\s+(\w+\s+){0,3}(חלב|לחם|מים|אוכל|מסמך|קובץ|דוח)',
    ]
    
    for pattern in imperative_with_object:
        if re.search(pattern, text_lower):
            return clean_task_text(text, text)
    
    # Check for questions about doing something
    question_patterns = [
        r'who\s+(will|can|should)\s+(bring|buy|get|make)',
        r'מי\s+(יביא|יקנה|יעשה|יכין)',
    ]
    
    for pattern in question_patterns:
        if re.search(pattern, text_lower):
            return clean_task_text(text, text)
    
    return None


def clean_task_text(original: str, extracted: str) -> str:
    """Clean and format task text."""
    # If extracted is too short, use original
    if len(extracted.strip()) < 5:
        text = original
    else:
        text = extracted
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]
    
    return text.strip()


def clean_text(text: str) -> str:
    """Remove emojis and normalize text."""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r' ', text)
    text = re.sub(r'([!?.]){2,}', r'\1', text)
    return text.strip()


def is_repetitive_or_irrelevant_fast(text: str, recent_messages: List[str], window_size: int = 15) -> bool:
    """Fast rule-based check for noise."""
    text_lower = text.lower().strip()
    
    # Very short messages
    if len(text_lower) < 5:
        return True
    
    # Common noise
    if len(text_lower.split()) < 3:
        common_noise = [
            'ok', 'yes', 'no', 'thanks', 'thank you', 'got it', 'sure', 
            'cool', 'lol', 'haha', 'wow', 'nice', 'good', 'great', 'bye',
            'אוקיי', 'כן', 'לא', 'תודה', 'סבבה', 'יופי', 'נחמד', 'טוב',
            'בסדר', 'מעולה', 'אהה', 'אוק', 'יש', 'שלום', 'היי', 'הי'
        ]
        if text_lower in common_noise:
            return True
    
    # Check similarity with recent messages
    for recent in recent_messages[-window_size:]:
        similarity = SequenceMatcher(None, text_lower, recent.lower()).ratio()
        if similarity > 0.85:
            return True
    
    return False


def is_valid_task(task_text: str) -> bool:
    """Check if task is valid."""
    if not task_text:
        return False
    
    # Minimum length
    if len(task_text.strip()) < 5:
        return False
    
    # Must have alphabetic content
    if not any(c.isalpha() for c in task_text):
        return False
    
    # Check if it's actually a question without action
    question_without_action = [
        r'^(what|why|how|when|where|who)\s+(is|are|was|were|do|does|did)',
        r'^(מה|למה|איך|מתי|איפה|מי)\s+(זה|זאת|היה|הייתה)',
    ]
    
    for pattern in question_without_action:
        if re.match(pattern, task_text.lower()):
            # Only filter out if it doesn't contain action words
            if not re.search(r'(bring|buy|get|make|הביא|קנה|עשה)', task_text.lower()):
                return False
    
    return True


def calculate_similarity(task1: str, task2: str) -> float:
    """Calculate similarity between tasks."""
    text1 = task1.lower().strip()
    text2 = task2.lower().strip()
    
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    jaccard = len(intersection) / len(union) if union else 0.0
    
    sequence = SequenceMatcher(None, text1, text2).ratio()
    
    return 0.6 * jaccard + 0.4 * sequence


def merge_similar_tasks(tasks: List[Dict]) -> List[Dict]:
    """Merge similar tasks."""
    if not tasks:
        return []
    
    merged = []
    used_indices = set()
    
    for i, task1 in enumerate(tasks):
        if i in used_indices:
            continue
        
        similar_group = [task1]
        
        for j, task2 in enumerate(tasks[i+1:], start=i+1):
            if j in used_indices:
                continue
            
            similarity = calculate_similarity(task1['content'], task2['content'])
            
            if similarity > 0.7:
                similar_group.append(task2)
                used_indices.add(j)
        
        if len(similar_group) > 1:
            merged_content = max(similar_group, key=lambda x: len(x['content']))['content']
            earliest = min(similar_group, key=lambda x: x.get('date', '') + x.get('time', ''))
            
            merged_task = {
                'content': merged_content,
                'date': earliest['date'],
                'time': earliest['time'],
                'from': ', '.join(sorted(set(t['from'] for t in similar_group))),
                'group': earliest['group'],
                'merged_from': len(similar_group)
            }
            merged.append(merged_task)
        else:
            merged.append(task1)
        
        used_indices.add(i)
    
    return merged


def process_json_file(input_file: str, output_file: str, log_file: Optional[str] = None):
    """Process messages using rule-based detection (no AI needed)."""
    
    if log_file is None:
        log_file = output_file.replace('.json', '_processing.log')
    
    log_entries = []
    
    def log(message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        print(entry)
        log_entries.append(entry)
    
    input_dir = os.path.dirname(input_file)
    if input_dir and not os.path.exists(input_dir):
        log(f"Creating missing directory: {input_dir}")
        os.makedirs(input_dir, exist_ok=True)
    
    if not os.path.exists(input_file):
        log(f"Creating missing file: {input_file}")
        with open(input_file, "w", encoding="utf-8") as f:
            json.dump([], f)
    
    with open(input_file, "r", encoding="utf-8") as f:
        messages = json.load(f)
    
    log(f"Processing {len(messages)} messages using rule-based detection...")
    
    recent_messages = []
    results = []
    skipped_count = 0
    
    for idx, msg in enumerate(messages):
        content = msg.get("content", "").strip()
        if not content:
            skipped_count += 1
            continue
        
        cleaned = clean_text(content)
        
        if is_repetitive_or_irrelevant_fast(cleaned, recent_messages):
            skipped_count += 1
            continue
        
        recent_messages.append(cleaned)
        
        # Detect task using rules
        task = detect_task_with_rules(cleaned)
        
        if task and is_valid_task(task):
            results.append({
                "content": task,
                "date": msg.get("date"),
                "time": msg.get("time") + ":00" if len(msg.get("time", "")) == 5 else msg.get("time"),
                "from": msg.get("from"),
                "group": msg.get("group")
            })
    
    log(f"Found {len(results)} tasks ({skipped_count} messages skipped as noise)")
    
    merged_results = merge_similar_tasks(results)
    log(f"Merged into {len(merged_results)} unique tasks")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_results, f, indent=2, ensure_ascii=False)
    
    log(f"✓ Processed {len(merged_results)} tasks → saved to {output_file}")
    
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("\n".join(log_entries))
    
    log(f"✓ Processing log saved to {log_file}")
    
    print("\n" + "="*60)
    print("PROCESSING SUMMARY (RULE-BASED)")
    print("="*60)
    print(f"Total messages: {len(messages)}")
    print(f"Skipped as noise: {skipped_count}")
    print(f"Tasks found: {len(results)}")
    print(f"Final unique tasks: {len(merged_results)}")
    print(f"Processing speed: INSTANT (no AI calls)")
    print("="*60)


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "raw_messages.json")
    output_file = os.path.join(script_dir, "processed_messages.json")
    
    process_json_file(input_file, output_file)

    
 
    
         
    
    
  

   
    
  