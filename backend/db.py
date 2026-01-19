
from altair import Dict
import pyodbc
from datetime import datetime
import re
from encryption_utils import encrypt_text, decrypt_text

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

def task_exists(cursor, encrypted_content):
    query = """
    SELECT COUNT(*) FROM Tasks
    WHERE content = ?
    """
    cursor.execute(query, (encrypted_content,))
    count = cursor.fetchone()[0]
    return count > 0

def save_task_to_db(task):
    content = task.get("content", "")
    date_str = task.get("date", "")
    time_str = task.get("time", "")
    sender_name = task.get("from", "")
    group_name = task.get("group", "")
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

    encrypted_content = encrypt_text(content)

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        if task_exists(cursor, encrypted_content):
            cursor.close()
            conn.close()
            return {"status": "skipped", "message": "Task already exists in DB."}
        
        insert_query = """
        INSERT INTO Tasks (content, date, time, sender_name, group_name, category)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_query, encrypted_content, date_obj, time_obj, sender_name, group_name, category)
        conn.commit()

        cursor.close()
        conn.close()

        return {"status": "success", "message": "Task added to DB."}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_tasks_from_db() -> list[Dict]:
    conn = None
    tasks = []
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        select_query = """
        SELECT task_id, content, date, time, sender_name, group_name, category
        FROM Tasks
        ORDER BY date DESC, time DESC
        """
        cursor.execute(select_query)
        rows = cursor.fetchall()

        for row in rows:
            date_str = row[2].strftime("%Y-%m-%d") if row[2] else "N/A"
            time_str = row[3].strftime("%H:%M:%S") if row[3] else "N/A"
            
            encrypted_content = row[1]
            decrypted_content = decrypt_text(encrypted_content) if encrypted_content else ""
            
            tasks.append({
                "id": row[0],  
                "content": decrypted_content,
                "date": date_str,
                "time": time_str,
                "from": row[4],
                "group": row[5],
                "category": row[6] if row[6] else "General"
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
    task_id = task.get("id", None)
    
    if task_id is None:
        return {"status": "error", "message": "Task ID is required for deletion"}

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        delete_query = """
        DELETE FROM Tasks
        WHERE task_id = ?
        """
        cursor.execute(delete_query, task_id)
        conn.commit()

        cursor.close()
        conn.close()
        return {"status": "success", "message": "Task deleted from DB."}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_last_task_timestamp():
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

def get_task_by_id(task_id: int):
    conn = None
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        query = """
        SELECT content, date, time, sender_name, group_name, category
        FROM Tasks
        WHERE task_id = ?
        """
        cursor.execute(query, (task_id,))
        row = cursor.fetchone()
        
        if row:
            date_str = row[1].strftime("%Y-%m-%d") if row[1] else "N/A"
            time_str = row[2].strftime("%H:%M:%S") if row[2] else "N/A"
            
            encrypted_content = row[0]
            decrypted_content = decrypt_text(encrypted_content) if encrypted_content else ""
            
            return {
                "id": task_id,
                "content": decrypted_content,
                "date": date_str,
                "time": time_str,
                "from": row[3],
                "group": row[4],
                "category": row[5] if row[5] else "General"
            }
        
        cursor.close()
        conn.close()
        return None
        
    except Exception as e:
        print(f"Error fetching task by ID: {e}")
        return None
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

def truncate_tasks_table():
    conn = None
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        cursor.execute("TRUNCATE TABLE Tasks")
        conn.commit()

        cursor.close()
        conn.close()
        print("Tasks table truncated successfully")

    except Exception as e:
        print(f"Error truncating Tasks table: {e}")

    finally:
        if conn:
            try:
                conn.close()
            except:
                pass