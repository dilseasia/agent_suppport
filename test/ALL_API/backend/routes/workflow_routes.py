from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.item_model import AuthConfigRecord
from schemas.request_schema import (
    CreateAuthConfigRequest,
    DeleteAuthConfigRequest,
    ConnectRequest,
    StatusRequest
)
from services.composio_service import (
    create_auth_config,
    delete_auth_config,
    connect_auth_config,
    set_auth_config_status,
    fetch_auth_config_details
)

router = APIRouter(prefix="/workflow")

# ------------------------
# Existing Basic Operations
# ------------------------

@router.post("/create-auth-config")
async def create_auth_config_route(
    data: CreateAuthConfigRequest,
    x_api_key: str = Header(...)
):
    try:
        return create_auth_config(
            composio_api_key=x_api_key,
            organization_id=data.organization_id,
            toolkit_slug=data.toolkit_slug,
            auth_type=data.auth_type,
            bearer_token=data.bearer_token,
            api_key_secret=data.api_key_secret,
            scopes=data.scopes,
            config_name=data.config_name
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/delete-auth-config")
async def delete_auth_config_route(
    data: DeleteAuthConfigRequest,
    x_api_key: str = Header(...)
):
    try:
        return delete_auth_config(
            composio_api_key=x_api_key,
            organization_id=data.organization_id,
            nanoid=data.nanoid
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/connect-auth-config")
async def connect_auth_config_route(
    data: ConnectRequest,
    x_api_key: str = Header(...)
):
    try:
        return connect_auth_config(
            composio_api_key=x_api_key,
            organization_id=data.organization_id,
            auth_config_id=data.auth_config_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/set-status")
async def set_status_route(
    data: StatusRequest,
    x_api_key: str = Header(...)
):
    try:
        return set_auth_config_status(
            composio_api_key=x_api_key,
            organization_id=data.organization_id,
            nanoid=data.nanoid,
            status=data.status
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ------------------------
# New Combined Operation
# ------------------------

@router.post("/create-fetch-save")
async def create_fetch_save_auth_config(
    data: CreateAuthConfigRequest,
    x_api_key: str = Header(...),
    db: Session = Depends(get_db)
):
    try:
        # Step 1 — Create auth config
        created = create_auth_config(
            composio_api_key=x_api_key,
            organization_id=data.organization_id,
            toolkit_slug=data.toolkit_slug,
            auth_type=data.auth_type,
            bearer_token=data.bearer_token,
            api_key_secret=data.api_key_secret,
            scopes=data.scopes or [],
            config_name=data.config_name
        )

        # Step 1.1 — Extract nanoid from nested response
        nanoid = created.get("auth_config", {}).get("id")
        if not nanoid:
            raise HTTPException(
                status_code=400,
                detail=f"Create failed: no ID returned. Response: {created}"
            )

        # Step 2 — Fetch details
        details = fetch_auth_config_details(
            composio_api_key=x_api_key,
            organization_id=data.organization_id,
            nanoid=nanoid
        )

        # Step 3 — Save to DB
        record = AuthConfigRecord(
            organization_id=data.organization_id,
            toolkit_slug=data.toolkit_slug,
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

        # Step 4 — Verify the record exists in DB
        saved_record = db.query(AuthConfigRecord).filter_by(auth_config_id=nanoid).first()
        if not saved_record:
            raise HTTPException(status_code=500, detail="Record not found in DB after save.")

        # Step 5 — Return response
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
