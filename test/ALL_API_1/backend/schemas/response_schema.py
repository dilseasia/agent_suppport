from pydantic import BaseModel
from typing import List, Optional, Any

# -----------------------------
# Auth Config Responses
# -----------------------------
class AuthConfig(BaseModel):
    nanoid: Optional[str]
    id: Optional[str]
    name: Optional[str]
    toolkit: Optional[Any]
    auth_scheme: Optional[str]
    type: Optional[str]
    scopes: Optional[List[str]] = []
    connections_count: Optional[int] = 0

class AuthConfigListResponse(BaseModel):
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
    redirect_url: Optional[str]
    connected_account_id: Optional[str]

# -----------------------------
# Status Responses
# -----------------------------
class StatusUpdateResponse(BaseModel):
    message: str
    data: Optional[Any] = None
