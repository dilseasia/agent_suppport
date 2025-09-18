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
