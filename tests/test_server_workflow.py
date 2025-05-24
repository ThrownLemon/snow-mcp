"""
Tests for the ServiceNow MCP server workflow management integration.
"""

import pytest
from unittest.mock import MagicMock, patch

from servicenow_mcp.server import ServiceNowMCP
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig


class TestServerWorkflow:
    """Tests for the ServiceNow MCP server workflow management integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.auth_config = AuthConfig(
            type=AuthType.BASIC,
            basic=BasicAuthConfig(username="test_user", password="test_password"),
        )
        self.server_config = ServerConfig(
            instance_url="https://test.service-now.com",
            auth=self.auth_config,
        )
        
        # Create the server instance with our test config
        self.config = {
            "instance_url": "https://test.service-now.com",
            "auth": {
                "type": "basic",
                "basic": {
                    "username": "test_user",
                    "password": "test_password",
                },
            },
        }
        
        # Create the server instance
        self.server = ServiceNowMCP(self.config)
        
        # Mock the MCP server
        self.server.mcp_server = MagicMock()
        self.server.mcp_server.resource = MagicMock()
        self.server.mcp_server.tool = MagicMock()
        
    def tearDown(self):
        """Tear down test fixtures."""
        # No need to stop any patchers in the updated implementation
        pass

    def test_register_workflow_tools(self):
        """Test that workflow tools are registered with the MCP server."""
        # The current implementation registers tools differently
        # Test that the server has initialized the tool_definitions attribute
        assert hasattr(self.server, 'tool_definitions'), "Server should have tool_definitions attribute"
        
        # Check that the server has registered handlers
        assert hasattr(self.server, 'mcp_server'), "Server should have mcp_server attribute"
        
        # Check that workflow tools are in the tool definitions
        workflow_tools = [name for name in self.server.tool_definitions.keys() 
                         if name.startswith('list_workflow') or 
                            name.startswith('get_workflow') or
                            name.startswith('create_workflow') or
                            name.startswith('update_workflow') or
                            name.startswith('activate_workflow') or
                            name.startswith('deactivate_workflow') or
                            name.startswith('add_workflow') or
                            name.startswith('delete_workflow') or
                            name.startswith('reorder_workflow')]
        
        assert len(workflow_tools) > 0, "Expected workflow tools in tool definitions"
        
        # Check for some expected workflow tool functions
        expected_functions = [
            'list_workflows',
            'get_workflow_details',
            'list_workflow_versions',
            'get_workflow_activities',
            'create_workflow',
            'update_workflow',
            'activate_workflow',
            'deactivate_workflow',
            'add_workflow_activity',
            'update_workflow_activity',
            'delete_workflow_activity',
            'reorder_workflow_activities',
        ]
        
        for func in expected_functions:
            assert func in self.server.tool_definitions.keys(), f"Expected {func} to be registered as a tool"


if __name__ == "__main__":
    pytest.main([__file__])