from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
import json
import webbrowser
import requests

from config import API_KEY, BASE_URL, HEADERS
from database import get_db
from models.item_model import ConnectedAccount
from schemas.request_schema import (
    CreateAuthConfigRequest,
    DeleteAuthConfigRequest,
    SetStatusRequest,
    ToolRequest,
    ToolParameterRequest,
    ConnectAuthConfigRequest,
    ListAuthConfigsRequest,
    CreateAndConnectRequest
)
from schemas.response_schema import (
    AuthConfigListResponse,
    CreateAuthConfigResponse,
    DeleteAuthConfigResponse,
    ConnectAuthConfigResponse,
    StatusUpdateResponse,
    ToolListResponse,
    ToolParameterResponse,
    ConnectedAccountsByOrgResponse,
    ConnectedAccountResponse,
    # ParameterInfo,
    AuthConfig,
    # ToolItem
)
from services.composio_service import (
    create_auth_config,
    delete_auth_config,
    set_auth_config_status,
    fetch_tools_clean,
    get_tool_schema,
    extract_parameter_list
)

router = APIRouter(prefix="/routes", tags=["Composio API"])


# ------------------------
# Create Auth Config
# ------------------------
@router.post("/create-auth-config", response_model=CreateAuthConfigResponse, summary="Create a new authentication configuration")
async def create_auth_config_route(req: CreateAuthConfigRequest):
    try:
        created = create_auth_config(req)
        return CreateAuthConfigResponse(data=created, message="Auth config created successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------------
# Delete Auth Config
# ------------------------
@router.post("/delete-auth-config", response_model=DeleteAuthConfigResponse, summary="Delete an authentication configuration")
async def delete_auth_config_route(req: DeleteAuthConfigRequest):
    try:
        result = delete_auth_config(req)
        return DeleteAuthConfigResponse(message="Auth config deleted successfully", data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------------
# Connect External Account (Gmail / API)
# ------------------------
@router.post("/connect", response_model=ConnectAuthConfigResponse, summary="Initiate connection flow for external account")
async def connect_external(req: ConnectAuthConfigRequest):
    payload = {"auth_config_id": req.auth_config_id, "user_id": req.user_id}
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}

    try:
        resp = requests.post(f"{BASE_URL}/connected_accounts/link", headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        res_json = resp.json()
        redirect_url = res_json.get("redirect_url") or res_json.get("redirectUrl")
        connected_account_id = res_json.get("connected_account_id")

        if redirect_url:
            webbrowser.open(redirect_url)

        return ConnectAuthConfigResponse(
            message="Connection flow initiated",
            redirect_url=redirect_url,
            connected_account_id=connected_account_id
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to initiate connection: {str(e)}")


# ------------------------
# Set Auth Config Status
# ------------------------
@router.post("/set-status", response_model=StatusUpdateResponse, summary="Update the status of an authentication configuration")
async def set_status_route(req: SetStatusRequest):
    try:
        updated = set_auth_config_status(req)
        return StatusUpdateResponse(message=f"Auth config {req.nanoid} status updated to {req.status}", data=updated)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------------
# List Tools
# ------------------------
@router.post("/tools", response_model=ToolListResponse, summary="Fetch list of tools from a toolkit")
async def list_tools(req: ToolRequest):
    try:
        return fetch_tools_clean(toolkit_slug=req.toolkit_slug, tool_slugs=req.tool_slugs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------------
# Get Tool Parameters
# ------------------------
@router.post("/tool/parameters", response_model=ToolParameterResponse, summary="Get parameters for a specific tool")
async def get_tool_parameters(req: ToolParameterRequest):
    tool_schema = get_tool_schema(tool_slug=req.tool_slug)
    if not tool_schema:
        raise HTTPException(status_code=404, detail=f"Tool '{req.tool_slug}' not found")

    parameters = extract_parameter_list(tool_schema)
    params_response = [param.dict() for param in parameters]

    return ToolParameterResponse(
        tool_slug=tool_schema.slug,
        tool_name=tool_schema.name,
        parameters=params_response
    )

# Endpoint: List Auth Configs
# -----------------------------
@router.post(
    "/list-auth-configs",
    response_model=AuthConfigListResponse,
    summary="List all authentication configurations"
)
async def list_auth_configs(req: ListAuthConfigsRequest):
    try:
        #  Fetch auth configs
        configs_resp = requests.get(
            f"{BASE_URL}/auth_configs?organization_id={req.organization_id}",
            headers=HEADERS,
            timeout=20
        )
        configs_resp.raise_for_status()
        configs_data = configs_resp.json().get("items", [])

        #  Fetch connected accounts
        connected_resp = requests.get(
            f"{BASE_URL}/connected_accounts?organization_id={req.organization_id}",
            headers=HEADERS,
            timeout=20
        )
        connected_resp.raise_for_status()
        connected_accounts = connected_resp.json().get("items", [])

        #  Count connections per auth_config
        counts = {}
        for acc in connected_accounts:
            auth_id = (
                acc.get("auth_config_id") or
                acc.get("authConfigId") or
                (acc.get("auth_config") or {}).get("nanoid")
            )
            if auth_id:
                counts[auth_id] = counts.get(auth_id, 0) + 1

        #  Build AuthConfig items
        items = [
            AuthConfig(
                id=cfg.get("nanoid") or cfg.get("id", ""),
                name=cfg.get("name", ""),
                organization_id=req.organization_id,
                auth_scheme=cfg.get("auth_scheme", ""),
                type=cfg.get("type", ""),
                status=cfg.get("status", ""),
                toolkit_slug=cfg.get("toolkit", {}).get("slug"),
                connections_count=counts.get(cfg.get("nanoid") or cfg.get("id", ""), 0),
                scopes=cfg.get("scopes", [])
            )
            for cfg in configs_data
        ]

        return AuthConfigListResponse(
            message=f"Found {len(items)} auth config(s)",
            items=items
        )

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

# ------------------------
# Create and Connect (combined)
# ------------------------
@router.post("/create-and-connect", response_model=ConnectAuthConfigResponse)
async def create_and_connect(req: CreateAndConnectRequest, db: Session = Depends(get_db)):
    try:
        #  Create Auth Config payload
        config_name = req.config_name or f"{req.toolkit_slug.capitalize()} Auth Config"
        auth_type = req.auth_type or "OAUTH2"

        if req.bearer_token:
            auth_type = "BEARER_TOKEN"
        elif req.api_key_secret:
            auth_type = "API_KEY"

        auth_config_payload = {
            "toolkit": {"slug": req.toolkit_slug},
            "auth_config": {"name": config_name}
        }

        if auth_type == "OAUTH2":
            auth_config_payload["auth_config"].update({
                "type": "use_composio_managed_auth",
                "auth_scheme": "OAUTH2",
                "scopes": req.scopes or []
            })
        elif auth_type == "BEARER_TOKEN":
            auth_config_payload["auth_config"].update({
                "type": "user_provided_auth",
                "auth_scheme": "BEARER_TOKEN",
                "credentials": {"bearer_token": req.bearer_token}
            })
        elif auth_type == "API_KEY":
            auth_config_payload["auth_config"].update({
                "type": "user_provided_auth",
                "auth_scheme": "API_KEY",
                "credentials": {"api_key": req.api_key_secret}
            })
        else:
            raise ValueError(f"Unsupported auth_type: {auth_type}")

        headers = {
            "x-api-key": API_KEY,
            "Content-Type": "application/json",
            "x-organization-id": req.organization_id
        }

        # Log payload for debugging
        print("Auth Config Payload:", json.dumps(auth_config_payload, indent=2))

        #  Send request to create auth config
        response = requests.post(f"{BASE_URL}/auth_configs", headers=headers, json=auth_config_payload)
        response.raise_for_status()
        auth_config_data = response.json().get("auth_config")
        auth_config_id = auth_config_data.get("id") or auth_config_data.get("nanoid")

        if not auth_config_id:
            raise HTTPException(status_code=400, detail="Auth config creation failed: Missing ID")

        #  Connect external account
        connect_payload = {
            "auth_config_id": auth_config_id,
            "user_id": req.user_id
        }
        print("Connect Payload:", json.dumps(connect_payload, indent=2))

        connect_resp = requests.post(
            f"{BASE_URL}/connected_accounts/link",
            headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
            json=connect_payload
        )
        connect_resp.raise_for_status()
        connect_data = connect_resp.json()

        connected_account_id = connect_data.get("connected_account_id")
        redirect_url = connect_data.get("redirect_url") or connect_data.get("redirectUrl")

        if redirect_url:
            webbrowser.open(redirect_url)

        #  Save to DB
        db_record = ConnectedAccount(
            organization_id=req.organization_id,
            auth_config_id=auth_config_id,
            connected_account_id=connected_account_id,
            tools_slug_name=req.toolkit_slug,
            user_id=req.user_id,
            status=req.status or "enabled",
            is_connected=bool(connected_account_id)
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)

        return ConnectAuthConfigResponse(
            message="Auth config created and account connected",
            redirect_url=redirect_url,
            connected_account_id=connected_account_id,
            status=db_record.status,
            is_connected=db_record.is_connected
        )

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# -----------------------------
# Endpoint
# -----------------------------
@router.get(
    "/connected-accounts-by-org",
    response_model=ConnectedAccountsByOrgResponse,
    summary="Get connected accounts for a specific organization"
)
def get_connected_accounts_by_org(organization_id: str = Query(...), db: Session = Depends(get_db)):
    org_records = db.query(ConnectedAccount).filter(ConnectedAccount.organization_id == organization_id).all()
    if not org_records:
        return ConnectedAccountsByOrgResponse(organization_id=organization_id, connected_accounts=[])

    connected_ids = [rec.connected_account_id for rec in org_records]

    try:
        response = requests.get(f"{BASE_URL}/connected_accounts", headers={"x-api-key": API_KEY}, timeout=20)
        response.raise_for_status()
        external_accounts = response.json().get("items", [])

        filtered_accounts = [
            ConnectedAccountResponse(
                connected_account_id=acc.get("id"),
                tool_slug=(acc.get("toolkit") or {}).get("slug"),
                user_id=acc.get("user_id"),
                status=acc.get("status"),
                created_at=acc.get("created_at"),
                updated_at=acc.get("updated_at"),
                auth_config_id=(acc.get("auth_config") or {}).get("id"),
                auth_scheme=(acc.get("auth_config") or {}).get("auth_scheme"),
                is_disabled=acc.get("is_disabled", False),
                data_status=(acc.get("data") or {}).get("status"),
                scopes=(acc.get("data") or {}).get("scope", []),
                callback_url=(acc.get("data") or {}).get("callback_url")
            )
            for acc in external_accounts if acc.get("id") in connected_ids
        ]

        return ConnectedAccountsByOrgResponse(organization_id=organization_id, connected_accounts=filtered_accounts)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch connected accounts: {str(e)}")
