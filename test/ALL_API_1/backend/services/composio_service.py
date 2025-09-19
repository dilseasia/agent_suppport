import requests
from typing import Dict, Any, Optional, List
from config import API_KEY

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


def set_auth_config_status(nanoid: str, status: str, api_key: str) -> dict:
    """
    Enable or disable an authentication configuration.

    Args:
        nanoid (str): The ID of the authentication configuration (ex: ac_ABC123xyz)
        status (str): The status to set ("ENABLED" or "DISABLED")
        api_key (str): Your Composio API key

    Returns:
        dict: The JSON response from the API or an error dict
    """
    url = f"https://backend.composio.dev/api/v3/auth_configs/{nanoid}/{status}"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.patch(url, headers=headers)
        response.raise_for_status()  # will raise HTTPError for 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def fetch_auth_config_details(composio_api_key: str, organization_id: str, nanoid: str):
    url = f"{COMPOSIO_BASE_URL}/auth_configs/{nanoid}"
    headers = {
        "x-api-key": composio_api_key,
        "x-organization-id": organization_id
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_tools_clean(base_url: str, api_key: str, toolkit_slug: str, tool_slugs: Optional[List[str]] = None) -> Dict:
    """
    Fetch tools for a given toolkit_slug (and optional tool_slugs)
    and return a clean dict with slug + name. Debug info is printed.
    """
    url = f"{base_url}/tools"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    params: Dict[str, str] = {"toolkit_slug": toolkit_slug}
    if tool_slugs:
        params["tool_slugs"] = ",".join(tool_slugs)

    # --- Debugging ---
    print("=== Fetching Tools Debug ===")
    print("URL:", url)
    print("Headers:", headers)
    print("Params:", params)
    print("============================")

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching tools: {e}")
        return {"total_tools_found": 0, "tools": []}

    # Debug: print raw response
    print("Full API response:", data)

    items = data.get("items", [])
    clean_list = [{"slug": tool.get("slug"), "name": tool.get("name")} for tool in items]

    print(f"Found {len(items)} tools for toolkit '{toolkit_slug}'")

    # Debug: print each tool
    for tool in items:
        print(f"- {tool.get('slug')}: {tool.get('name')}")

    return {"total_tools_found": len(items), "tools": clean_list}


def get_tools(toolkit_slug: str = None, tool_slugs: List[str] = None,
              important: bool = None, limit: int = 20, search: str = None) -> Dict:

    api_key = API_KEY
    base_url = COMPOSIO_BASE_URL
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    url = f"{base_url}/tools"
    params = {}
    if toolkit_slug:
        params["toolkit_slug"] = toolkit_slug
    if tool_slugs:
        params["tool_slugs"] = ",".join(tool_slugs)
    if important is not None:
        params["important"] = "true" if important else "false"
    if limit:
        params["limit"] = limit
    if search:
        params["search"] = search

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        tools = response.json()

        items = tools.get("items", [])
        print(f"Found {len(items)} tools")
        for tool in items[:]:  # show first 3
            print(f"- {tool.get('slug')}: {tool.get('name')}")

        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching tools: {e}")
        return {}


def get_tool_schema(tool_slug: str) -> Dict:
    url = f"https://backend.composio.dev/api/v3/tools"
    params = {"tool_slugs": tool_slug}
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        response = requests.get(url, headers=headers, params=params)
        print("DEBUG: status_code:", response.status_code)
        print("DEBUG: response:", response.text)
        response.raise_for_status()
        data = response.json()

        if data.get("items"):
            tool = data["items"][0]
            return {
                "slug": tool.get("slug"),
                "name": tool.get("name"),
                "description": tool.get("description"),
                "parameters": tool.get("input_parameters", {}),
                "response_schema": tool.get("output_parameters", {}),
                "toolkit_slug": tool.get("toolkit", {}).get("slug")
            }
        else:
            print(f"Tool {tool_slug} not found")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching tool schema: {e}")
        return {}


def extract_parameter_list(tool_schema: Dict) -> Dict[int, Dict]:
    """
    Convert the 'parameters' schema into a numbered dictionary.
    Keys are 1,2,3,... and values are param info.
    """
    params = tool_schema.get("parameters", {})
    properties = params.get("properties", {})
    required_fields = params.get("required", [])

    numbered_dict = {}
    counter = 1

    for param_name, param_data in properties.items():
        numbered_dict[counter] = {
            "name": param_name,
            "required": str(param_name in required_fields).lower(),
            "optional": str(param_name not in required_fields).lower(),
            "type": param_data.get("type", "unknown")
        }
        counter += 1

    return numbered_dict



def search_toolkits_service(api_key: str, search_term: str) -> list:
    """
    Search toolkits by name or slug.

    Args:
        api_key (str): Composio API key
        search_term (str): Term to search in toolkit name or slug

    Returns:
        list: Matching toolkit items
    """
    url = f"{COMPOSIO_BASE_URL}/toolkits"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])

        # Filter toolkits by search_term (case-insensitive)
        results = [
            item for item in items
            if search_term.lower() in item.get("name", "").lower()
            or search_term.lower() in item.get("slug", "").lower()
        ]
        return results

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch toolkits: {str(e)}")
    except ValueError:
        raise RuntimeError(f"Failed to parse JSON response: {response.text}")