"""
Tests for the script include tools.

This module contains tests for the script include tools in the ServiceNow MCP server.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
import requests # For requests.exceptions.RequestException

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.script_include_tools import (
    list_script_includes,
    get_script_include,
    ListScriptIncludesParams,
    GetScriptIncludeParams,
    ScriptIncludeResponse # Assuming tools return this Pydantic model
)
from servicenow_mcp.utils.config import ServerConfig, AuthConfig, AuthType, BasicAuthConfig


class TestScriptIncludeTools:
    """Tests for the script include tools."""

    def setup_method(self):
        """Set up test fixtures."""
        auth_config = AuthConfig(
            type=AuthType.BASIC,
            basic=BasicAuthConfig(
                username="test_user",
                password="test_password"
            )
        )
        self.server_config = ServerConfig(
            instance_url="https://test.service-now.com",
            api_url="https://test.service-now.com/api/now", # Assuming a base api_url
            auth=auth_config,
            timeout=10
        )
        self.auth_manager = MagicMock(spec=AuthManager)
        self.auth_manager.get_headers.return_value = {"Authorization": "Bearer test"}
        # Removed: self.script_include_resource = ScriptIncludeResource(self.server_config, self.auth_manager)

    @patch("servicenow_mcp.tools.script_include_tools.requests.get")
    def test_list_script_includes(self, mock_get):
        """Test listing script includes."""
        mock_response_data = [
            {
                "sys_id": "123",
                "name": "TestScriptInclude",
                "script": "var TestScriptInclude = Class.create();",
                "description": "Test Script Include",
                "api_name": "global.TestScriptInclude",
                "client_callable": "true",
                "active": "true",
            }
        ]
        mock_api_response = MagicMock()
        mock_api_response.json.return_value = {"result": mock_response_data}
        mock_api_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_api_response

        params = ListScriptIncludesParams(
            limit=1, offset=0, query="TestScriptInclude", active=True, client_callable=True
        )
        response = list_script_includes(self.server_config, self.auth_manager, params)

        assert response.get('success', False)
        # Check that we have script_includes and verify the first one
        script_includes = response.get('script_includes', [])
        assert len(script_includes) == 1
        assert script_includes[0].get('sys_id') == mock_response_data[0].get('sys_id')
        assert script_includes[0].get('name') == mock_response_data[0].get('name')
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == f"{self.server_config.instance_url}/api/now/table/sys_script_include"
        assert kwargs["params"]["sysparm_limit"] == 1
        assert kwargs["params"]["sysparm_offset"] == 0
        assert "nameLIKETestScriptInclude" in kwargs["params"]["sysparm_query"]
        assert "active=true" in kwargs["params"]["sysparm_query"]
        assert "client_callable=true" in kwargs["params"]["sysparm_query"]

    @patch("servicenow_mcp.tools.script_include_tools.requests.get")
    def test_get_script_include(self, mock_get):
        """Test getting a script include."""
        mock_response_data = {"sys_id": "123", "name": "TestScriptInclude", "script": "var Test;"}
        # The tool's _get_script_include_by_id_or_name makes two calls if ID is not sys_id
        # For simplicity, assume script_include_id is sys_id for this direct get_script_include test
        mock_api_response = MagicMock()
        # Set up the mock to return what get_record_by_id_or_name expects
        mock_api_response.json.return_value = {"result": mock_response_data}
        mock_api_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_api_response

        params = GetScriptIncludeParams(script_include_id="123") # Assuming "123" is a sys_id
        response = get_script_include(self.server_config, self.auth_manager, params)

        assert response.get('success', False)
        # Check only the fields we care about
        script_include = response.get('script_include', {})
        assert script_include.get('sys_id') == mock_response_data.get('sys_id')
        assert script_include.get('name') == mock_response_data.get('name')
        assert script_include.get('script') == mock_response_data.get('script')
        # The actual get_script_include tool function calls _get_script_include_by_id_or_name,
        # which might make one or two API calls depending on whether script_include_id is a name or sys_id.
        # If "123" is treated as sys_id by the internal helper:
        # Verify that mock_get was called
        mock_get.assert_called_once()
        # Check that the URL is correct (first argument)
        args, kwargs = mock_get.call_args
        assert args[0] == f"{self.server_config.instance_url}/api/now/table/sys_script_include"
        # Check that the query includes the name parameter
        assert 'sysparm_query' in kwargs['params']
        assert 'name=123' in kwargs['params']['sysparm_query']


    @patch("servicenow_mcp.tools.script_include_tools.requests.get")
    def test_list_script_includes_error(self, mock_get):
        """Test listing script includes with an error."""
        mock_get.side_effect = requests.exceptions.RequestException("Test error")

        params = ListScriptIncludesParams()
        response = list_script_includes(self.server_config, self.auth_manager, params)

        assert not response.get('success', True)
        assert "Error listing script includes: Test error" in response.get('message', '')

    @patch("servicenow_mcp.tools.script_include_tools.requests.get")
    def test_get_script_include_error(self, mock_get):
        """Test getting a script include with an error."""
        mock_get.side_effect = requests.exceptions.RequestException("Test error")

        params = GetScriptIncludeParams(script_include_id="123")
        response = get_script_include(self.server_config, self.auth_manager, params)

        assert not response.get('success', True)
        # The message might vary depending on how _get_script_include_by_id_or_name handles errors
        assert "Error accessing sys_script_include" in response.get('message', '')


class TestListScriptIncludesParams:
    """Tests for the script include list parameters."""

    def test_list_script_includes_params(self): # Updated method name
        """Test script include list parameters."""
        params = ListScriptIncludesParams(
            limit=20,
            offset=10,
            active=True,
            client_callable=False,
            query="Test"
        )
        assert params.limit == 20
        assert params.offset == 10
        assert params.active
        assert not params.client_callable
        assert params.query == "Test"

    def test_list_script_includes_params_defaults(self): # Updated method name
        """Test script include list parameters defaults."""
        params = ListScriptIncludesParams()
        assert params.limit == 10 # Default from Pydantic model
        assert params.offset == 0 # Default from Pydantic model
        assert params.active is None
        assert params.client_callable is None
        assert params.query is None


if __name__ == "__main__":
    pytest.main([__file__])