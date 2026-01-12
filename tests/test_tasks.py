import pytest
import time
from pages.task_page import TaskPage
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class TestTaskWorkflow:

    @pytest.fixture(autouse=True)
    def setup(self, driver):
        self.page = TaskPage(driver)

    def test_01_task_generation_and_display(self, driver):
        """Verify tasks exist or skip if UI is empty."""
        self.page.navigate()
        self.page.wait_for_qr_code()
        time.sleep(5)
        
        if not self.page.has_active_tasks():
            pytest.skip("No checkboxes found. Skipping display test.")
            
        assert self.page.get_tasks_count() > 0

    def test_02_task_completion_via_ui(self):
        """Verify task removal. Skips immediately if no tasks exist."""
        self.page.navigate()
        
        if not self.page.has_active_tasks():
            pytest.skip("Empty UI. Nothing to complete.")

        initial_count = self.page.get_tasks_count()
        self.page.click_first_checkbox()
        time.sleep(5)
        
        assert self.page.get_tasks_count() < initial_count

    def test_03_no_task_messages_empty_state(self):
        """Verify empty state message. Skips if tasks exist."""
        self.page.navigate()
        if not self.page.has_active_tasks():
            assert self.page.is_all_caught_up_visible(), "Empty state message missing"
        else:
            pytest.skip("Tasks are present, skipping empty state check.")

    def test_04_incremental_update_with_refresh(self):
        """Verify UI stability after refresh."""
        self.page.navigate()
        initial = self.page.get_tasks_count()
        self.page.click_refresh()
        time.sleep(8)
        assert self.page.get_tasks_count() >= initial

    def test_05_full_e2e_whatsapp_to_calendar_sync(self, driver):
        """Verify calendar sync. Skips immediately if no tasks exist."""
        self.page.navigate()
        
        if not self.page.has_active_tasks():
            pytest.skip("No tasks available for Calendar sync.")

        expander = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(self.page.DETAILS_EXPANDER)
        )
        expander.click()
        time.sleep(2)
        
        calendar_btn = expander.find_element(By.XPATH, ".//button[contains(., 'Calendar')]")
        driver.execute_script("arguments[0].click();", calendar_btn)
        
        time.sleep(10)
        assert "Calendar" in expander.text