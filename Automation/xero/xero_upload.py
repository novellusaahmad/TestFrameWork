import requests
import csv
import os
import json
import re
from datetime import datetime
from datetime import timezone
import shutil
from azure.storage.filedatalake import DataLakeServiceClient
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Azure Storage account details (from environment variables)
STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME")
STORAGE_ACCOUNT_KEY = os.getenv("STORAGE_ACCOUNT_KEY")
FILE_SYSTEM_NAME = os.getenv("FILE_SYSTEM_NAME", "xero")  # Default to "xero" if not set
LOCAL_FOLDER_PATH = os.path.join(os.getcwd(), "xero_exports")  # Relative folder location
REMOTE_FOLDER_PATH = "xero_extract"  # Folder name in ADLS

def authenticate_datalake():
    """Authenticate to Azure Data Lake using account key."""
    try:
        service_client = DataLakeServiceClient(
            account_url=f"https://{STORAGE_ACCOUNT_NAME}.dfs.core.windows.net",
            credential=STORAGE_ACCOUNT_KEY
        )
        print("Authentication successful!")
        return service_client
    except Exception as e:
        print(f"Error during authentication: {e}")
        return None

def upload_folder_to_adls(service_client):
    """Upload a local folder to Azure Data Lake Storage Gen2."""
    try:
        file_system_client = service_client.get_file_system_client(FILE_SYSTEM_NAME)
        print(f"Connected to file system: {FILE_SYSTEM_NAME}")

        # Delete the remote folder if it exists
        try:
            remote_dir_client = file_system_client.get_directory_client(REMOTE_FOLDER_PATH)
            remote_dir_client.delete_directory()
            print(f"Deleted existing remote folder: {REMOTE_FOLDER_PATH}")
        except Exception as e:
            print(f"No existing remote folder to delete or error occurred: {e}")

        # Check if the local folder exists and has files
        if not os.path.exists(LOCAL_FOLDER_PATH):
            print(f"Local folder '{LOCAL_FOLDER_PATH}' does not exist!")
            return

        for root, _, files in os.walk(LOCAL_FOLDER_PATH):
            if not files:
                print(f"No files found in the folder '{root}'")
            for file in files:
                local_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_file_path, LOCAL_FOLDER_PATH)
                remote_file_path = f"{REMOTE_FOLDER_PATH.lower()}/{relative_path.lower()}".replace("\\", "/")

                # Log paths being processed
                print(f"Processing file: {local_file_path} -> {remote_file_path}")

                # Create directory structure in ADLS if it doesn't exist
                try:
                    directory_client = file_system_client.get_directory_client(os.path.dirname(remote_file_path))
                    directory_client.create_directory()
                    print(f"Directory created or already exists: {os.path.dirname(remote_file_path)}")
                except Exception as dir_err:
                    print(f"Error creating directory: {dir_err}")

                # Upload the file
                try:
                    file_client = file_system_client.get_file_client(remote_file_path)

                    with open(local_file_path, "rb") as f:
                        file_client.upload_data(f, overwrite=True)
                    print(f"Uploaded: {local_file_path} -> {remote_file_path}")
                except Exception as upload_err:
                    print(f"Error uploading file {local_file_path} to {remote_file_path}: {upload_err}")

        delete_local_folder(LOCAL_FOLDER_PATH)

        print("Upload complete and local folder deleted.")
    except Exception as e:
        print(f"Error during upload: {e}")


# Xero API credentials
CLIENT_ID = 'B84057C2274744FE989EBEB07FA0183C'
CLIENT_SECRET = 'AaQyPWjWhLkbGPEaVcD2_cOOe7TTvg9g4gsaBypy_Nvj_ArD'
TOKEN_URL = 'https://identity.xero.com/connect/token'
API_URL = "https://api.xero.com/api.xro/2.0/"
REFRESH_TOKEN_FILE = "xero_tokens.json"

# Modules to Extract
MODULES = ["Accounts", "BankTransactions", "Contacts", "Invoices", "Payments", "ManualJournals", "Currencies", "Organisations"]
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
    new_tokens = response.json()
    
    if "access_token" not in new_tokens:
        raise Exception(f"Failed to refresh access token: {new_tokens}")
    
    save_tokens(new_tokens)
    return new_tokens["access_token"]

def delete_local_folder(folder_path):
    """ Delete the specified local folder and its contents. """
    try:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            print(f"Deleted local folder: {folder_path}")
        else:
            print(f"Folder '{folder_path}' does not exist.")
    except Exception as e:
        print(f"Error while deleting folder: {e}")


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

def fetch_xero_data():
    """ Fetch all data from Xero and save it in separate folders per organization """
    access_token = refresh_access_token()
    
    # Get Xero Tenant IDs
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    tenants_response = requests.get("https://api.xero.com/connections", headers=headers)
    
    if tenants_response.status_code != 200:
        return f"Failed to get tenants: {tenants_response.json()}"
    
    tenants = tenants_response.json()
    if not tenants:
        return "No connected Xero organizations found."
    
    for tenant in tenants:
        tenant_id = tenant['tenantId']
        org_name = tenant['tenantName'].replace(" ", "_")

        for module in MODULES:
            print(f"Fetching {module} for {org_name}...")

            api_headers = {
                "Authorization": f"Bearer {access_token}",
                "Xero-tenant-id": tenant_id,
                "Accept": "application/json"
            }
            response = requests.get(f"{API_URL}{module}", headers=api_headers)
            org_folder = os.path.join(os.getcwd(), "xero_exports", org_name, module)
            print(org_folder)
            os.makedirs(org_folder.lower(), exist_ok=True)
            
            # Set permissions for the folder
            os.chmod(org_folder.lower(), 0o700)
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch {module} for {org_name}: {response.json()}")
                continue
            
            data = response.json().get(module, [])
            csv_file_path = os.path.join(org_folder.lower(), f"{org_name}_{module}_{filename}.csv")
            
            with open(csv_file_path, mode="w", newline="", encoding="utf-8") as file:
                csv_writer = csv.writer(file)
                
                if not data:
                    print(f"⚠ No data for {module} in {org_name}")
                    continue
                
                if module == "Journals":
                    all_rows = []
                    for entry in data:
                        common_fields = {key: format_date(entry.get(key, "")) for key in entry.keys() if key != "JournalLines"}
                        
                        for line in entry.get("JournalLines", []):
                            row = {**common_fields, **line}
                            row.setdefault("SourceID", "")  # Ensure SourceID exists
                            row.setdefault("SourceType", "")  # Ensure SourceType exists
                            all_rows.append(row)

                    headers = sorted(set(key for row in all_rows for key in row.keys()))
                    headers.append("Load_Date")  # Add Load_Date column
                    headers.append("Account_Type")
                    csv_writer.writerow(headers)
                    for row in all_rows:
                        row_values = [row.get(header, "") for header in headers[:-2]]  # Exclude "Load_Date","Account_Type"
                        row_values.append(current_datetime.strftime("%Y-%m-%d"))  # Add today's date
                        row_values.append('P/L' if row["AccountType"] in ['EXPENSE', 'REVENUE'] else 'B/S')
                        csv_writer.writerow(row_values)
                
                else:
                    flattened_data = flatten_data(data)
                    headers = sorted(set(key for entry in flattened_data for key in entry.keys()))
                    headers.append("Load_Date")  # Add Load_Date column
                    csv_writer.writerow(headers)
                    
                    for entry in flattened_data:
                        row_values = [format_date(entry.get(header, "")) for header in headers[:-1]]  # Exclude "Load_Date"
                        row_values.append(current_datetime.strftime("%Y-%m-%d"))  # Add today's date
                        csv_writer.writerow(row_values)

            # Set permissions for the CSV file
            os.chmod(csv_file_path, 0o600)
            
            print(f"✅ {module} data saved for {org_name} at {csv_file_path}")
    
    return "All data extracted successfully!"

if __name__ == "__main__":
    #print(fetch_xero_data())
    if not STORAGE_ACCOUNT_NAME or not STORAGE_ACCOUNT_KEY:
        print("Azure Storage credentials not set in environment variables.")
    else:
        service_client = authenticate_datalake()
        if service_client:
            upload_folder_to_adls(service_client)
        else:
            print("Authentication failed, cannot proceed with upload.")

