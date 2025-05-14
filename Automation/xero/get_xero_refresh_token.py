import requests
from flask import Flask, request, redirect
from urllib.parse import urlencode
import json

# Xero app credentials
CLIENT_ID = 'B84057C2274744FE989EBEB07FA0183C'
CLIENT_SECRET = 'AaQyPWjWhLkbGPEaVcD2_cOOe7TTvg9g4gsaBypy_Nvj_ArD'
REDIRECT_URI = 'http://localhost:5000/callback'

TOKEN_URL = 'https://identity.xero.com/connect/token'
AUTH_URL = 'https://login.xero.com/identity/connect/authorize'
REFRESH_TOKEN_FILE = "xero_tokens.json"

app = Flask(__name__)

@app.route('/')
def authorize():
    """ Redirect user to Xero's authentication page """
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'accounting.reports.read accounting.attachments.read files payroll.employees payroll.employees.read payroll.payslip payroll.payslip.read payroll.settings.read projects.read projects accounting.settings accounting.settings.read accounting.attachments files.read accounting.transactions accounting.journals.read accounting.transactions.read assets.read assets accounting.contacts accounting.contacts.read payroll.settings offline_access',
    }
    return redirect(f"{AUTH_URL}?{urlencode(params)}")

@app.route('/callback')
def callback():
    """ Handle OAuth callback, get the refresh token, and save it """
    auth_code = request.args.get('code')
    if not auth_code:
        return "Authorization failed. Please try again."

    # Exchange authorization code for tokens
    token_data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    
    token_response = requests.post(TOKEN_URL, data=token_data)
    tokens = token_response.json()

    if 'refresh_token' not in tokens:
        return f"Failed to obtain tokens: {tokens}"

    # Save tokens to a local file
    with open(REFRESH_TOKEN_FILE, "w") as file:
        json.dump(tokens, file)

    return "Authorization successful! Refresh token saved."

if __name__ == '__main__':
    app.run(debug=True)
