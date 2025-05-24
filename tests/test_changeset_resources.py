"""
Tests for the changeset tools.

This module contains tests for the changeset tools in the ServiceNow MCP server.
"""

import pytest
from unittest.mock import MagicMock, patch
import requests # Ensure requests is imported for requests.exceptions.RequestException

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.changeset_tools import (
    list_changesets,
    get_changeset_details,
    ListChangesetsParams,
    GetChangesetDetailsParams,
    # Assuming the tool functions return a Pydantic model or dict, not a JSON string directly
)
from servicenow_mcp.utils.config import ServerConfig, AuthConfig, AuthType, BasicAuthConfig


class TestChangesetTools:
    """Tests for the changeset tools."""

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
        # Removed: self.changeset_resource = ChangesetResource(self.server_config, self.auth_manager)

    @patch("servicenow_mcp.tools.changeset_tools.requests.get")
    def test_list_changesets(self, mock_get):
        """Test listing changesets."""
        mock_response_data = [
            {
                "sys_id": "123",
                "name": "Test Changeset",
                "state": "in_progress",
                "application": "Test App",
                "developer": "test.user",
            }
        ]
        mock_api_response = MagicMock()
        mock_api_response.json.return_value = {"result": mock_response_data} # ServiceNow typically wraps in 'result'
        mock_api_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_api_response

        params = ListChangesetsParams(
            limit=10,
            offset=0,
            state="in_progress",
            application="Test App",
            developer="test.user",
        )
        # Assuming list_changesets now returns a dict/Pydantic model
        response = list_changesets(self.server_config, self.auth_manager, params)

        assert response["success"] # Or response.success if Pydantic model
        assert response["changesets"] == mock_response_data # Or response.data
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == f"{self.server_config.instance_url}/api/now/table/sys_update_set"
        assert kwargs["params"]["sysparm_limit"] == 10
        assert kwargs["params"]["sysparm_offset"] == 0
        # Check that the query string contains the expected filters
        query_string = kwargs["params"]["sysparm_query"]
        assert "state=in_progress" in query_string
        assert "application=Test App" in query_string
        assert "developer=test.user" in query_string


    @patch("servicenow_mcp.tools.changeset_tools.requests.get")
    def test_get_changeset_details(self, mock_get):
        """Test getting changeset details."""
        # Mock the first API call to get changeset details
        mock_response_data = {"sys_id": "123", "name": "Test Changeset"}
        mock_api_response = MagicMock()
        mock_api_response.json.return_value = {"result": mock_response_data}
        mock_api_response.raise_for_status = MagicMock()
        
        # Mock the second API call to get changes
        mock_changes_response = MagicMock()
        mock_changes_response.json.return_value = {"result": []}
        mock_changes_response.raise_for_status = MagicMock()
        
        # Configure mock to return different responses for different calls
        mock_get.side_effect = [mock_api_response, mock_changes_response]

        params = GetChangesetDetailsParams(changeset_id="123")
        response = get_changeset_details(self.server_config, self.auth_manager, params)

        assert response["success"]
        assert response["changeset"] == mock_response_data
        # Check that both API calls were made correctly
        assert mock_get.call_count == 2
        
        # Check first call to get changeset details
        first_call = mock_get.call_args_list[0]
        assert first_call[0][0] == f"{self.server_config.instance_url}/api/now/table/sys_update_set/{params.changeset_id}"
        
        # Check second call to get changes
        second_call = mock_get.call_args_list[1]
        assert second_call[0][0] == f"{self.server_config.instance_url}/api/now/table/sys_update_xml"

    @patch("servicenow_mcp.tools.changeset_tools.requests.get")
    def test_list_changesets_error(self, mock_get):
        """Test listing changesets with an error."""
        mock_get.side_effect = requests.exceptions.RequestException("Test error")

        params = ListChangesetsParams()
        response = list_changesets(self.server_config, self.auth_manager, params)

        assert not response["success"]
        assert "Test error" in response["message"]

    @patch("servicenow_mcp.tools.changeset_tools.requests.get")
    def test_get_changeset_details_error(self, mock_get):
        """Test getting a changeset with an error."""
        mock_get.side_effect = requests.exceptions.RequestException("Test error")

        params = GetChangesetDetailsParams(changeset_id="123")
        response = get_changeset_details(self.server_config, self.auth_manager, params)

        assert not response["success"]
        assert "Test error" in response["message"]


class TestListChangesetsParams:
    """Tests for the ListChangesetsParams class."""

    def test_list_changesets_params(self): # Updated method name
        """Test ListChangesetsParams."""
        params = ListChangesetsParams(
            limit=20,
            offset=10,
            state="in_progress",
            application="Test App",
            developer="test.user",
        )
        assert params.limit == 20
        assert params.offset == 10
        assert params.state == "in_progress"
        assert params.application == "Test App"
        assert params.developer == "test.user"

    def test_list_changesets_params_defaults(self): # Updated method name
        """Test ListChangesetsParams defaults."""
        params = ListChangesetsParams()
        assert params.limit == 10 # Default from Pydantic model
        assert params.offset == 0 # Default from Pydantic model
        assert params.state is None
        assert params.application is None
        assert params.developer is None


if __name__ == "__main__":
    pytest.main([__file__])
