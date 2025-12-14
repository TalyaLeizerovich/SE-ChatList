import uuid
import requests
import streamlit as st
from typing import List

# ==================== CONFIG ====================
API_URL = "http://127.0.0.1:8000/processed_tasks"
API_DELETE_URL = "http://127.0.0.1:8000/delete_tasks"
API_REFRESH_URL = "http://127.0.0.1:8000/refresh"


WHATSAPP_GREEN_DARK = "#075e54"
WHATSAPP_BACKGROUND = "#e7fce3"
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
            "id": str(uuid.uuid4()),
            "content": task.get("content", ""),
            "from": task.get("from", ""),
            "group": task.get("group", ""),
            "date": task.get("date", ""),
            "time": task.get("time", ""),
            "done": False
        })

    return processed_tasks

def delete_task_via_api(task: dict) -> dict:
    """
    Deletes the given task by calling the backend API.
    Expects the backend to handle deletion by task details.
    """
    try:
        response = requests.post(API_DELETE_URL, json=task, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": f"API returned {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def refresh_new_tasks() -> dict:
    """
    Calls the /refresh endpoint to check for new messages from WhatsApp.
    Returns the result including how many new tasks were found.
    """
    try:
        response = requests.post(API_REFRESH_URL, timeout=120)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": f"API returned {response.status_code}"}
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "The process took too long. Please try again."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==================== STREAMLIT UI ====================
st.set_page_config(page_title="ChatList Task Processor", layout="wide")

# ---- Custom CSS ----
st.markdown(f"""
<style>

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

/* כפתור רענון שקוף עם מסגרת */
div[data-testid="stButton"] > button {{
    background-color: transparent !important;
    border: 2px solid {WHATSAPP_GREEN_DARK} !important;
    color: {WHATSAPP_GREEN_DARK} !important;
    font-weight: 600 !important;
}}

div[data-testid="stButton"] > button:hover {{
    background-color: rgba(7, 94, 84, 0.1) !important;
    border: 2px solid {WHATSAPP_GREEN_DARK} !important;
}}

</style>
""", unsafe_allow_html=True)


# ---- Branding ----
st.markdown("<div class='title'>ChatList</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Turning Group Chat Chaos into a To-Do Checklist</div>", unsafe_allow_html=True)
st.write("")

# ====================== REFRESH BUTTON ======================
col1, col2 = st.columns([0.85, 0.15])

with col2:
    if st.button("🔄 refrash tasks", use_container_width=True):
        with st.spinner("Checking for new messages on WhatsApp... (This may take up to 2 minutes)"):
            result = refresh_new_tasks()
            
            if result.get("status") == "success":
                new_count = result.get("new_tasks_found", 0)
                if new_count > 0:
                    st.success(f"✅ Found {new_count} new tasks!")
                else:
                    st.info("ℹ️ No new tasks found")
                
                # Reload tasks from DB
                st.session_state.tasks = get_processed_tasks()
                st.rerun()
            else:
                st.error(f"❌ Error: {result.get('message', 'Unknown error')}")

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
            # Delete from DB
            delete_task_via_api(task)
        else:
            remaining_tasks.append(task)

    if removed_any:
        st.session_state.tasks = remaining_tasks

        for k in list(st.session_state.keys()):
            if k.startswith("task_done_"):
                del st.session_state[k]

        st.rerun()