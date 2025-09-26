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


# from fastapi import FastAPI, HTTPException, Query
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi import APIRouter
# from pydantic import BaseModel, Field
# from typing import Dict, Any, Optional, List
# import requests
# from dataclasses import dataclass
# from enum import Enum
# from config import API_KEY


# router = APIRouter()

# # Configuration
# COMPOSIO_API_KEY = API_KEY
# COMPOSIO_BASE_URL = "https://backend.composio.dev"

# @dataclass
# class ConnectedAccount:
#     id: str
#     user_id: str
#     toolkit_slug: str
#     auth_config_id: str
#     access_token: str
#     refresh_token: str
#     status: str
#     auth_scheme: str

# connected_accounts_cache = {}

# # ============ ENUMS ============

# class OrderBy(str, Enum):
#     """Event ordering options"""
#     START_TIME = "startTime"
#     UPDATED = "updated"

# class SendUpdates(str, Enum):
#     """Send update notification options"""
#     ALL = "all"
#     EXTERNAL_ONLY = "externalOnly"
#     NONE = "none"

# class Visibility(str, Enum):
#     """Event visibility options"""
#     DEFAULT = "default"
#     PUBLIC = "public"
#     PRIVATE = "private"
#     CONFIDENTIAL = "confidential"

# class ACLRole(str, Enum):
#     """ACL role options"""
#     OWNER = "owner"
#     WRITER = "writer"
#     READER = "reader"
#     FREE_BUSY_READER = "freeBusyReader"

# # ============ PYDANTIC SCHEMAS ============

# class AttendeeModel(BaseModel):
#     """Attendee information model"""
#     email: str = Field(..., description="Email address of the attendee")
#     optional: Optional[bool] = Field(None, description="Whether attendance is optional")
#     responseStatus: Optional[str] = Field(None, description="Response status (needsAction, accepted, declined, tentative)")

# class EventTimeModel(BaseModel):
#     """Event time model"""
#     dateTime: str = Field(..., description="ISO 8601 datetime string (e.g., '2025-09-20T10:00:00')")
#     timeZone: Optional[str] = Field(None, description="IANA timezone (e.g., 'America/New_York')")

# class CreateEventRequest(BaseModel):
#     """
#     Request schema for creating a Google Calendar event.
    
#     This endpoint creates a new event in the specified Google Calendar.
#     All datetime fields should be in ISO 8601 format.
#     """
#     summary: str = Field(..., description="Title/summary of the event", example="Team Meeting")
#     start_datetime: str = Field(..., description="Start time in ISO 8601 format", example="2025-09-20T10:00:00")
#     end_datetime: str = Field(..., description="End time in ISO 8601 format", example="2025-09-20T11:00:00")
#     description: Optional[str] = Field("", description="Detailed description of the event", example="Weekly team sync meeting")
#     location: Optional[str] = Field("", description="Location of the event", example="Conference Room A")
#     attendees: Optional[List[str]] = Field(None, description="List of attendee email addresses", example=["user1@example.com", "user2@example.com"])
#     calendar_id: Optional[str] = Field("primary", description="Calendar ID where event will be created", example="primary")
#     create_meeting_room: Optional[bool] = Field(False, description="Whether to create a Google Meet room")
#     # send_updates: Optional[SendUpdates] = Field(None, description="Whether to send notification emails")
#     visibility: Optional[Visibility] = Field(None, description="Visibility of the event")

# class UpdateEventRequest(BaseModel):
#     """
#     Request schema for updating an existing Google Calendar event.
    
#     Only fields that need to be updated should be provided.
#     All other fields will remain unchanged.
#     """
#     event_id: str = Field(..., description="Unique identifier of the event to update", example="abc123def456")
#     calendar_id: Optional[str] = Field("primary", description="Calendar ID containing the event")
#     summary: Optional[str] = Field(None, description="New title/summary for the event")
#     description: Optional[str] = Field(None, description="New description for the event")
#     location: Optional[str] = Field(None, description="New location for the event")
#     start_datetime: str = Field(..., description="Start time in ISO 8601 format", example="2025-09-20T10:00:00")
#     end_datetime: str = Field(..., description="End time in ISO 8601 format", example="2025-09-20T11:00:00")
#     attendees: Optional[List[str]] = Field(None, description="New list of attendee email addresses")
#     # send_updates: Optional[SendUpdates] = Field(None, description="Whether to send update notifications")

# class PatchEventRequest(BaseModel):
#     """
#     Request schema for patching an event (partial update).
    
#     Similar to update but uses PATCH semantics - only specified fields are modified.
#     """
#     event_id: str = Field(..., description="Unique identifier of the event to patch")
#     calendar_id: Optional[str] = Field("primary", description="Calendar ID containing the event")
#     data: Dict[str, Any] = Field({}, description="Dictionary of fields to update", example={"summary": "New Title", "location": "New Location"})

# class DeleteEventRequest(BaseModel):
#     """
#     Request schema for deleting a Google Calendar event.
    
#     This permanently removes the event from the calendar.
#     """
#     event_id: str = Field(..., description="Unique identifier of the event to delete")
#     calendar_id: Optional[str] = Field("primary", description="Calendar ID containing the event")
#     # send_updates: Optional[SendUpdates] = Field(None, description="Whether to send cancellation notifications")

# class MoveEventRequest(BaseModel):
#     """
#     Request schema for moving an event between calendars.
    
#     This transfers ownership and location of an event.
#     """
#     event_id: str = Field(..., description="Unique identifier of the event to move")
#     source_calendar_id: str = Field(..., description="Calendar ID where event currently exists")
#     destination_calendar_id: str = Field(..., description="Calendar ID where event should be moved")

# class QuickAddRequest(BaseModel):
#     """
#     Request schema for quick adding an event using natural language.
    
#     Google Calendar will parse the text and create an event.
#     Examples: "Lunch tomorrow at 1pm", "Meeting with John next Tuesday at 3pm for 2 hours"
#     """
#     text: str = Field(..., description="Natural language description of the event", example="Lunch tomorrow at 1pm")
#     calendar_id: Optional[str] = Field("primary", description="Calendar ID where event will be created")

# class RemoveAttendeeRequest(BaseModel):
#     """
#     Request schema for removing an attendee from an event.
#     """
#     event_id: str = Field(..., description="Unique identifier of the event")
#     attendee_email: str = Field(..., description="Email address of attendee to remove")
#     calendar_id: Optional[str] = Field("primary", description="Calendar ID containing the event")

# class FindFreeSlotsRequest(BaseModel):
#     """
#     Request schema for finding free time slots in calendars.
    
#     Returns available time periods when all specified calendars are free.
#     """
#     time_min: Optional[str] = Field(None, description="Start of time range in ISO 8601 format", example="2025-09-20T09:00:00")
#     time_max: Optional[str] = Field(None, description="End of time range in ISO 8601 format", example="2025-09-20T17:00:00")
#     # calendars: Optional[List[str]] = Field(None, description="List of calendar IDs to check", example=["primary", "user@example.com"])

# class QueryFreeBusyRequest(BaseModel):
#     """
#     Request schema for querying free/busy information.
    
#     Returns busy time blocks for specified calendars within a time range.
#     """
#     time_min: str = Field(..., description="Start of time range in ISO 8601 format")
#     time_max: str = Field(..., description="End of time range in ISO 8601 format")
#     calendars: List[str] = Field(..., description="List of calendar IDs to query")

# class WatchEventsRequest(BaseModel):
#     """
#     Request schema for setting up event change notifications.
    
#     Establishes a webhook to receive notifications when events change.
#     """
#     calendar_id: Optional[str] = Field("primary", description="Calendar ID to watch")
#     channel_id: Optional[str] = Field(None, description="Unique identifier for the notification channel")
#     webhook_url: Optional[str] = Field(None, description="URL where notifications will be sent")

# class SyncEventsRequest(BaseModel):
#     """
#     Request schema for synchronizing events.
    
#     Retrieves incremental changes since last sync.
#     """
#     calendar_id: Optional[str] = Field("primary", description="Calendar ID to sync")
#     sync_token: Optional[str] = Field(None, description="Token from previous sync operation")

# class CreateCalendarRequest(BaseModel):
#     """
#     Request schema for creating a new Google Calendar.
#     """
#     summary: str = Field(..., description="Title/name of the calendar", example="Project Tasks")
#     description: Optional[str] = Field(None, description="Description of the calendar")
#     location: Optional[str] = Field(None, description="Geographic location")
#     time_zone: Optional[str] = Field(None, description="IANA timezone", example="America/New_York")

# class UpdateCalendarRequest(BaseModel):
#     """
#     Request schema for updating calendar properties.
#     """
#     calendar_id: str = Field(..., description="Unique identifier of the calendar")
#     summary: Optional[str] = Field(None, description="New title/name for the calendar")
#     description: Optional[str] = Field(None, description="New description")
#     location: Optional[str] = Field(None, description="New location")
#     time_zone: Optional[str] = Field(None, description="New timezone")

# class PatchCalendarRequest(BaseModel):
#     """
#     Request schema for patching calendar properties (partial update).
#     """
#     calendar_id: str = Field(..., description="Unique identifier of the calendar")
#     data: Dict[str, Any] = Field({}, description="Dictionary of fields to update")

# class DeleteCalendarRequest(BaseModel):
#     """
#     Request schema for deleting a calendar.
    
#     Warning: This permanently deletes the calendar and all its events.
#     """
#     calendar_id: str = Field(..., description="Unique identifier of the calendar to delete")

# class ClearCalendarRequest(BaseModel):
#     """
#     Request schema for clearing all events from a calendar.
    
#     Warning: This deletes all events but keeps the calendar itself.
#     """
#     calendar_id: str = Field(..., description="Unique identifier of the calendar to clear")

# class InsertCalendarToListRequest(BaseModel):
#     """
#     Request schema for adding a calendar to user's calendar list.
#     """
#     calendar_id: str = Field(..., description="Unique identifier of the calendar to add")
#     color_id: Optional[str] = Field(None, description="Color ID for calendar display")
#     hidden: Optional[bool] = Field(False, description="Whether calendar should be hidden")

# class UpdateCalendarListRequest(BaseModel):
#     """
#     Request schema for updating calendar list entry properties.
#     """
#     calendar_id: str = Field(..., description="Unique identifier of the calendar")
#     data: Dict[str, Any] = Field({}, description="Dictionary of properties to update")

# class UpdateACLRuleRequest(BaseModel):
#     """
#     Request schema for updating calendar access control rules.
#     """
#     calendar_id: str = Field(..., description="Unique identifier of the calendar")
#     rule_id: str = Field(..., description="Unique identifier of the ACL rule")
#     role: ACLRole = Field(..., description="New access role to assign")

# class WatchSettingsRequest(BaseModel):
#     """
#     Request schema for watching calendar settings changes.
#     """
#     channel_id: str = Field(..., description="Unique identifier for the notification channel")
#     webhook_url: str = Field(..., description="URL where notifications will be sent")

# # ============ HELPER FUNCTIONS ============

# def fetch_connected_accounts():
#     """Fetch and cache all connected accounts from Composio"""
#     url = f"{COMPOSIO_BASE_URL}/api/v3/connected_accounts"
#     headers = {"x-api-key": COMPOSIO_API_KEY}
#     params = {"toolkit_slugs": "", "user_ids": "", "auth_config_ids": ""}
    
#     response = requests.get(url, headers=headers, params=params)
#     response.raise_for_status()
#     data = response.json()
    
#     accounts = {}
#     for item in data.get("items", []):
#         toolkit_slug = item["toolkit"]["slug"]
#         account = ConnectedAccount(
#             id=item["id"],
#             user_id=item["user_id"],
#             toolkit_slug=toolkit_slug,
#             auth_config_id=item["auth_config"]["id"],
#             access_token=item["data"]["access_token"],
#             refresh_token=item["data"]["refresh_token"],
#             status=item["status"],
#             auth_scheme=item["authScheme"]
#         )
#         accounts[toolkit_slug] = account
    
#     return accounts

# def execute_composio_tool(tool_slug: str, arguments: Dict[str, Any] = None, text: str = "") -> Dict[str, Any]:
#     """
#     Execute a Composio tool with the provided arguments.
    
#     Args:
#         tool_slug: The Composio tool identifier (e.g., 'GOOGLECALENDAR_CREATE_EVENT')
#         arguments: Dictionary of arguments for the tool
#         text: Text input for natural language processing tools
        
#     Returns:
#         Dict containing the tool execution result
        
#     Raises:
#         HTTPException: If account not found or tool execution fails
#     """
#     if not connected_accounts_cache:
#         connected_accounts_cache.update(fetch_connected_accounts())

    
#     toolkit_slug = tool_slug.split("_")[0].lower()
#     account = connected_accounts_cache.get(toolkit_slug)

#     if not account:
#         raise HTTPException(status_code=404, detail=f"No connected account found for toolkit: {toolkit_slug}")
    
#     url = f"{COMPOSIO_BASE_URL}/api/v3/tools/execute/{tool_slug}"
#     headers = {"x-api-key": COMPOSIO_API_KEY, "Content-Type": "application/json"}

    
#     body = {
#         "connected_account_id": account.id,
#         "user_id": account.user_id,
#         "custom_auth_params": {},
#         "allow_tracing": False,
#         "arguments": arguments or {},
#         "custom_connection_data": {
#             "authScheme": account.auth_scheme,
#             "toolkitSlug": account.toolkit_slug,
#             "val": {"access_token": account.access_token}
#         }
#     }
    
#     # if text:
#     #     body["text"] = text
#     #     body.pop("arguments", None)

    
#     response = requests.post(url, headers=headers, json=body)

#     if response.status_code != 200:
#         raise HTTPException(status_code=response.status_code, detail=response.text)
    
#     return response.json()

# # ============ EVENT ENDPOINTS ============

# @router.post("/events/create", tags=["Events"])
# async def create_event(request: CreateEventRequest):
#     """
#     Create a new Google Calendar event.
    
#     Creates an event with the specified details including time, location, attendees, and more.
#     Supports creating Google Meet meetings and sending invitation emails.
    
#     **Parameters:**
#     - **summary**: The event title/name (required)
#     - **start_datetime**: Start time in ISO 8601 format (required)
#     - **end_datetime**: End time in ISO 8601 format (required)
#     - **description**: Detailed event description (optional)
#     - **location**: Event location (optional)
#     - **attendees**: List of attendee emails (optional)
#     - **calendar_id**: Target calendar ID (default: "primary")
#     - **create_meeting_room**: Create Google Meet link (default: false)
#     # - **send_updates**: Send notification emails (optional)
#     - **visibility**: Event visibility setting (optional)
    
#     **Returns:**
#     - Event object with ID and details
    
#     **Example:**
#     ```json
#     {
#         "summary": "Team Standup",
#         "start_datetime": "2025-09-20T10:00:00",
#         "end_datetime": "2025-09-20T10:30:00",
#         "description": "Daily team sync",
#         "location": "Conference Room A",
#         "attendees": ["john@example.com", "jane@example.com"]
#     }
#     ```
#     """
#     arguments = {
#         "summary": request.summary,
#         "description": request.description,
#         "location": request.location,
#         "start_datetime": request.start_datetime,
#         "end": request.end_datetime,
#         "calendar_id": request.calendar_id,
#         "create_meeting_room": request.create_meeting_room
#     }
    
#     if request.attendees:
#         arguments["attendees"] = [email for email in request.attendees]
#     # if request.send_updates:
#     #     arguments["send_updates"] = request.send_updates.value
#     if request.visibility:
#         arguments["visibility"] = request.visibility.value
    
#     return execute_composio_tool("GOOGLECALENDAR_CREATE_EVENT", arguments)

# @router.get("/events/list", tags=["Events"])
# async def list_events(
#     calendar_id: str = Query("primary", description="Calendar ID to list events from"),
#     time_min: Optional[str] = Query(None, description="Lower bound (inclusive) for event start time (ISO 8601)"),
#     time_max: Optional[str] = Query(None, description="Upper bound (exclusive) for event end time (ISO 8601)"),
#     max_results: int = Query(10, description="Maximum number of events to return", ge=1, le=2500),
#     single_events: bool = Query(True, description="Whether to expand recurring events into instances"),
#     order_by: Optional[OrderBy] = Query(None, description="Sort order for results"),
#     show_deleted: bool = Query(False, description="Include deleted/cancelled events"),
#     page_token: Optional[str] = Query(None, description="Token for pagination")
# ):
#     """
#     List events from a Google Calendar.
    
#     Retrieves a list of events from the specified calendar with optional filtering and pagination.
#     Can filter by time range, include deleted events, and control result ordering.
    
#     **Query Parameters:**
#     - **calendar_id**: Which calendar to query (default: "primary")
#     - **time_min**: Start of time window (ISO 8601 format)
#     - **time_max**: End of time window (ISO 8601 format)
#     - **max_results**: Number of events to return (1-2500)
#     - **single_events**: Expand recurring events (default: true)
#     - **order_by**: Sort by 'startTime' or 'updated'
#     - **show_deleted**: Include cancelled events (default: false)
#     - **page_token**: For retrieving next page of results
    
#     **Returns:**
#     - List of event objects with pagination info
#     """
#     arguments = {
#         "calendar_id": calendar_id,
#         "max_results": max_results,
#         "single_events": single_events,
#         "show_deleted": show_deleted
#     }
    
#     if time_min:
#         arguments["time_min"] = time_min
#     if time_max:
#         arguments["time_max"] = time_max
#     if order_by:
#         arguments["order_by"] = order_by.value
#     if page_token:
#         arguments["page_token"] = page_token
    
#     return execute_composio_tool("GOOGLECALENDAR_EVENTS_LIST", arguments)

# @router.get("/events/find", tags=["Events"])
# async def find_event(
#     query: str = Query("", description="Free text search query"),
#     calendar_id: str = Query("primary", description="Calendar ID to search in"),
#     time_min: Optional[str] = Query(None, description="Start of time range (ISO 8601)"),
#     time_max: Optional[str] = Query(None, description="End of time range (ISO 8601)"),
#     max_results: int = Query(10, description="Maximum number of results", ge=1, le=2500)
# ):
#     """
#     Find events in Google Calendar using search query.
    
#     Searches through event titles, descriptions, locations, and attendees.
#     Can be combined with time range filters for more specific results.
    
#     **Query Parameters:**
#     - **query**: Text to search for in events
#     - **calendar_id**: Which calendar to search (default: "primary")
#     - **time_min**: Filter events starting after this time
#     - **time_max**: Filter events ending before this time
#     - **max_results**: Number of results to return
    
#     **Returns:**
#     - List of matching event objects
#     """
#     arguments = {
#         "calendar_id": calendar_id,
#         "max_results": max_results
#     }
    
#     if query:
#         arguments["query"] = query
#     if time_min:
#         arguments["time_min"] = time_min
#     if time_max:
#         arguments["time_max"] = time_max
    
#     return execute_composio_tool("GOOGLECALENDAR_FIND_EVENT", arguments)

# @router.put("/events/update", tags=["Events"])
# async def update_event(request: UpdateEventRequest):
#     """
#     Update an existing Google Calendar event.
    
#     Modifies specified fields of an event. Only provided fields will be updated,
#     others remain unchanged. Can update time, attendees, location, and other properties.
    
#     **Request Body:**
#     - **event_id**: ID of event to update (required)
#     - **calendar_id**: Calendar containing the event (default: "primary")
#     - **summary**: New event title (optional)
#     - **description**: New description (optional)
#     - **location**: New location (optional)
#     - **start_time**: New start time (ISO 8601) (optional)
#     - **end_time**: New end time (ISO 8601) (optional)
#     - **attendees**: New attendee list (optional)
#     # - **send_updates**: Notification preference (optional)
    
#     **Returns:**
#     - Updated event object
#     """
#     arguments = {
#         "calendar_id": request.calendar_id,
#         "event_id": request.event_id
#     }
    
#     if request.summary:
#         arguments["summary"] = request.summary
#     if request.description:
#         arguments["description"] = request.description
#     if request.location:
#         arguments["location"] = request.location
#     if request.start_datetime:
#         arguments["start_datetime"] = request.start_datetime
#     if request.end_datetime:
#         arguments["end_datetime"] = request.end_datetime
#     if request.attendees:
#         arguments["attendees"] = [email for email in request.attendees]
#     # if request.send_updates:
#     #     arguments["send_updates"] = request.send_updates.value
    
#     return execute_composio_tool("GOOGLECALENDAR_UPDATE_EVENT", arguments)

# @router.patch("/events/patch", tags=["Events"])
# async def patch_event(request: PatchEventRequest):
#     """
#     Partially update an event using PATCH semantics.
    
#     Similar to update but allows arbitrary field modifications through the data parameter.
#     Useful for updating specific properties not covered by the standard update endpoint.
    
#     **Request Body:**
#     - **event_id**: ID of event to patch (required)
#     - **calendar_id**: Calendar containing the event (default: "primary")
#     - **data**: Dictionary of fields to update (optional)
    
#     **Returns:**
#     - Patched event object
#     """
#     arguments = {
#         "calendar_id": request.calendar_id,
#         "event_id": request.event_id,
#         **request.data
#     }
    
#     return execute_composio_tool("GOOGLECALENDAR_PATCH_EVENT", arguments)

# @router.delete("/events/delete", tags=["Events"])
# async def delete_event(request: DeleteEventRequest):
#     """
#     Delete a Google Calendar event.
    
#     Permanently removes the event from the calendar. Optionally sends cancellation
#     notifications to attendees.
    
#     **Request Body:**
#     - **event_id**: ID of event to delete (required)
#     - **calendar_id**: Calendar containing the event (default: "primary")
#     # - **send_updates**: Send cancellation emails (optional)
    
#     **Returns:**
#     - Success confirmation
    
#     **Note:** This action cannot be undone. The event will be permanently deleted.
#     """
#     arguments = {
#         "calendar_id": request.calendar_id,
#         "event_id": request.event_id
#     }
    
#     # if request.send_updates:
#     #     arguments["send_updates"] = request.send_updates.value
    
#     return execute_composio_tool("GOOGLECALENDAR_DELETE_EVENT", arguments)

# @router.post("/events/move", tags=["Events"])
# async def move_event(request: MoveEventRequest):
#     """
#     Move an event from one calendar to another.
    
#     Transfers the event to a different calendar, changing its organizer.
#     The event ID remains the same but the calendar ID changes.
    
#     **Request Body:**
#     - **event_id**: ID of event to move (required)
#     - **source_calendar_id**: Current calendar ID (required)
#     - **destination_calendar_id**: Target calendar ID (required)
    
#     **Returns:**
#     - Moved event object with new calendar association
#     """
#     arguments = {
#         "calendar_id": request.source_calendar_id,
#         "event_id": request.event_id,
#         "destination": request.destination_calendar_id
#     }
    
#     return execute_composio_tool("GOOGLECALENDAR_EVENTS_MOVE", arguments)

# @router.get("/events/instances", tags=["Events"])
# async def get_event_instances(
#     event_id: str = Query(..., description="ID of the recurring event"),
#     calendar_id: str = Query("primary", description="Calendar ID"),
#     time_min: Optional[str] = Query(None, description="Start time for instances (ISO 8601)"),
#     time_max: Optional[str] = Query(None, description="End time for instances (ISO 8601)")
# ):
#     """
#     Get instances of a recurring event.
    
#     Returns individual occurrences of a recurring event within a specified time range.
#     Each instance is returned as a separate event object.
    
#     **Query Parameters:**
#     - **event_id**: ID of the recurring event (required)
#     - **calendar_id**: Which calendar contains the event (default: "primary")
#     - **time_min**: Start of time range for instances
#     - **time_max**: End of time range for instances
    
#     **Returns:**
#     - List of event instance objects
#     """
#     arguments = {
#         "calendar_id": calendar_id,
#         "event_id": event_id
#     }
    
#     if time_min:
#         arguments["time_min"] = time_min
#     if time_max:
#         arguments["time_max"] = time_max
    
#     return execute_composio_tool("GOOGLECALENDAR_EVENTS_INSTANCES", arguments)

# @router.post("/events/watch", tags=["Events"])
# async def watch_events(request: WatchEventsRequest):
#     """
#     Set up push notifications for event changes.
    
#     Establishes a webhook to receive real-time notifications when events are
#     created, modified, or deleted in the specified calendar.
    
#     **Request Body:**
#     - **calendar_id**: Calendar to watch (default: "primary")
#     - **channel_id**: Unique channel identifier (optional)
#     - **webhook_url**: URL to receive notifications (optional)
    
#     **Returns:**
#     - Channel information and expiration details
    
#     **Note:** Webhooks require a publicly accessible HTTPS endpoint.
#     """
#     arguments = {
#         "calendar_id": request.calendar_id
#     }
    
#     if request.channel_id:
#         arguments["channel_id"] = request.channel_id
#     if request.webhook_url:
#         arguments["webhook_url"] = request.webhook_url
    
#     return execute_composio_tool("GOOGLECALENDAR_EVENTS_WATCH", arguments)

# @router.post("/events/sync", tags=["Events"])
# async def sync_events(request: SyncEventsRequest):
#     """
#     Synchronize events incrementally.
    
#     Retrieves only events that have changed since the last sync operation.
#     More efficient than fetching all events repeatedly.
    
#     **Request Body:**
#     - **calendar_id**: Calendar to sync (default: "primary")
#     - **sync_token**: Token from previous sync (optional, required for incremental sync)
    
#     **Returns:**
#     - Changed events and new sync token
    
#     **Usage:**
#     1. First call without sync_token to get all events
#     2. Store returned sync_token
#     3. Subsequent calls use sync_token to get only changes
#     """
#     arguments = {
#         "calendar_id": request.calendar_id
#     }
    
#     if request.sync_token:
#         arguments["sync_token"] = request.sync_token
    
#     return execute_composio_tool("GOOGLECALENDAR_SYNC_EVENTS", arguments)

# @router.post("/events/quick-add", tags=["Events"])
# async def quick_add_event(request: QuickAddRequest):
#     """
#     Create event using natural language.
    
#     Google Calendar parses the text and automatically creates an event with
#     appropriate time, title, and other details extracted from the description.
    
#     **Request Body:**
#     - **text**: Natural language event description (required)
#     - **calendar_id**: Target calendar (default: "primary")
    
#     **Examples of text input:**
#     - "Lunch tomorrow at 1pm"
#     - "Meeting with John next Tuesday at 3pm for 2 hours"
#     - "Dentist appointment on June 3rd at 10am"
#     - "Weekly standup every Monday at 9am"
    
#     **Returns:**
#     - Created event object
#     """
#     arguments = {
#         "text": request.text,
#         "calendar_id": request.calendar_id
#     }
    
#     return execute_composio_tool("GOOGLECALENDAR_QUICK_ADD", arguments)

# @router.post("/events/remove-attendee", tags=["Events"])
# async def remove_attendee(request: RemoveAttendeeRequest):
#     """
#     Remove an attendee from an event.
    
#     Removes the specified person from the event's attendee list and optionally
#     sends them a cancellation notification.
    
#     **Request Body:**
#     - **event_id**: ID of the event (required)
#     - **attendee_email**: Email of attendee to remove (required)
#     - **calendar_id**: Calendar containing the event (default: "primary")
    
#     **Returns:**
#     - Updated event object without the removed attendee
#     """
#     arguments = {
#         "calendar_id": request.calendar_id,
#         "event_id": request.event_id,
#         "attendee_email": request.attendee_email
#     }
    
#     return execute_composio_tool("GOOGLECALENDAR_REMOVE_ATTENDEE", arguments)

# # Continue with remaining endpoints...
# # (Due to length, I'll include the rest in the next part)

# @router.post("/freebusy/find-slots", tags=["Free/Busy"])
# async def find_free_slots(request: FindFreeSlotsRequest):
#     """
#     Find available time slots across multiple calendars.
    
#     Analyzes multiple calendars to find time periods when all are free.
#     Useful for scheduling meetings with multiple participants.
    
#     **Request Body:**
#     - **time_min**: Start of search window (ISO 8601) (optional)
#     - **time_max**: End of search window (ISO 8601) (optional)
#     # - **calendars**: List of calendar IDs to check (optional)
    
#     **Returns:**
#     - List of free time slots with start and end times
    
#     **Example:**
#     ```json
#     {
#         "time_min": "2025-09-20T09:00:00",
#         "time_max": "2025-09-20T17:00:00",
#         "calendars": ["primary", "user@example.com"]
#     }
#     ```
#     """
#     arguments = {}
    
#     if request.time_min:
#         arguments["time_min"] = request.time_min
#     if request.time_max:
#         arguments["time_max"] = request.time_max
#     # if request.calendars:
#     #     arguments["items"] = [{"id": cal_id} for cal_id in request.calendars]
    
#     return execute_composio_tool("GOOGLECALENDAR_FIND_FREE_SLOTS", arguments)

# # @router.post("/freebusy/query", tags=["Free/Busy"])
# # async def query_free_busy(request: QueryFreeBusyRequest):
# #     """
# #     Query free/busy information for calendars.
    
# #     Returns time periods when specified calendars are busy (have events).
# #     Useful for checking availability before scheduling.
    
# #     **Request Body:**
# #     - **time_min**: Start of query window (ISO 8601) (required)
# #     - **time_max**: End of query window (ISO 8601) (required)
# #     - **calendars**: List of calendar IDs to query (required)
    
# #     **Returns:**
# #     - Busy time blocks for each calendar
    
# #     **Example:**
# #     ```json
# #     {
# #         "time_min": "2025-09-20T00:00:00",
# #         "time_max": "2025-09-21T00:00:00",
# #         "calendars": ["primary", "team@example.com"]
# #     }
# #     ```
# #     """
# #     arguments = {
# #         "time_min": request.time_min,
# #         "time_max": request.time_max,
# #         "items": [{"id": cal_id} for cal_id in request.calendars]
# #     }
    
# #     return execute_composio_tool("GOOGLECALENDAR_FREE_BUSY_QUERY", arguments)

# # ============ CALENDAR ENDPOINTS ============

# @router.get("/calendars/list", tags=["Calendars"])
# async def list_calendars(
#     min_access_role: Optional[str] = Query(None, description="Minimum access role filter (owner, writer, reader, freeBusyReader)"),
#     show_deleted: bool = Query(False, description="Include deleted calendars"),
#     show_hidden: bool = Query(False, description="Include hidden calendars")
# ):
#     """
#     List all Google Calendars accessible to the user.
    
#     Returns calendars from the user's calendar list with optional filtering
#     by access level and inclusion of deleted/hidden calendars.
    
#     **Query Parameters:**
#     - **min_access_role**: Filter by minimum access level
#       - owner: Full ownership
#       - writer: Can modify events
#       - reader: Read-only access
#       - freeBusyReader: Can only see free/busy info
#     - **show_deleted**: Include deleted calendars (default: false)
#     - **show_hidden**: Include hidden calendars (default: false)
    
#     **Returns:**
#     - List of calendar objects with properties and access info
#     """
#     arguments = {
#         "show_deleted": show_deleted,
#         "show_hidden": show_hidden
#     }
    
#     if min_access_role:
#         arguments["min_access_role"] = min_access_role
    
#     return execute_composio_tool("GOOGLECALENDAR_LIST_CALENDARS", arguments)

# @router.get("/calendars/get", tags=["Calendars"])
# async def get_calendar(
#     calendar_id: str = Query("primary", description="Calendar ID to retrieve")
# ):
#     """
#     Get details of a specific Google Calendar.
    
#     Retrieves comprehensive information about a calendar including
#     timezone, description, location, and access settings.
    
#     **Query Parameters:**
#     - **calendar_id**: ID of the calendar (default: "primary")
    
#     **Returns:**
#     - Calendar object with:
#       - summary: Calendar name
#       - description: Calendar description
#       - location: Geographic location
#       - timeZone: IANA timezone
#       - accessRole: User's access level
#     """
#     arguments = {
#         "calendar_id": calendar_id
#     }
    
#     return execute_composio_tool("GOOGLECALENDAR_GET_CALENDAR", arguments)

# @router.post("/calendars/create", tags=["Calendars"])
# async def create_calendar(request: CreateCalendarRequest):
#     """
#     Create a new Google Calendar.
    
#     Creates a secondary calendar with specified properties.
#     The user becomes the owner of the new calendar.
    
#     **Request Body:**
#     - **summary**: Calendar name/title (required)
#     - **description**: Calendar description (optional)
#     - **location**: Geographic location (optional)
#     - **time_zone**: IANA timezone identifier (optional)
    
#     **Returns:**
#     - Created calendar object with ID
    
#     **Example:**
#     ```json
#     {
#         "summary": "Project Deadlines",
#         "description": "Important project milestones",
#         "location": "New York",
#         "time_zone": "America/New_York"
#     }
#     ```
#     """
#     arguments = {
#         "summary": request.summary
#     }
    
#     if request.description:
#         arguments["description"] = request.description
#     if request.location:
#         arguments["location"] = request.location
#     if request.time_zone:
#         arguments["time_zone"] = request.time_zone
    
#     return execute_composio_tool("GOOGLECALENDAR_DUPLICATE_CALENDAR", arguments)

# @router.put("/calendars/update", tags=["Calendars"])
# async def update_calendar(request: UpdateCalendarRequest):
#     """
#     Update properties of an existing calendar.
    
#     Modifies calendar metadata including name, description, location, and timezone.
#     Only the calendar owner can perform updates.
    
#     **Request Body:**
#     - **calendar_id**: Calendar to update (required)
#     - **summary**: New calendar name (optional)
#     - **description**: New description (optional)
#     - **location**: New location (optional)
#     - **time_zone**: New timezone (optional)
    
#     **Returns:**
#     - Updated calendar object
#     """
#     arguments = {
#         "calendar_id": request.calendar_id
#     }
    
#     if request.summary:
#         arguments["summary"] = request.summary
#     if request.description:
#         arguments["description"] = request.description
#     if request.location:
#         arguments["location"] = request.location
#     if request.time_zone:
#         arguments["time_zone"] = request.time_zone
    
#     return execute_composio_tool("GOOGLECALENDAR_CALENDARS_UPDATE", arguments)

# @router.patch("/calendars/patch", tags=["Calendars"])
# async def patch_calendar(request: PatchCalendarRequest):
#     """
#     Patch specific calendar fields.
    
#     Allows partial updates using PATCH semantics. Only specified fields
#     are modified, others remain unchanged.
    
#     **Request Body:**
#     - **calendar_id**: Calendar to patch (required)
#     - **data**: Dictionary of fields to update (optional)
    
#     **Returns:**
#     - Patched calendar object
#     """
#     arguments = {
#         "calendar_id": request.calendar_id,
#         **request.data
#     }
    
#     return execute_composio_tool("GOOGLECALENDAR_PATCH_CALENDAR", arguments)

# @router.delete("/calendars/delete", tags=["Calendars"])
# async def delete_calendar(request: DeleteCalendarRequest):
#     """
#     Permanently delete a calendar.
    
#     Removes the calendar and all its events permanently.
#     Only secondary calendars can be deleted (not the primary calendar).
    
#     **Request Body:**
#     - **calendar_id**: Calendar to delete (required)
    
#     **Returns:**
#     - Success confirmation
    
#     **Warning:** This action is irreversible. All events will be lost.
#     """
#     arguments = {
#         "calendar_id": request.calendar_id
#     }
    
#     return execute_composio_tool("GOOGLECALENDAR_CALENDARS_DELETE", arguments)

# @router.post("/calendars/clear", tags=["Calendars"])
# async def clear_calendar(request: ClearCalendarRequest):
#     """
#     Clear all events from a calendar.
    
#     Removes all events while keeping the calendar itself.
#     Useful for resetting a calendar without deleting it.
    
#     **Request Body:**
#     - **calendar_id**: Calendar to clear (required)
    
#     **Returns:**
#     - Success confirmation
    
#     **Warning:** All events will be permanently deleted.
#     """
#     arguments = {
#         "calendar_id": request.calendar_id
#     }
    
#     return execute_composio_tool("GOOGLECALENDAR_CLEAR_CALENDAR", arguments)

# @router.get("/calendars/timezone", tags=["Calendars"])
# async def get_calendar_timezone(
#     calendar_id: str = Query("primary", description="Calendar ID")
# ):
#     """
#     Get the timezone of a specific calendar.
    
#     Retrieves the IANA timezone identifier for the calendar.
#     Useful for properly displaying event times.
    
#     **Query Parameters:**
#     - **calendar_id**: Calendar to query (default: "primary")
    
#     **Returns:**
#     - Timezone information object
    
#     **Example Response:**
#     ```json
#     {
#         "successful": true,
#         "data": {
#             "timeZone": "America/New_York"
#         }
#     }
#     ```
#     """
#     result = execute_composio_tool("GOOGLECALENDAR_GET_CALENDAR", {"calendar_id": calendar_id})
    
#     if result.get("data") and result["data"].get("timeZone"):
#         return {
#             "successful": True,
#             "data": {
#                 "timeZone": result["data"]["timeZone"]
#             }
#         }
#     return result

# # ============ CALENDAR LIST ENDPOINTS ============

# @router.post("/calendar-list/insert", tags=["Calendar List"])
# async def insert_calendar_to_list(request: InsertCalendarToListRequest):
#     """
#     Add a calendar to the user's calendar list.
    
#     Inserts an existing calendar into the user's list, making it visible
#     in Google Calendar. Can set display color and visibility.
    
#     **Request Body:**
#     - **calendar_id**: Calendar to add (required)
#     - **color_id**: Color for calendar display (optional)
#     - **hidden**: Whether to hide calendar (default: false)
    
#     **Returns:**
#     - Calendar list entry object
#     """
#     arguments = {
#         "id": request.calendar_id,
#         "hidden": request.hidden
#     }
    
#     if request.color_id:
#         arguments["color_id"] = request.color_id
    
#     return execute_composio_tool("GOOGLECALENDAR_CALENDAR_LIST_INSERT", arguments)

# @router.put("/calendar-list/update", tags=["Calendar List"])
# async def update_calendar_list_entry(request: UpdateCalendarListRequest):
#     """
#     Update calendar list entry properties.
    
#     Modifies how a calendar appears in the user's calendar list,
#     including color, notifications, and visibility settings.
    
#     **Request Body:**
#     - **calendar_id**: Calendar to update (required)
#     - **data**: Dictionary of properties to update (optional)
    
#     **Returns:**
#     - Updated calendar list entry
#     """
#     arguments = {
#         "calendar_id": request.calendar_id,
#         **request.data
#     }
    
#     return execute_composio_tool("GOOGLECALENDAR_CALENDAR_LIST_UPDATE", arguments)

# # ============ ACL ENDPOINTS ============

# @router.get("/acl/list", tags=["Access Control"])
# async def list_acl_rules(
#     calendar_id: str = Query("primary", description="Calendar ID")
# ):
#     """
#     List access control rules for a calendar.
    
#     Returns all ACL rules showing who has access to the calendar
#     and their permission levels.
    
#     **Query Parameters:**
#     - **calendar_id**: Calendar to query (default: "primary")
    
#     **Returns:**
#     - List of ACL rules with:
#       - id: Rule identifier
#       - role: Access level (owner, writer, reader, freeBusyReader)
#       - scope: User or group the rule applies to
#     """
#     arguments = {
#         "calendar_id": calendar_id
#     }
    
#     return execute_composio_tool("GOOGLECALENDAR_LIST_ACL_RULES", arguments)

# @router.put("/acl/update", tags=["Access Control"])
# async def update_acl_rule(request: UpdateACLRuleRequest):
#     """
#     Update an access control rule.
    
#     Modifies permissions for a specific user or group.
#     Changes take effect immediately.
    
#     **Request Body:**
#     - **calendar_id**: Calendar containing the rule (required)
#     - **rule_id**: ACL rule to update (required)
#     - **role**: New access level (required)
#       - owner: Full control
#       - writer: Can create/modify events
#       - reader: View-only access
#       - freeBusyReader: Can only see busy/free times
    
#     **Returns:**
#     - Updated ACL rule object
#     """
#     arguments = {
#         "calendar_id": request.calendar_id,
#         "rule_id": request.rule_id,
#         "role": request.role.value
#     }
    
#     return execute_composio_tool("GOOGLECALENDAR_UPDATE_ACL_RULE", arguments)

# # ============ SETTINGS ENDPOINTS ============

# @router.get("/settings/list", tags=["Settings"])
# async def list_settings():
#     """
#     List Google Calendar settings for the authenticated user.
    
#     Returns user preferences and configuration options including
#     timezone, date format, and notification defaults.
    
#     **Returns:**
#     - List of setting objects with:
#       - id: Setting identifier
#       - value: Current setting value
    
#     **Common Settings:**
#     - timezone: User's default timezone
#     - dateFieldOrder: Date format preference
#     - timeFormat: 12-hour or 24-hour format
#     - defaultEventLength: Default event duration
#     """
#     return execute_composio_tool("GOOGLECALENDAR_SETTINGS_LIST", {})

# @router.post("/settings/watch", tags=["Settings"])
# async def watch_settings(request: WatchSettingsRequest):
#     """
#     Set up notifications for settings changes.
    
#     Establishes a webhook to receive notifications when user settings
#     are modified.
    
#     **Request Body:**
#     - **channel_id**: Unique channel identifier (required)
#     - **webhook_url**: URL for notifications (required)
    
#     **Returns:**
#     - Channel configuration with expiration time
    
#     **Note:** Requires HTTPS webhook endpoint.
#     """
#     arguments = {
#         "channel_id": request.channel_id,
#         "webhook_url": request.webhook_url
#     }
    
#     return execute_composio_tool("GOOGLECALENDAR_SETTINGS_WATCH", arguments)

# # ============ UTILITY ENDPOINTS ============

# @router.get("/utils/current-datetime", tags=["Utilities"])
# async def get_current_datetime(
#     utc_offset: str = Query("+00:00", description="UTC offset (e.g., '+05:30' for IST, '-08:00' for PST)")
# ):
#     """
#     Get current date and time in specified timezone.
    
#     Returns the current datetime adjusted for the specified UTC offset.
#     Useful for timezone conversions and scheduling.
    
#     **Query Parameters:**
#     - **utc_offset**: UTC offset string (default: "+00:00")
#       - Format: ±HH:MM
#       - Examples: "+05:30" (India), "-08:00" (PST), "+00:00" (UTC)
    
#     **Returns:**
#     - Current datetime in specified timezone
    
#     **Example Response:**
#     ```json
#     {
#         "successful": true,
#         "data": {
#             "datetime": "2025-09-20T10:30:00+05:30",
#             "timezone": "UTC+05:30"
#         }
#     }
#     ```
#     """
#     arguments = {
#         "utc_offset": utc_offset
#     }
    
#     return execute_composio_tool("GOOGLECALENDAR_GET_CURRENT_DATE_TIME", arguments)

# @router.get("/utils/connected-accounts", tags=["Utilities"])
# async def get_connected_accounts():
#     """
#     Get all connected Composio accounts.
    
#     Returns information about all authenticated Google Calendar connections
#     available to the API.
    
#     **Returns:**
#     - List of connected accounts with:
#       - toolkit: Service name (googlecalendar)
#       - id: Account identifier
#       - user_id: Associated user
#       - status: Connection status (ACTIVE, INACTIVE)
    
#     **Use Case:**
#     Check which Google accounts are connected and available for use.
#     """
#     if not connected_accounts_cache:
#         connected_accounts_cache.update(fetch_connected_accounts())
    
#     return {
#         "accounts": [
#             {
#                 "toolkit": slug,
#                 "id": account.id,
#                 "user_id": account.user_id,
#                 "status": account.status
#             }
#             for slug, account in connected_accounts_cache.items()
#         ]
#     }

# @router.post("/utils/refresh-accounts", tags=["Utilities"])
# async def refresh_connected_accounts():
#     """
#     Refresh the connected accounts cache.
    
#     Fetches latest connection information from Composio.
#     Call this after connecting a new account or if you suspect
#     the cache is stale.
    
#     **Returns:**
#     - Refresh confirmation with account count
    
#     **Example Response:**
#     ```json
#     {
#         "message": "Connected accounts refreshed",
#         "count": 2
#     }
#     ```
#     """
#     connected_accounts_cache.clear()
#     connected_accounts_cache.update(fetch_connected_accounts())
#     return {"message": "Connected accounts refreshed", "count": len(connected_accounts_cache)}

# # ============ HEALTH CHECK ENDPOINTS ============

# # @router.get("/", tags=["Health"])
# # async def root():
# #     """
# #     API root endpoint with documentation links.
    
# #     Provides an overview of available endpoint categories and
# #     links to API documentation.
    
# #     **Returns:**
# #     - API information and endpoint categories
# #     """
# #     return {
# #         "message": "Composio Google Calendar API",
# #         "version": "1.0.0",
# #         "documentation": "/docs",
# #         "endpoints": {
# #             "events": "Event creation, updating, deletion, and management",
# #             "calendars": "Calendar operations and properties",
# #             "freebusy": "Availability and scheduling queries",
# #             "acl": "Access control and sharing",
# #             "settings": "User preferences and configuration",
# #             "utils": "Utility functions and helpers"
# #         }
# #     }

# # @router.get("/health", tags=["Health"])
# # async def health_check():
# #     """
# #     Health check endpoint for monitoring.
    
# #     Returns API status and configuration validation.
# #     Use for uptime monitoring and deployment verification.
    
# #     **Returns:**
# #     - Health status and configuration check
    
# #     **Example Response:**
# #     ```json
# #     {
# #         "status": "healthy",
# #         "composio_api_key": "configured",
# #         "connected_accounts": 2
# #     }
# #     ```
# #     """
# #     account_count = len(connected_accounts_cache) if connected_accounts_cache else 0
# #     return {
# #         "status": "healthy",
# #         "composio_api_key": "configured" if COMPOSIO_API_KEY else "missing",
# #         "connected_accounts": account_count
# #     }

    