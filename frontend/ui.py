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

# Import existing modules
import backend.processing as processing 
import backend.db as db

# ==================== Configuration & Styling ====================
RAW_MESSAGES_FILE = "C:/softwareEngineer/ChatList/backend/raw_messages.json"
PROCESSED_MESSAGES_FILE = "C:/softwareEngineer/ChatList/backend/processed_messages.json"

# --- WHATSAPP COLOR PALETTE (Clean, solid colors) ---
WHATSAPP_GREEN_DARK = "#075e54"      
WHATSAPP_BACKGROUND = "#F0F0F0"     # Light gray/off-white background

# --- NOTE: Removed image path variables and base64 logic ---

# ==================== Core Backend Functions for Gradio ====================

def ensure_processed_file_exists():
    """Create the processed_messages.json as an empty list if it's missing."""
    try:
        directory = os.path.dirname(PROCESSED_MESSAGES_FILE)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        if not os.path.exists(PROCESSED_MESSAGES_FILE):
            with open(PROCESSED_MESSAGES_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise
ensure_processed_file_exists()

def run_complete_pipeline_gradio() -> str:
    """Runs the processing pipeline and returns a status message."""
    try:
        processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)
        
        with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
            tasks_count = len(tasks)
        
        added, skipped, errors = 0, 0, 0
        for task in tasks:
            result = db.save_task_to_db(task)
            if result["status"] == "success": added += 1
            elif result["status"] == "skipped": skipped += 1
            else: errors += 1
        
        return f"✅ SUCCESS: Pipeline executed. Tasks processed: {tasks_count}."
    except Exception as e:
        return f"❌ ERROR during pipeline execution: {str(e)}"

def get_processed_tasks_gradio() -> List[List[str]]:
    """Loads tasks and formats them for Gradio's Dataframe/Table component."""
    ensure_processed_file_exists()
    try:
        with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
            tasks: List[Dict] = json.load(f)
    except Exception:
        tasks = []

    table_data = []
    for task in tasks:
        display_time = task.get("time", "N/A")[:5] if task.get("time") else "N/A"
        
        table_data.append([
            False, # Status column (Checkbox)
            task.get("content", ""),
            task.get("from", ""),
            task.get("group", ""),
            task.get("date", ""),
            display_time
        ])
    return table_data

def handle_task_done(tasks_table_data):
    """
    Removes a task from the display list if the user marks it as 'Done'.
    tasks_table_data is now a pandas DataFrame.
    """
    # 1. Check if DataFrame is empty using .empty
    if tasks_table_data.empty:
        return []
    
    # 2. Filter out rows where the 'Done' column (column index 0) is True
    # We must explicitly convert the DataFrame back to the List[List] format 
    # that Gradio expects as the return type for the Dataframe component.
    
    # Filter rows where the first column (index 0) is NOT True (i.e., not marked as done)
    new_df = tasks_table_data[tasks_table_data.iloc[:, 0] != True]
    
    # Convert the resulting DataFrame back to the list-of-lists structure for Gradio
    return new_df.values.tolist()

# ==================== Gradio UI Interface ====================

# --------------------------------------------------
# 1. Custom CSS for Clean Design and Floating Button
# --------------------------------------------------
custom_css = f"""
    /* --- FONT and CLEAN BACKGROUND --- */
    .gradio-container, body {{
        background-color: {WHATSAPP_BACKGROUND} !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }}
    
    /* --- Branding & Title Styling (Simplified) --- */
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

    /* --- Floating Button (Top Right) --- */
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
    /* Hide the original control panel entirely */
    #pipeline_control_panel {{ display: none !important; }}

    /* --- Task List Item Styling (Dataframe) --- */
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
        background-color: white !important; /* Solid white background for tasks */
    }}
"""

# --------------------------------------------------
# 2. Define Components
# --------------------------------------------------
status_output = gr.Textbox(label="Pipeline Status", interactive=False, elem_id="status_box", visible=False)
run_button = gr.Button("🔄", variant="primary", size="sm", elem_id="float_run_button") 

task_table = gr.Dataframe(
    headers=["Done", "Task Content", "Sender", "Group", "Date", "Time"],
    datatype=["bool", "str", "str", "str", "str", "str"], 
    column_count=6, 
    column_widths=[0.5, 4, 2, 2, 1, 1], 
    row_count=10,
    label="", 
    interactive=True, 
    wrap=True
)

# --------------------------------------------------
# 3. Define UI Layout
# --------------------------------------------------
with gr.Blocks(
    title="ChatList Task Processor"
) as demo:
    
    # 1. Branding (Top Left Corner) - Simplified HTML without image
    gr.HTML(
        f"""
        <div id="branding-container">
            <div id="main-header-title">ChatList</div>
            <div id="main-header-subtitle">Turning Group Chat Chaos into a To-Do Checklist</div>
        </div>
        """
    )

    # 2. Floating Button Control (Top Right) - HIDDEN PANEL
    # The button remains functional via CSS
    with gr.Row(elem_id="pipeline_control_panel"):
        gr.Column(run_button.render(), scale=1) 
        gr.Column(status_output.render(), scale=4) 
        
    # 3. Task Display (Centered content)
    with gr.Row():
        gr.Column(scale=1) # Spacer Left
        with gr.Column(scale=4): # Main Content Area
            task_table.render()
        gr.Column(scale=1) # Spacer Right
    
    # --- EVENT HANDLERS ---
    
    run_button.click(
        fn=run_complete_pipeline_gradio, 
        inputs=[],
        outputs=status_output 
    ).then(
        fn=get_processed_tasks_gradio, 
        inputs=[],
        outputs=task_table
    )
    
    task_table.change(
        fn=handle_task_done,
        inputs=[task_table],
        outputs=[task_table]
    )
    
    demo.load(get_processed_tasks_gradio, inputs=None, outputs=task_table)

# Run the app
if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=8000, css=custom_css)