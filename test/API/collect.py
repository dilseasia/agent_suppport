from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSON
from database import Base

class AuthConfigRecord(Base):
    __tablename__ = "auth_configs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String, nullable=False)
    toolkit_slug = Column(String, nullable=False)
    auth_config_id = Column(String, nullable=False)

    uuid = Column(String, nullable=True)
    name = Column(String, nullable=True)
    auth_scheme = Column(String, nullable=True)
    is_composio_managed = Column(Boolean, nullable=True)
    client_id = Column(String, nullable=True)
    client_secret = Column(String, nullable=True)
    oauth_redirect_uri = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=True)
    toolkit_logo = Column(String, nullable=True)
    last_updated_at = Column(DateTime, nullable=True)
    no_of_connections = Column(Integer, nullable=True)
    expected_input_fields = Column(JSON, nullable=True)
    restrict_to_following_tools = Column(JSON, nullable=True)
    type = Column(String, nullable=True)
    tools_for_connected_account_creation = Column(JSON, nullable=True)
    tools_available_for_execution = Column(JSON, nullable=True)
    deprecated_default_connector_id = Column(String, nullable=True)
    deprecated_member_uuid = Column(String, nullable=True)
    deprecated_toolkit_id = Column(String, nullable=True)
    deprecated_expected_input_fields = Column(JSON, nullable=True)


from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "postgresql+psycopg2://composio_user_new:daljeet123@localhost:5432/composio_new_db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from models import AuthConfigRecord

COMPOSIO_BASE_URL = "https://backend.composio.dev/api/v3"

def create_auth_config(
    composio_api_key: str,
    toolkit_slug: str,
    auth_type: str = "OAUTH2",
    bearer_token: Optional[str] = None,
    api_key_secret: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    config_name: Optional[str] = None
) -> Dict[str, Any]:
    url = f"{COMPOSIO_BASE_URL}/auth_configs"
    headers = {"x-api-key": composio_api_key, "Content-Type": "application/json"}

    if not config_name:
        config_name = f"{toolkit_slug.capitalize()} Auth Config"

    if bearer_token:
        auth_type = "BEARER_TOKEN"
    elif api_key_secret:
        auth_type = "API_KEY"
    else:
        auth_type = "OAUTH2"

    if auth_type == "OAUTH2":
        data = {
            "toolkit": {"slug": toolkit_slug},
            "auth_config": {"type": "use_composio_managed_auth", "auth_scheme": "OAUTH2", "scopes": scopes or [], "name": config_name}
        }
    elif auth_type == "BEARER_TOKEN":
        data = {
            "toolkit": {"slug": toolkit_slug},
            "auth_config": {"type": "user_provided_auth", "auth_scheme": "BEARER_TOKEN", "name": config_name, "credentials": {"bearer_token": bearer_token}}
        }
    elif auth_type == "API_KEY":
        data = {
            "toolkit": {"slug": toolkit_slug},
            "auth_config": {"type": "user_provided_auth", "auth_scheme": "API_KEY", "name": config_name, "credentials": {"api_key": api_key_secret}}
        }
    else:
        raise ValueError(f"Unsupported auth type: {auth_type}")

    print("Payload:", data)
    response = requests.post(url, json=data, headers=headers)
    print("Status:", response.status_code, response.text)
    response.raise_for_status()
    return response.json()

def save_auth_config_to_db(db: Session, org_id: str, toolkit_slug: str, auth_data: dict) -> AuthConfigRecord:
    ac = auth_data.get("auth_config", {})
    created_at = ac.get("created_at")
    last_updated_at = ac.get("last_updated_at")
    if created_at:
        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    if last_updated_at:
        last_updated_at = datetime.fromisoformat(last_updated_at.replace("Z", "+00:00"))

    record = AuthConfigRecord(
        organization_id=org_id,
        toolkit_slug=toolkit_slug,
        auth_config_id=ac.get("id") or auth_data.get("nanoid"),
        uuid=ac.get("uuid"),
        name=ac.get("name"),
        auth_scheme=ac.get("auth_scheme"),
        is_composio_managed=ac.get("is_composio_managed"),
        client_id=ac.get("credentials", {}).get("client_id"),
        client_secret=ac.get("credentials", {}).get("client_secret"),
        oauth_redirect_uri=ac.get("credentials", {}).get("oauth_redirect_uri"),
        created_by=ac.get("created_by"),
        created_at=created_at,
        status=ac.get("status"),
        toolkit_logo=ac.get("toolkit", {}).get("logo"),
        last_updated_at=last_updated_at,
        no_of_connections=ac.get("no_of_connections"),
        expected_input_fields=ac.get("expected_input_fields"),
        restrict_to_following_tools=ac.get("restrict_to_following_tools"),
        type=ac.get("type"),
        tools_for_connected_account_creation=ac.get("tool_access_config", {}).get("tools_for_connected_account_creation"),
        tools_available_for_execution=ac.get("tool_access_config", {}).get("tools_available_for_execution"),
        deprecated_default_connector_id=ac.get("deprecated_params", {}).get("default_connector_id"),
        deprecated_member_uuid=ac.get("deprecated_params", {}).get("member_uuid"),
        deprecated_toolkit_id=ac.get("deprecated_params", {}).get("toolkit_id"),
        deprecated_expected_input_fields=ac.get("deprecated_params", {}).get("expected_input_fields")
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from schemas import AuthRequest, AuthResponse
from service import create_auth_config, save_auth_config_to_db

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Composio Auth API")

@app.post("/create-auth", response_model=AuthResponse)
def create_and_store_auth(req: AuthRequest, db: Session = Depends(get_db)):
    """
    Single endpoint to create an auth config in Composio,
    then store it in the local database and return the record.
    """
    try:
        # 1️⃣ Create auth config in Composio
        print("=== Creating auth config in Composio ===")
        created = create_auth_config(
            composio_api_key=req.composio_api_key,
            toolkit_slug=req.toolkit_slug,
            bearer_token=req.bearer_token,
            api_key_secret=req.api_key_secret,
            scopes=req.scopes,
            config_name=req.config_name
        )
        print("Created response:", created)

        # 2️⃣ Save response to local database
        print("=== Saving auth config to database ===")
        record = save_auth_config_to_db(db, req.organization_id, req.toolkit_slug, created)
        print("Saved record:", record)

        # 3️⃣ Return saved record
        return record

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
