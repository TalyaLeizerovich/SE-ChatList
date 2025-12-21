import uuid
import requests
import streamlit as st
from typing import List, Dict
import urllib.parse

# ==================== CONFIG ====================
API_URL = "http://127.0.0.1:8000/processed_tasks"
API_DELETE_URL = "http://127.0.0.1:8000/delete_tasks"
API_REFRESH_URL = "http://127.0.0.1:8000/refresh"

WHATSAPP_GREEN_DARK = "#075e54"
WHATSAPP_BACKGROUND = "#e7fce3"
TASK_BG = "#FFFFFF"
TASK_BORDER_RADIUS = "12px"
CATEGORY_BADGE_BG = "#dcf8c6" 

is_view_only = st.query_params.get("view_only") == "true"

# ==================== UTILS ====================
def get_processed_tasks() -> List[dict]:
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            tasks = response.json()
        else:
            tasks = []
    except Exception as e:
        if not is_view_only:
            st.error(f"Could not connect to Backend: {e}")
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
            "category": task.get("category", "General"),
            "done": False
        })
    return processed_tasks

def sort_tasks(tasks: List[dict], sort_option: str) -> List[dict]:
    if sort_option == "Date":
        return sorted(tasks, key=lambda t: t.get("date", ""))
    if sort_option == "Time":
        return sorted(tasks, key=lambda t: t.get("time", ""))
    return tasks

def delete_task_via_api(task: dict) -> dict:
    try:
        response = requests.post(API_DELETE_URL, json=task, timeout=5)
        return response.json() if response.status_code == 200 else {"status": "error"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def refresh_new_tasks() -> dict:
    try:
        response = requests.post(API_REFRESH_URL, timeout=180)
        return response.json() if response.status_code == 200 else {"status": "error"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==================== STREAMLIT UI ====================
st.set_page_config(page_title="ChatList Task Processor", layout="wide")

st.markdown(f"""
<style>
    body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
        background-color: {WHATSAPP_BACKGROUND} !important;
    }}
    .title {{ color: {WHATSAPP_GREEN_DARK}; font-weight: 700; font-size: 2.5rem; margin-bottom: 0; }}
    .subtitle {{ color: #444; font-size: 1.1rem; font-weight: 500; margin-top: 2px; }}
    
    .category-header {{
        background-color: {WHATSAPP_GREEN_DARK};
        color: white;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 15px 0 8px 0;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .task-row {{
        display: flex;
        flex-direction: column;
        padding: 12px 16px;
        border-radius: {TASK_BORDER_RADIUS};
        background-color: {TASK_BG};
        margin-bottom: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .category-badge {{
        background-color: {CATEGORY_BADGE_BG};
        color: #075e54;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        text-transform: uppercase;
    }}
    .share-link {{
        display: inline-block;
        padding: 6px 10px;
        border-radius: 6px;
        text-decoration: none;
        background: #f2f2f2;
        color: #222;
        margin-right: 8px;
        font-size: 0.9rem;
    }}
    
    div[data-testid="stButton"] > button {{
        border: 1.5px solid {WHATSAPP_GREEN_DARK} !important;
        color: {WHATSAPP_GREEN_DARK} !important;
        padding: 2px 10px !important;
        font-size: 0.8rem !important;
        height: auto !important;
        width: auto !important;
    }}
</style>
""", unsafe_allow_html=True)

header_col, refresh_col = st.columns([0.85, 0.15])

with header_col:
    st.markdown("<div class='title'>ChatList</div>", unsafe_allow_html=True)
    if is_view_only:
        st.markdown("<div class='subtitle'>📖 View-Only Mode</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='subtitle'>Turning Group Chat Chaos into a To-Do Checklist</div>", unsafe_allow_html=True)

if not is_view_only:
    with refresh_col:
        st.write("<div style='padding-top: 15px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh"):
            with st.spinner("Syncing..."):
                result = refresh_new_tasks()
                if result.get("status") == "success":
                    st.session_state.tasks = get_processed_tasks()
                    st.rerun()

# ---- SESSION STATE ----
if "tasks" not in st.session_state:
    st.session_state.tasks = get_processed_tasks()

# ====================== MAIN SCREEN ======================
if not st.session_state.tasks:
    st.markdown("<div style='text-align: center; padding: 50px;'><h3>🎉 All caught up!</h3></div>", unsafe_allow_html=True)
else:
    all_categories = sorted(list(set(t["category"] for t in st.session_state.tasks if t.get("category"))))
    
    col_sort, _ = st.columns([0.2, 0.8])
    with col_sort:
        sort_option = st.selectbox("Sort by:", ["Date", "Time"])

    for cat in all_categories:
        st.markdown(f"<div class='category-header'>{cat}</div>", unsafe_allow_html=True)
        
        cat_tasks = [t for t in st.session_state.tasks if t["category"] == cat]
        cat_tasks = sort_tasks(cat_tasks, sort_option)

        for task in cat_tasks:
            task_id = task["id"]
            
            if is_view_only:
                content_col = st.container()
            else:
                cols = st.columns([0.04, 0.96])
                with cols[0]:
                    if st.checkbox("", key=f"task_done_{task_id}"):
                        delete_task_via_api(task)
                        st.session_state.tasks = [t for t in st.session_state.tasks if t["id"] != task_id]
                        st.rerun()
                content_col = cols[1]

            with content_col:
                with st.expander(task['content']):
                    st.markdown(f"""
                    <div class='task-row'>
                        <div><span class='category-badge'>{task['category']}</span></div>
                        <div style='font-size: 1.1rem; margin-top: 8px;'><strong>{task['content']}</strong></div>
                        <div style='color: #666; font-size: 0.9rem;'>
                            👤 From: {task['from']} | 👥 Group: {task['group']}<br>
                            📅 Date: {task['date']} | ⏰ Time: {task['time']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if not is_view_only:
                        view_only_link = "http://localhost:8501/?view_only=true"
                        
                        share_text = (
                            "Hey! Just wanted to share this task with you:\n\n"
                            f"Task: {task['content']}\n"
                            f"Category: {task['category']}\n\n"
                            f"Want to watch my full task list? Click here: {view_only_link}"
                        )
                        
                        encoded_share_text = urllib.parse.quote(share_text)
                        
                        st.markdown(f"""
                            <a class='share-link' href='https://wa.me/?text={encoded_share_text}' target='_blank'>WhatsApp</a>
                            <a class='share-link' href='https://calendar.google.com' target='_blank'>Google Calendar</a>
                        """, unsafe_allow_html=True)