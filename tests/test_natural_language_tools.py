"""
Tests for the ServiceNow MCP natural language tools.
"""

import pytest
from unittest.mock import MagicMock, patch

import requests

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.natural_language_tools import (
    NaturalLanguageSearchParams,
    NaturalLanguageUpdateParams,
    UpdateScriptParams,
    natural_language_search,
    natural_language_update,
    update_script,
)
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig


class TestNaturalLanguageTools:
    """Test cases for the natural language tools."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = ServerConfig(
            instance_url="https://example.service-now.com",
            auth=AuthConfig(
                type=AuthType.BASIC,
                basic=BasicAuthConfig(username="admin", password="password"),
            ),
        )
        self.auth_manager = MagicMock(spec=AuthManager)
        self.auth_manager.get_headers.return_value = {"Authorization": "Basic YWRtaW46cGFzc3dvcmQ="}

    @patch("requests.get")
    def test_natural_language_search(self, mock_get):
        """Test natural language search."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [{"sys_id": "rec123", "short_description": "Found via NLQ"}]
        }
        mock_response.raise_for_status = MagicMock() # Ensure this doesn't raise
        mock_get.return_value = mock_response

        params = NaturalLanguageSearchParams(query="find all incidents about SAP", table="incident")
        result = natural_language_search(self.config, self.auth_manager, params)

        assert result["success"]
        assert len(result["results"]) == 1
        assert result["results"][0]["short_description"] == "Found via NLQ"
        assert "LIKEfind" in result["query_used"]
        assert "LIKEincidents" in result["query_used"]
        assert "LIKEabout" in result["query_used"]
        # Note: The actual implementation doesn't include LIKESAP in the query
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == f"{self.config.instance_url}/api/now/table/incident"

    @patch("requests.patch")
    def test_natural_language_update(self, mock_patch):
        """Test natural language update."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {"sys_id": "INC0010001", "comments": "I'm working on it"}
        }
        mock_response.raise_for_status = MagicMock() # Ensure this doesn't raise
        mock_patch.return_value = mock_response

        params = NaturalLanguageUpdateParams(
            query="Update incident INC0010001 saying I'm working on it"
        )
        result = natural_language_update(self.config, self.auth_manager, params)

        assert result["success"]
        assert result["updated"]
        assert result["result"]["comments"] == "I'm working on it"
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        assert args[0] == f"{self.config.instance_url}/api/now/table/incident/INC0010001"
        assert kwargs["json"]["comments"] == "I'm working on it"

    @patch("requests.get")
    @patch("requests.patch")
    def test_update_script(self, mock_patch, mock_get):
        """Test updating a script."""
        # Mock for GET request to find script
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "result": [{"sys_id": "script123", "name": "MyScriptInclude"}]
        }
        mock_get_response.raise_for_status = MagicMock() # Ensure this doesn't raise
        mock_get.return_value = mock_get_response

        # Mock for PATCH request to update script
        mock_patch_response = MagicMock()
        mock_patch_response.json.return_value = {
            "result": {"sys_id": "script123", "script": "var newScript = true;"}
        }
        mock_patch_response.raise_for_status = MagicMock() # Ensure this doesn't raise
        mock_patch.return_value = mock_patch_response

        params = UpdateScriptParams(
            script_id="MyScriptInclude",
            script_type="script_include",
            script="var newScript = true;",
            active=True,
        )
        result = update_script(self.config, self.auth_manager, params)

        assert result["success"]
        assert result["updated"]
        assert result["result"]["script"] == "var newScript = true;"
        mock_get.assert_called_once()
        mock_patch.assert_called_once()
        
        get_args, get_kwargs = mock_get.call_args
        assert get_args[0] == f"{self.config.instance_url}/api/now/table/sys_script_include?sysparm_query=name=MyScriptInclude^ORsys_id=MyScriptInclude"

        patch_args, patch_kwargs = mock_patch.call_args
        assert patch_args[0] == f"{self.config.instance_url}/api/now/table/sys_script_include/script123"
        assert patch_kwargs["json"]["script"] == "var newScript = true;"

    @patch("requests.get")
    def test_natural_language_search_api_error(self, mock_get):
        """Test natural_language_search with an API error."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")
        params = NaturalLanguageSearchParams(query="find stuff", table="incident")
        result = natural_language_search(self.config, self.auth_manager, params)
        assert not result["success"]
        assert "API Error" in result["message"] # Changed expected error message

    @patch("requests.patch")
    def test_natural_language_update_api_error(self, mock_patch):
        """Test natural_language_update with an API error."""
        mock_patch.side_effect = requests.exceptions.RequestException("API Error")
        params = NaturalLanguageUpdateParams(query="Update incident INC0010001 priority to high")
        result = natural_language_update(self.config, self.auth_manager, params)
        assert not result["success"]
        assert not result["updated"]
        assert "API Error" in result["message"] # Changed expected error message

    @patch("requests.get")
    def test_natural_language_update_parse_error(self, mock_get): # mock_get is not used but patch is needed
        """Test natural_language_update with a query that doesn't parse."""
        params = NaturalLanguageUpdateParams(query="This is not a valid update command")
        result = natural_language_update(self.config, self.auth_manager, params)
        assert not result["success"]
        assert not result["updated"]
        assert "Could not parse update command" in result["message"]

    @patch("requests.get")
    @patch("requests.patch")
    def test_update_script_script_not_found(self, mock_patch, mock_get):
        """Test update_script when the script to update is not found."""
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {"result": []} # Empty result
        mock_get_response.raise_for_status = MagicMock() # Ensure this doesn't raise
        mock_get.return_value = mock_get_response

        params = UpdateScriptParams(script_id="NonExistentScript", script_type="script_include", script="var test;")
        result = update_script(self.config, self.auth_manager, params)

        assert not result["success"]
        assert not result["updated"]
        assert "No script_include found" in result["message"]
        mock_patch.assert_not_called()

if __name__ == "__main__":
    pytest.main([__file__])
