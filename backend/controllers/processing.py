# import json
# import re
# import requests

# # ------------------------------------------------------
# # פונקציה שמריצה את Llama3 ב–Ollama מקומי
# # ------------------------------------------------------
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
#         return data.get("response", "").strip()
#     except Exception as e:
#         raise RuntimeError(f"Ollama error: {str(e)}")


# # ------------------------------------------------------
# # החלק הקודם של הלוגיקה נשאר זהה
# # ------------------------------------------------------
# CANDIDATE_LABELS = ["task", "not_task"]


# def is_actionable(text: str, threshold=0.6) -> bool:
#     """
#     במקום Zero-shot של HuggingFace,
#     משתמשים עכשיו בלוגיקה זהה — אבל דרך המודל Llama3.
#     """
#     prompt = f"""
# Classify the following message as either "task" or "not_task".
# Return ONLY one word: task / not_task.

# Message: "{text}"
# """
#     label = ollama_generate(prompt).lower().strip()

#     # עדיין שומרים על הלוגיקה:
#     return label == "task"


# def extract_task_from_text(text: str) -> str:
#     """
#     אותו דבר כמו T5 — רק ש-Llama3 מבצע את ההפקה.
#     """
#     prompt = f"""
# Extract the actionable task from this message.
# Return ONLY the task itself. No explanations.

# Message: {text}
# """
#     return ollama_generate(prompt)


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
#         "time": msg_obj.get("time") + ":00" if len(msg_obj.get("time","")) == 5 else msg_obj.get("time"),
#         "from": msg_obj.get("from"),
#         "group": msg_obj.get("group")
#     }


# def process_json_file(input_file: str, output_file: str):
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
#     process_json_file("raw_messages.json", "processed_messages.json")























import json

import re

from transformers import pipeline





action_classifier = pipeline(

    "zero-shot-classification",

    model="facebook/bart-large-mnli"

)





task_extractor = pipeline(

    "text2text-generation",

    model="google/flan-t5-small"

)



CANDIDATE_LABELS = ["task", "not_task"]



def is_actionable(text: str, threshold=0.6) -> bool:

    result = action_classifier(text, candidate_labels=CANDIDATE_LABELS, multi_label=False)

    label = result['labels'][0]

    score = result['scores'][0]

    return label == "task" and score >= threshold



def extract_task_from_text(text: str) -> str:

    prompt = (

        f"Extract the task from this message. "

        f"Return only the action that should be done, "

        f"do not add extra words or explanations, do not change pronouns.\n\nMessage: {text}"

    )

    result = task_extractor(prompt, max_length=50)[0]['generated_text']

    return result.strip()



def heuristic_fix(task_text: str, original_text: str) -> str:

   

    if re.match(r"i('m| will)", task_text.lower()):

        match = re.search(r"(bring|send|upload|prepare|finish|review|update|schedule).+", original_text, re.IGNORECASE)

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

        "time": msg_obj.get("time") + ":00" if len(msg_obj.get("time","")) == 5 else msg_obj.get("time"),

        "from": msg_obj.get("from"),

        "group": msg_obj.get("group")

    }







def process_json_file(input_file: str, output_file: str):

    with open(input_file, "r", encoding="utf-8") as f:

        messages = json.load(f)



    results = []



    for msg in messages:

        processed = process_message(msg)

        if processed:

            results.append(processed)



    with open(output_file, "w", encoding="utf-8") as f:

        json.dump(results, f, indent=2, ensure_ascii=False)



    print(f"Processed {len(results)} tasks → saved to {output_file}")





if __name__ == "__main__":

    #process_json_file("C:/softwareEngineer/ChatList/backend/raw_messages.json", "C:/softwareEngineer/ChatList/backend/processed_messages.json")

    process_json_file("raw_messages.json", "processed_messages.json")

