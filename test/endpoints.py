from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
import webbrowser

# ================================
# Configuration
# ================================
API_KEY = "ak_GepAqzYQ6d6WggBF_zot"
BASE_URL = "https://backend.composio.dev/api/v3"

HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

app = FastAPI(title="Composio API Endpoints")

# ================================
# Request Models
# ================================
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

# ================================
# Helper Functions
# ================================
def create_auth_config(
    toolkit_slug: str,
    auth_type: str = "OAUTH2",
    bearer_token: Optional[str] = None,
    api_key_secret: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    config_name: Optional[str] = None
) -> Dict[str, Any]:
    url = f"{BASE_URL}/auth_configs"
    if not config_name:
        config_name = f"{toolkit_slug.capitalize()} Auth Config"

    if bearer_token:
        auth_type = "BEARER_TOKEN"
    elif api_key_secret:
        auth_type = "API_KEY"
    else:
        auth_type = "OAUTH2"

    if auth_type == "OAUTH2":
        data = {
            "toolkit": {"slug": toolkit_slug},
            "auth_config": {
                "type": "use_composio_managed_auth",
                "auth_scheme": "OAUTH2",
                "scopes": scopes or [],
                "name": config_name,
            },
        }
    elif auth_type == "BEARER_TOKEN":
        data = {
            "toolkit": {"slug": toolkit_slug},
            "auth_config": {
                "type": "user_provided_auth",
                "auth_scheme": "BEARER_TOKEN",
                "name": config_name,
                "credentials": {"bearer_token": bearer_token},
            },
        }
    elif auth_type == "API_KEY":
        data = {
            "toolkit": {"slug": toolkit_slug},
            "auth_config": {
                "type": "user_provided_auth",
                "auth_scheme": "API_KEY",
                "name": config_name,
                "credentials": {"api_key": api_key_secret},
            },
        }
    else:
        raise ValueError(f"Unsupported auth type: {auth_type}")

    resp = requests.post(url, headers=HEADERS, json=data)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


def delete_auth_config(nanoid: str):
    url = f"{BASE_URL}/auth_configs/{nanoid}"
    resp = requests.delete(url, headers=HEADERS)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return {"message": f"Auth config {nanoid} deleted", "data": resp.json()}


def get_auth_config(nanoid: str):
    url = f"{BASE_URL}/auth_configs/{nanoid}"
    resp = requests.get(url, headers=HEADERS)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


def list_auth_configs():
    url = f"{BASE_URL}/auth_configs"
    resp = requests.get(url, headers=HEADERS)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


def connect_gmail(auth_config_id: str, user_id: str = "default_user"):
    url = f"{BASE_URL}/connected_accounts/link"
    payload = {"auth_config_id": auth_config_id, "user_id": user_id}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=20)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    redirect_url = data.get("redirect_url") or data.get("redirectUrl")
    connected_account_id = data.get("connected_account_id")
    if redirect_url:
        webbrowser.open(redirect_url)
    return {"connected_account_id": connected_account_id, "redirect_url": redirect_url}


def search_toolkits(search_term: str, limit: int = 100):
    url = f"{BASE_URL}/toolkits"
    params = {"limit": limit}
    resp = requests.get(url, headers=HEADERS, params=params)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    items = resp.json().get("items", [])
    results = [
        item for item in items
        if search_term.lower() in item.get("name", "").lower() or search_term.lower() in item.get("slug", "").lower()
    ]
    return results


def update_auth_config(nanoid: str, api_key: str, new_credentials: dict):
    """
    Update credentials and fetch the updated client_id and client_secret to verify change.
    """
    headers = {"x-api-key": api_key}

    # Step 1: Get current type
    try:
        resp = requests.get(f"{BASE_URL}/auth_configs/{nanoid}", headers=headers)
        resp.raise_for_status()
        current_config = resp.json()
        current_type = current_config.get("type", "default")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch current config: {e}")

    # Step 2: Update credentials
    payload = {
        "type": current_type,
        "credentials": new_credentials
    }
    headers["Content-Type"] = "application/json"

    try:
        resp = requests.patch(f"{BASE_URL}/auth_configs/{nanoid}", headers=headers, json=payload)
        if not resp.ok:
            raise HTTPException(status_code=resp.status_code, detail=f"Update failed: {resp.text}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Network error during update: {e}")

    # Step 3: Fetch updated config to verify
    try:
        resp = requests.get(f"{BASE_URL}/auth_configs/{nanoid}", headers={"x-api-key": api_key})
        resp.raise_for_status()
        updated_config = resp.json()
        creds = updated_config.get("credentials", {})
        client_id = creds.get("client_id")
        client_secret = creds.get("client_secret")
        return {
            "updated_config": updated_config,
            "client_id": client_id,
            "client_secret": client_secret
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch updated config: {e}")


# ================================
# FastAPI Endpoints
# ================================
@app.post("/create-auth-config")
def create_auth_config_route(body: CreateAuthConfigRequest):
    return create_auth_config(
        body.toolkit_slug,
        body.auth_type,
        body.bearer_token,
        body.api_key_secret,
        body.scopes,
        body.config_name
    )

@app.post("/delete-auth-config")
def delete_auth_config_route(body: DeleteAuthConfigRequest):
    return delete_auth_config(body.nanoid)

@app.post("/get-auth-config")
def get_auth_config_route(body: GetAuthConfigRequest):
    return get_auth_config(body.nanoid)

@app.get("/list-auth-configs")
def list_auth_configs_route():
    return list_auth_configs()

@app.post("/connect-gmail")
def connect_gmail_route(body: ConnectRequest):
    return connect_gmail(body.auth_config_id)

@app.post("/search-toolkits")
def search_toolkits_route(body: ToolSearchRequest):
    return search_toolkits(body.search_term)

@app.post("/update-auth-config")
def update_auth_config_route(body: UpdateAuthConfigRequest):
    """
    Endpoint to update only the credentials of an auth config.
    """
    return update_auth_config(body.nanoid, API_KEY, body.new_credentials)
