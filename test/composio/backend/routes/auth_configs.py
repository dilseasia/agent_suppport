# backend/routes/auth_configs.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import requests
import time
from backend.config import API_KEY, BASE_URL, HEADERS

router = APIRouter()

# -----------------------------
# Request Models
# -----------------------------
class CreateAuthConfigRequest(BaseModel):
    organization_id: str
    toolkit_slug: str
    auth_type: str = "OAUTH2"
    bearer_token: Optional[str] = None
    api_key_secret: Optional[str] = None
    scopes: Optional[List[str]] = []
    config_name: Optional[str] = None


class DeleteAuthConfigRequest(BaseModel):
    organization_id: str
    nanoid: str


class ConnectRequest(BaseModel):
    organization_id: str
    auth_config_id: str


class StatusRequest(BaseModel):
    organization_id: str
    nanoid: str  # auth_config id
    status: str  # "ENABLED" or "DISABLED"


# -----------------------------
# Endpoints
# -----------------------------
@router.post("/create-auth-config")
def create_auth_config(body: CreateAuthConfigRequest):
    url = f"{BASE_URL}/auth_configs?organization_id={body.organization_id}"

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
def list_auth_configs(organization_id: str = Query(..., description="Organization ID")):
    configs_url = f"{BASE_URL}/auth_configs?organization_id={organization_id}"
    configs_resp = requests.get(configs_url, headers=HEADERS)
    if not configs_resp.ok:
        raise HTTPException(status_code=configs_resp.status_code, detail=configs_resp.text)
    configs_data = configs_resp.json()
    configs = configs_data.get("items", [])

    # Get connected accounts for this organization
    connected_url = f"{BASE_URL}/connected_accounts?organization_id={organization_id}"
    connected_resp = requests.get(connected_url, headers=HEADERS)
    if not connected_resp.ok:
        raise HTTPException(status_code=connected_resp.status_code, detail=connected_resp.text)
    connected_data = connected_resp.json()
    connected_accounts = connected_data.get("items", [])

    # Count connections per auth_config
    counts = {}
    for acc in connected_accounts:
        raw_auth = acc.get("auth_config_id") or acc.get("authConfigId") or acc.get("auth_config")
        if isinstance(raw_auth, dict):
            auth_id = raw_auth.get("nanoid") or raw_auth.get("id")
        else:
            auth_id = raw_auth
        if not auth_id:
            continue
        counts[auth_id] = counts.get(auth_id, 0) + 1

    for cfg in configs:
        cfg_id = cfg.get("nanoid") or cfg.get("id")
        cfg["connections_count"] = counts.get(cfg_id, 0)

    return {"items": configs}


@router.delete("/delete-auth-config/{nanoid}")
def delete_auth_config(nanoid: str, organization_id: str = Query(...)):
    url = f"{BASE_URL}/auth_configs/{nanoid}?organization_id={organization_id}"
    resp = requests.delete(url, headers=HEADERS)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return {"message": f"Auth config {nanoid} deleted successfully", "data": resp.json()}


# -----------------------------
# Connect Gmail Function
# -----------------------------
def connect_gmail(organization_id: str, auth_config_id: str):
    url = f"{BASE_URL}/connected_accounts/link?organization_id={organization_id}"
    payload = {"auth_config_id": auth_config_id, "user_id": "daljeet44"}  # <-- dynamic user_id later
    r = requests.post(url, headers=HEADERS, json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()
    redirect_url = data.get("redirect_url") or data.get("redirectUrl")
    connected_account_id = data.get("connected_account_id")
    return redirect_url, connected_account_id


@router.post("/connect-auth-config")
def connect_auth_config(body: ConnectRequest):
    try:
        redirect_url, connected_account_id = connect_gmail(body.organization_id, body.auth_config_id)
        if not redirect_url:
            raise HTTPException(status_code=500, detail="Failed to get redirect URL from backend.")
        return {"redirect_url": redirect_url, "connected_account_id": connected_account_id}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/set-auth-config-status")
def set_auth_config_status(body: StatusRequest):
    url = f"{BASE_URL}/auth_configs/{body.nanoid}/{body.status}?organization_id={body.organization_id}"
    try:
        r = requests.patch(url, headers=HEADERS)
        r.raise_for_status()
        return {"message": f"Auth config {body.nanoid} status set to {body.status}", "data": r.json()}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
