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
RAW_MESSAGES_FILE = "raw_messages.json"
PROCESSED_MESSAGES_FILE = "processed_messages.json"


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


# --------------------
# Startup event - run all automatically
# --------------------
@app.on_event("startup")
def startup_event():
    """Run the complete pipeline when server starts"""
    try:
        # Step 1: Process messages
        processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)
        # Step 2: Load to DB
        ensure_processed_file_exists()
        with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        for task in tasks:
            db.save_task_to_db(task)
        print(f"Startup complete: {len(tasks)} tasks processed and loaded to DB")
    except Exception as e:
        print(f"Error during startup pipeline: {e}")


# ==================== Endpoints ====================
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


@app.get("/processed_tasks")
def get_processed_tasks():
    return db.get_tasks_from_db()


@app.post("/process")
def process_messages():
    try:
        processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)
        with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        return {"status": "success", "tasks_found": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/load-db")
def load_to_database():
    try:
        ensure_processed_file_exists()
        with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        for task in tasks:
            db.save_task_to_db(task)
        return {"status": "success", "tasks_loaded": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run-all")
def run_complete_pipeline():
    try:
        processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)
        with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        for task in tasks:
            db.save_task_to_db(task)
        return {"status": "success", "tasks_processed": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CLI Commands ====================
def cli_serve():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1].lower() == "serve":
        cli_serve()
    else:
        print("Use 'serve' to start the server: python main.py serve")



