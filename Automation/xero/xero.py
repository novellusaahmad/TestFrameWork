import requests
import json
import os
import time
from datetime import datetime, timedelta, timezone
import re

# Xero API credentials
CLIENT_ID = 'B84057C2274744FE989EBEB07FA0183C'
CLIENT_SECRET = 'AaQyPWjWhLkbGPEaVcD2_cOOe7TTvg9g4gsaBypy_Nvj_ArD'
TOKEN_URL = 'https://identity.xero.com/connect/token'
API_URL = "https://api.xero.com/api.xro/2.0/"
REFRESH_TOKEN_FILE = "xero_tokens.json"

# Modules to Extract (All Modules)
MODULES = ["Accounts", "BankTransactions", "Contacts", "Invoices",
           "Payments", "ManualJournals", "Currencies", "Organisations","CreditNotes","BankTransfers","BatchPayments","Overpayments","TrackingCategories"]

# Date and Filename Formatting
current_datetime = datetime.now()
filename = current_datetime.strftime("%Y-%m-%d")  # Format date as filename
print("Generated filename:", filename)


def load_tokens():
    """ Load refresh and access tokens from a local file """
    if os.path.exists(REFRESH_TOKEN_FILE):
        with open(REFRESH_TOKEN_FILE, "r") as file:
            return json.load(file)
    return {}


def save_tokens(tokens):
    """ Save tokens to a local file """
    with open(REFRESH_TOKEN_FILE, "w") as file:
        json.dump(tokens, file)


def refresh_access_token():
    """ Refresh the access token using the refresh token """
    tokens = load_tokens()
    refresh_token = tokens.get("refresh_token")
    
    if not refresh_token:
        raise Exception("No refresh token found. Please authenticate manually first.")
    
    token_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    
    response = requests.post(TOKEN_URL, data=token_data)
    
    if response.status_code != 200:
        print(f"Failed to refresh access token: {response.text}")
        raise Exception(f"Failed to refresh access token: {response.text}")
    
    new_tokens = response.json()
    
    if "access_token" not in new_tokens:
        raise Exception(f"Failed to refresh access token: {new_tokens}")
    
    save_tokens(new_tokens)
    return new_tokens["access_token"]


def convert_date_from_xero_format(date_str):
    """
    Convert /Date(1716544999043+0000)/ format to yyyy-mm-dd.
    """
    # Regex to extract the timestamp and timezone offset
    match = re.match(r'/Date\((\d+)([+-]\d{4})\)/', date_str)
    
    if not match:
        # If the date format does not match, return the input as is (avoid ValueError)
        return date_str
    
    timestamp = int(match.group(1))  # Extract timestamp in milliseconds
    timezone_offset = match.group(2)  # Extract timezone offset
    
    # Convert timestamp to seconds
    timestamp_in_seconds = timestamp / 1000
    
    # Create datetime object in UTC
    dt_utc = datetime.fromtimestamp(timestamp_in_seconds, timezone.utc)
    
    # Apply timezone offset (assuming it's in the format +0000 or -0500 etc.)
    hours_offset = int(timezone_offset[:3])
    minutes_offset = int(timezone_offset[0] + timezone_offset[3:5])
    offset = timedelta(hours=hours_offset, minutes=minutes_offset)
    
    # Adjust datetime based on the timezone offset
    dt_local = dt_utc + offset
    
    # Format the datetime as yyyy-mm-dd
    return dt_local.strftime('%Y-%m-%d')


def format_date_fields(data):
    """ Format all date fields in the data from ISO to yyyy-mm-dd, including Xero /Date format """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                # Check if value is in the /Date(...) format
                if value.startswith('/Date(') and value.endswith(')/'):
                    data[key] = convert_date_from_xero_format(value)
                # Check for ISO date format
                elif 'T' in value:
                    try:
                        # Attempt to parse and reformat date string
                        date_obj = datetime.fromisoformat(value.replace('Z', ''))
                        data[key] = date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        pass  # If it's not a date string, skip formatting
            elif isinstance(value, (dict, list)):
                format_date_fields(value)  # Recursive call if value is a dict or list
    elif isinstance(data, list):
        for item in data:
            format_date_fields(item)  # Recursive call for each item in the list
    return data


def fetch_data_with_offset(access_token, tenant_id, module, start_offset=0, batch_size=99):
    """ Fetch data using offset parameter dynamically determined from pageCount and itemCount for any module """
    page_size = batch_size  # The number of records to fetch per request
    offset = start_offset  # Start from a specific record number
    
    api_headers = {
        "Authorization": f"Bearer {access_token}",
        "Xero-tenant-id": tenant_id,
        "Accept": "application/json"
    }
    
    all_data = []
    print(f"Fetching {module} starting from offset {start_offset}...")

    while True:
        url = f"{API_URL}{module}?pageSize={page_size}&offset={offset}"
        response = requests.get(url, headers=api_headers)
        
        print(f"Fetching data from offset {offset}...")  # Debugging print
        
        if response.status_code == 401:  # Token expired
            print("Access token expired. Refreshing token...")
            access_token = refresh_access_token()  # Refresh the access token
            api_headers["Authorization"] = f"Bearer {access_token}"  # Update the header with the new token
            continue  # Retry the same request with the new token
        
        if response.status_code != 200:
            print(f"Failed to fetch {module} at offset {offset}. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Handle rate limiting (429 Too Many Requests)
            if response.status_code == 429:  # Too Many Requests
                print("Rate limit exceeded. Retrying after a short delay.")
                time.sleep(60)  # Wait 1 minute before retrying
                continue  # Retry the same offset (sequential fetching)
            
            # Handle other errors and retry logic (e.g., 500 Internal Server Errors)
            if response.status_code >= 500:
                print("Server error, retrying after delay.")
                time.sleep(60)  # Wait for a minute before retrying
                continue  # Retry the same offset (sequential fetching)
            
            break  # If it's another error, break out of the loop
        
        try:
            data = response.json()
            module_data = data.get(module, [])  # Fetch the data for the given module
            page_count = data.get("pageCount", 1)  # This is the number of pages available
            item_count = data.get("items", 0)  # Total items, which is the full number of records
            print(f"Fetched {len(module_data)} {module} records at offset {offset}.")  # Print number of records fetched per request
            current_page = (offset // page_size) + 1  # Calculate current page number
            print(f"Page {current_page}/{page_count} of {module} data.")  # Print the current page of the module
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response at offset {offset}. Response: {response.text}")
            break
        
        # Add fetched data to all_data list
        all_data.extend(module_data)
        
        # If we fetched fewer than the page size, we are likely at the last page
        if offset + page_size >= item_count:
            print(f"All {module} data fetched, stopping at offset {offset}.")
            break
        
        # Update the offset for the next page of data
        offset += page_size
    
    print(f"Total {module} records fetched: {len(all_data)}")  # Print the total number of records fetched for the module
    return all_data


def save_data_to_json(data, org_name, module_name):
    """ Save the fetched data to a JSON file within a specific folder structure """
    org_name = org_name.lower()
    module_name = module_name.lower()
    
    # Create the folder structure
    folder_path = f"xero_exports/{org_name}/{module_name}"
    os.makedirs(folder_path, exist_ok=True)
    
    # Define the filename based on the org name, module name, and date
    json_filename = f"{folder_path}/file_{filename}.json"
    
    # Add load_date and org name
    load_date = current_datetime.strftime('%Y-%m-%d')
    for record in data:
        record['load_date'] = load_date
        record['org'] = org_name
    
    # Format all dates
    data = format_date_fields(data)
    
    # Save the data to a JSON file
    with open(json_filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Data saved to {json_filename}")


def fetch_xero_data():
    """ Fetch data from Xero for all organizations and save it in a JSON file """
    access_token = refresh_access_token()
    
    # Get Xero Tenant IDs (all connected organizations)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    tenants_response = requests.get("https://api.xero.com/connections", headers=headers)
    
    if tenants_response.status_code != 200:
        return f"Failed to get tenants: {tenants_response.text}"
    
    tenants = tenants_response.json()
    if not tenants:
        return "No connected Xero organizations found."
    
    # Iterate over all tenants and fetch data for each module
    for tenant in tenants:
        tenant_id = tenant['tenantId']
        org_name = tenant['tenantName'].replace(" ", "_").lower()  # Convert to lowercase

        print(f"Fetching data for {org_name}...")

        # Iterate over all modules and fetch their data
        for module in MODULES:
            print(f"Fetching {module} for {org_name}...")
            all_data = fetch_data_with_offset(
                access_token, tenant_id, module, start_offset=0, batch_size=99
            )
            
            # Save data to a JSON file in the specific folder structure
            save_data_to_json(all_data, org_name, module)  # Convert to lowercase
            print(f"Data extracted successfully for {module} in {org_name}!")
    
    return "Data extracted successfully for all organizations and modules!"


if __name__ == "__main__":
    print(fetch_xero_data())
