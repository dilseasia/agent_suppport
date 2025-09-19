from pydantic import BaseModel
from typing import Optional, List

class CreateAuthConfigRequest(BaseModel):
    organization_id: str
    toolkit_slug: str
    auth_type: str = "OAUTH2"  # OAUTH2 | BEARER_TOKEN | API_KEY
    bearer_token: Optional[str] = None
    api_key_secret: Optional[str] = None
    scopes: Optional[List[str]] = []
    config_name: Optional[str] = None

class DeleteAuthConfigRequest(BaseModel):
    organization_id: str
    nanoid: str

class ConnectRequest(BaseModel):
    organization_id: str
    auth_config_id: str

class StatusRequest(BaseModel):
    organization_id: str
    nanoid: str
    status: str  # "ENABLED" or "DISABLED"
