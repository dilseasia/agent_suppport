import requests
from typing import Dict, Any, Optional, List

COMPOSIO_BASE_URL = "https://backend.composio.dev/api/v3"


def create_auth_config(
    composio_api_key: str,
    organization_id: str,
    toolkit_slug: str,
    auth_type: str = "OAUTH2",
    bearer_token: Optional[str] = None,
    api_key_secret: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    config_name: Optional[str] = None
) -> Dict[str, Any]:

    url = f"{COMPOSIO_BASE_URL}/auth_configs"
    headers = {
        "x-api-key": composio_api_key,
        "Content-Type": "application/json",
        "x-organization-id": organization_id
    }

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
        raise ValueError(f"❌ Unsupported auth type: {auth_type}")

    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()


def delete_auth_config(composio_api_key: str, organization_id: str, nanoid: str) -> Dict[str, Any]:
    url = f"{COMPOSIO_BASE_URL}/auth_configs/{nanoid}"
    headers = {
        "x-api-key": composio_api_key,
        "x-organization-id": organization_id
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response.json()


def connect_auth_config(composio_api_key: str, organization_id: str, auth_config_id: str) -> Dict[str, Any]:
    url = f"{COMPOSIO_BASE_URL}/auth_configs/{auth_config_id}/connect"
    headers = {
        "x-api-key": composio_api_key,
        "x-organization-id": organization_id
    }
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()


def set_auth_config_status(composio_api_key: str, organization_id: str, nanoid: str, status: str) -> Dict[str, Any]:
    url = f"{COMPOSIO_BASE_URL}/auth_configs/{nanoid}/status"
    headers = {
        "x-api-key": composio_api_key,
        "x-organization-id": organization_id
    }
    data = {"status": status}
    response = requests.patch(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()

import requests
from typing import Dict, Any, Optional, List

COMPOSIO_BASE_URL = "https://backend.composio.dev/api/v3"


def create_auth_config(
    composio_api_key: str,
    organization_id: str,
    toolkit_slug: str,
    auth_type: str = "OAUTH2",
    bearer_token: Optional[str] = None,
    api_key_secret: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    config_name: Optional[str] = None
) -> Dict[str, Any]:

    url = f"{COMPOSIO_BASE_URL}/auth_configs"
    headers = {
        "x-api-key": composio_api_key,
        "Content-Type": "application/json",
        "x-organization-id": organization_id
    }

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
        raise ValueError(f"❌ Unsupported auth type: {auth_type}")

    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_auth_config_details(composio_api_key: str, organization_id: str, nanoid: str):
    url = f"{COMPOSIO_BASE_URL}/auth_configs/{nanoid}"
    headers = {
        "x-api-key": composio_api_key,
        "x-organization-id": organization_id
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
