import pyodbc
import json
from datetime import datetime

# --- Connect to SOMEE DB ---
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=ChatListDB.mssql.somee.com;"
        "UID=Talya_L_SQLLogin_1;"
        "PWD=vryyr46iae;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
        "DATABASE=ChatListDB;"
)

def task_exists(cursor, content, date_obj, time_obj, sender_name, group_name):
    """Checks if a task with the same details already exists"""
    query = """
    SELECT COUNT(*) FROM Tasks
    WHERE content = ? AND date = ? AND time = ? AND sender_name = ? AND group_name = ?
    """
    cursor.execute(query, content, date_obj, time_obj, sender_name, group_name)
    count = cursor.fetchone()[0]
    return count > 0

def save_task_to_db(task):
    content = task.get("content", "")
    date_str = task.get("date", "")
    time_str = task.get("time", "")
    sender_name = task.get("from", "")
    group_name = task.get("group", "")

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        date_obj = None

    try:
        time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
    except:
        time_obj = None

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Check if task already exists
        if task_exists(cursor, content, date_obj, time_obj, sender_name, group_name):
            cursor.close()
            conn.close()
            return {"status": "skipped", "message": "Task already exists in DB."}

        # Insert task into table
        insert_query = """
        INSERT INTO Tasks (content, date, time, sender_name, group_name)
        VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(insert_query, content, date_obj, time_obj, sender_name, group_name)
        conn.commit()

        cursor.close()
        conn.close()

        return {"status": "success", "message": "Task added to DB."}

    except Exception as e:
        return {"status": "error", "message": str(e)}



