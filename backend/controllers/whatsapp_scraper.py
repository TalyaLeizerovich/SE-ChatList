from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import re
from datetime import datetime

# ============================
# CONFIG
# ============================
RAW_MESSAGES_FILE = r"C:\softwareEngineer\ChatList\backend\controllers\raw_messages.json"
SESSION_PATH = r"C:\softwareEngineer\whatsapp_profile"
TARGET_GROUP = "ChatList"
SCROLL_PAUSE = 1.5
MAX_SCROLLS = 100

# ============================
# UTILITY - COMBINE DATE TIME
# ============================
def combine_date_time(date_str, time_str):
    """
    Combines date + time strings into datetime object.
    Expected formats:
    date: YYYY-MM-DD
    time: HH:MM
    """
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except Exception:
        return None

# ============================
# OPEN WHATSAPP
# ============================
def open_whatsapp():
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={SESSION_PATH}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.get("https://web.whatsapp.com/")
    print("Opening WhatsApp Web...")
    print("Waiting for WhatsApp to load (this may take a moment)...")
    print("If you see a QR code - please scan it now!\n")
    
    max_wait = 120
    start_time = time.time()
    loaded = False
    
    while time.time() - start_time < max_wait:
        try:
            if (driver.find_elements(By.CSS_SELECTOR, "[data-testid='chat-list']") or
                driver.find_elements(By.CSS_SELECTOR, "div[id='pane-side']") or
                driver.find_elements(By.CSS_SELECTOR, "div[data-testid='chatlist-panel-body']") or
                driver.find_elements(By.CSS_SELECTOR, "div._2aBzC") or
                driver.find_elements(By.CSS_SELECTOR, "div#side")):
                loaded = True
                break
        except:
            pass
        
        time.sleep(1)
        elapsed = int(time.time() - start_time)
        if elapsed % 10 == 0 and elapsed > 0:
            print(f"Still waiting... ({elapsed} seconds elapsed)")
    
    if loaded:
        print("\nWhatsApp loaded successfully!")
        time.sleep(3)
    else:
        print("\nERROR: Could not detect WhatsApp interface.")
        print("Please check if WhatsApp Web opened correctly in the browser.")
        driver.quit()
        exit(1)
    
    return driver

# ============================
# FIND CHATLIST GROUP
# ============================
def find_chatlist_group(driver):
    print(f"\nSearching for group: {TARGET_GROUP}...")
    
    time.sleep(3)
    
    try:
        try:
            search_box = driver.find_element(By.CSS_SELECTOR, "[data-testid='chat-list-search']")
            search_box.click()
            time.sleep(0.5)
            
            search_input = driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='3']")
            search_input.send_keys(TARGET_GROUP)
            time.sleep(2)
            
            chat_result = driver.find_element(By.CSS_SELECTOR, "[data-testid='cell-frame-container']")
            chat_result.click()
            print(f"Entered group: {TARGET_GROUP} (via search)")
            time.sleep(2)
            return True
        except:
            print("Search method failed, trying to find in chat list...")
        
        chats = driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
        
        if not chats:
            chats = driver.find_elements(By.CSS_SELECTOR, "div._2aBzC")
        
        if not chats:
            chats = driver.find_elements(By.XPATH, "//div[@role='row']")
        
        print(f"Found {len(chats)} chats in the list")
        
        for chat in chats:
            try:
                chat_text = chat.text
                if TARGET_GROUP in chat_text:
                    print(f"Found {TARGET_GROUP} in chat list!")
                    driver.execute_script("arguments[0].scrollIntoView(true);", chat)
                    time.sleep(0.5)
                    chat.click()
                    print(f"Entered group: {TARGET_GROUP}")
                    time.sleep(2)
                    return True
            except:
                continue
        
        print(f"Could not find group '{TARGET_GROUP}' in visible chats.")
        print("Make sure the group name is spelled correctly and the chat exists.")
        return False
        
    except Exception as e:
        print(f"Error finding group: {e}")
        return False

# ============================
# SCROLL CHAT TO TOP
# ============================
def scroll_chat_to_top(driver):
    print("\nScrolling up to load older messages...")
    
    try:
        chat_container = None
        selectors = [
            "[data-testid='conversation-panel-messages']",
            "div[data-testid='conversation-panel-body']",
            "div.copyable-area",
            "div._2u2nG",
            "div#main div[role='application']"
        ]
        
        for selector in selectors:
            try:
                chat_container = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"Found chat container using selector: {selector}")
                break
            except:
                continue
        
        if not chat_container:
            print("Warning: Could not find chat container for scrolling")
            print("Attempting to continue without scrolling...")
            time.sleep(3)
            return
        
        scroll_count = 0
        last_height = 0
        
        for i in range(MAX_SCROLLS):
            driver.execute_script("arguments[0].scrollTop = 0;", chat_container)
            time.sleep(SCROLL_PAUSE)
            
            current_height = driver.execute_script("return arguments[0].scrollTop", chat_container)
            
            if current_height == 0 and last_height == 0:
                print(f"Reached top of chat after {i+1} scrolls")
                break
            
            last_height = current_height
            scroll_count = i + 1
            
            if (i + 1) % 10 == 0:
                print(f"   Completed {i+1} scrolls...")
        
        print(f"Finished scrolling - {scroll_count} scrolls total")
        time.sleep(2)
        
    except Exception as e:
        print(f"Error during scrolling: {e}")
        print("Continuing anyway...")

# ============================
# SCRAPE MESSAGES
# ============================
def scrape_messages(driver):
    print("\nCollecting messages...")
    
    try:
        messages = []
        
        try:
            messages = driver.find_elements(By.XPATH, "//*[@data-pre-plain-text]")
            if len(messages) > 0:
                print(f"Found {len(messages)} messages using XPATH (data-pre-plain-text)")
        except:
            pass
        
        if len(messages) == 0:
            selectors = [
                "div.message-in, div.message-out",
                "div[data-testid='msg-container']",
                "div._amk4, div._amk5",
                "div.copyable-text"
            ]
            
            for selector in selectors:
                try:
                    messages = driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(messages) > 0:
                        print(f"Found {len(messages)} messages using selector: {selector}")
                        break
                except:
                    continue
        
        if len(messages) == 0:
            print("No messages found with any selector")
            return []
        
        results = []
        
        for idx, msg in enumerate(messages):
            try:
                text = ""
                try:
                    text_elem = msg.find_element(By.CSS_SELECTOR, "span.selectable-text")
                    text = text_elem.text
                except:
                    try:
                        text_elem = msg.find_element(By.CSS_SELECTOR, "span.copyable-text")
                        text = text_elem.text
                    except:
                        try:
                            text_elems = msg.find_elements(By.CSS_SELECTOR, "span")
                            text = " ".join([elem.text for elem in text_elems if elem.text])
                        except:
                            text = ""
                
                raw_header = ""
                try:
                    raw_header = msg.get_attribute("data-pre-plain-text")
                except:
                    pass
                
                results.append({
                    "raw_header": raw_header,
                    "content": text,
                    "has_metadata": bool(raw_header and raw_header.strip())
                })
                    
            except Exception as e:
                continue
        
        print(f"Successfully collected {len(results)} messages with valid metadata")
        
        if len(results) > 0:
            print("\n--- SAMPLE MESSAGE (first one) ---")
            print(f"Content: {results[0]['content'][:100] if results[0]['content'] else 'EMPTY'}...")
            print(f"Raw header: {results[0]['raw_header'][:100] if results[0]['raw_header'] else 'EMPTY'}")
            print("-----------------------------------\n")
        
        return results
        
    except Exception as e:
        print(f"Error collecting messages: {e}")
        return []

# ============================
# PARSE METADATA
# ============================
def parse_metadata(raw_header):
    try:
        pattern1 = r"\[(\d{1,2}:\d{2}),?\s*(\d{1,2}\.\d{1,2}\.\d{4})\]\s*(.*?):"
        match = re.search(pattern1, raw_header)
        
        if match:
            time_str = match.group(1)
            date_str = match.group(2)
            sender = match.group(3).strip()
            
            date_obj = datetime.strptime(date_str, "%d.%m.%Y")
            time_obj = datetime.strptime(time_str, "%H:%M")
            
            return {
                "date": date_obj.strftime("%Y-%m-%d"),
                "time": time_obj.strftime("%H:%M"),
                "from": sender
            }
        
        pattern2 = r"\[(\d{1,2}:\d{2}),?\s*(\d{1,2}/\d{1,2}/\d{4})\]\s*(.*?):"
        match = re.search(pattern2, raw_header)
        
        if match:
            time_str = match.group(1)
            date_str = match.group(2)
            sender = match.group(3).strip()
            
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            time_obj = datetime.strptime(time_str, "%H:%M")
            
            return {
                "date": date_obj.strftime("%Y-%m-%d"),
                "time": time_obj.strftime("%H:%M"),
                "from": sender
            }
        
        return {"date": "", "time": "", "from": ""}
        
    except Exception as e:
        print(f"Error parsing metadata: {raw_header[:50]}... | Error: {e}")
        return {"date": "", "time": "", "from": ""}

# ============================
# CONVERT TO FINAL FORMAT
# ============================
def convert_to_final_format(scraped_messages):
    print("\nConverting to final format...")
    
    final_messages = []
    messages_with_metadata = 0
    messages_without_metadata = 0
    
    for msg in scraped_messages:
        if msg.get("has_metadata"):
            messages_with_metadata += 1
            meta = parse_metadata(msg["raw_header"])
            
            final_messages.append({
                "content": msg["content"],
                "date": meta["date"],
                "time": meta["time"],
                "from": meta["from"],
                "group": TARGET_GROUP
            })
        else:
            messages_without_metadata += 1
    
    print(f"Messages WITH metadata: {messages_with_metadata}")
    print(f"Messages WITHOUT metadata: {messages_without_metadata}")
    
    valid_messages = [m for m in final_messages if m["date"] and m["from"]]
    
    print(f"{len(valid_messages)} valid messages after parsing")
    
    if len(valid_messages) == 0 and messages_without_metadata > 0:
        print("\nWARNING: Found messages but none have metadata!")
        print("This means WhatsApp's structure might have changed.")
        print("Saving RAW data for inspection...")
        
        raw_file = RAW_MESSAGES_FILE.replace(".json", "_raw_debug.json")
        try:
            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(scraped_messages, f, ensure_ascii=False, indent=2)
            print(f"Raw debug file saved: {raw_file}")
        except:
            pass
    
    return valid_messages

# ============================
# SAVE JSON
# ============================
def save_json(data):
    try:
        with open(RAW_MESSAGES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nSaved successfully: {RAW_MESSAGES_FILE}")
        print(f"Total: {len(data)} messages")
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False

# ============================
# MAIN - WITH min_datetime SUPPORT
# ============================
def run_scraper(min_datetime: datetime | None = None):
    """
    Main function to run the scraper.
    If min_datetime is provided, only messages sent AFTER it are kept.
    """
    driver = None
    
    try:
        print("=" * 60)
        print("WhatsApp ChatList Scraper")
        if min_datetime:
            print(f"Filtering messages after: {min_datetime}")
        print("=" * 60)
        
        driver = open_whatsapp()
        
        if not find_chatlist_group(driver):
            print("\nChatList group not found - exiting")
            return False
        
        scroll_chat_to_top(driver)
        
        scraped = scrape_messages(driver)
        
        if not scraped:
            print("\nNo messages found")
            return False
        
        final_data = convert_to_final_format(scraped)
        
        # --------- FILTER NEW MESSAGES ONLY ---------
        if min_datetime:
            filtered = []
            
            for msg in final_data:
                msg_dt = combine_date_time(msg["date"], msg["time"])
                if msg_dt and msg_dt > min_datetime:
                    filtered.append(msg)
            
            print(f"\n>>> Filtered {len(filtered)} new messages out of {len(final_data)} total")
            final_data = filtered
        else:
            print(f"\n>>> No min_datetime provided, keeping all {len(final_data)} messages")
        
        if save_json(final_data):
            print("\n" + "=" * 60)
            print("Completed successfully!")
            print("=" * 60)
            return True
        
        return False
        
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user")
        return False
    
    except Exception as e:
        print(f"\nGeneral error: {e}")
        return False
    
    finally:
        if driver:
            print("\nClosing browser...")
            driver.quit()

if __name__ == "__main__":
    run_scraper()