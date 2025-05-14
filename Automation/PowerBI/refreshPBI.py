from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

import time

# Replace with your credentials and dataset URL
USERNAME = 'aahmad@novelluscapital.co.uk'
PASSWORD = 'BlueWatch804!'
DATASET_URL = 'https://app.powerbi.com/groups/71153f62-9f44-47cd-b6d5-c3e56e8977ba/datasets/179f2f8c-a9a6-4c92-ac7d-b8af3dd5dfbb/details?experience=power-bi'  # Replace with actual URL

# Set up ChromeDriver
#service = Service('path_to_chromedriver')  # Replace with your chromedriver path
#options = webdriver.ChromeOptions()
#options.add_argument("--start-maximized")

options = EdgeOptions()

options.add_argument("--headless=new")
options.add_argument("--inprivate")   
options.add_argument("--disable-extensions")
options.add_argument("--disable-cache")
            # Automatically finds Microsoft Edge installed on Windows in its default path
driver = webdriver.Edge(service=EdgeService(), options=options)
driver.maximize_window()
driver.delete_all_cookies()

#driver = webdriver.Chrome(service=service, options=options)

try:
    # Step 1: Go to Power BI login
    driver.get("https://app.powerbi.com/")
    time.sleep(5)
    # Step 2: Enter email
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "email"))).send_keys(USERNAME + Keys.RETURN)
    time.sleep(5)
    # Step 3: Enter password (depending on your org’s login flow)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "passwd"))).send_keys(PASSWORD + Keys.RETURN)
    time.sleep(5)
    # Step 4: Handle "Stay signed in?" prompt
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "idBtn_Back"))).click()
# ✅ Add wait time before navigating
    time.sleep(5)  # Wait for 5 seconds before proceeding

    # Step 5: Go to dataset settings page
    driver.get(DATASET_URL)
    time.sleep(3)
    # Step 6: Click the dropdown (span text "Refresh")
    dropdown_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//span[normalize-space(text())='Refresh']"))
    )
    dropdown_button.click()
    time.sleep(3)
    # Step 7: Click the "Refresh now" button inside the dropdown
    refresh_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@title='Refresh now' and @role='menuitem']//span[normalize-space()='Refresh now']"))
    )
    refresh_button.click()

    print("Dataset refresh triggered successfully.")

    time.sleep(10)  # Wait for operation to start or complete

finally:
    driver.quit()
