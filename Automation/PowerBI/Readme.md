# Power BI Dataset Refresh Automation Using Selenium

## Overview

This script automates the login process to Microsoft Power BI, navigates to a specified dataset, and triggers a manual refresh using Microsoft Edge in headless mode. It leverages Selenium WebDriver for browser automation.

---

## Prerequisites

- Python installed on the system  
- Microsoft Edge browser installed  
- Edge WebDriver (compatible with your version of Edge) added to system PATH  
- Selenium library (`pip install selenium`)  
- Valid Power BI account credentials  
- Dataset URL from Power BI  

---

## Configuration

Update the following variables with valid credentials and dataset information before running the script:

```python
USERNAME = 'your_email@domain.com'
PASSWORD = 'your_password'
DATASET_URL = 'https://app.powerbi.com/groups/.../datasets/...'

## 1. Setup Microsoft Edge WebDriver
options = EdgeOptions()
options.add_argument("--headless=new")
options.add_argument("--inprivate")
options.add_argument("--disable-extensions")
options.add_argument("--disable-cache")

driver = webdriver.Edge(service=EdgeService(), options=options)
driver.maximize_window()
driver.delete_all_cookies()

## 2. Login to Power BI
driver.get("https://app.powerbi.com/")
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "email"))).send_keys(USERNAME + Keys.RETURN)
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "passwd"))).send_keys(PASSWORD + Keys.RETURN)
WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "idBtn_Back"))).click()

## 3. Navigate to Dataset and Trigger Refresh
driver.get(DATASET_URL)

dropdown_button = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, "//span[normalize-space(text())='Refresh']"))
)
dropdown_button.click()

refresh_button = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, "//button[@title='Refresh now' and @role='menuitem']//span[normalize-space()='Refresh now']"))
)
refresh_button.click()

## 4. Completion and Cleanup
print("Dataset refresh triggered successfully.")
time.sleep(10)
driver.quit()
