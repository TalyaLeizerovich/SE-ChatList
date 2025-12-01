import json
import os
import sys
import gradio as gr
from typing import List, Dict
import pandas as pd

# ==================== FIX: PATH & IMPORTS ====================
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

import backend.db as db


# ==================== Configuration & Styling ====================
WHATSAPP_GREEN_DARK = "#075e54"
WHATSAPP_BACKGROUND = "#F0F0F0"


# ==================== Core Logic Functions ====================

def load_tasks() -> List[List[str]]:
    """Load tasks from DB and format for table."""
    try:
        tasks: List[Dict] = db.get_tasks_from_db()
    except Exception:
        tasks = []

    table = []
    for t in tasks:
        time_display = t.get("time", "N/A")[:5] if t.get("time") else "N/A"
        table.append([
            False,
            t.get("content", ""),
            t.get("from", ""),
            t.get("group", ""),
            t.get("date", ""),
            time_display,
            t.get("id", "")  # hidden ID column
        ])
    return table


def mark_task_done(table):
    """Remove rows where 'Done' = True."""
    if table.empty:
        return []

    new_df = table[table.iloc[:, 0] != True]
    return new_df.values.tolist()


def delete_selected_task(table):
    try:
        df = pd.DataFrame(table)
        target_row = df[df.iloc[:, 0] == True]

        if len(target_row) == 0:
            return table, "No task selected for deletion"

        task_id = target_row.iloc[0, 6]
        db.delete_task(task_id)

        df = df[df.iloc[:, 0] != True]
        return df.values.tolist(), "Task deleted"

    except Exception as e:
        return table, f"Error deleting task: {e}"


def refresh():
    return load_tasks()


# ==================== Gradio UI CSS ====================

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
        line-height: 1; 
    }}
    #main-header-subtitle {{
        color: #444; 
        font-size: 0.9rem;
        font-weight: 500;
        margin-top: 5px; 
    }}

    #float_refresh_button {{
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
    #pipeline_control_panel {{ display: none !important; }}
    
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


# ==================== Gradio UI Components ====================

status = gr.Textbox(label="Status", visible=False)

refresh_button = gr.Button("🔄", elem_id="float_refresh_button")

task_table = gr.Dataframe(
    headers=["Done", "Task Content", "Sender", "Group", "Date", "Time", "ID"],
    datatype=["bool", "str", "str", "str", "str", "str", "str"],
    column_widths=[1, 4, 2, 2, 1, 1, 0.01],
    interactive=True,
    visible=True,
    wrap=True
)


# ==================== Layout ====================

with gr.Blocks(title="ChatList Task Viewer") as demo:

    gr.HTML(
        f"""
        <div id="branding-container">
            <div id="main-header-title">ChatList Viewer</div>
            <div id="main-header-subtitle">Viewing tasks loaded from the Backend</div>
        </div>
        """
    )

    refresh_button.render()

    with gr.Row():
        gr.Column(scale=1)
        with gr.Column(scale=4):
            task_table.render()
        gr.Column(scale=1)

    refresh_button.click(refresh, outputs=task_table)

    task_table.change(
        fn=mark_task_done,
        inputs=[task_table],
        outputs=[task_table]
    )

    demo.load(load_tasks, outputs=[task_table])


# ==================== Run App ====================

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", css=custom_css)
