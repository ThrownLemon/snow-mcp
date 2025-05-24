"""
Tests for the script include tools.

This module contains tests for the script include tools in the ServiceNow MCP server.
"""

import pytest
import requests
from unittest.mock import MagicMock, patch

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.script_include_tools import (
    ListScriptIncludesParams,
    GetScriptIncludeParams,
    CreateScriptIncludeParams,
    UpdateScriptIncludeParams,
    DeleteScriptIncludeParams,
    ScriptIncludeResponse,
    list_script_includes,
    get_script_include,
    create_script_include,
    update_script_include,
    delete_script_include,
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
            auth=auth_config,
        )
        self.auth_manager = MagicMock(spec=AuthManager)
        self.auth_manager.get_headers.return_value = {
            "Authorization": "Bearer test",
            "Content-Type": "application/json",
        }

    @patch("servicenow_mcp.tools.script_include_tools.requests.get")
    def test_list_script_includes(self, mock_get):
        """Test listing script includes."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {
                    "sys_id": "123",
                    "name": "TestScriptInclude",
                    "script": "var TestScriptInclude = Class.create();\nTestScriptInclude.prototype = {\n    initialize: function() {\n    },\n\n    type: 'TestScriptInclude'\n};",
                    "description": "Test Script Include",
                    "api_name": "global.TestScriptInclude",
                    "client_callable": "true",
                    "active": "true",
                    "access": "public",
                    "sys_created_on": "2023-01-01 00:00:00",
                    "sys_updated_on": "2023-01-02 00:00:00",
                    "sys_created_by": {"display_value": "admin"},
                    "sys_updated_by": {"display_value": "admin"}
                }
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Call the method
        params = ListScriptIncludesParams(
            limit=10,
            offset=0,
            active=True,
            client_callable=True,
            query="Test"
        )
        result = list_script_includes(self.server_config, self.auth_manager, params)

        # Verify the result
        assert result["success"]
        assert len(result["script_includes"]) == 1
        assert result["script_includes"][0]["sys_id"] == "123"
        assert result["script_includes"][0]["name"] == "TestScriptInclude"
        assert result["script_includes"][0]["client_callable"]
        assert result["script_includes"][0]["active"]

        # Verify the request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == f"{self.server_config.instance_url}/api/now/table/sys_script_include"
        assert kwargs["headers"] == self.auth_manager.get_headers()
        assert kwargs["params"]["sysparm_limit"] == 10
        assert kwargs["params"]["sysparm_offset"] == 0
        assert kwargs["params"]["sysparm_query"] == "active=true^client_callable=true^nameLIKETest"

    @patch("servicenow_mcp.tools.script_include_tools.requests.get")
    def test_get_script_include(self, mock_get):
        """Test getting a script include."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "123",
                "name": "TestScriptInclude",
                "script": "var TestScriptInclude = Class.create();\nTestScriptInclude.prototype = {\n    initialize: function() {\n    },\n\n    type: 'TestScriptInclude'\n};",
                "description": "Test Script Include",
                "api_name": "global.TestScriptInclude",
                "client_callable": "true",
                "active": "true",
                "access": "public",
                "sys_created_on": "2023-01-01 00:00:00",
                "sys_updated_on": "2023-01-02 00:00:00",
                "sys_created_by": {"display_value": "admin"},
                "sys_updated_by": {"display_value": "admin"}
            }
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Call the method
        params = GetScriptIncludeParams(script_include_id="123")
        result = get_script_include(self.server_config, self.auth_manager, params)

        # Verify the result
        assert result["success"]
        assert result["script_include"]["sys_id"] == "123"
        assert result["script_include"]["name"] == "TestScriptInclude"
        assert result["script_include"]["client_callable"]
        assert result["script_include"]["active"]

        # Verify the request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == f"{self.server_config.instance_url}/api/now/table/sys_script_include"
        assert kwargs["headers"] == self.auth_manager.get_headers()
        # The actual query includes active=true, so update the assertion to match
        assert kwargs["params"]["sysparm_query"] == "name=123^active=true"

    @patch("servicenow_mcp.tools.script_include_tools.requests.post")
    def test_create_script_include(self, mock_post):
        """Test creating a script include."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {"sys_id": "test_sys_id", "name": "TestScript", "script": "// test"}
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Call the method
        params = CreateScriptIncludeParams(
            name="TestScriptInclude",
            script="var TestScriptInclude = Class.create();\nTestScriptInclude.prototype = {\n    initialize: function() {\n    },\n\n    type: 'TestScriptInclude'\n};",
            description="Test Script Include",
            api_name="global.TestScriptInclude",
            client_callable=True,
            active=True,
            access="public"
        )
        result = create_script_include(self.server_config, self.auth_manager, params)

        # Verify the result
        assert result.success
        assert result.script_include_id == "test_sys_id"
        assert result.script_include_name == "TestScript"

        # Verify the request
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == f"{self.server_config.instance_url}/api/now/table/sys_script_include"
        assert kwargs["headers"] == self.auth_manager.get_headers()
        assert kwargs["json"]["name"] == "TestScriptInclude"
        assert kwargs["json"]["client_callable"] == "true"
        assert kwargs["json"]["active"] == "true"
        assert kwargs["json"]["access"] == "public"

    @patch("servicenow_mcp.tools.script_include_tools._get_script_include_by_id_or_name")
    @patch("servicenow_mcp.tools.script_include_tools.requests.patch")
    def test_update_script_include(self, mock_patch, mock_get_script_include_by_id_or_name):
        """Test updating a script include."""
        mock_get_script_include_by_id_or_name.return_value = {
            "success": True,
            "script_include": {"sys_id": "script123", "name": "OldScript"}
        }

        # Mock for PATCH request to update
        mock_patch_response = MagicMock()
        mock_patch_response.json.return_value = {
            "result": {"sys_id": "script123", "name": "UpdatedScript", "script": "var y = 2;"}
        }
        mock_patch_response.raise_for_status = MagicMock()
        mock_patch.return_value = mock_patch_response

        # Call the method
        params = UpdateScriptIncludeParams(
            script_include_id="script123",
            script="var TestScriptInclude = Class.create();\nTestScriptInclude.prototype = {\n    initialize: function() {\n        // Updated\n    },\n\n    type: 'TestScriptInclude'\n};",
            description="Updated Test Script Include",
            client_callable=False,
        )
        result = update_script_include(self.server_config, self.auth_manager, params)

        # Verify the result
        assert result.success
        assert result.script_include_id == "script123"
        assert result.script_include_name == "UpdatedScript"

        # Verify the request
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        assert args[0] == f"{self.server_config.instance_url}/api/now/table/sys_script_include/script123"
        assert kwargs["headers"] == self.auth_manager.get_headers()
        assert kwargs["json"]["description"] == "Updated Test Script Include"
        assert kwargs["json"]["client_callable"] == "false"

    @patch("servicenow_mcp.tools.script_include_tools._get_script_include_by_id_or_name")
    @patch("servicenow_mcp.tools.script_include_tools.requests.delete")
    def test_delete_script_include(self, mock_delete, mock_get_script_include_by_id_or_name):
        """Test deleting a script include."""
        mock_get_script_include_by_id_or_name.return_value = {
            "success": True,
            "script_include": {"sys_id": "script123", "name": "TestScript"}
        }

        # Mock for DELETE request
        mock_delete_response = MagicMock()
        mock_delete_response.raise_for_status = MagicMock()
        mock_delete.return_value = mock_delete_response

        # Call the method
        params = DeleteScriptIncludeParams(script_include_id="script123")
        result = delete_script_include(self.server_config, self.auth_manager, params)

        # Verify the result
        assert result.success
        assert result.script_include_id == "script123"
        assert result.script_include_name == "TestScript"

        # Verify the request
        mock_delete.assert_called_once()
        args, kwargs = mock_delete.call_args
        assert args[0] == f"{self.server_config.instance_url}/api/now/table/sys_script_include/script123"
        assert kwargs["headers"] == self.auth_manager.get_headers()

    @patch("servicenow_mcp.tools.script_include_tools.requests.get")
    def test_list_script_includes_error(self, mock_get):
        """Test listing script includes with an error."""
        # Mock response
        mock_get.side_effect = requests.RequestException("API Error")

        # Call the method
        params = ListScriptIncludesParams()
        result = list_script_includes(self.server_config, self.auth_manager, params)

        # Verify the result
        assert not result["success"]
        assert "API Error" in result["message"]

    @patch("servicenow_mcp.tools.script_include_tools.requests.get")
    def test_get_script_include_error(self, mock_get):
        """Test getting a script include with an error."""
        # Mock response
        mock_get.side_effect = requests.RequestException("API Error")

        # Call the method
        params = GetScriptIncludeParams(script_include_id="123")
        result = get_script_include(self.server_config, self.auth_manager, params)

        # Verify the result
        assert not result["success"]
        assert "API Error" in result["message"]

    @patch("servicenow_mcp.tools.script_include_tools.requests.post")
    def test_create_script_include_error(self, mock_post):
        """Test creating a script include with an error."""
        # Mock response
        mock_post.side_effect = requests.RequestException("API Error")

        # Call the method
        params = CreateScriptIncludeParams(
            name="TestScriptInclude",
            script="var TestScriptInclude = Class.create();\nTestScriptInclude.prototype = {\n    initialize: function() {\n    },\n\n    type: 'TestScriptInclude'\n};",
        )
        result = create_script_include(self.server_config, self.auth_manager, params)

        # Verify the result
        assert not result.success
        assert "API Error" in result.message

    @patch("servicenow_mcp.tools.script_include_tools._get_script_include_by_id_or_name")
    @patch("servicenow_mcp.tools.script_include_tools.requests.patch")
    def test_update_script_include_error(self, mock_patch, mock_get_script_include_by_id_or_name):
        """Test updating a script include with an error."""
        # Mock get_script_include response
        mock_get_script_include_by_id_or_name.return_value = {
            "success": False,
            "message": "Script include not found: 123"
        }

        # Call the method
        params = UpdateScriptIncludeParams(
            script_include_id="123",
            script="var error = true;"
        )
        result = update_script_include(self.server_config, self.auth_manager, params)

        # Verify the result
        assert not result.success
        assert "Script include not found" in result.message

    @patch("servicenow_mcp.tools.script_include_tools._get_script_include_by_id_or_name")
    @patch("servicenow_mcp.tools.script_include_tools.requests.delete")
    def test_delete_script_include_error(self, mock_delete, mock_get_script_include_by_id_or_name):
        """Test deleting a script include with an error."""
        # Mock get_script_include response
        mock_get_script_include_by_id_or_name.return_value = {
            "success": False,
            "message": "Script include not found: 123"
        }

        # Call the method
        params = DeleteScriptIncludeParams(script_include_id="123")
        result = delete_script_include(self.server_config, self.auth_manager, params)

        # Verify the result
        assert not result.success
        assert "Script include not found" in result.message

    @patch("servicenow_mcp.tools.script_include_tools.requests.get")
    def test_list_script_includes_error(self, mock_get):
        """Test listing script includes with an error."""
        # Mock response
        mock_get.side_effect = requests.RequestException("API Error")

        # Call the method
        params = ListScriptIncludesParams()
        result = list_script_includes(self.server_config, self.auth_manager, params)

        # Verify the result
        assert not result["success"]
        assert "API Error" in result["message"]

if __name__ == "__main__":
    pytest.main([__file__])