import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from models import AuthConfigRecord

COMPOSIO_BASE_URL = "https://backend.composio.dev/api/v3"

def create_auth_config(
    composio_api_key: str,
    toolkit_slug: str,
    auth_type: str = "OAUTH2",
    bearer_token: Optional[str] = None,
    api_key_secret: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    config_name: Optional[str] = None
) -> Dict[str, Any]:
    url = f"{COMPOSIO_BASE_URL}/auth_configs"
    headers = {"x-api-key": composio_api_key, "Content-Type": "application/json"}

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
            "auth_config": {"type": "use_composio_managed_auth", "auth_scheme": "OAUTH2", "scopes": scopes or [], "name": config_name}
        }
    elif auth_type == "BEARER_TOKEN":
        data = {
            "toolkit": {"slug": toolkit_slug},
            "auth_config": {"type": "user_provided_auth", "auth_scheme": "BEARER_TOKEN", "name": config_name, "credentials": {"bearer_token": bearer_token}}
        }
    elif auth_type == "API_KEY":
        data = {
            "toolkit": {"slug": toolkit_slug},
            "auth_config": {"type": "user_provided_auth", "auth_scheme": "API_KEY", "name": config_name, "credentials": {"api_key": api_key_secret}}
        }
    else:
        raise ValueError(f"Unsupported auth type: {auth_type}")

    print("Payload:", data)
    response = requests.post(url, json=data, headers=headers)
    print("Status:", response.status_code, response.text)
    response.raise_for_status()
    return response.json()

def save_auth_config_to_db(db: Session, org_id: str, toolkit_slug: str, auth_data: dict) -> AuthConfigRecord:
    ac = auth_data.get("auth_config", {})
    created_at = ac.get("created_at")
    last_updated_at = ac.get("last_updated_at")
    if created_at:
        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    if last_updated_at:
        last_updated_at = datetime.fromisoformat(last_updated_at.replace("Z", "+00:00"))

    record = AuthConfigRecord(
        organization_id=org_id,
        toolkit_slug=toolkit_slug,
        auth_config_id=ac.get("id") or auth_data.get("nanoid"),
        uuid=ac.get("uuid"),
        name=ac.get("name"),
        auth_scheme=ac.get("auth_scheme"),
        is_composio_managed=ac.get("is_composio_managed"),
        client_id=ac.get("credentials", {}).get("client_id"),
        client_secret=ac.get("credentials", {}).get("client_secret"),
        oauth_redirect_uri=ac.get("credentials", {}).get("oauth_redirect_uri"),
        created_by=ac.get("created_by"),
        created_at=created_at,
        status=ac.get("status"),
        toolkit_logo=ac.get("toolkit", {}).get("logo"),
        last_updated_at=last_updated_at,
        no_of_connections=ac.get("no_of_connections"),
        expected_input_fields=ac.get("expected_input_fields"),
        restrict_to_following_tools=ac.get("restrict_to_following_tools"),
        type=ac.get("type"),
        tools_for_connected_account_creation=ac.get("tool_access_config", {}).get("tools_for_connected_account_creation"),
        tools_available_for_execution=ac.get("tool_access_config", {}).get("tools_available_for_execution"),
        deprecated_default_connector_id=ac.get("deprecated_params", {}).get("default_connector_id"),
        deprecated_member_uuid=ac.get("deprecated_params", {}).get("member_uuid"),
        deprecated_toolkit_id=ac.get("deprecated_params", {}).get("toolkit_id"),
        deprecated_expected_input_fields=ac.get("deprecated_params", {}).get("expected_input_fields")
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
