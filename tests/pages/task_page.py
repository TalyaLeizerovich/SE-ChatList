import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TaskPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 20)
        self.url = "http://localhost:8501"

    # Precise Selectors for Streamlit
    QR_CODE = (By.TAG_NAME, "img")
    CHECKBOX_RAW = (By.CSS_SELECTOR, "div[data-testid='stCheckbox']")
    CHECKBOX_LABEL = (By.CSS_SELECTOR, "div[data-testid='stCheckbox'] label")
    REFRESH_BTN = (By.XPATH, "//button[contains(., 'Refresh')]")
    DETAILS_EXPANDER = (By.CSS_SELECTOR, "div[data-testid='stExpander']")
    
    def navigate(self):
        """Navigates to the app and waits for initial load."""
        self.driver.get(self.url)
        time.sleep(5)

    def wait_for_qr_code(self):
        """Checks for QR code presence."""
        try:
            return self.wait.until(EC.presence_of_element_located(self.QR_CODE))
        except:
            return None

    def has_active_tasks(self):
        """Fast pre-condition check: searches for any checkbox with a 2-second timeout."""
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(self.CHECKBOX_RAW)
            )
            return True
        except:
            return False

    def get_tasks_count(self):
        """Returns the number of actual checkboxes found."""
        return len(self.driver.find_elements(*self.CHECKBOX_RAW))

    def click_first_checkbox(self):
        """Clicks the checkbox using JS for stability."""
        checkbox = self.wait.until(EC.element_to_be_clickable(self.CHECKBOX_LABEL))
        self.driver.execute_script("arguments[0].click();", checkbox)
        time.sleep(5)

    def click_refresh(self):
        """Clicks the refresh button."""
        button = self.wait.until(EC.element_to_be_clickable(self.REFRESH_BTN))
        button.click()
        time.sleep(2)

    def is_all_caught_up_visible(self):
        """Checks if the empty state message is present in the DOM."""
        elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'All caught up')]")
        return len(elements) > 0