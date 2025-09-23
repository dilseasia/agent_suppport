from sqlalchemy import Column, String, Integer, Boolean, DateTime, ARRAY,func
from database import Base
from sqlalchemy.orm import Mapped, mapped_column


class AuthConfig(Base):
    __tablename__ = "auth_configs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String, nullable=False,unique=True)  # updated column name
    auth_config_id = Column(String, nullable=False, unique=True)
    uuid = Column(String, nullable=True)
    name = Column(String, nullable=True)
    auth_scheme = Column(String, nullable=True)
    is_composio_managed = Column(Boolean, nullable=True)

    # Credentials fields
    client_id = Column(String, nullable=True)
    client_secret = Column(String, nullable=True)
    verification_token = Column(String, nullable=True)
    scopes = Column(ARRAY(String), nullable=True)
    user_scopes = Column(ARRAY(String), nullable=True)
    oauth_redirect_uri = Column(String, nullable=True)

    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)
    last_updated_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=True)

    # Toolkit fields
    toolkit_slug = Column(String, nullable=True)
    toolkit_logo = Column(String, nullable=True)

    no_of_connections = Column(Integer, nullable=True)

    # Tool access config
    tools_for_connected_account_creation = Column(ARRAY(String), nullable=True)
    tools_available_for_execution = Column(ARRAY(String), nullable=True)

    type = Column(String, nullable=True)

    # Deprecated params
    deprecated_default_connector_id = Column(String, nullable=True)
    deprecated_member_uuid = Column(String, nullable=True)
    deprecated_toolkit_id = Column(String, nullable=True)
    deprecated_expected_input_fields = Column(ARRAY(String), nullable=True)

class ConnectedAccount(Base):
    __tablename__ = "connected_accounts"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String, nullable=False)
    auth_config_id = Column(String, nullable=False)
    connected_account_id = Column(String, nullable=False, unique=True)
    tools_slug_name = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="enable")  # from request
    is_connected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)