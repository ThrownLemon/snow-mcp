#!/usr/bin/env python
"""
Test script for workflow_tools module.
This script directly tests the workflow_tools functions with proper authentication.
"""

import pytest
import logging

from servicenow_mcp.tools.workflow_tools import (
    list_workflows,
    get_workflow_details,
    list_workflow_versions,
    get_workflow_activities,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_list_workflows(auth_manager, server_config):
    """Test listing workflows."""
    # Call the function
    params = {
        "limit": 10,
        "active": True,
    }
    result = list_workflows(auth_manager, server_config, params)
    
    # Assert that the result is as expected
    assert "workflows" in result, "Expected 'workflows' in result"
    assert "count" in result, "Expected 'count' in result"
    assert "total" in result, "Expected 'total' in result"


def test_get_workflow_details(auth_manager, server_config, workflow_id):
    """Test getting workflow details."""
    # Call the function
    params = {
        "workflow_id": workflow_id,
    }
    result = get_workflow_details(auth_manager, server_config, params)
    
    # Assert that the result is as expected
    assert "workflow" in result, "Expected 'workflow' in result"


def test_list_workflow_versions(auth_manager, server_config, workflow_id):
    """Test listing workflow versions."""
    # Call the function
    params = {
        "workflow_id": workflow_id,
    }
    result = list_workflow_versions(auth_manager, server_config, params)
    
    # Assert that the result is as expected
    assert "versions" in result, "Expected 'versions' in result"


def test_get_workflow_activities(auth_manager, server_config, workflow_id):
    """Test getting workflow activities."""
    # First, get the workflow versions
    versions_params = {
        "workflow_id": workflow_id,
    }
    versions_result = list_workflow_versions(auth_manager, server_config, versions_params)
    
    if "versions" in versions_result and versions_result["versions"]:
        version_id = versions_result["versions"][0]["sys_id"]
        
        # Call the function with the correct parameter
        params = {
            "version_id": version_id,
            "workflow_id": workflow_id  # Adding the required workflow_id parameter
        }
        result = get_workflow_activities(auth_manager, server_config, params)
        
        # Assert that the result is as expected
        assert "activities" in result, "Expected 'activities' in result"
    else:
        pytest.skip("No workflow versions found. Skipping test_get_workflow_activities.")


def test_with_swapped_params(auth_manager, server_config):
    """Test with invalid parameters."""
    # Call the function with an invalid parameter
    params = {
        "limit": "invalid",  # Should be an integer, not a string
        "active": True,
    }
    result = list_workflows(auth_manager, server_config, params)
    
    # Assert that the result contains an error
    assert "error" in result, "Expected 'error' in result with invalid parameters"

if __name__ == "__main__":
    logger.info("Testing workflow_tools module...")
    
    # Set up authentication and server configuration
    auth_manager, server_config = setup_auth_and_config()
    
    # Test list_workflows
    workflows_result = test_list_workflows(auth_manager, server_config)
    
    # If we got any workflows, test the other functions
    if "workflows" in workflows_result and workflows_result["workflows"]:
        workflow_id = workflows_result["workflows"][0]["sys_id"]
        
        # Test get_workflow_details
        test_get_workflow_details(auth_manager, server_config, workflow_id)
        
        # Test list_workflow_versions
        test_list_workflow_versions(auth_manager, server_config, workflow_id)
        
        # Test get_workflow_activities
        test_get_workflow_activities(auth_manager, server_config, workflow_id)
    else:
        logger.warning("No workflows found, skipping detail tests.")
    
    # Test with swapped parameters
    test_with_swapped_params(auth_manager, server_config)
    
    logger.info("Tests completed.") 