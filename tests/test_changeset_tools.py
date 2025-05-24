"""
Tests for the changeset tools.

This module contains tests for the changeset tools in the ServiceNow MCP server.
"""

import pytest
from unittest.mock import MagicMock, patch

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.changeset_tools import (
    AddFileToChangesetParams,
    CommitChangesetParams,
    CreateChangesetParams,
    GetChangesetDetailsParams,
    ListChangesetsParams,
    PublishChangesetParams,
    UpdateChangesetParams,
    add_file_to_changeset,
    commit_changeset,
    create_changeset,
    get_changeset_details,
    list_changesets,
    publish_changeset,
    update_changeset,
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
            auth=auth_config,
        )
        self.auth_manager = MagicMock(spec=AuthManager)
        self.auth_manager.get_headers.return_value = {"Authorization": "Bearer test"}

    @patch("servicenow_mcp.tools.changeset_tools.requests.get")
    def test_list_changesets(self, mock_get):
        """Test listing changesets."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {
                    "sys_id": "123",
                    "name": "Test Changeset",
                    "state": "in_progress",
                    "application": "Test App",
                    "developer": "test.user",
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Call the function
        params = {
            "limit": 10,
            "offset": 0,
            "state": "in_progress",
            "application": "Test App",
            "developer": "test.user",
        }
        result = list_changesets(self.auth_manager, self.server_config, params)

        # Verify the result
        assert result["success"]
        assert len(result["changesets"]) == 1
        assert result["changesets"][0]["sys_id"] == "123"
        assert result["changesets"][0]["name"] == "Test Changeset"

        # Verify the API call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == "https://test.service-now.com/api/now/table/sys_update_set"
        assert kwargs["headers"] == {"Authorization": "Bearer test"}
        assert kwargs["params"]["sysparm_limit"] == 10
        assert kwargs["params"]["sysparm_offset"] == 0
        assert "sysparm_query" in kwargs["params"]
        assert "state=in_progress" in kwargs["params"]["sysparm_query"]
        assert "application=Test App" in kwargs["params"]["sysparm_query"]
        assert "developer=test.user" in kwargs["params"]["sysparm_query"]

    @patch("servicenow_mcp.tools.changeset_tools.requests.get")
    def test_get_changeset_details(self, mock_get):
        """Test getting changeset details."""
        # Mock responses
        mock_changeset_response = MagicMock()
        mock_changeset_response.json.return_value = {
            "result": {
                "sys_id": "123",
                "name": "Test Changeset",
                "state": "in_progress",
                "application": "Test App",
                "developer": "test.user",
            }
        }
        mock_changeset_response.raise_for_status.return_value = None

        mock_changes_response = MagicMock()
        mock_changes_response.json.return_value = {
            "result": [
                {
                    "sys_id": "456",
                    "name": "test_file.py",
                    "type": "file",
                    "update_set": "123",
                }
            ]
        }
        mock_changes_response.raise_for_status.return_value = None

        # Set up the mock to return different responses for different URLs
        def side_effect(*args, **kwargs):
            url = args[0]
            if "sys_update_set" in url:
                return mock_changeset_response
            elif "sys_update_xml" in url:
                return mock_changes_response
            return None

        mock_get.side_effect = side_effect

        # Call the function
        params = {"changeset_id": "123"}
        result = get_changeset_details(self.auth_manager, self.server_config, params)

        # Verify the result
        assert result["success"]
        assert result["changeset"]["sys_id"] == "123"
        assert result["changeset"]["name"] == "Test Changeset"
        assert len(result["changes"]) == 1
        assert result["changes"][0]["sys_id"] == "456"
        assert result["changes"][0]["name"] == "test_file.py"

        # Verify the API calls
        assert mock_get.call_count == 2
        first_call_args, first_call_kwargs = mock_get.call_args_list[0]
        assert first_call_args[0] == "https://test.service-now.com/api/now/table/sys_update_set/123"
        assert first_call_kwargs["headers"] == {"Authorization": "Bearer test"}

        second_call_args, second_call_kwargs = mock_get.call_args_list[1]
        assert second_call_args[0] == "https://test.service-now.com/api/now/table/sys_update_xml"
        assert second_call_kwargs["headers"] == {"Authorization": "Bearer test"}
        assert second_call_kwargs["params"]["sysparm_query"] == "update_set=123"

    @patch("servicenow_mcp.tools.changeset_tools.requests.post")
    def test_create_changeset(self, mock_post):
        """Test creating a changeset."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "123",
                "name": "Test Changeset",
                "application": "Test App",
                "developer": "test.user",
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Call the function
        params = {
            "name": "Test Changeset",
            "application": "Test App",
            "developer": "test.user",
            "description": "Test description",
        }
        result = create_changeset(self.auth_manager, self.server_config, params)

        # Verify the result
        assert result["success"]
        assert result["changeset"]["sys_id"] == "123"
        assert result["changeset"]["name"] == "Test Changeset"
        assert result["message"] == "Changeset created successfully"

        # Verify the API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://test.service-now.com/api/now/table/sys_update_set"
        assert kwargs["headers"]["Authorization"] == "Bearer test"
        assert kwargs["headers"]["Content-Type"] == "application/json"
        assert kwargs["json"]["name"] == "Test Changeset"
        assert kwargs["json"]["application"] == "Test App"
        assert kwargs["json"]["developer"] == "test.user"
        assert kwargs["json"]["description"] == "Test description"

    @patch("servicenow_mcp.tools.changeset_tools.requests.patch")
    def test_update_changeset(self, mock_patch):
        """Test updating a changeset."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "123",
                "name": "Updated Changeset",
                "state": "in_progress",
                "application": "Test App",
                "developer": "test.user",
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response

        # Call the function
        params = {
            "changeset_id": "123",
            "name": "Updated Changeset",
            "state": "in_progress",
        }
        result = update_changeset(self.auth_manager, self.server_config, params)

        # Verify the result
        assert result["success"]
        assert result["changeset"]["sys_id"] == "123"
        assert result["changeset"]["name"] == "Updated Changeset"
        assert result["message"] == "Changeset updated successfully"

        # Verify the API call
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        assert args[0] == "https://test.service-now.com/api/now/table/sys_update_set/123"
        assert kwargs["headers"]["Authorization"] == "Bearer test"
        assert kwargs["headers"]["Content-Type"] == "application/json"
        assert kwargs["json"]["name"] == "Updated Changeset"
        assert kwargs["json"]["state"] == "in_progress"

    @patch("servicenow_mcp.tools.changeset_tools.requests.patch")
    def test_commit_changeset(self, mock_patch):
        """Test committing a changeset."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "123",
                "name": "Test Changeset",
                "state": "complete",
                "application": "Test App",
                "developer": "test.user",
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response

        # Call the function
        params = {
            "changeset_id": "123",
            "commit_message": "Commit message",
        }
        result = commit_changeset(self.auth_manager, self.server_config, params)

        # Verify the result
        assert result["success"]
        assert result["changeset"]["sys_id"] == "123"
        assert result["changeset"]["state"] == "complete"
        assert result["message"] == "Changeset committed successfully"

        # Verify the API call
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        assert args[0] == "https://test.service-now.com/api/now/table/sys_update_set/123"
        assert kwargs["headers"]["Authorization"] == "Bearer test"
        assert kwargs["headers"]["Content-Type"] == "application/json"
        assert kwargs["json"]["state"] == "complete"
        assert kwargs["json"]["description"] == "Commit message"

    @patch("servicenow_mcp.tools.changeset_tools.requests.patch")
    def test_publish_changeset(self, mock_patch):
        """Test publishing a changeset."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "123",
                "name": "Test Changeset",
                "state": "published",
                "application": "Test App",
                "developer": "test.user",
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response

        # Call the function
        params = {
            "changeset_id": "123",
            "publish_notes": "Publish notes",
        }
        result = publish_changeset(self.auth_manager, self.server_config, params)

        # Verify the result
        assert result["success"]
        assert result["changeset"]["sys_id"] == "123"
        assert result["changeset"]["state"] == "published"
        assert result["message"] == "Changeset published successfully"

        # Verify the API call
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        assert args[0] == "https://test.service-now.com/api/now/table/sys_update_set/123"
        assert kwargs["headers"]["Authorization"] == "Bearer test"
        assert kwargs["headers"]["Content-Type"] == "application/json"
        assert kwargs["json"]["state"] == "published"
        assert kwargs["json"]["description"] == "Publish notes"

    @patch("servicenow_mcp.tools.changeset_tools.requests.post")
    def test_add_file_to_changeset(self, mock_post):
        """Test adding a file to a changeset."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "456",
                "name": "test_file.py",
                "type": "file",
                "update_set": "123",
                "payload": "print('Hello, world!')",
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Call the function
        params = {
            "changeset_id": "123",
            "file_path": "test_file.py",
            "file_content": "print('Hello, world!')",
        }
        result = add_file_to_changeset(self.auth_manager, self.server_config, params)

        # Verify the result
        assert result["success"]
        assert result["file"]["sys_id"] == "456"
        assert result["file"]["name"] == "test_file.py"
        assert result["message"] == "File added to changeset successfully"

        # Verify the API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://test.service-now.com/api/now/table/sys_update_xml"
        assert kwargs["headers"]["Authorization"] == "Bearer test"
        assert kwargs["headers"]["Content-Type"] == "application/json"
        assert kwargs["json"]["update_set"] == "123"
        assert kwargs["json"]["name"] == "test_file.py"
        assert kwargs["json"]["payload"] == "print('Hello, world!')"
        assert kwargs["json"]["type"] == "file"


class TestChangesetToolsParams:
    """Tests for the changeset tools parameter classes."""

    def test_list_changesets_params(self):
        """Test ListChangesetsParams."""
        params = ListChangesetsParams(
            limit=20,
            offset=10,
            state="in_progress",
            application="Test App",
            developer="test.user",
            timeframe="recent",
            query="name=test",
        )
        assert params.limit == 20
        assert params.offset == 10
        assert params.state == "in_progress"
        assert params.application == "Test App"
        assert params.developer == "test.user"
        assert params.timeframe == "recent"
        assert params.query == "name=test"

    def test_get_changeset_details_params(self):
        """Test GetChangesetDetailsParams."""
        params = GetChangesetDetailsParams(changeset_id="123")
        assert params.changeset_id == "123"

    def test_create_changeset_params(self):
        """Test CreateChangesetParams."""
        params = CreateChangesetParams(
            name="Test Changeset",
            description="Test description",
            application="Test App",
            developer="test.user",
        )
        assert params.name == "Test Changeset"
        assert params.description == "Test description"
        assert params.application == "Test App"
        assert params.developer == "test.user"

    def test_update_changeset_params(self):
        """Test UpdateChangesetParams."""
        params = UpdateChangesetParams(
            changeset_id="123",
            name="Updated Changeset",
            description="Updated description",
            state="in_progress",
            developer="test.user",
        )
        assert params.changeset_id == "123"
        assert params.name == "Updated Changeset"
        assert params.description == "Updated description"
        assert params.state == "in_progress"
        assert params.developer == "test.user"

    def test_commit_changeset_params(self):
        """Test CommitChangesetParams."""
        params = CommitChangesetParams(
            changeset_id="123",
            commit_message="Commit message",
        )
        assert params.changeset_id == "123"
        assert params.commit_message == "Commit message"

    def test_publish_changeset_params(self):
        """Test PublishChangesetParams."""
        params = PublishChangesetParams(
            changeset_id="123",
            publish_notes="Publish notes",
        )
        assert params.changeset_id == "123"
        assert params.publish_notes == "Publish notes"

    def test_add_file_to_changeset_params(self):
        """Test AddFileToChangesetParams."""
        params = AddFileToChangesetParams(
            changeset_id="123",
            file_path="test_file.py",
            file_content="print('Hello, world!')",
        )
        assert params.changeset_id == "123"
        assert params.file_path == "test_file.py"
        assert params.file_content == "print('Hello, world!')"


if __name__ == "__main__":
    pytest.main([__file__]) 