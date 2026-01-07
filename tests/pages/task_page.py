import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class TaskPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 20)
        self.url = "http://localhost:8501"

    # Selectors for Streamlit
    QR_CODE = (By.TAG_NAME, "img")
    TASK_CONTAINER = (By.CSS_SELECTOR, "div[data-testid='stMarkdownContainer']")
    CHECKBOX = (By.CSS_SELECTOR, "div[data-testid='stCheckbox'] label")
    REFRESH_BTN = (By.XPATH, "//button[contains(., 'Refresh')]")
    SPINNER = (By.CSS_SELECTOR, "div[data-testid='stLoading']")
    DETAILS_EXPANDER = (By.CSS_SELECTOR, "div[data-testid='stExpander']")
    
    def navigate(self):
        self.driver.get(self.url)
        time.sleep(5)

    def wait_for_qr_code(self):
        try:
            return self.wait.until(EC.presence_of_element_located(self.QR_CODE))
        except TimeoutException:
            print("QR Code not found - user might be already logged in.")
            return None

    def get_tasks_count(self):
        # Refresh element list to avoid stale references
        tasks = self.driver.find_elements(*self.TASK_CONTAINER)
        # Filter out very short strings or empty containers
        return len([t for t in tasks if len(t.text.strip()) > 2])

    def click_first_checkbox(self):
        checkbox = self.wait.until(EC.element_to_be_clickable(self.CHECKBOX))
        checkbox.click()
        time.sleep(3)

    def click_refresh(self):
        button = self.wait.until(EC.element_to_be_clickable(self.REFRESH_BTN))
        button.click()
        
        # Soft check for spinner: don't fail if it disappears too fast
        try:
            print("Checking for spinner...")
            WebDriverWait(self.driver, 2).until(EC.presence_of_element_located(self.SPINNER))
            print("Spinner detected, waiting for it to finish...")
            WebDriverWait(self.driver, 15).until_not(EC.presence_of_element_located(self.SPINNER))
        except TimeoutException:
            print("Spinner finished too fast or didn't appear. Continuing...")

    def take_screenshot(self, name):
        # Ensure screenshot directory exists
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")
        path = f"screenshots/{name}_{int(time.time())}.png"
        self.driver.save_screenshot(path)
        print(f"Screenshot saved to: {path}")

    def is_all_caught_up_visible(self):
        try:
            condition = EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'All caught up')]"))
            return self.wait.until(condition).is_displayed()
        except TimeoutException:
            return False