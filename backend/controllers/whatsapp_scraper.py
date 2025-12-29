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
MAX_SCROLLS = 20  

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
# GET CHAT NAME
# ============================
def get_chat_name(chat_element):
    """
    Extracts the exact name/title of a chat.
    """
    try:
        # Method 1: Try to find the title attribute (most reliable)
        title_elem = chat_element.find_element(By.CSS_SELECTOR, "span[title]")
        return title_elem.get_attribute("title").strip()
    except:
        pass
   
    try:
        # Method 2: Try to find the chat name in specific selectors
        name_selectors = [
            "span[dir='auto'][title]",
            "span._11JPr",
            "div._21S-L span",
        ]
        for selector in name_selectors:
            try:
                elem = chat_element.find_element(By.CSS_SELECTOR, selector)
                name = elem.text.strip()
                if name:
                    return name
            except:
                continue
    except:
        pass
   
    try:
        # Method 3: Get first line of text (fallback)
        chat_text = chat_element.text.strip()
        if chat_text:
            return chat_text.split("\n")[0].strip()
    except:
        pass
   
    return ""

# ============================
# FIND CHATLIST GROUP
# ============================
def find_chatlist_group(driver):
    print(f"\nSearching for chat with EXACT name: '{TARGET_GROUP}'...")
   
    time.sleep(3)
   
    try:
        # Try search method first
        try:
            search_box = driver.find_element(By.CSS_SELECTOR, "[data-testid='chat-list-search']")
            search_box.click()
            time.sleep(0.5)
           
            search_input = driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='3']")
            search_input.send_keys(TARGET_GROUP)
            time.sleep(2)
           
            # Get all search results
            results = driver.find_elements(By.CSS_SELECTOR, "[data-testid='cell-frame-container']")
           
            print(f"Found {len(results)} search results")
           
            # Check each result for EXACT name match
            for result in results:
                try:
                    chat_name = get_chat_name(result)
                    print(f"  Checking: '{chat_name}'")
                   
                    # EXACT match only
                    if chat_name == TARGET_GROUP:
                        print(f"✓ Found EXACT match: '{TARGET_GROUP}'")
                        result.click()
                        time.sleep(2)
                        return True
                except:
                    continue
           
            print(f"No EXACT match found in search results")
           
            # Clear search before trying manual method
            try:
                back_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='back']")
                back_button.click()
                time.sleep(1)
            except:
                pass
               
        except Exception as e:
            print(f"Search method failed: {e}")
            print("Trying manual scan...")
       
        # Manual scan of chat list
        chats = driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
       
        if not chats:
            chats = driver.find_elements(By.CSS_SELECTOR, "div._2aBzC")
       
        if not chats:
            chats = driver.find_elements(By.XPATH, "//div[@role='row']")
       
        print(f"\nManually scanning {len(chats)} chats...")
       
        for idx, chat in enumerate(chats):
            try:
                chat_name = get_chat_name(chat)
               
                if not chat_name:
                    continue
               
                # Show progress every 5 chats
                if (idx + 1) % 5 == 0:
                    print(f"  Scanned {idx + 1}/{len(chats)} chats...")
               
                # EXACT match only
                if chat_name == TARGET_GROUP:
                    print(f"\n✓ Found EXACT match: '{TARGET_GROUP}'")
                    driver.execute_script("arguments[0].scrollIntoView(true);", chat)
                    time.sleep(0.5)
                    chat.click()
                    time.sleep(2)
                    return True
                   
            except Exception as e:
                continue
       
        print(f"\nCould not find a chat with EXACT name: '{TARGET_GROUP}'")
        print("\nTroubleshooting tips:")
        print(f"1. Make sure the chat/group name is EXACTLY: '{TARGET_GROUP}'")
        print("2. Check for extra spaces or different spelling")
        print("3. Make sure the chat appears in your chat list")
        print("4. Try scrolling down in WhatsApp to load more chats")
        return False
       
    except Exception as e:
        print(f"Error finding chat: {e}")
        return False

# ============================
# SCROLL CHAT (LIGHT SCROLL FOR TODAY ONLY)
# ============================
def scroll_chat_to_top(driver):
    print("\nScrolling up lightly to load today's messages...")
   
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
       
        print(f"Successfully collected {len(results)} messages")
       
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
# MAIN - WITH TODAY FILTER
# ============================
def run_scraper(min_datetime: datetime | None = None):
    """
    Main function to run the scraper.
    If min_datetime is provided, only messages sent AFTER it are kept.
    Otherwise, only messages from TODAY are kept.
    """
    driver = None
   
    try:
        print("=" * 60)
        print("WhatsApp Chat Scraper - EXACT NAME MATCH")
       
        if min_datetime is None:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            min_datetime = today_start
            print(f"Filtering messages from TODAY only: {today_start.strftime('%Y-%m-%d')}")
        else:
            print(f"Filtering messages after: {min_datetime}")
       
        print(f"Looking for chat with EXACT name: '{TARGET_GROUP}'")
        print("=" * 60)
       
        driver = open_whatsapp()
       
        if not find_chatlist_group(driver):
            print(f"\nChat with exact name '{TARGET_GROUP}' not found - exiting")
            return False
       
        scroll_chat_to_top(driver)
       
        scraped = scrape_messages(driver)
       
        if not scraped:
            print("\nNo messages found")
            return False
       
        final_data = convert_to_final_format(scraped)
       
        # --------- FILTER MESSAGES (TODAY OR AFTER min_datetime) ---------
        filtered = []
       
        for msg in final_data:
            msg_dt = combine_date_time(msg["date"], msg["time"])
            if msg_dt and msg_dt >= min_datetime:  
                filtered.append(msg)
       
        print(f"\n>>> Filtered {len(filtered)} messages from today out of {len(final_data)} total")
        final_data = filtered
       
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

















