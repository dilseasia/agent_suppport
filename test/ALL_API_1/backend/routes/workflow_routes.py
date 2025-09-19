from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import requests
import webbrowser

from services.composio_service import (
    fetch_tools_clean,
    get_tool_schema,
    extract_parameter_list,
    search_toolkits_service,
    create_auth_config,
    delete_auth_config,
    set_auth_config_status,
    fetch_auth_config_details
)
from database import get_db
from models.item_model import AuthConfigRecord
from schemas.request_schema import GmailConnectRequest, ToolkitSearchRequest

BASE_URL = "https://backend.composio.dev/api/v3"
router = APIRouter(prefix="/Routes")


# ------------------------
# Create Auth Config
# ------------------------
@router.post("/create-auth-config")
async def create_auth_config_route(data: dict):
    try:
        return create_auth_config(
            composio_api_key=data["api_key"],
            organization_id=data["organization_id"],
            toolkit_slug=data["toolkit_slug"],
            auth_type=data.get("auth_type"),
            bearer_token=data.get("bearer_token"),
            api_key_secret=data.get("api_key_secret"),
            scopes=data.get("scopes"),
            config_name=data.get("config_name")
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------------
# Delete Auth Config
# ------------------------
@router.post("/delete-auth-config")
async def delete_auth_config_route(data: dict):
    try:
        return delete_auth_config(
            composio_api_key=data["api_key"],
            organization_id=data["organization_id"],
            nanoid=data["nanoid"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------------
# Gmail Connect
# ------------------------
@router.post("/gmail/connect")
def connect_gmail_api(data: GmailConnectRequest):
    headers = {
        "x-api-key": data.api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "auth_config_id": data.auth_config_id,
        "user_id": data.user_id
    }

    try:
        response = requests.post(
            f"{BASE_URL}/connected_accounts/link",
            headers=headers,
            json=payload,
            timeout=20
        )
        response.raise_for_status()
        res_json = response.json()

        redirect_url = res_json.get("redirect_url") or res_json.get("redirectUrl")
        connected_account_id = res_json.get("connected_account_id")

        if redirect_url:
            webbrowser.open(redirect_url)

        return {
            "message": "Gmail connect flow initiated",
            "redirect_url": redirect_url,
            "connected_account_id": connected_account_id
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to initiate Gmail connection: {str(e)}"
        )


# ------------------------
# Search Toolkits
# ------------------------
@router.post("/toolkits/search")
def search_toolkits_api(data: ToolkitSearchRequest):
    try:
        results = search_toolkits_service(
            api_key=data.api_key,
            search_term=data.search_term
        )
        if not results:
            return {
                "message": f"No toolkits found for search term '{data.search_term}'",
                "items": []
            }
        return {
            "message": f"Found {len(results)} toolkit(s)",
            "items": results
        }
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------------
# Set Auth Config Status
# ------------------------
@router.post("/set-status")
async def set_status_route(data: dict):
    try:
        return set_auth_config_status(
            nanoid=data["nanoid"],
            status=data["status"],
            api_key=data["api_key"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------------
# Create-Fetch-Save Auth Config
# ------------------------
@router.post("/create-fetch-save")
async def create_fetch_save_auth_config(data: dict, db: Session = Depends(get_db)):
    try:
        # Create Auth Config
        created = create_auth_config(
            composio_api_key=data["api_key"],
            organization_id=data["organization_id"],
            toolkit_slug=data["toolkit_slug"],
            auth_type=data.get("auth_type"),
            bearer_token=data.get("bearer_token"),
            api_key_secret=data.get("api_key_secret"),
            scopes=data.get("scopes") or [],
            config_name=data.get("config_name")
        )

        nanoid = created.get("auth_config", {}).get("id")
        if not nanoid:
            raise HTTPException(
                status_code=400,
                detail=f"No ID returned in response: {created}"
            )

        # Fetch Auth Config Details
        details = fetch_auth_config_details(
            composio_api_key=data["api_key"],
            organization_id=data["organization_id"],
            nanoid=nanoid
        )

        # Save to DB
        record = AuthConfigRecord(
            organization_id=data["organization_id"],
            toolkit_slug=data["toolkit_slug"],
            auth_config_id=nanoid,
            uuid=details.get("uuid"),
            name=details.get("name"),
            auth_scheme=details.get("auth_scheme"),
            is_composio_managed=details.get("is_composio_managed"),
            client_id=details.get("client_id"),
            client_secret=details.get("client_secret"),
            oauth_redirect_uri=details.get("oauth_redirect_uri"),
            created_by=details.get("created_by"),
            created_at=details.get("created_at"),
            status=details.get("status"),
            toolkit_logo=details.get("toolkit_logo"),
            last_updated_at=details.get("last_updated_at"),
            no_of_connections=details.get("no_of_connections"),
            expected_input_fields=details.get("expected_input_fields"),
            restrict_to_following_tools=details.get("restrict_to_following_tools"),
            type=details.get("type"),
            tools_for_connected_account_creation=details.get("tools_for_connected_account_creation"),
            tools_available_for_execution=details.get("tools_available_for_execution"),
            deprecated_default_connector_id=details.get("deprecated_default_connector_id"),
            deprecated_member_uuid=details.get("deprecated_member_uuid"),
            deprecated_toolkit_id=details.get("deprecated_toolkit_id"),
            deprecated_expected_input_fields=details.get("deprecated_expected_input_fields"),
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        saved_record = db.query(AuthConfigRecord).filter_by(auth_config_id=nanoid).first()
        if not saved_record:
            raise HTTPException(status_code=500, detail="Record not found in DB after save.")

        return {
            "message": "Created, fetched, saved, and verified successfully",
            "composio": details,
            "saved_record": {
                "id": saved_record.id,
                "auth_config_id": saved_record.auth_config_id,
                "name": saved_record.name,
                "status": saved_record.status
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error in create-fetch-save: {str(e)}")


# ------------------------
# List Tools
# ------------------------
@router.post("/tools")
async def list_tools(data: dict):
    try:
        result = fetch_tools_clean(
            base_url=BASE_URL,
            api_key=data["api_key"],
            toolkit_slug=data["toolkit_slug"],
            tool_slugs=data.get("tool_slugs")
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------------
# Get Tool Parameters
# ------------------------
@router.post("/tool/parameters")
async def get_tool_parameters(data: dict):
    tool_schema = get_tool_schema(
        tool_slug=data["tool_slug"],
        api_key=data["api_key"]
    )
    if not tool_schema:
        raise HTTPException(status_code=404, detail=f"Tool '{data['tool_slug']}' not found")

    parameters = extract_parameter_list(tool_schema)
    return {
        "tool_slug": tool_schema.get("slug"),
        "tool_name": tool_schema.get("name"),
        "parameters": parameters
    }
