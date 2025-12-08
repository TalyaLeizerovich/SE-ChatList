import os
import sys
import json
import gradio as gr
import pandas as pd
import requests
from typing import List

# ==================== FIX: PATH ====================
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

# ==================== CONFIG ====================
API_URL = "http://127.0.0.1:8000/processed_tasks"

WHATSAPP_GREEN_DARK = "#075e54"      
WHATSAPP_BACKGROUND = "#F0F0F0"

# ==================== UTILS ====================
def get_processed_tasks_gradio() -> List[List[str]]:
    """Fetch tasks from backend via GET request and format for Gradio Dataframe."""
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            tasks = response.json()
        else:
            tasks = []
    except Exception:
        tasks = []

    table_data = []
    for task in tasks:
        display_time = task.get("time", "N/A")[:5] if task.get("time") else "N/A"
        table_data.append([
            False,  # Checkbox for "Done"
            task.get("content", ""),
            task.get("from", ""),
            task.get("group", ""),
            task.get("date", ""),
            display_time
        ])
    return table_data

def handle_task_done(tasks_table_data):
    """Remove tasks marked as Done from display."""
    if isinstance(tasks_table_data, pd.DataFrame):
        # Keep rows where first column (Done) is not True
        new_df = tasks_table_data[tasks_table_data.iloc[:, 0] != True]
        return new_df.values.tolist()
    return tasks_table_data

# ==================== GRADIO UI ====================
custom_css = f"""
.gradio-container, body {{
    background-color: {WHATSAPP_BACKGROUND} !important;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
}}
#branding-container {{
    display: block;
    margin-bottom: 20px; 
}}
#main-header-title {{
    color: {WHATSAPP_GREEN_DARK};
    font-weight: 700;
    font-size: 1.8rem; 
}}
#main-header-subtitle {{
    color: #444; 
    font-size: 0.9rem;
    font-weight: 500;
    margin-top: 5px; 
}}
#float_run_button {{
    position: fixed !important; 
    top: 20px; 
    right: 20px; 
    width: 45px !important; 
    height: 45px !important;
    z-index: 1000; 
    font-size: 1.3em;
    border-radius: 50%; 
    background-color: {WHATSAPP_GREEN_DARK} !important;
    border: 2px solid white;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    color: white; 
}}
.gr-dataframe {{
    border-radius: 8px !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    border: none !important;
}}
.gr-dataframe thead th {{
    background-color: {WHATSAPP_GREEN_DARK} !important;
    color: white !important;
}}
.gr-dataframe tbody tr td {{
    background-color: white !important;
}}
"""

# ------------------ Components ------------------
status_output = gr.Textbox(label="Pipeline Status", interactive=False, visible=False)
run_button = gr.Button("🔄", variant="primary", size="sm", elem_id="float_run_button")

task_table = gr.Dataframe(
    headers=["Done", "Task Content", "Sender", "Group", "Date", "Time"],
    datatype=["bool", "str", "str", "str", "str", "str"],
    column_count=6,
    column_widths=[0.5, 4, 2, 2, 1, 1],
    row_count=10,
    interactive=True,
    wrap=True
)

# ------------------ Layout ------------------
with gr.Blocks(title="ChatList Task Processor") as demo:
    # Branding
    gr.HTML(f"""
        <div id="branding-container">
            <div id="main-header-title">ChatList</div>
            <div id="main-header-subtitle">Turning Group Chat Chaos into a To-Do Checklist</div>
        </div>
    """)

    # Floating Run Button
    run_button.render()
    status_output.render()

    # Task Table
    task_table.render()

    # ------------------ Events ------------------
    run_button.click(get_processed_tasks_gradio, inputs=None, outputs=task_table)
    task_table.change(handle_task_done, inputs=[task_table], outputs=[task_table])
    demo.load(get_processed_tasks_gradio, inputs=None, outputs=task_table)

# ------------------ Launch ------------------
if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=8001, css=custom_css)
