from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
import time

# ================================
# Configuration
# ================================
API_KEY = "ak_GepAqzYQ6d6WggBF_zot"  # <-- Replace with your Composio API key
BASE_URL = "https://backend.composio.dev/api/v3"

HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

app = FastAPI(title="Composio Integration API")


# ================================
# Request Models
# ================================
class ConnectRequest(BaseModel):
    auth_config_id: str


class UpdateAuthConfigRequest(BaseModel):
    update_data: dict


class SetStatusRequest(BaseModel):
    status: str


class GetToolsRequest(BaseModel):
    user_id: str
    toolkits: Optional[List[str]] = None


# ================================
# Helper Functions
# ================================
def create_github_auth_config(config_name: str = "GitHub OAuth2 Config"):
    url = f"{BASE_URL}/auth_configs"
    payload = {
        "toolkit": {"slug": "github"},
        "auth_config": {
            "type": "use_composio_managed_auth",
            "auth_scheme": "OAUTH2",
            "scopes": ["repo", "user"],
            "name": config_name
        }
    }
    resp = requests.post(url, headers=HEADERS, json=payload)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


def create_google_calendar_auth_config(config_name: str = "Google Calendar OAuth2 Config"):
    url = f"{BASE_URL}/auth_configs"
    payload = {
        "toolkit": {"slug": "googlecalendar"},
        "auth_config": {
            "type": "use_composio_managed_auth",
            "auth_scheme": "OAUTH2",
            "scopes": [
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/calendar.events"
            ],
            "name": config_name
        }
    }
    resp = requests.post(url, headers=HEADERS, json=payload)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


def create_gmail_auth_config(config_name: str = "Gmail OAuth2 Config"):
    url = f"{BASE_URL}/auth_configs"
    payload = {
        "toolkit": {"slug": "gmail"},
        "auth_config": {
            "type": "use_composio_managed_auth",
            "auth_scheme": "OAUTH2",
            "scopes": [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.send"
            ],
            "name": config_name
        }
    }
    resp = requests.post(url, headers=HEADERS, json=payload)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


def connect_account(auth_config_id: str, user_id: str = "default_user"):
    url = f"{BASE_URL}/connected_accounts/link"
    payload = {"auth_config_id": auth_config_id, "user_id": user_id}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=20)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    return {
        "redirect_url": data.get("redirect_url") or data.get("redirectUrl"),
        "connected_account_id": data.get("connected_account_id")
    }


def poll_connection_status(connected_account_id: str):
    url = f"{BASE_URL}/connected_accounts/{connected_account_id}"
    for _ in range(20):
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if not resp.ok:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        status = (resp.json().get("status") or "").upper()
        if status in ("CONNECTED", "ACTIVE"):
            return {"status": status, "message": "Connected successfully"}
        if status in ("FAILED", "ERROR"):
            return {"status": status, "message": "Connection failed"}
        time.sleep(3)
    return {"status": "TIMEOUT", "message": "Connection did not complete in time"}


def list_auth_configs():
    url = f"{BASE_URL}/auth_configs"
    resp = requests.get(url, headers=HEADERS)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


def delete_auth_config(nanoid: str):
    url = f"{BASE_URL}/auth_configs/{nanoid}"
    resp = requests.delete(url, headers=HEADERS)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return {"message": f"Auth config {nanoid} deleted", "data": resp.json()}


def update_auth_config(nanoid: str, update_data: dict):
    url = f"{BASE_URL}/auth_configs/{nanoid}"
    resp = requests.patch(url, headers=HEADERS, json=update_data)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return {"message": f"Auth config {nanoid} updated", "data": resp.json()}


def set_auth_config_status(nanoid: str, status: str):
    url = f"{BASE_URL}/auth-configs/{nanoid}/status"
    resp = requests.patch(url, headers=HEADERS, json={"status": status.upper()})
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return {"message": f"Auth config {nanoid} set to {status.upper()}", "data": resp.json()}


def get_composio_tools(user_id: str, toolkits: Optional[List[str]] = None):
    url = f"{BASE_URL}/tools"
    params = {"user_id": user_id}
    if toolkits:
        params["toolkits"] = ",".join(toolkits)
    resp = requests.get(url, headers=HEADERS, params=params)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json().get("tools", [])


# ================================
# API Routes
# ================================

# --- GitHub OAuth2 ---
@app.post("/create-github-auth")
def create_github_auth_route():
    return create_github_auth_config()


# --- Google Calendar OAuth2 ---
@app.post("/create-google-calendar-auth")
def create_google_calendar_auth_route():
    return create_google_calendar_auth_config()


# --- Gmail OAuth2 ---
@app.post("/create-gmail-auth")
def create_gmail_auth_route():
    return create_gmail_auth_config()


# --- Connect Account ---
@app.post("/connect-account")
def connect_account_route(body: ConnectRequest):
    return connect_account(body.auth_config_id)


# --- Poll Connection Status ---
@app.get("/poll-connection-status")
def poll_connection_status_route(connected_account_id: str):
    return poll_connection_status(connected_account_id)


# --- List Auth Configs ---
@app.get("/list-auth-configs")
def list_auth_configs_route():
    return list_auth_configs()


# --- Delete Auth Config ---
@app.delete("/delete-auth-config/{nanoid}")
def delete_auth_config_route(nanoid: str):
    return delete_auth_config(nanoid)


# --- Update Auth Config ---
@app.patch("/update-auth-config/{nanoid}")
def update_auth_config_route(nanoid: str, body: UpdateAuthConfigRequest):
    return update_auth_config(nanoid, body.update_data)


# --- Set Auth Config Status ---
@app.patch("/set-auth-config-status/{nanoid}")
def set_auth_config_status_route(nanoid: str, body: SetStatusRequest):
    return set_auth_config_status(nanoid, body.status)


# --- Get Composio Tools ---
@app.post("/get-tools")
def get_tools_route(body: GetToolsRequest):
    return get_composio_tools(body.user_id, body.toolkits)
