"""
Tests for the ServiceNow MCP table tools.
"""

import unittest
from unittest.mock import MagicMock, patch

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


class MockResponse:
    """Mock response object for testing."""
    
    def __init__(self, json_data, status_code=200, headers=None):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = headers or {}
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if 400 <= self.status_code < 600:
            raise requests.exceptions.HTTPError(f"HTTP Error {self.status_code}")


class TestTableTools(unittest.TestCase):
    """Test cases for table tools."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ServerConfig(
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
        self.auth_manager = MagicMock()
        self.auth_manager.get_headers.return_value = {"Authorization": "Bearer test_token"} # Changed get_auth_headers to get_headers
    
    @patch('requests.get')
    def test_list_tables_success(self, mock_get):
        """Test successful table listing."""
        # Mock response
        mock_response = {
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
        mock_get.return_value = MockResponse(mock_response)
        
        # Call the function
        params = ListTablesParams(limit=10, offset=0)
        response = list_tables(self.config, self.auth_manager, params)
        
        # Assertions
        self.assertTrue(response["success"])
        self.assertEqual(len(response["tables"]), 1)
        self.assertEqual(response["tables"][0]["name"], "incident")
        self.assertEqual(response["count"], 1)
        
        # Verify the request was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        params = kwargs.get("params", {})
        self.assertEqual(params.get("sysparm_limit"), 10)
        self.assertEqual(params.get("sysparm_offset"), 0)
    
    @patch('requests.get')
    def test_get_records_success(self, mock_get):
        """Test successful record retrieval."""
        # Mock response
        mock_response = {
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
        mock_get.return_value = MockResponse(mock_response)
        
        # Call the function
        params = GetRecordsParams(
            table_name="incident",
            query="active=true",
            fields=["number", "short_description"],
            limit=1
        )
        response = get_records(self.config, self.auth_manager, params)
        
        # Assertions
        self.assertTrue(response["success"])
        self.assertEqual(len(response["records"]), 1)
        self.assertEqual(response["records"][0]["number"], "INC0010001")
        self.assertEqual(response["count"], 1)
        
        # Verify the request was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        params = kwargs.get("params", {})
        self.assertEqual(params.get("sysparm_limit"), 1)
        self.assertEqual(params.get("sysparm_query"), "active=true")
        self.assertEqual(params.get("sysparm_fields"), "number,short_description")
    
    @patch('servicenow_mcp.tools.table_records_tools.requests.get') # Patched correct module
    def test_get_record_success(self, mock_get):
        """Test successful single record retrieval."""
        # Mock response for requests.get inside the tool
        mock_api_response_data = {
            "sys_id": "123",
            "number": "INC0010001",
            "short_description": "Test incident"
        }
        # get_record expects response.json().get("result", {})
        mock_get.return_value = MockResponse({"result": mock_api_response_data})
    
        # Call the function with GetRecordParams
        params = GetRecordParams(
            table_name="incident",
            sys_id="123",
            fields=["number", "short_description"]
        )
        response = get_record(
            config=self.config,
            auth_manager=self.auth_manager,
            params=params
        )
    
        # Assertions
        self.assertTrue(response["success"])
        self.assertEqual(response["record"]["sys_id"], "123")
        self.assertEqual(response["record"]["number"], "INC0010001")
        self.assertEqual(response["record"]["short_description"], "Test incident")
        
        # Verify the request was made correctly
        expected_request_params = {}
        if params.fields:
            expected_request_params["sysparm_fields"] = ",".join(params.fields)
        
        mock_get.assert_called_once_with(
            f"{self.config.instance_url}/api/now/table/incident/123",
            headers=self.auth_manager.get_headers(), # Corrected to get_headers
            params=expected_request_params
        )
    
    @patch('requests.get')
    def test_get_table_schema_success(self, mock_get):
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
        def mock_get_side_effect(url, *args, **kwargs):
            if "sys_db_object" in url:
                return MockResponse(table_response)
            elif "sys_dictionary" in url:
                return MockResponse(fields_response)
            return MockResponse({}, 404)
        
        mock_get.side_effect = mock_get_side_effect
        
        # Call the function
        params = GetTableSchemaParams(table_name="incident")
        response = get_table_schema(self.config, self.auth_manager, params)
        
        # Assertions
        self.assertTrue(response["success"])
        self.assertEqual(response["name"], "incident")
        self.assertIn("number", response["fields"])
        self.assertIn("short_description", response["fields"])
        self.assertEqual(response["fields"]["number"]["type"], "string")
        self.assertTrue(response["fields"]["number"]["mandatory"])
        self.assertTrue(response["fields"]["number"]["read_only"])
        
        # Verify the requests were made correctly
        self.assertEqual(mock_get.call_count, 2)
    
    @patch('requests.get')
    def test_list_table_schemas_success(self, mock_get):
        """Test successful listing of table schemas."""
        # Mock response
        mock_response = {
            "result": [
                {"name": "incident", "label": "Incident"},
                {"name": "problem", "label": "Problem"}
            ]
        }
        mock_get.return_value = MockResponse(mock_response)
        
        # Call the function
        response = list_table_schemas(self.config, self.auth_manager)
        
        # Assertions
        self.assertTrue(response["success"])
        self.assertEqual(len(response["tables"]), 2)
        self.assertEqual(response["tables"][0]["name"], "incident")
        self.assertEqual(response["tables"][1]["name"], "problem")
        
        # Verify the request was made correctly
        mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
