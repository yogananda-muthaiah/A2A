"""
sales_order_a2a.py
A very simple A2A agent that creates a Sales Order in SAP S/4HANA Cloud.
This code uses only basic Python. No classes, no async, no extra magic.
"""

import os
import json
import requests
from dotenv import load_dotenv

# 1. Load settings from .env file
load_dotenv()

# 2. Read SAP connection data
CLIENT_ID = os.getenv("SAP_CLIENT_ID")
CLIENT_SECRET = os.getenv("SAP_CLIENT_SECRET")
TOKEN_URL = os.getenv("SAP_TOKEN_URL")
API_BASE = os.getenv("SAP_API_BASE")

# 3. Read the JSON payload for the Sales Order
with open("sales_order_payload.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

# 4. Get OAuth token (Client Credentials flow)
token_data = {
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
}
token_resp = requests.post(TOKEN_URL, data=token_data, timeout=10)
token_resp.raise_for_status()  # stop if error
access_token = token_resp.json()["access_token"]

# 5. Build headers for the OData call
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# 6. Call SAP to create the Sales Order
create_url = f"{API_BASE}/A_SalesOrder"
response = requests.post(create_url, headers=headers, json=payload, timeout=30)

# 7. Show result to the user
if response.status_code in (200, 201):
    result = response.json()["d"]
    print("OK – Sales Order created:")
    print("  Number:", result["SalesOrder"])
    print("  Status:", result.get("OverallSDProcessStatusDesc", "N/A"))
else:
    print("ERROR – SAP returned status", response.status_code)
    try:
        error_json = response.json()
        print("Details:", json.dumps(error_json, indent=2))
    except Exception:
        print("Raw answer:", response.text)
