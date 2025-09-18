from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from typing import Optional, Any

class AuthRequest(BaseModel):
    organization_id: str
    toolkit_slug: str
    composio_api_key: str
    bearer_token: Optional[str] = None
    api_key_secret: Optional[str] = None
    scopes: Optional[List[str]] = None
    config_name: Optional[str] = None
from typing import Optional, Any

class AuthResponse(BaseModel):
    id: int
    organization_id: str
    toolkit_slug: str
    auth_config_id: str
    uuid: Optional[str] = None
    name: Optional[str] = None
    auth_scheme: Optional[str] = None
    is_composio_managed: Optional[bool] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    oauth_redirect_uri: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    status: Optional[str] = None
    toolkit_logo: Optional[str] = None
    last_updated_at: Optional[datetime] = None
    no_of_connections: Optional[int] = None
    expected_input_fields: Optional[Any] = None
    restrict_to_following_tools: Optional[Any] = None  # <--- change from dict to Any
    type: Optional[str] = None
    tools_for_connected_account_creation: Optional[Any] = None
    tools_available_for_execution: Optional[Any] = None
    deprecated_default_connector_id: Optional[str] = None
    deprecated_member_uuid: Optional[str] = None
    deprecated_toolkit_id: Optional[str] = None
    deprecated_expected_input_fields: Optional[Any] = None

    class Config:
        from_attributes = True  # for Pydantic v2

