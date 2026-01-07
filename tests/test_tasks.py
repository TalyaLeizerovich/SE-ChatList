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