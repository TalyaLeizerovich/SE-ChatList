# import os
# import sys
# import json
# import gradio as gr
# import pandas as pd
# import requests
# from typing import List

# # ==================== FIX: PATH ====================
# current_dir = os.path.dirname(os.path.abspath(__file__))
# root_dir = os.path.dirname(current_dir)
# sys.path.append(root_dir)

# # ==================== CONFIG ====================
# API_URL = "http://127.0.0.1:8000/processed_tasks"

# WHATSAPP_GREEN_DARK = "#075e54"      
# WHATSAPP_BACKGROUND = "#F0F0F0"

# # ==================== UTILS ====================
# def get_processed_tasks_gradio() -> List[List[str]]:
#     """Fetch tasks from backend via GET request and format for Gradio Dataframe."""
#     try:
#         response = requests.get(API_URL, timeout=5)
#         if response.status_code == 200:
#             tasks = response.json()
#         else:
#             tasks = []
#     except Exception:
#         tasks = []

#     table_data = []
#     for task in tasks:
#         display_time = task.get("time", "N/A")[:5] if task.get("time") else "N/A"
#         table_data.append([
#             False,  # Checkbox for "Done"
#             task.get("content", ""),
#             task.get("from", ""),
#             task.get("group", ""),
#             task.get("date", ""),
#             display_time
#         ])
#     return table_data

# def handle_task_done(tasks_table_data):
#     """Remove tasks marked as Done from display."""
#     if isinstance(tasks_table_data, pd.DataFrame):
#         # Keep rows where first column (Done) is not True
#         new_df = tasks_table_data[tasks_table_data.iloc[:, 0] != True]
#         return new_df.values.tolist()
#     return tasks_table_data

# # ==================== GRADIO UI ====================
# custom_css = f"""
# .gradio-container, body {{
#     background-color: {WHATSAPP_BACKGROUND} !important;
#     font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
# }}
# #branding-container {{
#     display: block;
#     margin-bottom: 20px; 
# }}
# #main-header-title {{
#     color: {WHATSAPP_GREEN_DARK};
#     font-weight: 700;
#     font-size: 1.8rem; 
# }}
# #main-header-subtitle {{
#     color: #444; 
#     font-size: 0.9rem;
#     font-weight: 500;
#     margin-top: 5px; 
# }}
# #float_run_button {{
#     position: fixed !important; 
#     top: 20px; 
#     right: 20px; 
#     width: 45px !important; 
#     height: 45px !important;
#     z-index: 1000; 
#     font-size: 1.3em;
#     border-radius: 50%; 
#     background-color: {WHATSAPP_GREEN_DARK} !important;
#     border: 2px solid white;
#     box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
#     color: white; 
# }}
# .gr-dataframe {{
#     border-radius: 8px !important;
#     box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
#     border: none !important;
# }}
# .gr-dataframe thead th {{
#     background-color: {WHATSAPP_GREEN_DARK} !important;
#     color: white !important;
# }}
# .gr-dataframe tbody tr td {{
#     background-color: white !important;
# }}
# """

# # ------------------ Components ------------------
# status_output = gr.Textbox(label="Pipeline Status", interactive=False, visible=False)
# run_button = gr.Button("🔄", variant="primary", size="sm", elem_id="float_run_button")

# task_table = gr.Dataframe(
#     headers=["Done", "Task Content", "Sender", "Group", "Date", "Time"],
#     datatype=["bool", "str", "str", "str", "str", "str"],
#     column_count=6,
#     column_widths=[0.5, 4, 2, 2, 1, 1],
#     row_count=10,
#     interactive=True,
#     wrap=True
# )

# # ------------------ Layout ------------------
# with gr.Blocks(title="ChatList Task Processor") as demo:
#     # Branding
#     gr.HTML(f"""
#         <div id="branding-container">
#             <div id="main-header-title">ChatList</div>
#             <div id="main-header-subtitle">Turning Group Chat Chaos into a To-Do Checklist</div>
#         </div>
#     """)

#     # Floating Run Button
#     run_button.render()
#     status_output.render()

#     # Task Table
#     task_table.render()

#     # ------------------ Events ------------------
#     run_button.click(get_processed_tasks_gradio, inputs=None, outputs=task_table)
#     task_table.change(handle_task_done, inputs=[task_table], outputs=[task_table])
#     demo.load(get_processed_tasks_gradio, inputs=None, outputs=task_table)

# # ------------------ Launch ------------------
# if __name__ == "__main__":
#     demo.launch(server_name="127.0.0.1", server_port=8001, css=custom_css)






import uuid
import requests
import streamlit as st
from typing import List

# ==================== CONFIG ====================
API_URL = "http://127.0.0.1:8000/processed_tasks"

WHATSAPP_GREEN_DARK = "#075e54"
WHATSAPP_BACKGROUND = "#e7fce3"  # <<< UPDATED TO MINT GREEN >>> 
TASK_BG = "#FFFFFF"
TASK_BORDER_RADIUS = "12px"

# ==================== UTILS ====================
def get_processed_tasks() -> List[dict]:
    """
    Fetch tasks from the backend (DB / API) and format for Streamlit display.
    Adds a 'done' flag (default False) for checkbox handling.
    """
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            tasks = response.json()
        else:
            tasks = []
    except Exception:
        tasks = []

    processed_tasks = []
    for task in tasks:
        processed_tasks.append({
            "id": str(uuid.uuid4()),        # stable unique ID
            "content": task.get("content", ""),
            "from": task.get("from", ""),
            "group": task.get("group", ""),
            "date": task.get("date", ""),
            "time": task.get("time", ""),
            "done": False                   # for Streamlit checkbox
        })

    return processed_tasks


# ==================== STREAMLIT UI ====================
st.set_page_config(page_title="ChatList Task Processor", layout="wide")

# ---- Custom CSS ----
st.markdown(f"""
<style>

/* <<< NEW GLOBAL MINT GREEN BACKGROUND >>> */
body {{
    background-color: {WHATSAPP_BACKGROUND} !important;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}}
[data-testid="stAppViewContainer"] {{
    background-color: {WHATSAPP_BACKGROUND} !important;
}}
[data-testid="stMain"] {{
    background-color: {WHATSAPP_BACKGROUND} !important;
}}

/* Titles */
.title {{
    color: {WHATSAPP_GREEN_DARK};
    font-weight: 700;
    font-size: 3rem;
    margin-bottom: 0;
}}
.subtitle {{
    color: #444;
    font-size: 1.5rem;
    font-weight: 500;
    margin-top: 4px;
}}

/* <<< NEW SMALLER HEADER >>> */
.task-header-small {{
    font-size: 1.8rem;
    font-weight: 600;
    margin-bottom: 16px;
    color: #333;
}}

.task-header {{
    font-size: 2rem;
    font-weight: 600;
    margin-bottom: 16px;
}}

.empty-message {{
    text-align: center;
    color: #666;
    font-size: 1.5rem;
    padding: 40px 0;
}}

.task-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: {TASK_BORDER_RADIUS};
    background-color: {TASK_BG};
    margin-bottom: 12px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}}

.task-content {{
    font-size: 1.5rem;
    line-height: 2rem;
}}

.task-content small {{
    font-size: 1.2rem;
    color: #555;
}}

.share-link {{
    display: inline-block;
    padding: 6px 10px;
    border-radius: 6px;
    text-decoration: none;
    background: #f2f2f2;
    color: #222;
    margin-right: 8px;
    font-size: 1.2rem;
}}

.share-link:hover {{
    background: #e6e6e6;
}}

</style>
""", unsafe_allow_html=True)


# ---- Branding ----
st.markdown("<div class='title'>ChatList</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Turning Group Chat Chaos into a To-Do Checklist</div>", unsafe_allow_html=True)
st.write("")

# ====================== SESSION STATE ======================
if "tasks" not in st.session_state:
    tasks = get_processed_tasks()
    for t in tasks:
        if "id" not in t:
            t["id"] = str(uuid.uuid4())
    st.session_state.tasks = tasks
else:
    for t in st.session_state.tasks:
        if "id" not in t:
            t["id"] = str(uuid.uuid4())

# ====================== MAIN SCREEN ======================
if not st.session_state.tasks:
    st.markdown("<div class='empty-message'>🎉 No tasks to show — you're all caught up!</div>", unsafe_allow_html=True)

else:
    st.markdown("<div class='task-header-small'>Your Tasks for Today</div>", unsafe_allow_html=True)

    for task in st.session_state.tasks:
        task_id = task["id"]
        cols = st.columns([0.05, 0.95])
        done_col, content_col = cols

        # Checkbox
        with done_col:
            checkbox_key = f"task_done_{task_id}"
            checked = st.checkbox("", key=checkbox_key)

        # Task content in expander
        with content_col:
            with st.expander(task.get("content", "Task")):
                st.markdown(f"""
                <div class='task-row'>
                    <div class='task-content'>
                        <strong>{task.get('content','Untitled Task')}</strong><br>
                        <small>Sender: {task.get('from','N/A')} | Group: {task.get('group','N/A')}</small><br>
                        <small>Date: {task.get('date','N/A')} {task.get('time','N/A')}</small><br>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.write("### Share this task:")
                share_text = f"{task.get('content','Task')}"
                whatsapp_url = f"https://wa.me/?text={share_text.replace(' ', '%20')}"
                google_calendar_url = "https://calendar.google.com"
                family_url = "https://family-app.example.com/share"

                st.markdown(
                    f"""
                    <a class='share-link' href='{whatsapp_url}' target='_blank'>WhatsApp</a>
                    <a class='share-link' href='{google_calendar_url}' target='_blank'>Google Calendar</a>
                    <a class='share-link' href='{family_url}' target='_blank'>Share with Family</a>
                    """,
                    unsafe_allow_html=True
                )

    # Remove checked tasks
    remaining_tasks = []
    removed_any = False
    for task in st.session_state.tasks:
        key = f"task_done_{task['id']}"
        if st.session_state.get(key, False):
            removed_any = True
        else:
            remaining_tasks.append(task)

    if removed_any:
        st.session_state.tasks = remaining_tasks

        for k in list(st.session_state.keys()):
            if k.startswith("task_done_"):
                del st.session_state[k]

        st.rerun()
