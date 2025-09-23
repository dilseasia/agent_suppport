from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# -----------------------------
# Auth Config Requests
# -----------------------------
class CreateAuthConfigRequest(BaseModel):
    organization_id: str
    toolkit_slug: str
    auth_type: Optional[str] = "OAUTH2"
    bearer_token: Optional[str] = None
    api_key_secret: Optional[str] = None
    scopes: Optional[List[str]] = None
    config_name: Optional[str] = None

class DeleteAuthConfigRequest(BaseModel):
    organization_id: str
    nanoid: str

class ConnectAuthConfigRequest(BaseModel):
    organization_id: str
    auth_config_id: str
    user_id: str

class SetStatusRequest(BaseModel):
    nanoid: str
    status: str

class ListAuthConfigsRequest(BaseModel):
    organization_id: str

# -----------------------------
# Tools Requests
# -----------------------------
class ToolRequest(BaseModel):
    toolkit_slug: str
    tool_slugs: Optional[List[str]] = None

class ToolParameterRequest(BaseModel):
    tool_slug: str

class ToolkitSearchRequest(BaseModel):
    search_term: str

# -----------------------------
# Combined Auth & Connect
# -----------------------------
class CreateAndConnectRequest(BaseModel):
    organization_id: str
    toolkit_slug: str
    user_id: str
    auth_type: Optional[str] = "OAUTH2"
    bearer_token: Optional[str] = None
    api_key_secret: Optional[str] = None
    scopes: Optional[List[str]] = None
    config_name: Optional[str] = None
    status: Optional[str] = "enabled"
    is_connected: Optional[bool] = None

# -----------------------------
# Tool Parameters
# -----------------------------
class ParameterInfo(BaseModel):
    name: str
    required: bool
    optional: bool
    type: str

# -----------------------------
# Tool Schema (used internally)
# -----------------------------
class ToolSchemaResponse(BaseModel):
    slug: str
    name: str
    description: Optional[str]
    parameters: Dict[str, Any]
    response_schema: Dict[str, Any]
    toolkit_slug: Optional[str]

class AuthConfig(BaseModel):
    id: str
    name: Optional[str] = None
    organization_id: str
    toolkit_slug: Optional[str] = None
    auth_scheme: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    scopes: Optional[List[str]] = []
    connections_count: Optional[int] = 0