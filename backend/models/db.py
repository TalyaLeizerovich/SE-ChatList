from altair import Dict
import pyodbc
from datetime import datetime
import re

# --- Connect to SOMEE DB ---
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=ChatListDB.mssql.somee.com;"
    "UID=Talya_L_SQLLogin_1;"
    "PWD=vryyr46iae;"
    "Encrypt=no;"
    "TrustServerCertificate=yes;"
    "Connection Timeout=30;"
    "DATABASE=ChatListDB;"
)

def is_empty_or_invalid_content(content):
    if content is None or content == "":
        return True
    
    content_lower = content.strip().lower()
    
    invalid_phrases = [
        "none", "no task", "no actionable task", "there is no task",
        "there is no actionable task", "no action required",
        "not a task", "not actionable", "n/a",
    ]
    
    for phrase in invalid_phrases:
        if phrase in content_lower:
            return True
    
    if re.match(r'^none[.,!?\s]*$', content_lower):
        return True
    
    return False

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
    # הוספת שליפת הקטגוריה מהמילון
    category = task.get("category", "General") 

    if is_empty_or_invalid_content(content):
        return {"status": "skipped", "message": "Task with empty or None content was not added to DB."}

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

        # עדכון השאילתה להכלת עמודת category
        insert_query = """
        INSERT INTO Tasks (content, date, time, sender_name, group_name, category)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_query, content, date_obj, time_obj, sender_name, group_name, category)
        conn.commit()

        cursor.close()
        conn.close()

        return {"status": "success", "message": "Task added to DB."}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_tasks_from_db() -> list[Dict]:
    """
    Retrieves all tasks from the SOMEE SQL Server DB and formats them 
    as a list of dictionaries for the Gradio frontend.
    """
    conn = None
    tasks = []
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # הוספת category לשאילתת ה-SELECT
        select_query = """
        SELECT content, date, time, sender_name, group_name, category
        FROM Tasks
        ORDER BY date DESC, time DESC
        """
        cursor.execute(select_query)
        rows = cursor.fetchall()

        for row in rows:
            date_str = row[1].strftime("%Y-%m-%d") if row[1] else "N/A"
            time_str = row[2].strftime("%H:%M:%S") if row[2] else "N/A"
            
            tasks.append({
                "content": row[0],
                "date": date_str,
                "time": time_str,
                "from": row[3],
                "group": row[4],
                "category": row[5] if row[5] else "General"  # טיפול בערכי NULL ישנים
            })

        cursor.close()
        conn.close()
        return tasks

    except pyodbc.Error as e:
        print(f"SQL Error fetching tasks: {e}")
        return []
    except Exception as e:
        print(f"General Error fetching tasks: {e}")
        return []
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

def delete_task_from_db(task):
    """
    Deletes a task from the Tasks table based on all identifying fields.
    """
    content = task.get("content", "")
    date_str = task.get("date", "")
    time_str = task.get("time", "")
    sender_name = task.get("from", "")
    group_name = task.get("group", "")
    category = task.get("category", "")

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
    except:
        date_obj = None

    try:
        time_obj = datetime.strptime(time_str, "%H:%M:%S").time() if time_str else None
    except:
        time_obj = None

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # הוספנו את category ל-WHERE כדי לוודא מחיקה מדויקת
        delete_query = """
        DELETE FROM Tasks
        WHERE content = ? AND date = ? AND time = ? AND sender_name = ? AND group_name = ? AND (category = ? OR category IS NULL)
        """
        cursor.execute(delete_query, content, date_obj, time_obj, sender_name, group_name, category)
        conn.commit()

        cursor.close()
        conn.close()
        return {"status": "success", "message": "Task deleted from DB."}

    except Exception as e:
        return {"status": "error", "message": str(e)} 

def get_last_task_timestamp():
    """
    Returns datetime of the latest task in DB (date + time).
    """
    conn = None
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        query = """
        SELECT MAX(CAST(date AS DATETIME) + CAST(time AS DATETIME))
        FROM Tasks
        """
        cursor.execute(query)
        result = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return result 

    except Exception as e:
        print(f"Error fetching last task timestamp: {e}")
        return None