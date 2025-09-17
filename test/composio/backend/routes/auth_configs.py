from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import webbrowser, requests
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

class GetAuthConfigRequest(BaseModel):
    nanoid: str

class UpdateAuthConfigRequest(BaseModel):
    nanoid: str
    new_credentials: dict

class ConnectRequest(BaseModel):
    auth_config_id: str

class ToolSearchRequest(BaseModel):
    search_term: str

# -----------------------------
# Endpoints
# -----------------------------
@router.post("/create-auth-config")
def create_auth_config(body: CreateAuthConfigRequest):
    url = f"{BASE_URL}/auth_configs"
    if not body.config_name:
        body.config_name = f"{body.toolkit_slug.capitalize()} Auth Config"

    if body.bearer_token:
        auth_type = "BEARER_TOKEN"
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
        auth_type = "API_KEY"
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
        auth_type = "OAUTH2"
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

# -----------------------------
# Fixed Delete Endpoint
# -----------------------------
@router.delete("/delete-auth-config/{nanoid}")
def delete_auth_config(nanoid: str):
    """
    Delete an auth config by nanoid (fixed to avoid 422 errors)
    """
    url = f"{BASE_URL}/auth_configs/{nanoid}"
    resp = requests.delete(url, headers=HEADERS)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return {"message": f"Auth config {nanoid} deleted successfully", "data": resp.json()}

# -----------------------------
# Connect Endpoint
# -----------------------------
@router.post("/connect-auth-config")
def connect_auth_config(body: ConnectRequest):
    """
    Connect an auth config using its ID
    """
    url = f"{BASE_URL}/auth_configs/{body.auth_config_id}/connect"
    resp = requests.post(url, headers=HEADERS)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return {"message": f"Auth config {body.auth_config_id} connected successfully", "data": resp.json()}
