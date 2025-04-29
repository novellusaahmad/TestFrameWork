import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import os
import pandas as pd
import re

TEST_CASES_FILE = "test_cases.json"

# --- Helper Functions ---

def load_test_cases():
    if os.path.exists(TEST_CASES_FILE):
        with open(TEST_CASES_FILE, "r") as file:
            return json.load(file)
    return []

def save_test_cases(test_cases):
    with open(TEST_CASES_FILE, "w") as file:
        json.dump(test_cases, file, indent=4)

def find_element(driver, step):
    selector_type = step["selector_type"]
    selector_value = step["selector_value"]

    selectors = {
        "id": By.ID,
        "name": By.NAME,
        "xpath": By.XPATH,
        "css_selector": By.CSS_SELECTOR,
        "class_name": By.CLASS_NAME,
        "tag_name": By.TAG_NAME,
        "link_text": By.LINK_TEXT,
        "partial_link_text": By.PARTIAL_LINK_TEXT,
        "placeholder": By.XPATH
    }

    if selector_type == "placeholder":
        selector_value = f"//*[@placeholder='{selector_value}']"

    return driver.find_element(selectors[selector_type], selector_value)

def substitute_placeholders(text, csv_row):
    if csv_row is None or not isinstance(text, str):
        return text

    placeholders = re.findall(r"\{\{(.*?)\}\}", text)
    for ph in placeholders:
        value = csv_row.get(ph) if isinstance(csv_row, (dict, pd.Series)) else None
        text = text.replace(f"{{{{{ph}}}}}", str(value) if value and pd.notna(value) else '')
    return text

def capture_notification(driver):
    try:
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'Vue-Toastification__toast-body') or @role='alert']"))
        )
        elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'Vue-Toastification__toast-body') or @role='alert']")
        return [el.text.strip() for el in elements if el.text.strip()]
    except:
        return []

def run_test_case(test_case, headless=True, repeat=1, csv_row=None):
    logs = []
    for i in range(repeat):
        logs.append(f"▶️ Run {i + 1}/{repeat} - '{test_case['name']}'")
        try:
            options = Options()
            if headless:
                options.add_argument("--headless")
                            # Add options to clear cache and cookies
            options.add_argument("--incognito")  # Start browser in incognito mode
            options.add_argument("--disable-extensions")  # Disable extensions to avoid interference
            options.add_argument("--disable-cache")  # Disable the cache
            driver = webdriver.Chrome(options=options)
            driver.maximize_window()
            driver.delete_all_cookies()
            driver.refresh()
            for step in test_case["steps"]:
                action = step["action"]
                wait_time = step.get("wait", 0)

                if action == "visit":
                    #driver.refresh()
                    expected_url = substitute_placeholders(step["url"], csv_row)
                    # Clear cookies and cache before navigating to the URL
                    #driver.delete_all_cookies()
                    #driver.execute_script("window.localStorage.clear();")
                    #driver.execute_script("window.sessionStorage.clear();")
                    #driver.get(expected_url)
                    driver.refresh()
                    driver.get(expected_url)
                    time.sleep(1)  # Give the page time to load

                    actual_url = driver.current_url
                    page_title = driver.title
                    logs.append(f"🌐 {page_title} {expected_url}")

                    if expected_url.rstrip('/') != actual_url.rstrip('/'):
                        logs.append(f"❌ No Access")
                        #logs.append(f"❌ URL Mismatch: Expected '{expected_url}' but got '{actual_url}'")
                        #driver.quit()
                        #return logs  # Stop test execution early

                    # Toast Notifications
                    notifications = capture_notification(driver)
                    for note in notifications:
                        logs.append(f"🔔 Popup Detected: '{note}'")
                        time.sleep(10)

                    # JS Alert
                    try:
                        alert = driver.switch_to.alert
                        logs.append(f"⚠️ JS Alert Detected: '{alert.text}'")
                        alert.accept()
                        time.sleep(10)
                    except:
                        pass

                elif action == "click":
                    find_element(driver, step).click()
                    logs.append(f"🖱️ Clicked {step['selector_type']} = {step['selector_value']}")

                    notifications = capture_notification(driver)
                    for note in notifications:
                        logs.append(f"🔔 Popup Detected: '{note}'")
                        time.sleep(10)

                    try:
                        alert = driver.switch_to.alert
                        logs.append(f"⚠️ JS Alert Detected: '{alert.text}'")
                        alert.accept()
                        time.sleep(10)
                    except:
                        pass

                    try:
                        WebDriverWait(driver, 2).until(
                            EC.presence_of_all_elements_located((By.CLASS_NAME, "el-form-item__error"))
                        )
                        for el in driver.find_elements(By.CLASS_NAME, "el-form-item__error"):
                            error_text = el.text.strip()
                            if error_text:
                                logs.append(f"❗ Validation Error: '{error_text}'")
                    except:
                        continue

                elif action == "input":
                    element = find_element(driver, step)
                    element.clear()
                    value = substitute_placeholders(step["text"], csv_row)
                    element.send_keys(value)
                    logs.append(f"⌨️ Input '{value}'")

                elif action == "assert":
                    value = substitute_placeholders(step["text"], csv_row)
                    assert value in driver.page_source
                    logs.append(f"✅ Asserted '{value}' in page source")

                elif action == "select_dropdown":
                    dropdown_id = step["selector_value"]
                    option_text = substitute_placeholders(step["text"], csv_row)
                    dropdown = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, dropdown_id))
                    )
                    dropdown.click()
                    option = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH, f"//li[text()='{option_text}']"))
                    )
                    option.click()
                    logs.append(f"🔽 Selected '{option_text}' from dropdown ID '{dropdown_id}'")

                if wait_time > 0:
                    time.sleep(wait_time)

            driver.quit()

        except Exception as e:
            logs.append(f"❌ Error: {e}")
            try:
                driver.quit()
            except:
                pass

    return logs

# --- Streamlit UI ---

st.set_page_config(layout="wide")
st.title("🧪 Web Automation Test Runner")

if "steps" not in st.session_state:
    st.session_state.steps = []
if "editing_index" not in st.session_state:
    st.session_state.editing_index = None
if "active_test_name" not in st.session_state:
    st.session_state.active_test_name = ""

test_cases = load_test_cases()

# Sidebar for Test Case Management
with st.sidebar:
    st.header("📦 Manage Test Cases")
    mode = st.radio("Mode", ["Create New", "Edit Existing", "Delete"])

    if mode == "Create New":
        test_name = st.text_input("Test Name", key="create_name")
        if test_name in [tc["name"] for tc in test_cases]:
            st.warning("Test name must be unique.")
            test_name = None

    elif mode == "Edit Existing":
        selected = st.selectbox("Select Test Case", [tc["name"] for tc in test_cases])
        test_name = selected
        if st.session_state.active_test_name != selected:
            selected_case = next(tc for tc in test_cases if tc["name"] == selected)
            st.session_state.steps = selected_case["steps"]
            st.session_state.active_test_name = selected

    elif mode == "Delete":
        del_name = st.selectbox("Select Test Case", [tc["name"] for tc in test_cases])
        if st.button("⚠️ Confirm Delete"):
            test_cases = [tc for tc in test_cases if tc["name"] != del_name]
            save_test_cases(test_cases)
            st.success(f"🗑️ Deleted '{del_name}'")
            st.rerun()
        test_name = None

    editing = st.session_state.steps[st.session_state.editing_index] if st.session_state.editing_index is not None else None
    action = st.selectbox("Action", ["visit", "click", "input", "assert", "select_dropdown"],
                          index=(["visit", "click", "input", "assert", "select_dropdown"].index(editing["action"]) if editing else 0))
    wait_time = st.number_input("Wait Time", min_value=0, value=editing.get("wait", 0) if editing else 0)

    if action == "visit":
        url = st.text_input("URL", value=editing.get("url", "") if editing else "")
    elif action in ["input", "assert", "click"]:
        selector_type = st.selectbox("Selector Type", [
            "id", "name", "xpath", "css_selector", "class_name",
            "tag_name", "link_text", "partial_link_text", "placeholder"
        ], index=(["id", "name", "xpath", "css_selector", "class_name",
                   "tag_name", "link_text", "partial_link_text", "placeholder"]
                  .index(editing.get("selector_type", "xpath")) if editing else 0))
        selector_value = st.text_input("Selector Value", value=editing.get("selector_value", "") if editing else "")
        text = st.text_input("Text", value=editing.get("text", "") if editing and action in ["input", "assert"] else "") if action in ["input", "assert"] else None
    elif action == "select_dropdown":
        selector_type = "id"
        selector_value = st.text_input("Dropdown ID", value=editing.get("selector_value", "") if editing else "")
        text = st.text_input("Option Text", value=editing.get("text", "") if editing else "")

    if st.session_state.editing_index is not None:
        if st.button("💾 Save Edited Step"):
            idx = st.session_state.editing_index
            if action == "visit":
                st.session_state.steps[idx] = {"action": "visit", "url": url, "wait": wait_time}
            else:
                step = {
                    "action": action,
                    "selector_type": selector_type,
                    "selector_value": selector_value,
                    "wait": wait_time
                }
                if action in ["input", "assert", "select_dropdown"]:
                    step["text"] = text
                st.session_state.steps[idx] = step
            st.session_state.editing_index = None
            st.rerun()

        if st.button("❌ Cancel"):
            st.session_state.editing_index = None
            st.rerun()
    else:
        if st.button("Add Step"):
            if action == "visit" and url:
                st.session_state.steps.append({"action": "visit", "url": url, "wait": wait_time})
            elif action != "visit":
                step = {
                    "action": action,
                    "selector_type": selector_type,
                    "selector_value": selector_value,
                    "wait": wait_time
                }
                if action in ["input", "assert", "select_dropdown"]:
                    step["text"] = text
                st.session_state.steps.append(step)
            st.rerun()

# Step Display
st.subheader(f"🧾 Steps for: {test_name or 'New Test'}")
for i, step in enumerate(st.session_state.steps):
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.json(step, expanded=False)
    with col2:
        if st.button("✏️", key=f"edit_{i}"):
            st.session_state.editing_index = i
            st.rerun()
    with col3:
        if st.button("🗑️", key=f"del_{i}"):
            st.session_state.steps.pop(i)
            st.rerun()

# Save Test Case
if st.button("💾 Save Test Case") and test_name:
    existing = next((tc for tc in test_cases if tc["name"] == test_name), None)
    if existing:
        existing["steps"] = st.session_state.steps
    else:
        test_cases.append({"name": test_name, "steps": st.session_state.steps})
    save_test_cases(test_cases)
    st.success(f"✅ Test case '{test_name}' saved!")
    st.session_state.steps = []
    st.session_state.active_test_name = ""
    st.rerun()

# Run Tests Section
st.subheader("🚀 Run Tests")
selected_cases = st.multiselect("Select Cases", [tc["name"] for tc in test_cases])
repeat = st.number_input("Repeat Count", min_value=1, value=1)
headless = st.checkbox("Run Headless", value=True)

# CSV Upload
st.subheader("📄 Load CSV Data")
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
csv_data = pd.read_csv(uploaded_file) if uploaded_file else None
if csv_data is not None:
    st.write("✅ CSV Loaded:")
    st.dataframe(csv_data)

logs_output = []

if st.button("▶️ Run Selected Tests"):
    st.subheader("📜 Logs")
    for name in selected_cases:
        test = next(tc for tc in test_cases if tc["name"] == name)
        if csv_data is not None:
            for idx, row in csv_data.iterrows():
                logs = run_test_case(test, headless=headless, repeat=1, csv_row=row)
                for log in logs:
                    st.write(log)
                    logs_output.append(log)
        else:
            logs = run_test_case(test, headless=headless, repeat=repeat)
            for log in logs:
                st.write(log)
                logs_output.append(log)

    st.download_button("Download Log File", "\n".join(logs_output), file_name="test_logs.txt", mime="text/plain")
