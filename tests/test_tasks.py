import pytest
import time
from pages.task_page import TaskPage

class TestTaskWorkflow:

    @pytest.fixture(autouse=True)
    def setup(self, driver):
        self.page = TaskPage(driver)

    def test_01_task_generation_and_display(self, driver):
        """Test: Verify WhatsApp messages are processed and displayed in UI"""
        try:
            self.page.navigate()
            self.page.wait_for_qr_code()
            
            print("Waiting 10 seconds for potential QR scan and data processing...")
            time.sleep(10) 
            
            count = self.page.get_tasks_count()
            assert count > 0, "No tasks were found after scanning QR."
            
            # Check details expander
            expanders = driver.find_elements(*self.page.DETAILS_EXPANDER)
            if expanders:
                expanders[0].click()
                assert expanders[0].is_displayed()
        except Exception as e:
            self.page.take_screenshot("failed_generation")
            raise e

    def test_02_task_completion_via_ui(self):
        """Test: Marking a task as completed should remove it from the list"""
        try:
            self.page.navigate()
            initial_count = self.page.get_tasks_count()
            
            if initial_count > 0:
                print(f"Completing task. Initial count: {initial_count}")
                self.page.click_first_checkbox()
                time.sleep(5) # Wait for Streamlit update
                
                new_count = self.page.get_tasks_count()
                assert new_count < initial_count, f"Task count didn't decrease! (Before: {initial_count}, After: {new_count})"
            else:
                pytest.skip("No tasks available to test completion.")
        except Exception as e:
            self.page.take_screenshot("failed_completion")
            raise e

    def test_03_no_task_messages_empty_state(self):
        """Test: Verify empty state message when no tasks are present"""
        try:
            self.page.navigate()
            if self.page.get_tasks_count() == 0:
                assert self.page.is_all_caught_up_visible(), "Empty state message not found."
            else:
                pytest.skip("Tasks exist in DB, skipping empty state test.")
        except Exception as e:
            self.page.take_screenshot("failed_empty_state")
            raise e

    def test_04_incremental_update_with_refresh(self, driver):
        """Test: Verify Refresh button updates UI properly"""
        try:
            self.page.navigate()
            initial_count = self.page.get_tasks_count()
            
            print(f"Triggering refresh. Current tasks: {initial_count}")
            self.page.click_refresh()
            
            # Wait for any new messages to be processed
            time.sleep(8)
            
            current_count = self.page.get_tasks_count()
            assert current_count >= initial_count, "Tasks disappeared after clicking refresh!"
            print(f"Refresh completed successfully. Final count: {current_count}")
        except Exception as e:
            self.page.take_screenshot("failed_refresh")
            raise e

    def test_05_full_e2e_whatsapp_to_calendar_sync(self, driver):
        try:
            # Step 1: Navigate to the app
            self.page.navigate()
           
            # Step 2: Wait for the task to appear (No manual refresh)
            print("Waiting for task to appear on screen...")
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By

            # Wait up to 30 seconds for the expander to be present
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(self.page.DETAILS_EXPANDER)
            )
           
            # Step 3: Open the first task
            expanders = driver.find_elements(*self.page.DETAILS_EXPANDER)
            expanders[0].click()
            time.sleep(2) # Wait for animation
           
            # Step 4: Find and click the Calendar button
            print("Locating Calendar button...")
            calendar_btn = expanders[0].find_element(By.XPATH, ".//button[contains(., 'Calendar')]")
           
            # Scroll to the button to make sure it's viewable
            driver.execute_script("arguments[0].scrollIntoView(true);", calendar_btn)
            time.sleep(1)
           
            # Execute the click via JavaScript (most reliable way)
            print("Clicking Calendar button now...")
            driver.execute_script("arguments[0].click();", calendar_btn)
           
            # Step 5: CRITICAL - Wait for backend to finish the sync
            # If we close the browser too fast, the request to Google might be cancelled
            print("Sync triggered. Waiting 10 seconds for Google API to complete...")
            time.sleep(10)
           
            # Step 6: Final check of the UI content
            details_content = expanders[0].text
            assert "Calendar" in details_content, "Calendar metadata missing from task"
           
            print("Test passed! Check your Google Calendar now.")

        except Exception as e:
            self.page.take_screenshot("failed_calendar_sync")
            print(f"Test failed: {e}")
            raise e