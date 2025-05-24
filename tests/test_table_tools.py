"""
Tests for the ServiceNow MCP table tools.
"""

import pytest
from unittest.mock import MagicMock

from servicenow_mcp.tools.table_tools import (
    list_tables,
    ListTablesParams,
    TableInfo,
    ListTablesResponse
)
from servicenow_mcp.tools.table_records_tools import (
    get_records,
    get_record,
    GetRecordsParams,
    GetRecordParams,
    RecordsResponse,
    RecordResponse
)
from servicenow_mcp.tools.table_schema_tools import (
    get_table_schema,
    list_table_schemas,
    GetTableSchemaParams,
    TableSchemaResponse,
    TableSchemaListResponse
)
from servicenow_mcp.utils.config import ServerConfig
import requests # Added for using requests.exceptions


@pytest.fixture
def mock_response():
    """Fixture to create mock response objects for testing."""
    
    def _create_mock_response(json_data, status_code=200, headers=None):
        mock = MagicMock()
        mock.json.return_value = json_data
        mock.status_code = status_code
        mock.headers = headers or {}
        
        def raise_for_status():
            if 400 <= status_code < 600:
                raise requests.exceptions.HTTPError(f"HTTP Error {status_code}")
        
        mock.raise_for_status = raise_for_status
        return mock
    
    return _create_mock_response


@pytest.fixture
def config():
    """Fixture to provide a ServerConfig for testing."""
    return ServerConfig(
        instance_url="https://test-instance.service-now.com",
        auth={
            "type": "basic",
            "basic": {
                "username": "test_user",
                "password": "test_password"
            }
        },
        timeout=30
    )

@pytest.fixture
def auth_manager():
    """Fixture to provide a mock AuthManager for testing."""
    manager = MagicMock()
    manager.get_headers.return_value = {"Authorization": "Bearer test_token"}
    return manager
    
def test_list_tables_success(monkeypatch, config, auth_manager, mock_response):
    """Test successful table listing."""
    # Mock response
    response_data = {
        "result": [
            {
                "name": "incident",
                "label": "Incident",
                "description": "Incident Management",
                "is_extendable": True,
                "is_view": False,
                "sys_created_on": "2023-01-01T00:00:00Z",
                "sys_updated_on": "2023-01-01T01:00:00Z"
            }
        ],
        "headers": {
            "x-total-count": "1"
        }
    }
    
    # Setup mock
    mock = mock_response(response_data)
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: mock)
    
    # Call the function
    params = ListTablesParams(limit=10, offset=0)
    response = list_tables(config, auth_manager, params)
    
    # Assertions
    assert response["success"] is True
    assert len(response["tables"]) == 1
    assert response["tables"][0]["name"] == "incident"
    assert response["count"] == 1
    
    # We can't directly verify the request parameters with monkeypatch
    # If needed, we could use pytest-mock instead for more detailed verification
    
def test_get_records_success(monkeypatch, config, auth_manager, mock_response):
    """Test successful record retrieval."""
    # Mock response
    response_data = {
        "result": [
            {
                "sys_id": "123",
                "number": "INC0010001",
                "short_description": "Test incident"
            }
        ],
        "headers": {
            "x-total-count": "1"
        }
    }
    
    # Setup mock
    mock = mock_response(response_data)
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: mock)
    
    # Call the function
    params = GetRecordsParams(
        table_name="incident",
        query="active=true",
        fields=["number", "short_description"],
        limit=1
    )
    response = get_records(config, auth_manager, params)
    
    # Assertions
    assert response["success"] is True
    assert len(response["records"]) == 1
    assert response["records"][0]["number"] == "INC0010001"
    assert response["count"] == 1
    
def test_get_record_success(monkeypatch, config, auth_manager, mock_response):
    """Test successful single record retrieval."""
    # Mock response data
    mock_api_response_data = {
        "sys_id": "123",
        "number": "INC0010001",
        "short_description": "Test incident"
    }
    
    # Setup mock for the specific module
    mock = mock_response({"result": mock_api_response_data})
    
    # We need to patch the specific module that makes the request
    import servicenow_mcp.tools.table_records_tools
    monkeypatch.setattr(servicenow_mcp.tools.table_records_tools.requests, 'get', 
                        lambda *args, **kwargs: mock)
    
    # Call the function with GetRecordParams
    params = GetRecordParams(
        table_name="incident",
        sys_id="123",
        fields=["number", "short_description"]
    )
    response = get_record(
        config=config,
        auth_manager=auth_manager,
        params=params
    )

    # Assertions
    assert response["success"] is True
    assert response["record"]["sys_id"] == "123"
    assert response["record"]["number"] == "INC0010001"
    assert response["record"]["short_description"] == "Test incident"
    
def test_get_table_schema_success(monkeypatch, config, auth_manager, mock_response):
    """Test successful table schema retrieval."""
    # Mock table metadata response
    table_response = {
        "result": [{
            "name": "incident",
            "label": "Incident",
            "description": "Incident Management",
            "sys_created_on": "2023-01-01T00:00:00Z",
            "sys_updated_on": "2023-01-01T01:00:00Z"
        }]
    }
    
    # Mock field schema response
    fields_response = {
        "result": [
            {
                "element": "number",
                "column_label": "Number",
                "internal_type": "string",
                "mandatory": "true",
                "read_only": "true",
                "description": "Auto-generated unique identifier"
            },
            {
                "element": "short_description",
                "column_label": "Short Description",
                "internal_type": "string",
                "mandatory": "true",
                "read_only": "false",
                "description": "Brief description of the incident"
            }
        ]
    }
    
    # Set up mock to return different responses for different URLs
    request_count = 0
    
    def mock_get_side_effect(*args, **kwargs):
        nonlocal request_count
        url = args[0] if args else kwargs.get('url', '')
        
        if "sys_db_object" in url:
            return mock_response(table_response)
        elif "sys_dictionary" in url:
            request_count += 1
            return mock_response(fields_response)
        return mock_response({}, 404)
    
    monkeypatch.setattr(requests, 'get', mock_get_side_effect)
    
    # Call the function
    params = GetTableSchemaParams(table_name="incident")
    response = get_table_schema(config, auth_manager, params)
    
    # Assertions
    assert response["success"] is True
    assert response["name"] == "incident"
    assert "number" in response["fields"]
    assert "short_description" in response["fields"]
    assert response["fields"]["number"]["type"] == "string"
    assert response["fields"]["number"]["mandatory"] is True
    assert response["fields"]["number"]["read_only"] is True
    
def test_list_table_schemas_success(monkeypatch, config, auth_manager, mock_response):
    """Test successful listing of table schemas."""
    # Mock response
    response_data = {
        "result": [
            {"name": "incident", "label": "Incident"},
            {"name": "problem", "label": "Problem"}
        ]
    }
    
    # Setup mock
    mock = mock_response(response_data)
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: mock)
    
    # Call the function
    response = list_table_schemas(config, auth_manager)
    
    # Assertions
    assert response["success"] is True
    assert len(response["tables"]) == 2
    assert response["tables"][0]["name"] == "incident"
    assert response["tables"][1]["name"] == "problem"


# No need for unittest.main() with pytest
