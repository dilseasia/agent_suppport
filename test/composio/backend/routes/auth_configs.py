# backend/routes/auth_configs.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import requests
import webbrowser
import time
from backend.config import API_KEY, BASE_URL, HEADERS

router = APIRouter()

# -----------------------------
# Request Models
# -----------------------------
class CreateAuthConfigRequest(BaseModel):
    toolkit_slug: str
    auth_type: str = "OAUTH2"
    bearer_token: Optional[str] = None
    api_key_secret: Optional[str] = None
    scopes: Optional[List[str]] = []
    config_name: Optional[str] = None

class DeleteAuthConfigRequest(BaseModel):
    nanoid: str

class ConnectRequest(BaseModel):
    auth_config_id: str

# -----------------------------
# Endpoints
# -----------------------------
@router.post("/create-auth-config")
def create_auth_config(body: CreateAuthConfigRequest):
    url = f"{BASE_URL}/auth_configs"
    if not body.config_name:
        body.config_name = f"{body.toolkit_slug.capitalize()} Auth Config"

    if body.bearer_token:
        data = {
            "toolkit": {"slug": body.toolkit_slug},
            "auth_config": {
                "type": "user_provided_auth",
                "auth_scheme": "BEARER_TOKEN",
                "name": body.config_name,
                "credentials": {"bearer_token": body.bearer_token},
            },
        }
    elif body.api_key_secret:
        data = {
            "toolkit": {"slug": body.toolkit_slug},
            "auth_config": {
                "type": "user_provided_auth",
                "auth_scheme": "API_KEY",
                "name": body.config_name,
                "credentials": {"api_key": body.api_key_secret},
            },
        }
    else:
        data = {
            "toolkit": {"slug": body.toolkit_slug},
            "auth_config": {
                "type": "use_composio_managed_auth",
                "auth_scheme": "OAUTH2",
                "scopes": body.scopes or [],
                "name": body.config_name,
            },
        }

    resp = requests.post(url, headers=HEADERS, json=data)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@router.get("/list-auth-configs")
def list_auth_configs():
    url = f"{BASE_URL}/auth_configs"
    resp = requests.get(url, headers=HEADERS)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

@router.delete("/delete-auth-config/{nanoid}")
def delete_auth_config(nanoid: str):
    url = f"{BASE_URL}/auth_configs/{nanoid}"
    resp = requests.delete(url, headers=HEADERS)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return {"message": f"Auth config {nanoid} deleted successfully", "data": resp.json()}

# -----------------------------
# Connect Gmail Function
# -----------------------------
def connect_gmail(auth_config_id: str):
    """Initiate Gmail OAuth connection and open browser"""
    url = f"{BASE_URL}/connected_accounts/link"
    user_id = "daljeet44"  # replace with your app user id if needed
    payload = {"auth_config_id": auth_config_id, "user_id": user_id}

    r = requests.post(url, headers=HEADERS, json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()

    redirect_url = data.get("redirect_url") or data.get("redirectUrl")
    connected_account_id = data.get("connected_account_id")

    if redirect_url:
        webbrowser.open(redirect_url)

    return connected_account_id

def poll_connection_status(connected_account_id: str):
    """Poll connection status until CONNECTED"""
    url = f"{BASE_URL}/connected_accounts/{connected_account_id}"
    for i in range(20):
        r = requests.get(url, headers=HEADERS, timeout=15)
        if not r.ok:
            break
        status = r.json().get("status")
        if status and status.upper() in ("CONNECTED", "ACTIVE"):
            return True
        elif status and status.upper() in ("FAILED", "ERROR"):
            return False
        time.sleep(3)
    return False

# -----------------------------
# Connect Endpoint
# -----------------------------
@router.post("/connect-auth-config")
def connect_auth_config(body: ConnectRequest):
    try:
        connected_account_id = connect_gmail(body.auth_config_id)
        if not connected_account_id:
            raise HTTPException(status_code=500, detail="Failed to initiate connection.")

        success = poll_connection_status(connected_account_id)
        if not success:
            raise HTTPException(status_code=500, detail="Connection failed or timed out.")

        return {"message": "Connected successfully", "connected_account_id": connected_account_id}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
