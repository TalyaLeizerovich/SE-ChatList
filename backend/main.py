# import json
# import sys
# import os
# from datetime import datetime
# import uvicorn
# from fastapi import FastAPI, HTTPException

# # Import existing modules
# import processing
# import db

# # ==================== Configuration ====================
# RAW_MESSAGES_FILE = "C:/softwareEngineer/ChatList/backend/raw_messages.json"
# PROCESSED_MESSAGES_FILE = "C:/softwareEngineer/ChatList/backend/processed_messages.json"

# # --------------------
# # Ensure processed JSON exists (minimal change)
# # --------------------
# def ensure_processed_file_exists():
#     """
#     Create the processed_messages.json as an empty list if it's missing.
#     Minimal, safe and silent fix to avoid FileNotFoundError on first run.
#     """
#     try:
#         directory = os.path.dirname(PROCESSED_MESSAGES_FILE)
#         if directory and not os.path.exists(directory):
#             os.makedirs(directory, exist_ok=True)
#         if not os.path.exists(PROCESSED_MESSAGES_FILE):
#             # File doesn't exist, create empty JSON list
#             with open(PROCESSED_MESSAGES_FILE, "w", encoding="utf-8") as f:
#                 json.dump([], f, ensure_ascii=False, indent=2)
#     except Exception as e:
#         # If creation fails, raise exception to prevent silent failure
#         raise

# # Call it once on module import so main.py can be run as-is
# ensure_processed_file_exists()

# # ==================== FastAPI App ====================
# app = FastAPI(
#     title="ChatList Task Processor",
#     description="Process WhatsApp messages and load tasks to database",
#     version="1.0.0"
# )

# @app.get("/")
# def root():
#     """API root - health check"""
#     return {
#         "status": "running",
#         "message": "ChatList Task Processor API",
#         "endpoints": {
#             "process": "/process - Process raw messages",
#             "load_db": "/load-db - Load processed tasks to database",
#             "run_all": "/run-all - Run complete pipeline",
#             "health": "/health - Health check"
#         }
#     }

# @app.get("/health")
# def health_check():
#     """Health check endpoint"""
#     return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# @app.post("/process")
# def process_messages():
#     """Process raw messages using processing.py"""
#     try:
#         # Call processing.py function
#         processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)
        
#         # Count results
#         if os.path.exists(PROCESSED_MESSAGES_FILE):
#             with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
#                 tasks = json.load(f)
#                 tasks_count = len(tasks)
#         else:
#             tasks_count = 0
        
#         # Return API response
#         return {
#             "status": "success",
#             "message": "Messages processed successfully",
#             "details": {
#                 "output_file": PROCESSED_MESSAGES_FILE,
#                 "tasks_found": tasks_count
#             }
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/load-db")
# def load_to_database():
#     """Load processed messages to database using db.py"""
#     try:
#         # ensure file exists
#         ensure_processed_file_exists()
#         if not os.path.exists(PROCESSED_MESSAGES_FILE):
#             raise FileNotFoundError(f"Processed file not found: {PROCESSED_MESSAGES_FILE}")
        
#         # Read processed tasks
#         with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
#             tasks = json.load(f)
        
#         # Initialize counters
#         added = 0
#         skipped = 0
#         errors = 0
        
#         # Loop through tasks and save to database
#         for task in tasks:
#             result = db.save_task_to_db(task)
            
#             if result["status"] == "success":
#                 added += 1
#             elif result["status"] == "skipped":
#                 skipped += 1
#             else:
#                 errors += 1
        
#         # Return API response
#         return {
#             "status": "success",
#             "message": "Tasks loaded to database successfully",
#             "details": {
#                 "total_tasks": len(tasks),
#                 "added": added,
#                 "skipped": skipped,
#                 "errors": errors
#             }
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/run-all")
# def run_complete_pipeline():
#     """Run complete pipeline: processing.py + db.py"""
#     try:
#         # Step 1: Process messages
#         processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)
        
#         # Count processed tasks
#         with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
#             tasks = json.load(f)
#             tasks_count = len(tasks)
        
#         # Step 2: Load to DB
#         added = 0
#         skipped = 0
#         errors = 0
        
#         for task in tasks:
#             result = db.save_task_to_db(task)
            
#             if result["status"] == "success":
#                 added += 1
#             elif result["status"] == "skipped":
#                 skipped += 1
#             else:
#                 errors += 1
        
#         # Return API response
#         return {
#             "status": "success",
#             "message": "Complete pipeline executed successfully",
#             "details": {
#                 "processing": {
#                     "output_file": PROCESSED_MESSAGES_FILE,
#                     "tasks_found": tasks_count
#                 },
#                 "database": {
#                     "total_tasks": tasks_count,
#                     "added": added,
#                     "skipped": skipped,
#                     "errors": errors
#                 }
#             }
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# # ==================== CLI Commands ====================
# def cli_process():
#     """CLI: Process messages using processing.py"""
#     try:
#         processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)
#     except Exception as e:
#         sys.exit(1)

# def cli_load_db():
#     """CLI: Load to database using db.py"""
#     try:
#         ensure_processed_file_exists()
#         if not os.path.exists(PROCESSED_MESSAGES_FILE):
#             raise FileNotFoundError(f"Processed file not found: {PROCESSED_MESSAGES_FILE}")
        
#         with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
#             tasks = json.load(f)
        
#         added = 0
#         skipped = 0
#         errors = 0
        
#         for task in tasks:
#             result = db.save_task_to_db(task)
            
#             if result["status"] == "success":
#                 added += 1
#             elif result["status"] == "skipped":
#                 skipped += 1
#             else:
#                 errors += 1
#     except Exception as e:
#         sys.exit(1)

# def cli_run_all():
#     """CLI: Run complete pipeline using processing.py + db.py"""
#     try:
#         # Step 1: Process messages
#         processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)
        
#         # Step 2: Load to DB
#         ensure_processed_file_exists()
#         with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
#             tasks = json.load(f)
        
#         added = 0
#         skipped = 0
#         errors = 0
        
#         for task in tasks:
#             result = db.save_task_to_db(task)
            
#             if result["status"] == "success":
#                 added += 1
#             elif result["status"] == "skipped":
#                 skipped += 1
#             else:
#                 errors += 1
#     except Exception as e:
#         sys.exit(1)

# def cli_serve():
#     """CLI: Start FastAPI server"""
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

# def print_help():
#     """Print CLI help message"""
#     # Removed all prints, just a docstring placeholder
#     pass

# # ==================== Main Entry Point ====================
# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         print_help()
#         sys.exit(0)
    
#     command = sys.argv[1].lower()
    
#     if command == "process":
#         cli_process()
#     elif command == "load-db":
#         cli_load_db()
#     elif command == "run-all":
#         cli_run_all()
#     elif command == "serve":
#         cli_serve()
#     elif command == "help":
#         print_help()
#     else:
#         sys.exit(1)




import json
import sys
import os
from datetime import datetime
import uvicorn
from fastapi import FastAPI, HTTPException

# Import existing modules
import processing
import db

# ==================== Configuration ====================
RAW_MESSAGES_FILE = "C:/softwareEngineer/ChatList/backend/raw_messages.json"
PROCESSED_MESSAGES_FILE = "C:/softwareEngineer/ChatList/backend/processed_messages.json"

# --------------------
# Ensure processed JSON exists
# --------------------
def ensure_processed_file_exists():
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

# ==================== FastAPI App ====================
app = FastAPI(
    title="ChatList Task Processor",
    description="Process WhatsApp messages and load tasks to database",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "status": "running",
        "message": "ChatList Task Processor API",
        "endpoints": {
            "process": "/process",
            "load_db": "/load-db",
            "run_all": "/run-all",
            "health": "/health",
            "processed_tasks": "/processed_tasks"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ⭐⭐⭐ ה־endpoint החדש לתצוגה ב־UI ⭐⭐⭐
@app.get("/processed_tasks")
def get_processed_tasks():
    """
    UI endpoint – Returns processed tasks from SOMEe database
    """
    return db.get_processed_tasks_from_db()

@app.post("/process")
def process_messages():
    try:
        processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)

        if os.path.exists(PROCESSED_MESSAGES_FILE):
            with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
                tasks = json.load(f)
                tasks_count = len(tasks)
        else:
            tasks_count = 0

        return {
            "status": "success",
            "message": "Messages processed successfully",
            "details": {
                "output_file": PROCESSED_MESSAGES_FILE,
                "tasks_found": tasks_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/load-db")
def load_to_database():
    try:
        ensure_processed_file_exists()

        if not os.path.exists(PROCESSED_MESSAGES_FILE):
            raise FileNotFoundError(f"Processed file not found: {PROCESSED_MESSAGES_FILE}")

        with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)

        added = 0
        skipped = 0
        errors = 0

        for task in tasks:
            result = db.save_task_to_db(task)

            if result["status"] == "success":
                added += 1
            elif result["status"] == "skipped":
                skipped += 1
            else:
                errors += 1

        return {
            "status": "success",
            "message": "Tasks loaded to database successfully",
            "details": {
                "total_tasks": len(tasks),
                "added": added,
                "skipped": skipped,
                "errors": errors
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run-all")
def run_complete_pipeline():
    try:
        processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)

        with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
            tasks_count = len(tasks)

        added = 0
        skipped = 0
        errors = 0

        for task in tasks:
            result = db.save_task_to_db(task)

            if result["status"] == "success":
                added += 1
            elif result["status"] == "skipped":
                skipped += 1
            else:
                errors += 1

        return {
            "status": "success",
            "message": "Complete pipeline executed successfully",
            "details": {
                "processing": {
                    "output_file": PROCESSED_MESSAGES_FILE,
                    "tasks_found": tasks_count
                },
                "database": {
                    "total_tasks": tasks_count,
                    "added": added,
                    "skipped": skipped,
                    "errors": errors
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CLI Commands ====================
def cli_process():
    try:
        processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)
    except Exception as e:
        sys.exit(1)

def cli_load_db():
    try:
        ensure_processed_file_exists()
        with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)

        for task in tasks:
            db.save_task_to_db(task)

    except Exception as e:
        sys.exit(1)

def cli_run_all():
    try:
        processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)
        ensure_processed_file_exists()
        with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)

        for task in tasks:
            db.save_task_to_db(task)

    except Exception as e:
        sys.exit(1)

def cli_serve():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

def print_help():
    pass

# ==================== Main Entry Point ====================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "process":
        cli_process()
    elif command == "load-db":
        cli_load_db()
    elif command == "run-all":
        cli_run_all()
    elif command == "serve":
        cli_serve()
    elif command == "help":
        print_help()
    else:
        sys.exit(1)
