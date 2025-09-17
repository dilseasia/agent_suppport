import requests
import json
import uuid
import webbrowser
import time

API_KEY = "ak_GepAqzYQ6d6WggBF_zot"   # 🔑 replace with your key
BASE_URL = "https://backend.composio.dev/api/v3"

HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

def connect_gmail(auth_config_id: str):
    """Initiate Gmail OAuth connection and open browser"""
    url = f"{BASE_URL}/connected_accounts/link"
    # user_id = str(uuid.uuid4())  # 👈 yaha tum apna app user_id bhi de sakte ho
    user_id="daljeet44"
    payload = {"auth_config_id": auth_config_id, "user_id": user_id}

    r = requests.post(url, headers=HEADERS, json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()

    redirect_url = data.get("redirect_url") or data.get("redirectUrl")
    connected_account_id = data.get("connected_account_id")

    print("✅ Gmail connect flow initiated.")
    print("🔗 Redirect URL:", redirect_url)
    if redirect_url:
        webbrowser.open(redirect_url)

    return connected_account_id

def poll_connection_status(connected_account_id: str):
    """Poll connection status until CONNECTED"""
    url = f"{BASE_URL}/connected_accounts/{connected_account_id}"
    for i in range(20):
        r = requests.get(url, headers=HEADERS, timeout=15)
        if not r.ok:
            print("⚠️ Failed to fetch status:", r.text)
            break
        status = r.json().get("status")
        print(f"⏳ Attempt {i+1}: Status =", status)
        if status and status.upper() in ("CONNECTED", "ACTIVE"):
            print("🎉 Gmail Connected Successfully!")
            return True
        elif status and status.upper() in ("FAILED", "ERROR"):
            print("❌ Gmail Connection Failed.")
            return False
        time.sleep(3)
    print("⌛ Timeout waiting for connection.")
    return False

if __name__ == "__main__":

    AUTH_CONFIG_ID = "ac_GTcy9QcHBKJr"  
    
    connected_account_id = connect_gmail(AUTH_CONFIG_ID)
    if connected_account_id:
        poll_connection_status(connected_account_id)
