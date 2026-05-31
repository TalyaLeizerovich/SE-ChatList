## **Planning:**
#187
#190
#188
#189
#191

::: query-table 333d1336-480a-4fb0-9a90-40645828e360
:::



## **User story covered:**
#40
#50
#52
#53
#54
#58
#62
#77

::: query-table 15c7f088-3ec2-4f83-891f-741e1ab029c6
:::




## **Coding:**
The framework is developed in Python using Selenium and Pytest, following the Page Object Model (POM). It utilizes a pages/ directory for element locators and a tests/ directory for execution logic. The architecture features explicit waits and JavaScript executors to handle Streamlit’s dynamic UI, with Pytest fixtures in conftest.py managing the WebDriver lifecycle.
## **Result:**
* The system works properly end to end.
* When a task is marked as completed, the task is deleted from the to-do list.
* When the refresh button is clicked, the screen is updated and new tasks are displayed to the user.
* When the "add to calendar" button is clicked, the list is added to the user's Google calendar.
* When there are no messages with task content in the WhatsApp group, no to-do list is not displayed to the user.

## **bugs:**
*   Race Conditions: The automation script attempted to click the "Add to Calendar" button before the WhatsApp message parsing was complete, leading to NoSuchElementException even though the feature works for a human user.
    
*   Checkbox Interactivity Issues: Selenium failed to click the task checkboxes because Streamlit wraps them in multiple layers of <div> tags. The test initially failed with an ElementClickInterceptedException until it was fixed with a JavaScript executor.
    
*   Session Conflict: Running the tests multiple times caused a conflict with the Google Calendar session, where the "Add to Calendar" button was blocked by a pop-up that only appears during automated sessions.
    
*  Sync Latency during Refresh: In test_04, the automation verified the task count too quickly after clicking "Refresh", failing the test because it didn't wait for the Streamlit loading spinner to disappear.
