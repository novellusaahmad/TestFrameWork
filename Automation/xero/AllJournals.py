import requests
import csv
import os
import json
import re
import time
from datetime import datetime, timezone

# Xero API credentials
CLIENT_ID = 'B84057C2274744FE989EBEB07FA0183C'
CLIENT_SECRET = 'AaQyPWjWhLkbGPEaVcD2_cOOe7TTvg9g4gsaBypy_Nvj_ArD'
TOKEN_URL = 'https://identity.xero.com/connect/token'
API_URL = "https://api.xero.com/api.xro/2.0/"
REFRESH_TOKEN_FILE = "xero_tokens.json"

# Modules to Extract (only Journals in this case)
MODULES = [
    "Journals"
]

current_datetime = datetime.now()

# Format the date as a string for the filename (e.g., YYYY-MM-DD_HH-MM-SS)
filename = current_datetime.strftime("%Y-%m-%d")

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
        print(f"? Failed to refresh access token: {response.text}")
        raise Exception(f"Failed to refresh access token: {response.text}")
    
    new_tokens = response.json()
    
    if "access_token" not in new_tokens:
        raise Exception(f"Failed to refresh access token: {new_tokens}")
    
    save_tokens(new_tokens)
    return new_tokens["access_token"]

def format_date(value):
    """ Convert ISO date format or Xero date format to YYYY-MM-DD """
    if isinstance(value, str):
        match = re.match(r"/Date\((\d+)\+\d+\)/", value)
        if match:
            timestamp = int(match.group(1)) / 1000
            return datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%d")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return value

def flatten_data(data):
    """ Flatten the nested structures of data into a single row """
    def flatten_dict(d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                if v and isinstance(v[0], dict):
                    for i, sub_item in enumerate(v):
                        items.extend(flatten_dict(sub_item, f"{new_key}_{i}", sep=sep).items())
                else:
                    items.append((new_key, ', '.join(map(str, v))))
            else:
                items.append((new_key, v))
        return dict(items)
    
    return [flatten_dict(item) for item in data]

def fetch_journals_data_with_offset(access_token, tenant_id, start_offset=0, batch_size=99):
    """ Fetch journals data using offset parameter between start_offset and end_offset in batches of 'batch_size' """
    module = "Journals"
    page_size = batch_size  # The number of records to fetch per request
    offset = start_offset  # Start from a specific journal number
    
    api_headers = {
        "Authorization": f"Bearer {access_token}",
        "Xero-tenant-id": tenant_id,
        "Accept": "application/json"
    }
    
    all_journals = []
    
    while True:
        print(f"Fetching journals from offset {offset} to {offset + batch_size - 1}...")

        url = f"{API_URL}{module}?pageSize={page_size}&offset={offset}"
        response = requests.get(url, headers=api_headers)
        
        if response.status_code != 200:
            print(f"? Failed to fetch journals at offset {offset}. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Handle rate limiting
            if response.status_code == 429:  # Too Many Requests
                print("Rate limit exceeded. Retrying after a short delay.")
                time.sleep(60)  # Wait 1 minute before retrying
                continue
            
            # Handle other errors and retry logic
            if response.status_code >= 500:
                print("Server error, retrying after delay.")
                time.sleep(60)
                continue
            
            break
        
        try:
            data = response.json().get("Journals", [])
        except json.JSONDecodeError as e:
            print(f"? Error decoding JSON response at offset {offset}. Response: {response.text}")
            break
        
        if not data:
            print("?? No more journals to fetch.")
            break
        
        all_journals.extend(data)
        
        # Update offset for the next page
        offset += page_size
        
        # If fewer than page_size records are fetched, assume we've reached the end
        if len(data) < page_size:
            print("No more journals available. Stopping.")
            break
    
    return all_journals

def save_journals_to_csv(journals_data, csv_writer, org_name):
    """ Save the fetched journals data to a CSV file with organization name """
    all_rows = []
    
    for entry in journals_data:
        # Flatten common fields from the journal entry (excluding JournalLines)
        common_fields = {key: format_date(entry.get(key, "")) for key in entry.keys() if key != "JournalLines"}

        # Iterate over JournalLines to merge them with common fields
        for line in entry.get("JournalLines", []):
            row = {**common_fields, **line}
            row.setdefault("SourceID", "")  # Ensure SourceID exists
            row.setdefault("SourceType", "")  # Ensure SourceType exists
            row["Organization"] = org_name  # Add organization name to each row
            all_rows.append(row)

    if all_rows:
        headers = sorted(set(key for row in all_rows for key in row.keys()))
        headers.append("Load_Date")  # Add Load_Date column
        headers.append("Account_Type")  # Add Account_Type column
        headers.append("Organization")  # Add Organization column
        csv_writer.writerow(headers)
        
        # Write rows
        for row in all_rows:
            row_values = [row.get(header, "") for header in headers[:-3]]  # Exclude "Load_Date", "Account_Type", "Organization"
            row_values.append(current_datetime.strftime("%Y-%m-%d"))  # Add today's date
            row_values.append('P/L' if row.get("AccountType", "") in ['EXPENSE', 'REVENUE', 'OVERHEADS'] else 'B/S')
            row_values.append(row["Organization"])  # Add organization name to the row
            csv_writer.writerow(row_values)

def fetch_xero_data():
    """ Fetch data from Xero for all organizations and save it """
    access_token = refresh_access_token()
    
    # Get Xero Tenant IDs
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
    
    # Loop through all tenants (organizations)
    for tenant in tenants:
        tenant_id = tenant['tenantId']
        org_name = tenant['tenantName'].replace(" ", "_").lower()  # Convert organization name to lowercase

        print(f"Fetching data for organization: {org_name}...")

        # Create organization-specific folder (in lowercase)
        org_folder = os.path.join(os.getcwd(), "xero_exports", org_name)
        os.makedirs(org_folder, exist_ok=True)

        for module in MODULES:
            print(f"Fetching {module} data for {org_name}...")

            # Create a subfolder for each module (e.g., Journals) in lowercase
            module_folder = os.path.join(org_folder, module.lower())  # Convert module name to lowercase
            os.makedirs(module_folder, exist_ok=True)

            all_journals_data = fetch_journals_data_with_offset(access_token, tenant_id, start_offset=0)
            
            if all_journals_data:
                # Save to the module folder
                file_path = os.path.join(module_folder, f"journals_{filename}.csv")
                with open(file_path, "w", newline="") as file:
                    csv_writer = csv.writer(file)
                    save_journals_to_csv(all_journals_data, csv_writer, org_name)  # Pass org_name
                    print(f"Data saved to {file_path}.")

# Execute the script to fetch and save Xero data for all organizations
fetch_xero_data()
