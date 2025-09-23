import requests
from typing import List, Optional

from config import API_KEY
from schemas.request_schema import (
    CreateAuthConfigRequest,
    DeleteAuthConfigRequest,
    SetStatusRequest,
    ToolSchemaResponse,
    ParameterInfo,
)
from schemas.response_schema import (
    AuthConfig,
    ToolItem,
    ToolListResponse,
)

COMPOSIO_BASE_URL = "https://backend.composio.dev/api/v3"


def create_auth_config(req: CreateAuthConfigRequest) -> AuthConfig:
    url = f"{COMPOSIO_BASE_URL}/auth_configs"
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
        "x-organization-id": req.organization_id,
    }

    config_name = req.config_name or f"{req.toolkit_slug.capitalize()} Auth Config"

    # Decide auth type
    auth_type = req.auth_type or "OAUTH2"
    if req.bearer_token:
        auth_type = "BEARER_TOKEN"
    elif req.api_key_secret:
        auth_type = "API_KEY"

    # Build payload
    if auth_type == "OAUTH2":
        data = {
            "toolkit": {"slug": req.toolkit_slug},
            "auth_config": {
                "type": "use_composio_managed_auth",
                "auth_scheme": "OAUTH2",
                "scopes": req.scopes or [],
                "name": config_name,
            },
        }
    elif auth_type == "BEARER_TOKEN":
        data = {
            "toolkit": {"slug": req.toolkit_slug},
            "auth_config": {
                "type": "user_provided_auth",
                "auth_scheme": "BEARER_TOKEN",
                "name": config_name,
                "credentials": {"bearer_token": req.bearer_token},
            },
        }
    elif auth_type == "API_KEY":
        data = {
            "toolkit": {"slug": req.toolkit_slug},
            "auth_config": {
                "type": "user_provided_auth",
                "auth_scheme": "API_KEY",
                "name": config_name,
                "credentials": {"api_key": req.api_key_secret},
            },
        }
    else:
        raise ValueError(f"Unsupported auth type: {auth_type}")

    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    json_data = response.json().get("auth_config", {})

    return AuthConfig(
        id=json_data.get("id", ""),
        name=json_data.get("name", ""),
        organization_id=req.organization_id,
        toolkit_slug=req.toolkit_slug,
        auth_scheme=json_data.get("auth_scheme", ""),
        type=json_data.get("type", ""),
        status=json_data.get("status", ""),
        scopes=json_data.get("scopes", []),
        connections_count=0
    )


def delete_auth_config(req: DeleteAuthConfigRequest) -> dict:
    url = f"{COMPOSIO_BASE_URL}/auth_configs/{req.nanoid}"
    headers = {"x-api-key": API_KEY, "x-organization-id": req.organization_id}
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response.json()


def set_auth_config_status(req: SetStatusRequest) -> dict:
    url = f"{COMPOSIO_BASE_URL}/auth_configs/{req.nanoid}/{req.status}"
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    response = requests.patch(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_auth_config_details(organization_id: str, nanoid: str) -> dict:
    url = f"{COMPOSIO_BASE_URL}/auth_configs/{nanoid}"
    headers = {"x-api-key": API_KEY, "x-organization-id": organization_id}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_tools_clean(toolkit_slug: str, tool_slugs: Optional[List[str]] = None) -> ToolListResponse:
    url = f"{COMPOSIO_BASE_URL}/tools"
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    params = {"toolkit_slug": toolkit_slug}
    if tool_slugs:
        params["tool_slugs"] = ",".join(tool_slugs)

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    items = response.json().get("items", [])

    tools = [ToolItem(slug=tool.get("slug", ""), name=tool.get("name", "")) for tool in items]
    return ToolListResponse(total_tools_found=len(tools), tools=tools)


def get_tool_schema(tool_slug: str) -> Optional[ToolSchemaResponse]:
    url = f"{COMPOSIO_BASE_URL}/tools"
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    params = {"tool_slugs": tool_slug}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    items = response.json().get("items", [])

    if not items:
        return None

    tool = items[0]
    return ToolSchemaResponse(
        slug=tool.get("slug", ""),
        name=tool.get("name", ""),
        description=tool.get("description"),
        parameters=tool.get("input_parameters", {}),
        response_schema=tool.get("output_parameters", {}),
        toolkit_slug=tool.get("toolkit", {}).get("slug"),
    )


def extract_parameter_list(tool_schema: ToolSchemaResponse) -> List[ParameterInfo]:
    params = tool_schema.parameters or {}
    properties = params.get("properties", {})
    required_fields = params.get("required", [])

    return [
        ParameterInfo(
            name=param_name,
            required=param_name in required_fields,
            optional=param_name not in required_fields,
            type=param_data.get("type", "unknown"),
        )
        for param_name, param_data in properties.items()
    ]


def search_toolkits_service(search_term: str) -> list:
    url = f"{COMPOSIO_BASE_URL}/toolkits"
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    items = response.json().get("items", [])

    return [
        item
        for item in items
        if search_term.lower() in item.get("name", "").lower()
        or search_term.lower() in item.get("slug", "").lower()
    ]
