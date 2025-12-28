import json
import sys
import os
from datetime import datetime
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi import Body


# Import existing modules
import controllers.processing as processing
import controllers.whatsapp_scraper as whatsapp_scraper
import models.db as db
import controllers.calendar_controller as calendar
from controllers.data_parser import resolve_task_date


# ==================== Configuration ====================
RAW_MESSAGES_FILE = "controllers/raw_messages.json"
PROCESSED_MESSAGES_FILE = "processed_messages.json"

# --------------------
# Ensure previous JSON files are cleaned up
# --------------------
def cleanup_generated_files():
    files_to_delete = [
        RAW_MESSAGES_FILE,
        PROCESSED_MESSAGES_FILE
    ]

    for file_path in files_to_delete:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")


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
# Startup event - run initial scrape
# --------------------
@app.on_event("startup")
def startup_event():
    """Run the complete pipeline when server starts (initial load)"""
    try:
        print("\n=== Starting Initial Pipeline ===")
         # Step 0: Clear DB on startup
        print("\n[0/3] Clearing Tasks table...")
        db.truncate_tasks_table()

        # Step 0.5: Cleanup generated files
        print("\n[0.5/4] Cleaning generated JSON files...")
        cleanup_generated_files()
        
        # Step 1: Scrape WhatsApp messages (all messages - no filter)
        print("\n[1/3] Scraping WhatsApp messages...")
        whatsapp_scraper.run_scraper(min_datetime=None)
        
        # Step 2: Process messages
        print("\n[2/3] Processing messages...")
        processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)
        
        # Step 3: Load to DB
        print("\n[3/3] Loading to database...")
        ensure_processed_file_exists()
        with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        for task in tasks:
            db.save_task_to_db(task)
        
        print(f"\n=== Initial Pipeline Complete: {len(tasks)} tasks processed and loaded to DB ===\n")
    except Exception as e:
        print(f"\nError during startup pipeline: {e}\n")

# ==================== Endpoints ====================
@app.get("/")
def root():
    return {
        "status": "running",
        "message": "ChatList Task Processor API",
        "endpoints": {
            "refresh": "/refresh - Update with new messages only",
            "scrape": "/scrape",
            "process": "/process",
            "load_db": "/load-db",
            "run_all": "/run-all",
            "health": "/health",
            "processed_tasks": "/processed_tasks",
            "add_to_calendar": "/add-to-calendar",
            "delete_tasks": "/delete_tasks"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/processed_tasks")
def get_processed_tasks():
    return db.get_tasks_from_db()

@app.post("/refresh")
def refresh_new_messages():
    """
    Incremental update: fetch only NEW messages since last task in DB.
    This is the main endpoint for real-time updates.
    """
    try:
        # Step 1: Get timestamp of last processed task
        last_timestamp = db.get_last_task_timestamp()
        
        if last_timestamp:
            print(f"\nLast task timestamp: {last_timestamp}")
            print("Fetching only NEW messages after this time...")
        else:
            print("\nNo existing tasks found - fetching all messages")
        
        # Step 2: Scrape with filter
        whatsapp_scraper.run_scraper(min_datetime=last_timestamp)
        
        # Step 3: Process the new messages
        processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)
        
        # Step 4: Load new tasks to DB
        ensure_processed_file_exists()
        with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
            new_tasks = json.load(f)
        
        loaded_count = 0
        for task in new_tasks:
            db.save_task_to_db(task)
            loaded_count += 1
        
        return {
            "status": "success",
            "new_tasks_found": len(new_tasks),
            "tasks_loaded": loaded_count,
            "last_timestamp": last_timestamp.isoformat() if last_timestamp else None,
            "message": f"Successfully updated with {loaded_count} new tasks"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape")
def scrape_whatsapp():
    """Step 1: Scrape WhatsApp messages from ChatList group"""
    try:
        whatsapp_scraper.run_scraper(min_datetime=None)
        with open(RAW_MESSAGES_FILE, "r", encoding="utf-8") as f:
            messages = json.load(f)
        return {"status": "success", "messages_scraped": len(messages)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process")
def process_messages():
    """Step 2: Process raw messages into tasks"""
    try:
        processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)
        with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        return {"status": "success", "tasks_found": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/load-db")
def load_to_database():
    """Step 3: Load processed tasks to database"""
    try:
        ensure_processed_file_exists()
        with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        for task in tasks:
            db.save_task_to_db(task)
        return {"status": "success", "tasks_loaded": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/delete_tasks")
def delete_task(task: dict = Body(...)):
    """
    Delete a task from the database.
    Expects the task dictionary to contain at least:
    content, date, time, from, group
    """
    try:
        result = db.delete_task_from_db(task)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add-to-calendar")
def add_to_calendar(task_id: int = Body(..., embed=True)):
    """
    Add a task to Google Calendar.
    Expects JSON body: {"task_id": 123}
    """
    try:
        # Get task from database
        task = db.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Resolve the date from task content
        event_date = resolve_task_date(task["content"])
        
        # Add to calendar
        calendar.add_task_to_calendar(task["content"], event_date)

        return {
            "status": "success",
            "task_id": task_id,
            "task_content": task["content"],
            "added_for": event_date.date().isoformat(),
            "message": f"המשימה נוספה ליומן בתאריך {event_date.date().isoformat()}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding to calendar: {str(e)}")

@app.post("/run-all")
def run_complete_pipeline():
    """Run complete pipeline: Scrape → Process → Load to DB (all messages)"""
    try:
        # Step 1: Scrape (all messages)
        whatsapp_scraper.run_scraper(min_datetime=None)
        
        # Step 2: Process
        processing.process_json_file(RAW_MESSAGES_FILE, PROCESSED_MESSAGES_FILE)
        
        # Step 3: Load to DB
        with open(PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        for task in tasks:
            db.save_task_to_db(task)
        
        return {
            "status": "success",
            "pipeline_steps_completed": 3,
            "tasks_processed": len(tasks)
        }
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






