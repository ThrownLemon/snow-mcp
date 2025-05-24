"""Pytest configuration file for ServiceNow MCP tests."""

import os
import pytest
from dotenv import load_dotenv

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig, AuthConfig, AuthType, BasicAuthConfig

# Load environment variables
load_dotenv()

@pytest.fixture
def auth_manager():
    """Fixture to provide an authenticated AuthManager."""
    username = os.getenv("SERVICENOW_USERNAME")
    password = os.getenv("SERVICENOW_PASSWORD")
    
    auth_config = AuthConfig(
        type=AuthType.BASIC,
        basic=BasicAuthConfig(username=username, password=password),
    )
    
    return AuthManager(auth_config)

@pytest.fixture
def server_config():
    """Fixture to provide a ServerConfig."""
    instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
    username = os.getenv("SERVICENOW_USERNAME")
    password = os.getenv("SERVICENOW_PASSWORD")
    
    auth_config = AuthConfig(
        type=AuthType.BASIC,
        basic=BasicAuthConfig(username=username, password=password),
    )
    
    return ServerConfig(
        instance_url=instance_url,
        auth=auth_config,
    )

@pytest.fixture
def workflow_id(auth_manager, server_config):
    """Fixture to provide a workflow ID for testing."""
    from servicenow_mcp.tools.workflow_tools import list_workflows
    
    result = list_workflows(auth_manager, server_config, {"limit": 1})
    if "error" in result:
        pytest.skip(f"Could not get workflow ID: {result['error']}")
    
    if not result.get("workflows") or len(result["workflows"]) == 0:
        pytest.skip("No workflows found in the instance")
    
    return result["workflows"][0]["sys_id"]
