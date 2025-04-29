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
import csv
import io

# Constants
TEST_CASES_FILE = "test_cases.json"

# --- Helper Functions ---
def load_test_cases():
    """Load test cases from a JSON file."""
    if os.path.exists(TEST_CASES_FILE):
        with open(TEST_CASES_FILE, "r") as file:
            return json.load(file)
    return []

def save_test_cases(test_cases):
    """Save test cases to a JSON file."""
    with open(TEST_CASES_FILE, "w") as file:
        json.dump(test_cases, file, indent=4)

def find_element(driver, selector_type, selector_value):
    """Find an element by selector type."""
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
    """Replace placeholders in text with values from the CSV row."""
    if not isinstance(text, str) or csv_row is None:
        return text
    placeholders = re.findall(r"\{\{(.*?)\}\}", text)
    for placeholder in placeholders:
        value = csv_row.get(placeholder) if isinstance(csv_row, (dict, pd.Series)) else None
        text = text.replace(f"{{{{{placeholder}}}}}", str(value) if value and pd.notna(value) else '')
    return text

def capture_notification(driver):
    """Capture and close notifications or alerts from the page."""
    try:
        WebDriverWait(driver, 4).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//*[contains(@class, 'Vue-Toastification__toast-body') or @role='alert' or contains(@class, 'el-form-item__error')]")
            )
        )
        elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'Vue-Toastification__toast-body') or @role='alert' or contains(@class, 'el-form-item__error')]")
        notifications = [el.text.strip() for el in elements if el.text.strip()]

        for el in elements:
            try:
                close_button = el.find_element(By.XPATH, ".//button[contains(@class, 'close') or @aria-label='Close']")
                close_button.click()
                time.sleep(0.5)
            except Exception as e:
                print(f"Could not find close button for toast notification: {e}")

        return notifications
    except Exception as e:
        return []

def run_test_case(test_case, headless=True, repeat=1, csv_row=None):
    """Run a test case, repeat as necessary, and return the logs."""
    logs_output = []
    for _ in range(repeat):
        try:
            options = Options()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--incognito")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-cache")
            driver = webdriver.Chrome(options=options)
            driver.maximize_window()
            driver.delete_all_cookies()
            driver.refresh()

            for step in test_case["steps"]:
                action = step["action"]
                wait_time = step.get("wait", 0)

                step_log = {
                    "action": action,
                    "selector_type": step.get("selector_type", ""),
                    "selector_value": step.get("selector_value", ""),
                    "url": step.get("url", ""),
                    "text": step.get("text", ""),
                    "wait_time": wait_time,
                    "actual_url": "",
                    "status": "",
                    "js_alert": "No JS Alert",
                    "notifications": []
                }

                # Action handling
                if action == "visit":
                    driver.refresh()
                    expected_url = substitute_placeholders(step["url"], csv_row)
                    driver.get(expected_url)
                    time.sleep(1)

                    actual_url = driver.current_url
                    step_log["actual_url"] = actual_url
                    step_log["status"] = "✅ Success" if expected_url.rstrip('/') == actual_url.rstrip('/') else "❌ No Access"

                    notifications = capture_notification(driver)
                    if notifications:
                        step_log["notifications"] = notifications
                        if any("success" in str(n).lower() for n in notifications):
                            step_log["status"] = "✅ Success"
                        else:
                            step_log["status"] = "❌ Failed"

                elif action == "click":
                    find_element(driver, step["selector_type"], step["selector_value"]).click()
                    step_log["status"] = "✅ Clicked"
                    time.sleep(1)
                    notifications = capture_notification(driver)
                    if notifications:
                        step_log["notifications"] = notifications
                        if any("success" in str(n).lower() for n in notifications):
                            step_log["status"] = "✅ Success"
                        else:
                            step_log["status"] = "❌ Failed"

                elif action == "input":
                    element = find_element(driver, step["selector_type"], step["selector_value"])
                    element.clear()
                    value = substitute_placeholders(step["text"], csv_row)
                    element.send_keys(value)
                    step_log["status"] = f"✅ Input '{value}'"

                elif action == "assert":
                    value = substitute_placeholders(step["text"], csv_row)
                    assert value in driver.page_source
                    step_log["status"] = f"✅ Asserted '{value}' in page source"

                elif action == "select_dropdown":
                    dropdown_id = step["selector_value"]
                    option_text = substitute_placeholders(step["text"], csv_row)
                    dropdown = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.ID, dropdown_id))
                    )
                    dropdown.click()
                    option = WebDriverWait(driver, 2).until(
                        EC.visibility_of_element_located((By.XPATH, f"//li[text()='{option_text}']"))
                    )
                    option.click()
                    step_log["status"] = f"✅ Selected '{option_text}' from dropdown"

                # Add log entry for this step
                logs_output.append(step_log)

                if wait_time > 0:
                    time.sleep(wait_time)

            driver.quit()

        except Exception as e:
            logs_output.append({"status": f"❌ Error: {e}"})
            try:
                driver.quit()
            except:
                pass

    return logs_output
# Streamlit Interface
st.set_page_config(layout="wide")
st.title("🧪 Web Automation Test Runner")

if "steps" not in st.session_state:
    st.session_state.steps = []
if "editing_index" not in st.session_state:
    st.session_state.editing_index = None
if "active_test_name" not in st.session_state:
    st.session_state.active_test_name = ""

test_cases = load_test_cases()

# Sidebar for test case management
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

    # Step builder
    editing = st.session_state.steps[st.session_state.editing_index] if st.session_state.editing_index is not None else None

    action = st.selectbox("Action", ["visit", "click", "input", "assert"],
                          index=(["visit", "click", "input", "assert"].index(editing["action"]) if editing else 0))
    wait_time = st.number_input("Wait Time", min_value=0, value=editing.get("wait", 0) if editing else 0)

    if action == "visit":
        url = st.text_input("URL", value=editing.get("url", "") if editing else "")
    else:
        selector_type = st.selectbox("Selector Type", [
            "id", "name", "xpath", "css_selector", "class_name",
            "tag_name", "link_text", "partial_link_text", "placeholder"
        ], index=(["id", "name", "xpath", "css_selector", "class_name",
                   "tag_name", "link_text", "partial_link_text", "placeholder"]
                  .index(editing.get("selector_type", "xpath")) if editing else 0))
        selector_value = st.text_input("Selector Value", value=editing.get("selector_value", "") if editing else "")
        text = st.text_input("Text", value=editing.get("text", "") if editing and action in ["input", "assert"] else "") if action in ["input", "assert"] else None

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
                if action in ["input", "assert"]:
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
                if action in ["input", "assert"]:
                    step["text"] = text
                st.session_state.steps.append(step)
            st.rerun()

# Show current steps
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

# Save the test case
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

# Run test cases
st.subheader("🚀 Run Tests")
selected_cases = st.multiselect("Select Cases", [tc["name"] for tc in test_cases])
repeat = st.number_input("Repeat Count", min_value=1, value=1)
headless = st.checkbox("Run Headless", value=False)

# Upload CSV
st.subheader("📄 Load CSV Data")
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
csv_data = pd.read_csv(uploaded_file) if uploaded_file else None
if csv_data is not None:
    st.write("✅ CSV Loaded:")
    st.dataframe(csv_data)

# Run button
logs_output = []

if st.button("▶️ Run Selected Tests"):
    st.subheader("📜 Logs")
    for name in selected_cases:
        test = next(tc for tc in test_cases if tc["name"] == name)
        if csv_data is not None:
            for idx, row in csv_data.iterrows():
                logs = run_test_case(test, headless=headless, repeat=repeat, csv_row=row)
                for log in logs:
                    st.write(log)
                    logs_output.append(log)
        else:
            logs = run_test_case(test, headless=headless, repeat=repeat)
            for log in logs:
                st.write(log)
                logs_output.append(log)

    # Export logs to CSV and Excel
    logs_df = pd.DataFrame(logs_output)
    st.write(logs_df)

    if not logs_df.empty:
        # Export to CSV
        csv_data = logs_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="Download Log CSV",
            data=csv_data,
            file_name="test_logs.csv",
            mime="text/csv"
        )

        # Export to Excel
        excel_data = io.BytesIO()
        with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
            logs_df.to_excel(writer, index=False, sheet_name='Logs')

        # Move cursor to beginning of BytesIO stream
        excel_data.seek(0)
        st.download_button(
            label="Download Log Excel",
            data=excel_data,
            file_name="test_logs.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No logs to export.")
