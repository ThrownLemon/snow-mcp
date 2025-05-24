"""
Tests for the ServiceNow MCP incident tools.
"""

import unittest
from unittest.mock import MagicMock, patch

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


class TestIncidentTools(unittest.TestCase):
    """Test cases for the incident tools."""

    def setUp(self):
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

    @patch("requests.post")
    def test_create_incident(self, mock_post):
        """Test creating an incident."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {"sys_id": "inc123", "number": "INC0010001"}
        }
        mock_response.raise_for_status = MagicMock() 
        mock_post.return_value = mock_response

        params = CreateIncidentParams(
            short_description="Test incident",
            description="Detailed description of test incident",
            priority="1",
        )
        result = create_incident(self.config, self.auth_manager, params)

        self.assertTrue(result.success)
        self.assertEqual(result.incident_id, "inc123")
        self.assertEqual(result.incident_number, "INC0010001")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"{self.config.api_url}/table/incident")
        self.assertEqual(kwargs["json"]["short_description"], "Test incident")
        self.assertEqual(kwargs["json"]["priority"], "1")

    @patch("requests.get")
    @patch("requests.put")
    def test_update_incident_by_sys_id(self, mock_put, mock_get):
        """Test updating an incident by sys_id."""
        # Mock the PUT response
        mock_put_response = MagicMock()
        mock_put_response.json.return_value = {
            "result": {"sys_id": "inc123", "number": "INC0010001"}
        }
        mock_put_response.raise_for_status = MagicMock()
        mock_put.return_value = mock_put_response
        
        # Mock the GET response for incident lookup
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {"result": [{"sys_id": "inc123"}]}
        mock_get_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_get_response

        params = UpdateIncidentParams(incident_id="inc123", priority="2", work_notes="Investigating")
        result = update_incident(self.config, self.auth_manager, params)

        self.assertTrue(result.success)
        self.assertEqual(result.incident_id, "inc123")
        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        self.assertEqual(args[0], f"{self.config.api_url}/table/incident/inc123")
        self.assertEqual(kwargs["json"]["priority"], "2")
        self.assertEqual(kwargs["json"]["work_notes"], "Investigating")

    @patch("requests.get")
    @patch("requests.put")
    def test_update_incident_by_number(self, mock_put, mock_get):
        """Test updating an incident by incident number."""
        # Mock for GET request to find sys_id
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {"result": [{"sys_id": "inc123"}]}
        mock_get_response.raise_for_status = MagicMock() 
        mock_get.return_value = mock_get_response

        # Mock for PUT request to update
        mock_put_response = MagicMock()
        mock_put_response.json.return_value = {
            "result": {"sys_id": "inc123", "number": "INC0010001"}
        }
        mock_put_response.raise_for_status = MagicMock() 
        mock_put.return_value = mock_put_response

        params = UpdateIncidentParams(
            incident_id="INC0010001", priority="2", work_notes="Investigating"
        )
        result = update_incident(self.config, self.auth_manager, params)

        self.assertTrue(result.success)
        self.assertEqual(result.incident_id, "inc123")
        mock_get.assert_called_once()
        mock_put.assert_called_once()
        put_args, put_kwargs = mock_put.call_args
        self.assertEqual(put_args[0], f"{self.config.api_url}/table/incident/inc123")

    @patch("requests.get")
    @patch("requests.put")
    def test_add_comment_by_sys_id(self, mock_put, mock_get):
        """Test adding a comment to an incident by sys_id."""
        # Mock the PUT response
        mock_put_response = MagicMock()
        mock_put_response.json.return_value = {
            "result": {"sys_id": "inc123", "number": "INC0010001"}
        }
        mock_put_response.raise_for_status = MagicMock()
        mock_put.return_value = mock_put_response
        
        # Mock the GET response for incident lookup
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {"result": [{"sys_id": "inc123"}]}
        mock_get_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_get_response

        params = AddCommentParams(incident_id="inc123", comment="Test comment", is_work_note=True)
        result = add_comment(self.config, self.auth_manager, params)

        self.assertTrue(result.success)
        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        self.assertEqual(args[0], f"{self.config.api_url}/table/incident/inc123")
        self.assertEqual(kwargs["json"]["work_notes"], "Test comment")

    @patch("requests.get")
    @patch("requests.put")
    def test_add_comment_by_number(self, mock_put, mock_get):
        """Test adding a comment to an incident by incident number."""
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {"result": [{"sys_id": "inc123"}]}
        mock_get_response.raise_for_status = MagicMock() 
        mock_get.return_value = mock_get_response

        mock_put_response = MagicMock()
        mock_put_response.json.return_value = {
            "result": {"sys_id": "inc123", "number": "INC0010001"}
        }
        mock_put_response.raise_for_status = MagicMock() 
        mock_put.return_value = mock_put_response

        params = AddCommentParams(
            incident_id="INC0010001", comment="Test comment", is_work_note=False
        )
        result = add_comment(self.config, self.auth_manager, params)

        self.assertTrue(result.success)
        mock_get.assert_called_once()
        mock_put.assert_called_once()
        put_args, put_kwargs = mock_put.call_args
        self.assertEqual(put_args[0], f"{self.config.api_url}/table/incident/inc123")
        self.assertEqual(put_kwargs["json"]["comments"], "Test comment")

    @patch("requests.get")
    @patch("requests.put")
    def test_resolve_incident_by_sys_id(self, mock_put, mock_get):
        """Test resolving an incident by sys_id."""
        # Mock the PUT response
        mock_put_response = MagicMock()
        mock_put_response.json.return_value = {
            "result": {"sys_id": "inc123", "number": "INC0010001"}
        }
        mock_put_response.raise_for_status = MagicMock()
        mock_put.return_value = mock_put_response
        
        # Mock the GET response for incident lookup
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {"result": [{"sys_id": "inc123"}]}
        mock_get_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_get_response

        params = ResolveIncidentParams(
            incident_id="inc123",
            resolution_code="Solved (Permanently)",
            resolution_notes="Issue resolved.",
        )
        result = resolve_incident(self.config, self.auth_manager, params)

        self.assertTrue(result.success)
        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        self.assertEqual(args[0], f"{self.config.api_url}/table/incident/inc123")
        self.assertEqual(kwargs["json"]["state"], "6")
        self.assertEqual(kwargs["json"]["close_code"], "Solved (Permanently)")

    @patch("requests.get")
    @patch("requests.put")
    def test_resolve_incident_by_number(self, mock_put, mock_get):
        """Test resolving an incident by incident number."""
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {"result": [{"sys_id": "inc123"}]}
        mock_get_response.raise_for_status = MagicMock() 
        mock_get.return_value = mock_get_response

        mock_put_response = MagicMock()
        mock_put_response.json.return_value = {
            "result": {"sys_id": "inc123", "number": "INC0010001"}
        }
        mock_put_response.raise_for_status = MagicMock() 
        mock_put.return_value = mock_put_response

        params = ResolveIncidentParams(
            incident_id="INC0010001",
            resolution_code="Solved (Workaround)",
            resolution_notes="Workaround applied.",
        )
        result = resolve_incident(self.config, self.auth_manager, params)

        self.assertTrue(result.success)
        mock_get.assert_called_once()
        mock_put.assert_called_once()
        put_args, put_kwargs = mock_put.call_args
        self.assertEqual(put_args[0], f"{self.config.api_url}/table/incident/inc123")
        self.assertEqual(put_kwargs["json"]["close_code"], "Solved (Workaround)")

    @patch("requests.get")
    def test_list_incidents(self, mock_get):
        """Test listing incidents."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {"sys_id": "inc123", "number": "INC0010001", "short_description": "Test 1"},
                {"sys_id": "inc456", "number": "INC0010002", "short_description": "Test 2"},
            ]
        }
        mock_response.raise_for_status = MagicMock() 
        mock_get.return_value = mock_response

        params = ListIncidentsParams(limit=5, state="1", category="Software")
        result = list_incidents(self.config, self.auth_manager, params)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["incidents"]), 2)
        self.assertEqual(result["incidents"][0]["number"], "INC0010001")
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], f"{self.config.api_url}/table/incident")
        self.assertEqual(kwargs["params"]["sysparm_limit"], 5)
        self.assertIn("state=1", kwargs["params"]["sysparm_query"])
        self.assertIn("category=Software", kwargs["params"]["sysparm_query"])

    @patch("requests.post")
    def test_create_incident_api_error(self, mock_post):
        """Test create_incident with an API error."""
        mock_post.side_effect = requests.exceptions.RequestException("API Error")
        params = CreateIncidentParams(short_description="Error test")
        result = create_incident(self.config, self.auth_manager, params)
        self.assertFalse(result.success)
        self.assertIn("Failed to create incident", result.message)

    @patch("servicenow_mcp.tools.incident_tools._find_incident_sys_id")
    @patch("requests.patch")
    def test_update_incident_api_error(self, mock_patch, mock_find_incident_sys_id):
        """Test update_incident with an API error."""
        mock_find_incident_sys_id.return_value = {
            "success": False,
            "message": "Failed to find incident: 401 Client Error: Unauthorized for url: https://example.service-now.com/api/now/table/incident?sysparm_query=number%3Dinc123&sysparm_limit=1"
        }
        params = UpdateIncidentParams(incident_id="inc123", priority="1")
        result = update_incident(self.config, self.auth_manager, params)
        self.assertFalse(result.success)
        self.assertIn("Failed to find incident", result.message)

    @patch("requests.get")
    def test_update_incident_not_found_error(self, mock_get):
        """Test update_incident when incident number is not found."""
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {"result": []}
        mock_get_response.raise_for_status = MagicMock() 
        mock_get.return_value = mock_get_response

        params = UpdateIncidentParams(incident_id="INC_NOT_EXIST", priority="1")
        result = update_incident(self.config, self.auth_manager, params)
        self.assertFalse(result.success)
        self.assertIn("Incident not found", result.message)

    @patch("servicenow_mcp.tools.incident_tools._find_incident_sys_id")
    @patch("requests.put")
    def test_add_comment_api_error(self, mock_put, mock_find_incident_sys_id):
        """Test add_comment with an API error."""
        mock_find_incident_sys_id.return_value = {
            "success": False,
            "message": "Failed to find incident: 401 Client Error: Unauthorized for url: https://example.service-now.com/api/now/table/incident?sysparm_query=number%3Dinc123&sysparm_limit=1"
        }
        params = AddCommentParams(incident_id="inc123", comment="Error comment")
        result = add_comment(self.config, self.auth_manager, params)
        self.assertFalse(result.success)
        self.assertIn("Failed to find incident", result.message)

    @patch("servicenow_mcp.tools.incident_tools._find_incident_sys_id")
    @patch("requests.put")
    def test_resolve_incident_api_error(self, mock_put, mock_find_incident_sys_id):
        """Test resolve_incident with an API error."""
        mock_find_incident_sys_id.return_value = {
            "success": False,
            "message": "Failed to find incident: 401 Client Error: Unauthorized for url: https://example.service-now.com/api/now/table/incident?sysparm_query=number%3Dinc123&sysparm_limit=1"
        }
        params = ResolveIncidentParams(
            incident_id="inc123", resolution_code="Error", resolution_notes="Error"
        )
        result = resolve_incident(self.config, self.auth_manager, params)
        self.assertFalse(result.success)
        self.assertIn("Failed to find incident", result.message)

    @patch("requests.get")
    def test_list_incidents_api_error(self, mock_get):
        """Test list_incidents with an API error."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")
        params = ListIncidentsParams()
        result = list_incidents(self.config, self.auth_manager, params)
        self.assertFalse(result["success"])
        self.assertIn("API Error", result["message"])


if __name__ == "__main__":
    unittest.main()
