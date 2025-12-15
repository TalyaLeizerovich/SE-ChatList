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
import requests
import os
from typing import List, Dict, Optional
from difflib import SequenceMatcher





# Ollama LLM Integration - BATCH processing for speed
def ollama_generate_batch(messages: List[str]) -> List[Dict]:
    """Process multiple messages in ONE LLM call for maximum speed."""
    if not messages:
        return []
    
    # Create batch prompt
    numbered_messages = "\n".join([f"{i+1}. {msg}" for i, msg in enumerate(messages)])
    
    prompt = f"""You are a task detector. For each message below, output ONLY a JSON array.
For each message, return: {{"id": number, "is_task": true/false, "task": "extracted task or empty string"}}

Rules:
- is_task: true if someone needs to do/bring/prepare something
- task: the clear action needed (or "" if not a task)
- Keep it brief and clear

Messages:
{numbered_messages}

Output ONLY the JSON array, nothing else:"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        result = data.get("response", "").strip()
        
        # Try to parse JSON from response
        # Remove markdown code blocks if present
        result = re.sub(r'```json\s*|\s*```', '', result)
        result = result.strip()
        
        parsed = json.loads(result)
        return parsed if isinstance(parsed, list) else []
        
    except Exception as e:
        print(f"[WARNING] Batch processing failed: {str(e)}")
        return []

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

def is_repetitive_or_irrelevant_fast(text: str, recent_messages: List[str]) -> bool:
    """Fast rule-based check for noise."""
    text_lower = text.lower().strip()
    
    if len(text_lower.split()) < 3:
        common_noise = ['ok', 'yes', 'no', 'thanks', 'thank you', 'got it', 'sure', 
                       'cool', 'lol', 'haha', 'wow', 'nice', 'good', 'great', 'bye']
        if text_lower in common_noise:
            return True
    
    for recent in recent_messages[-5:]:
        similarity = SequenceMatcher(None, text_lower, recent.lower()).ratio()
        if similarity > 0.85:
            return True
    
    return False

def is_valid_task(task_text: str) -> bool:
    """Check if task is valid."""
    if not task_text:
        return False
    
    task_lower = task_text.lower().strip()
    
    invalid_responses = [
        "none", "no task", "no actionable task", "not a task", 
        "n/a", "not applicable", "empty", ""
    ]
    
    for invalid in invalid_responses:
        if task_lower == invalid or invalid in task_lower and len(task_lower) < 20:
            return False
    
    if len(task_text) < 3 or not any(c.isalpha() for c in task_text):
        return False
    
    return True

def calculate_similarity(task1: str, task2: str) -> float:
    """Calculate similarity between tasks."""
    words1 = set(task1.lower().split())
    words2 = set(task2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

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
            earliest = min(similar_group, key=lambda x: x.get('date', ''))
            
            merged_task = {
                'content': merged_content,
                'date': earliest['date'],
                'time': earliest['time'],
                'from': ', '.join(set(t['from'] for t in similar_group)),
                'group': earliest['group'],
                'merged_from': len(similar_group)
            }
            merged.append(merged_task)
        else:
            merged.append(task1)
        
        used_indices.add(i)
    
    return merged

def process_json_file(input_file: str, output_file: str):
    """Process messages using BATCH processing for speed."""
    input_dir = os.path.dirname(input_file)
    if input_dir and not os.path.exists(input_dir):
        print(f"[INFO] Creating missing directory: {input_dir}")
        os.makedirs(input_dir, exist_ok=True)
    
    if not os.path.exists(input_file):
        print(f"[INFO] Creating missing file: {input_file}")
        with open(input_file, "w", encoding="utf-8") as f:
            json.dump([], f)
    
    with open(input_file, "r", encoding="utf-8") as f:
        messages = json.load(f)
    
    print(f"[INFO] Processing {len(messages)} messages...")
    
    # Step 1: Fast filtering with rules
    recent_messages = []
    filtered_messages = []
    filtered_indices = []
    
    for idx, msg in enumerate(messages):
        content = msg.get("content", "").strip()
        if not content:
            continue
        
        cleaned = clean_text(content)
        
        if is_repetitive_or_irrelevant_fast(cleaned, recent_messages):
            continue
        
        recent_messages.append(cleaned)
        filtered_messages.append(msg)
        filtered_indices.append(idx)
    
    print(f"[INFO] After filtering: {len(filtered_messages)} potentially actionable messages")
    
    # Step 2: Batch process with LLM (process 20 at a time for safety)
    batch_size = 20
    results = []
    
    for i in range(0, len(filtered_messages), batch_size):
        batch = filtered_messages[i:i+batch_size]
        batch_contents = [clean_text(msg.get("content", "")) for msg in batch]
        
        print(f"[INFO] Processing batch {i//batch_size + 1}/{(len(filtered_messages)-1)//batch_size + 1}")
        
        llm_results = ollama_generate_batch(batch_contents)
        
        # Match results with original messages
        for j, msg in enumerate(batch):
            # Find corresponding LLM result
            llm_result = None
            for result in llm_results:
                if result.get("id") == j + 1:
                    llm_result = result
                    break
            
            if not llm_result:
                continue
            
            if not llm_result.get("is_task", False):
                continue
            
            task_text = llm_result.get("task", "").strip()
            
            if not is_valid_task(task_text):
                continue
            
            results.append({
                "content": task_text,
                "date": msg.get("date"),
                "time": msg.get("time") + ":00" if len(msg.get("time", "")) == 5 else msg.get("time"),
                "from": msg.get("from"),
                "group": msg.get("group")
            })
    
    print(f"[INFO] Found {len(results)} tasks before merging")
    
    # Step 3: Merge similar tasks
    merged_results = merge_similar_tasks(results)
    print(f"[INFO] Merged into {len(merged_results)} unique tasks")
    
    # Save results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_results, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Processed {len(merged_results)} tasks → saved to {output_file}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "raw_messages.json")
    output_file = os.path.join(script_dir, "processed_messages.json")
    
    process_json_file(input_file, output_file)
    
   



    
 
    
         
    
    
  

   
    
  