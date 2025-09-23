from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# -----------------------------
# Auth Config Responses
# -----------------------------
class AuthConfig(BaseModel):
    id: str
    name: Optional[str]
    organization_id: str
    toolkit_slug: Optional[str]
    auth_scheme: Optional[str]
    type: Optional[str]
    status: Optional[str]
    scopes: Optional[List[str]] = []
    connections_count: Optional[int] = 0

class AuthConfigListResponse(BaseModel):
    message: Optional[str]
    items: List[AuthConfig]

class CreateAuthConfigResponse(BaseModel):
    message: Optional[str] = "Auth config created successfully"
    data: AuthConfig

class DeleteAuthConfigResponse(BaseModel):
    message: str
    data: Optional[Any] = None

# -----------------------------
# Connect Responses
# -----------------------------
class ConnectAuthConfigResponse(BaseModel):
    message: Optional[str] = None
    redirect_url: Optional[str] = None
    connected_account_id: Optional[str] = None
    status: Optional[str] = None
    is_connected: Optional[bool] = None


# -----------------------------
# Status Responses
# -----------------------------
class StatusUpdateResponse(BaseModel):
    message: str
    data: Optional[Any] = None

# -----------------------------
# Tools Responses
# -----------------------------
class ToolItem(BaseModel):
    slug: str
    name: str

class ToolListResponse(BaseModel):
    total_tools_found: int
    tools: List[ToolItem]

class ToolParameterResponse(BaseModel):
    tool_slug: str
    tool_name: str
    parameters: List[Dict[str, Any]]  # Or List[ParameterInfo] if strict typing

# -----------------------------
# Connected Accounts Responses
# -----------------------------
class ConnectedAccountResponse(BaseModel):
    connected_account_id: str
    tool_slug: Optional[str]
    user_id: Optional[str]
    status: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    auth_config_id: Optional[str]
    auth_scheme: Optional[str]
    is_disabled: Optional[bool] = None
    data_status: Optional[str]
    scopes: Optional[List[str]] = []
    callback_url: Optional[str]

class ConnectedAccountsByOrgResponse(BaseModel):
    organization_id: str
    connected_accounts: List[ConnectedAccountResponse]
