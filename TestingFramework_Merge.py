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
from bs4 import BeautifulSoup
from datetime import datetime
from PIL import Image

TARGET_WIDTH_PX = 100
TARGET_HEIGHT_PX = 100

def get_image_scale(img_path, target_width_px=200, target_height_px=200):
    try:
        with Image.open(img_path) as img:
            original_width, original_height = img.size
            x_scale = target_width_px / original_width
            y_scale = target_height_px / original_height
            return x_scale, y_scale
    except Exception as e:
        print(f"Error calculating image scale: {e}")
        return 1.0, 1.0


# Create base filename with test case names and timestamp
#file_base_name = "_".join(selected_cases).replace(" ", "_")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Function to identify selectors from HTML tag
def identify_selectors_from_html(html_tag):
    soup = BeautifulSoup(html_tag, 'html.parser')
    element = soup.find()
    
    if element is None:
        return None
    
    selectors = {}
    
    # ID-based selector
    if element.get('id'):
        selectors['id'] = element.get('id')
    
    # Name-based selector
    if element.get('name'):
        selectors['name'] = element.get('name')
    
    # CSS Class-based selector
    if element.get('class'):
        selectors['css_selector'] = f".{' '.join(element.get('class'))}"
    
    # XPath selector
    xpath = f"//{element.name}"
    if element.get('id'):
        xpath += f"[@id='{element.get('id')}']"
    elif element.get('name'):
        xpath += f"[@name='{element.get('name')}']"
    if element.get('class'):
        xpath += f"[contains(@class, '{' '.join(element.get('class'))}')]"
    selectors['xpath'] = xpath
    
    # Placeholder (if input or textarea)
    if element.get('placeholder'):
        selectors['placeholder'] = element.get('placeholder')
    
    return selectors

TEST_CASES_FILE = "test_cases.json"

# Load / Save JSON test cases
def load_test_cases():
    if os.path.exists(TEST_CASES_FILE):
        with open(TEST_CASES_FILE, "r") as file:
            return json.load(file)
    return []

def save_test_cases(test_cases):
    with open(TEST_CASES_FILE, "w") as file:
        json.dump(test_cases, file, indent=4)

# Universal element finder
def find_element(driver, selector_type, selector_value, index=0):
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
    elements = driver.find_elements(selectors[selector_type], selector_value)
    if elements and index < len(elements):
        return elements[index]
    else:
        raise Exception(f"No element found at index {index} for {selector_type}: {selector_value}")

def substitute_placeholders(text, csv_row):
    if not isinstance(text, str) or csv_row is None:
        return text
    placeholders = re.findall(r"\{\{(.*?)\}\}", text)
    for placeholder in placeholders:
        value = csv_row.get(placeholder) if isinstance(csv_row, (dict, pd.Series)) else None
        text = text.replace(f"{{{{{placeholder}}}}}", str(value) if value and pd.notna(value) else '')
    return text

def capture_notification(driver):
    try:
        WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//*[contains(@class, 'Vue-Toastification__toast-body') or @role='alert' or contains(@class, 'el-form-item__error')]")
            )
        )
        elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'Vue-Toastification__toast-body') or @role='alert' or contains(@class, 'el-form-item__error')]")
        notifications = [el.text.strip() for el in elements if el.text.strip()]
        time.sleep(1)
        for el in elements:
            try:
                close_buttons = driver.find_elements(By.CSS_SELECTOR, ".Vue-Toastification__close-button")
                # Click each close button
                for button in close_buttons:
                    try:
                        button.click()
                    except Exception as e:
                        print(f"Error clicking toast close button: {e}")
                        time.sleep(0.5)
            except:
                pass
        return notifications
    except:
        return []

def run_test_case(test_case, headless=True, repeat=1, csv_row=None):
    logs_output = []
    for _ in range(repeat):
        try:
            options = Options()
            if headless:
                options.add_argument("--headless=new")
            options.add_argument("--incognito")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-cache")
            driver = webdriver.Chrome(options=options)
            driver.maximize_window()
            driver.delete_all_cookies()
            driver.refresh()
            driver.refresh()  

            for step in test_case["steps"]:
                action = step["action"]
                wait_time = step.get("wait", 0)
                index = step.get("index", 0)
                #driver.refresh()
                step_log = {
                    "action": action,
                    "selector_type": step.get("selector_type", ""),
                    "selector_value": step.get("selector_value", ""),
                    "url": step.get("url", ""),
                    "text": step.get("text", ""),
                    "index": index,
                    "wait_time": wait_time,
                    "actual_url": "",
                    "status": "",
                    "notifications": []
                }

                if action == "visit":
                    driver.refresh()
                    expected_url = substitute_placeholders(step["url"], csv_row)
                    driver.get(expected_url)
                    time.sleep(1)
                    actual_url = driver.current_url
                    step_log["actual_url"] = actual_url
                    step_log["status"] = "✅ Success" if expected_url.rstrip('/') == actual_url.rstrip('/') else "❌ No Access"
                                    # Generate screenshot file path
                    screenshot_filename = f"{SCREENSHOT_DIR}/step_{timestamp}_{action}_{int(time.time()*1000)}.png"
                    driver.save_screenshot(screenshot_filename)
                    step_log["screenshot"] = screenshot_filename
                    notifications = capture_notification(driver)
                    if notifications:
                        step_log["notifications"] = notifications
                        if any("success" in str(n).lower() for n in notifications):
                            step_log["status"] = "✅ Success"
                        else:
                            step_log["status"] = "❌ Failed"

                elif action == "click":
                    find_element(driver, step["selector_type"], step["selector_value"], index).click()
                    step_log["status"] = "✅ Clicked"
                    time.sleep(0.5)                    
                                                        # Generate screenshot file path
                    screenshot_filename = f"{SCREENSHOT_DIR}/step_{timestamp}_{action}_{int(time.time()*1000)}.png"
                    driver.save_screenshot(screenshot_filename)
                    step_log["screenshot"] = screenshot_filename
                    notifications = capture_notification(driver)
                    if notifications:
                        step_log["notifications"] = notifications
                        if any("success" in str(n).lower() for n in notifications):
                            step_log["status"] = "✅ Success"
                        else:
                            step_log["status"] = "❌ Failed"

                elif action == "input":
                    element = find_element(driver, step["selector_type"], step["selector_value"], index)
                    element.clear()
                    value = substitute_placeholders(step["text"], csv_row)
                    element.send_keys(value)
                                                        # Generate screenshot file path
                    screenshot_filename = f"{SCREENSHOT_DIR}/step_{timestamp}_{action}_{int(time.time()*1000)}.png"
                    driver.save_screenshot(screenshot_filename)
                    step_log["screenshot"] = screenshot_filename
                    step_log["status"] = f"✅ Input '{value}'"

                elif action == "assert":
                    value = substitute_placeholders(step["text"], csv_row)
                    assert value in driver.page_source
                                                        # Generate screenshot file path
                    screenshot_filename = f"{SCREENSHOT_DIR}/step_{timestamp}_{action}_{int(time.time()*1000)}.png"
                    driver.save_screenshot(screenshot_filename)
                    step_log["screenshot"] = screenshot_filename
                    step_log["status"] = f"✅ Asserted '{value}'"

                elif action == "select_dropdown":
                    dropdown = find_element(driver, step["selector_type"], step["selector_value"], index)
                    dropdown.click()
                                                        # Generate screenshot file path
                    screenshot_filename = f"{SCREENSHOT_DIR}/step_{timestamp}_{action}_{int(time.time()*1000)}.png"
                    driver.save_screenshot(screenshot_filename)
                    step_log["screenshot"] = screenshot_filename
                    time.sleep(1)

                    expected_text = substitute_placeholders(step["text"], csv_row).strip()
                    items = driver.find_elements(By.CSS_SELECTOR, "li.el-dropdown-menu__item")
                    selected = False
                    for item in items:
                        if item.is_displayed() and item.text.strip() == expected_text:
                            item.click()
                            step_log["status"] = f"✅ Selected '{item.text.strip()}'"
                            selected = True
                            
                            break
                    if not selected:
                        step_log["status"] = f"❌ Dropdown item '{expected_text}' not found"
                                                        # Generate screenshot file path
                    screenshot_filename = f"{SCREENSHOT_DIR}/step_{timestamp}_{action}_{int(time.time()*1000)}.png"
                    driver.save_screenshot(screenshot_filename)
                    step_log["screenshot"] = screenshot_filename
                    notifications = capture_notification(driver)
                    if notifications:
                        step_log["notifications"] = notifications
                        if any("success" in str(n).lower() for n in notifications):
                            step_log["status"] = "✅ Success"
                        else:
                            step_log["status"] = "❌ Failed"

                if csv_row is not None and "LoginEmail" in csv_row:
                    step_log["LoginEmail"] = csv_row["LoginEmail"]
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

# Streamlit App
st.set_page_config(layout="wide")
st.title("Automation Testing Framework")

if "steps" not in st.session_state:
    st.session_state.steps = []
if "editing_index" not in st.session_state:
    st.session_state.editing_index = None
if "active_test_name" not in st.session_state:
    st.session_state.active_test_name = ""


### HTML TAG SEARCH MOVED TO THE SIDE BAR###
#st.subheader("🔍 Identify Selector from HTML Tag")
#
#html_tag_input = st.text_area("Enter the HTML Tag", height=100)
#
#if html_tag_input:
#    selectors = identify_selectors_from_html(html_tag_input)
#    
#    if selectors:
#        st.write("### Suggested Selectors:")
#        for selector_type, selector_value in selectors.items():
#            st.write(f"- **{selector_type}**: `{selector_value}`")
#    else:
#        st.warning("Unable to parse the HTML tag. Please check the input format.")



test_cases = load_test_cases()

with st.sidebar:
    st.image("Logo.png", width=200)  # Provide the path to your logo image
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
    index = st.number_input("Element Index", min_value=0, value=editing.get("index", 0) if editing else 0) if action != "visit" else 0

    if action == "visit":
        url = st.text_input("URL", value=editing.get("url", "") if editing else "")
    else:
        selector_type = st.selectbox("Selector Type", [
            "id", "name", "xpath", "css_selector", "class_name", "tag_name", "link_text", "partial_link_text", "placeholder"
        ], index=(["id", "name", "xpath", "css_selector", "class_name", "tag_name", "link_text", "partial_link_text", "placeholder"].index(editing.get("selector_type", "xpath")) if editing else 0))
        selector_value = st.text_input("Selector Value", value=editing.get("selector_value", "") if editing else "")
        text = st.text_input("Text", value=editing.get("text", "") if editing and action in ["input", "assert", "select_dropdown"] else "") if action in ["input", "assert", "select_dropdown"] else None

    if st.session_state.editing_index is not None:
        if st.button("💾 Save Edited Step"):
            idx = st.session_state.editing_index
            if action == "visit":
                st.session_state.steps[idx] = {"action": "visit", "url": url, "wait": wait_time}
            else:
                step = {"action": action, "selector_type": selector_type, "selector_value": selector_value, "wait": wait_time, "index": index}
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
                step = {"action": action, "selector_type": selector_type, "selector_value": selector_value, "wait": wait_time, "index": index}
                if action in ["input", "assert", "select_dropdown"]:
                    step["text"] = text
                st.session_state.steps.append(step)
            st.rerun()
            

    # Section for identifying selectors from HTML
    st.subheader("🔍 Identify Selector from HTML Tag")

    html_tag_input = st.text_area("Enter the HTML Tag", height=200)

    if html_tag_input:
        selectors = identify_selectors_from_html(html_tag_input)
        
        if selectors:
            st.write("### Suggested Selectors:")
            for selector_type, selector_value in selectors.items():
                st.write(f"- **{selector_type}**: `{selector_value}`")
        else:
            st.warning("Unable to parse the HTML tag. Please check the input format.") 

# Display each step with options to edit, delete, and reorder
for i, step in enumerate(st.session_state.steps):
    col1, col2, col3, col4, col5 = st.columns([5, 1, 1, 1, 1])  # Added columns for reorder buttons
    with col1:
        st.write(step)  # Use st.write() instead of st.json() to ensure it's expanded
    with col2:
        if st.button("✏️", key=f"edit_{i}"):
            st.session_state.editing_index = i
            st.rerun()
    with col3:
        if st.button("🗑️", key=f"del_{i}"):
            st.session_state.steps.pop(i)
            st.rerun()
    with col4:
        if i > 0 and st.button("↑", key=f"move_up_{i}"):  # Move up button
            st.session_state.steps[i], st.session_state.steps[i - 1] = st.session_state.steps[i - 1], st.session_state.steps[i]
            st.rerun()
    with col5:
        if i < len(st.session_state.steps) - 1 and st.button("↓", key=f"move_down_{i}"):  # Move down button
            st.session_state.steps[i], st.session_state.steps[i + 1] = st.session_state.steps[i + 1], st.session_state.steps[i]
            st.rerun()

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

st.subheader("🚀 Run Tests")
selected_cases = st.multiselect("Select Cases", [tc["name"] for tc in test_cases])
repeat = st.number_input("Repeat Count", min_value=1, value=1)
headless = st.checkbox("Run Headless", value=False)

st.subheader("📄 Load CSV Data")
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
csv_data = pd.read_csv(uploaded_file) if uploaded_file else None
if csv_data is not None:
    st.write("✅ CSV Loaded:")
    st.dataframe(csv_data)


# Custom CSS to set a background image
background_image = 'Background.png'
st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url({background_image});
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        height: 100vh;
    }}
    </style>
    """,
    unsafe_allow_html=True
)
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

    logs_df = pd.DataFrame(logs_output)

    if "LoginEmail" in logs_df.columns:
        cols = ["LoginEmail"] + [col for col in logs_df.columns if col != "LoginEmail"]
        logs_df = logs_df[cols]

    st.write(logs_df)

    if not logs_df.empty:
        file_base_name = "_".join(selected_cases).replace(" ", "_")

        # CSV EXPORT
        csv_bytes = logs_df.to_csv(index=False).encode("utf-8-sig")
        csv_filename = f"{file_base_name}_{timestamp}_logs.csv"
        # Download CSV Button commented
        #st.download_button("Download Log CSV", data=csv_bytes, file_name=csv_filename, mime="text/csv")

        # EXCEL EXPORT with images
        excel_filename = f"{file_base_name}_{timestamp}_logs.xlsx"
        excel_data = io.BytesIO()

        with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
            workbook = writer.book
            cell_format_top_left = workbook.add_format({'valign': 'top', 'align': 'left'})
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#1F4E78',     # Blue background (Excel-style blue)
                'font_color': 'white',     # White font
                'valign': 'top',
                'align': 'left'
            })

            if "LoginEmail" in logs_df.columns:
                for email in logs_df["LoginEmail"].dropna().unique():
                    sheet_df = logs_df[logs_df["LoginEmail"] == email]
                    sheet_name = re.sub(r'[^A-Za-z0-9]', '_', str(email))[:31]  # Excel sheet name max length is 31
                    sheet_df.to_excel(writer, index=False, sheet_name=sheet_name, startrow=1, header=False)
                    worksheet = writer.sheets[sheet_name]

                    # Write headers
                    for col_num, value in enumerate(sheet_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    # Apply alignment to all data cells (excluding image insertion)
                    for row_num in range(1, len(sheet_df) + 1):
                        for col_num, col_name in enumerate(sheet_df.columns):
                            if col_name != "screenshot":
                                max_len = max(sheet_df[col_name].astype(str).map(len).max(),len(str(col_name)))
                                worksheet.set_column(col_num, col_num, max_len + 2)                            
                                cell_value = sheet_df.iloc[row_num - 1, col_num]
                                worksheet.write(row_num, col_num, str(cell_value), cell_format_top_left)
                    # Format screenshot column
                    for col_num, column in enumerate(sheet_df.columns):

                        if column == "screenshot":
                            worksheet.set_column(col_num, col_num, 25)  # Fixed width for images
                            for row_num, path in enumerate(sheet_df["screenshot"], start=1):
                                max_len = max(sheet_df[column].astype(str).map(len).max(),len(str(column)))
                                worksheet.set_column(col_num, col_num, max_len + 2)                                            
                                if os.path.exists(path):
                                    x_scale, y_scale = get_image_scale(path, 400, 200)
                                    worksheet.set_row(row_num, 153)
                                    worksheet.insert_image(row_num, col_num, path, {
                                        'x_offset': 2,
                                        'y_offset': 2,
                                        'x_scale': x_scale,
                                        'y_scale': y_scale,
                                        'object_position': 1
                                    })

            else:
                # Fallback: write full DataFrame to single sheet
                logs_df.to_excel(writer, index=False, sheet_name='Logs', startrow=1, header=False)
                worksheet = writer.sheets['Logs']
                for col_num, value in enumerate(logs_df.columns.values):
                    worksheet.write(0, col_num, value, cell_format_top_left)

        excel_data.seek(0)
        st.download_button("Download Log Excel", data=excel_data, file_name=excel_filename,
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # ✅ Cleanup: Delete screenshots after Excel is prepared
        for path in logs_df["screenshot"].dropna():
            if isinstance(path, str) and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    st.warning(f"⚠️ Could not delete {path}: {e}")
