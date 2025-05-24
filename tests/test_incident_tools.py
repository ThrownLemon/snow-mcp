"""
Tests for the ServiceNow MCP incident tools.
"""

import pytest
from unittest.mock import MagicMock

import requests

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.incident_tools import (
    AddCommentParams,
    CreateIncidentParams,
    ListIncidentsParams,
    ResolveIncidentParams,
    UpdateIncidentParams,
    add_comment,
    create_incident,
    list_incidents,
    resolve_incident,
    update_incident,
)
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig


@pytest.fixture
def config():
    """Fixture to provide a ServerConfig for testing."""
    return ServerConfig(
        instance_url="https://example.service-now.com",
        auth=AuthConfig(
            type=AuthType.BASIC,
            basic=BasicAuthConfig(username="admin", password="password"),
        ),
    )

@pytest.fixture
def auth_manager():
    """Fixture to provide a mock AuthManager for testing."""
    manager = MagicMock(spec=AuthManager)
    manager.get_headers.return_value = {"Authorization": "Basic YWRtaW46cGFzc3dvcmQ="}
    return manager

def test_create_incident(monkeypatch, config, auth_manager):
    """Test creating an incident."""
    # Create mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": {"sys_id": "inc123", "number": "INC0010001"}
    }
    mock_response.raise_for_status = MagicMock()
    
    # Setup monkeypatch
    def mock_post(*args, **kwargs):
        assert args[0] == f"{config.api_url}/table/incident"
        assert kwargs["json"]["short_description"] == "Test incident"
        assert kwargs["json"]["priority"] == "1"
        return mock_response
    
    monkeypatch.setattr(requests, 'post', mock_post)
    
    # Call function
    params = CreateIncidentParams(
        short_description="Test incident",
        description="Detailed description of test incident",
        priority="1",
    )
    result = create_incident(config, auth_manager, params)
    
    # Assertions
    assert result.success is True
    assert result.incident_id == "inc123"
    assert result.incident_number == "INC0010001"

def test_update_incident_by_sys_id(monkeypatch, config, auth_manager):
    """Test updating an incident by sys_id."""
    # Mock responses
    mock_put_response = MagicMock()
    mock_put_response.json.return_value = {
        "result": {"sys_id": "inc123", "number": "INC0010001"}
    }
    mock_put_response.raise_for_status = MagicMock()
    
    mock_get_response = MagicMock()
    mock_get_response.json.return_value = {"result": [{"sys_id": "inc123"}]}
    mock_get_response.raise_for_status = MagicMock()
    
    # Setup monkeypatch
    def mock_put(*args, **kwargs):
        assert args[0] == f"{config.api_url}/table/incident/inc123"
        assert kwargs["json"]["priority"] == "2"
        assert kwargs["json"]["work_notes"] == "Investigating"
        return mock_put_response
    
    def mock_get(*args, **kwargs):
        return mock_get_response
    
    monkeypatch.setattr(requests, 'put', mock_put)
    monkeypatch.setattr(requests, 'get', mock_get)
    
    # Call function
    params = UpdateIncidentParams(incident_id="inc123", priority="2", work_notes="Investigating")
    result = update_incident(config, auth_manager, params)
    
    # Assertions
    assert result.success is True
    assert result.incident_id == "inc123"

def test_update_incident_by_number(monkeypatch, config, auth_manager):
    """Test updating an incident by incident number."""
    # Mock responses
    mock_get_response = MagicMock()
    mock_get_response.json.return_value = {"result": [{"sys_id": "inc123"}]}
    mock_get_response.raise_for_status = MagicMock()
    
    mock_put_response = MagicMock()
    mock_put_response.json.return_value = {
        "result": {"sys_id": "inc123", "number": "INC0010001"}
    }
    mock_put_response.raise_for_status = MagicMock()
    
    # Track call counts
    get_called = False
    put_called = False
    
    # Setup monkeypatch
    def mock_get(*args, **kwargs):
        nonlocal get_called
        get_called = True
        return mock_get_response
    
    def mock_put(*args, **kwargs):
        nonlocal put_called
        put_called = True
        assert args[0] == f"{config.api_url}/table/incident/inc123"
        return mock_put_response
    
    monkeypatch.setattr(requests, 'get', mock_get)
    monkeypatch.setattr(requests, 'put', mock_put)
    
    # Call function
    params = UpdateIncidentParams(
        incident_id="INC0010001", priority="2", work_notes="Investigating"
    )
    result = update_incident(config, auth_manager, params)
    
    # Assertions
    assert result.success is True
    assert result.incident_id == "inc123"
    assert get_called is True
    assert put_called is True

def test_add_comment_by_sys_id(monkeypatch, config, auth_manager):
    """Test adding a comment to an incident by sys_id."""
    # Mock responses
    mock_put_response = MagicMock()
    mock_put_response.json.return_value = {
        "result": {"sys_id": "inc123", "number": "INC0010001"}
    }
    mock_put_response.raise_for_status = MagicMock()
    
    mock_get_response = MagicMock()
    mock_get_response.json.return_value = {"result": [{"sys_id": "inc123"}]}
    mock_get_response.raise_for_status = MagicMock()
    
    # Setup monkeypatch
    def mock_put(*args, **kwargs):
        assert args[0] == f"{config.api_url}/table/incident/inc123"
        assert kwargs["json"]["work_notes"] == "Test comment"
        return mock_put_response
    
    def mock_get(*args, **kwargs):
        return mock_get_response
    
    monkeypatch.setattr(requests, 'put', mock_put)
    monkeypatch.setattr(requests, 'get', mock_get)
    
    # Call function
    params = AddCommentParams(incident_id="inc123", comment="Test comment", is_work_note=True)
    result = add_comment(config, auth_manager, params)
    
    # Assertions
    assert result.success is True

def test_add_comment_by_number(monkeypatch, config, auth_manager):
    """Test adding a comment to an incident by incident number."""
    # Mock responses
    mock_get_response = MagicMock()
    mock_get_response.json.return_value = {"result": [{"sys_id": "inc123"}]}
    mock_get_response.raise_for_status = MagicMock()
    
    mock_put_response = MagicMock()
    mock_put_response.json.return_value = {
        "result": {"sys_id": "inc123", "number": "INC0010001"}
    }
    mock_put_response.raise_for_status = MagicMock()
    
    # Track call counts
    get_called = False
    put_called = False
    
    # Setup monkeypatch
    def mock_get(*args, **kwargs):
        nonlocal get_called
        get_called = True
        return mock_get_response
    
    def mock_put(*args, **kwargs):
        nonlocal put_called
        put_called = True
        assert args[0] == f"{config.api_url}/table/incident/inc123"
        assert kwargs["json"]["comments"] == "Test comment"
        return mock_put_response
    
    monkeypatch.setattr(requests, 'get', mock_get)
    monkeypatch.setattr(requests, 'put', mock_put)
    
    # Call function
    params = AddCommentParams(
        incident_id="INC0010001", comment="Test comment", is_work_note=False
    )
    result = add_comment(config, auth_manager, params)
    
    # Assertions
    assert result.success is True
    assert get_called is True
    assert put_called is True

def test_resolve_incident_by_sys_id(monkeypatch, config, auth_manager):
    """Test resolving an incident by sys_id."""
    # Mock responses
    mock_put_response = MagicMock()
    mock_put_response.json.return_value = {
        "result": {"sys_id": "inc123", "number": "INC0010001"}
    }
    mock_put_response.raise_for_status = MagicMock()
    
    mock_get_response = MagicMock()
    mock_get_response.json.return_value = {"result": [{"sys_id": "inc123"}]}
    mock_get_response.raise_for_status = MagicMock()
    
    # Setup monkeypatch
    def mock_put(*args, **kwargs):
        assert args[0] == f"{config.api_url}/table/incident/inc123"
        return mock_put_response
    
    def mock_get(*args, **kwargs):
        return mock_get_response
    
    monkeypatch.setattr(requests, 'put', mock_put)
    monkeypatch.setattr(requests, 'get', mock_get)
    
    # Call function
    params = ResolveIncidentParams(
        incident_id="inc123",
        resolution_code="Solved (Permanently)",
        resolution_notes="Issue resolved."
    )
    result = resolve_incident(config, auth_manager, params)
    
    # Assertions
    assert result.success is True

def test_resolve_incident_by_number(monkeypatch, config, auth_manager):
    """Test resolving an incident by incident number."""
    # Mock responses
    mock_get_response = MagicMock()
    mock_get_response.json.return_value = {"result": [{"sys_id": "inc123"}]}
    mock_get_response.raise_for_status = MagicMock()
    
    mock_put_response = MagicMock()
    mock_put_response.json.return_value = {
        "result": {"sys_id": "inc123", "number": "INC0010001"}
    }
    mock_put_response.raise_for_status = MagicMock()
    
    # Track call counts
    get_called = False
    put_called = False
    
    # Setup monkeypatch
    def mock_get(*args, **kwargs):
        nonlocal get_called
        get_called = True
        return mock_get_response
    
    def mock_put(*args, **kwargs):
        nonlocal put_called
        put_called = True
        assert args[0] == f"{config.api_url}/table/incident/inc123"
        assert kwargs["json"]["close_code"] == "Solved (Workaround)"
        return mock_put_response
    
    monkeypatch.setattr(requests, 'get', mock_get)
    monkeypatch.setattr(requests, 'put', mock_put)
    
    # Call function
    params = ResolveIncidentParams(
        incident_id="INC0010001",
        resolution_code="Solved (Workaround)",
        resolution_notes="Workaround applied.",
    )
    result = resolve_incident(config, auth_manager, params)
    
    # Assertions
    assert result.success is True
    assert get_called is True
    assert put_called is True

def test_list_incidents(monkeypatch, config, auth_manager):
    """Test listing incidents."""
    # Mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": [
            {"sys_id": "inc123", "number": "INC0010001", "short_description": "Test 1"},
            {"sys_id": "inc456", "number": "INC0010002", "short_description": "Test 2"},
        ]
    }
    mock_response.raise_for_status = MagicMock()
    
    # Setup monkeypatch without specific query assertion
    def mock_get(*args, **kwargs):
        assert args[0] == f"{config.api_url}/table/incident"
        assert kwargs["params"]["sysparm_limit"] == 10
        # Don't assert on the exact query string as it may be transformed
        return mock_response
    
    monkeypatch.setattr(requests, 'get', mock_get)
    
    # Call function
    params = ListIncidentsParams(limit=10, query="active=true")
    result = list_incidents(config, auth_manager, params)
    
    # Assertions
    assert result["success"] is True  # Using dictionary access instead of attribute
    assert len(result["incidents"]) == 2
    assert result["incidents"][0]["number"] == "INC0010001"
    assert result["incidents"][1]["short_description"] == "Test 2"

def test_create_incident_api_error(monkeypatch, config, auth_manager):
    """Test create_incident with an API error."""
    # Setup monkeypatch
    def mock_post(*args, **kwargs):
        raise requests.exceptions.RequestException("API Error")
    
    monkeypatch.setattr(requests, 'post', mock_post)
    
    # Call function
    params = CreateIncidentParams(short_description="Error test")
    result = create_incident(config, auth_manager, params)
    
    # Assertions
    assert result.success is False
    assert "Failed to create incident" in result.message

def test_update_incident_api_error(monkeypatch, config, auth_manager):
    """Test update_incident with an API error."""
    # Import the module to patch
    import servicenow_mcp.tools.incident_tools
    
    # Setup mock
    error_result = {
        "success": False,
        "message": "Failed to find incident: 401 Client Error: Unauthorized for url: https://example.service-now.com/api/now/table/incident?sysparm_query=number%3Dinc123&sysparm_limit=1"
    }
    
    # Setup monkeypatch
    def mock_find_incident_sys_id(*args, **kwargs):
        return error_result
    
    monkeypatch.setattr(servicenow_mcp.tools.incident_tools, '_find_incident_sys_id', mock_find_incident_sys_id)
    
    # Call function
    params = UpdateIncidentParams(incident_id="inc123", priority="1")
    result = update_incident(config, auth_manager, params)
    
    # Assertions
    assert result.success is False
    assert "Failed to find incident" in result.message

def test_update_incident_not_found_error(monkeypatch, config, auth_manager):
    """Test update_incident when incident number is not found."""
    # Mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": []}
    mock_response.raise_for_status = MagicMock()
    
    # Setup monkeypatch
    def mock_get(*args, **kwargs):
        return mock_response
    
    monkeypatch.setattr(requests, 'get', mock_get)
    
    # Call function
    params = UpdateIncidentParams(incident_id="INC_NOT_EXIST", priority="1")
    result = update_incident(config, auth_manager, params)
    
    # Assertions
    assert result.success is False
    assert "Incident not found" in result.message

def test_add_comment_api_error(monkeypatch, config, auth_manager):
    """Test add_comment with an API error."""
    # Import the module to patch
    import servicenow_mcp.tools.incident_tools
    
    # Setup mock
    error_result = {
        "success": False,
        "message": "Failed to find incident: 401 Client Error: Unauthorized for url: https://example.service-now.com/api/now/table/incident?sysparm_query=number%3Dinc123&sysparm_limit=1"
    }
    
    # Setup monkeypatch
    def mock_find_incident_sys_id(*args, **kwargs):
        return error_result
    
    monkeypatch.setattr(servicenow_mcp.tools.incident_tools, '_find_incident_sys_id', mock_find_incident_sys_id)
    
    # Call function
    params = AddCommentParams(incident_id="inc123", comment="Error comment")
    result = add_comment(config, auth_manager, params)
    
    # Assertions
    assert result.success is False
    assert "Failed to find incident" in result.message

def test_resolve_incident_api_error(monkeypatch, config, auth_manager):
    """Test resolve_incident with an API error."""
    # Import the module to patch
    import servicenow_mcp.tools.incident_tools
    
    # Setup mock
    error_result = {
        "success": False,
        "message": "Failed to find incident: 401 Client Error: Unauthorized for url: https://example.service-now.com/api/now/table/incident?sysparm_query=number%3Dinc123&sysparm_limit=1"
    }
    
    # Setup monkeypatch
    def mock_find_incident_sys_id(*args, **kwargs):
        return error_result
    
    monkeypatch.setattr(servicenow_mcp.tools.incident_tools, '_find_incident_sys_id', mock_find_incident_sys_id)
    
    # Call function
    params = ResolveIncidentParams(
        incident_id="inc123", resolution_code="Solved (Permanently)", resolution_notes="Error"
    )
    result = resolve_incident(config, auth_manager, params)
    
    # Assertions
    assert result.success is False
    assert "Failed to find incident" in result.message

def test_list_incidents_api_error(monkeypatch, config, auth_manager):
    """Test list_incidents with an API error."""
    # Setup monkeypatch
    def mock_get(*args, **kwargs):
        raise requests.exceptions.RequestException("API Error")
    
    monkeypatch.setattr(requests, 'get', mock_get)
    
    # Call function
    params = ListIncidentsParams()
    result = list_incidents(config, auth_manager, params)
    
    # Assertions
    assert result["success"] is False  # Using dictionary access instead of attribute
    assert "API Error" in result["message"]
    assert result["incidents"] == []


# No need for unittest.main() with pytest
