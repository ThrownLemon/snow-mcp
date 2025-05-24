#!/usr/bin/env python
"""
Script to run direct tests against a ServiceNow instance.
"""

import os
import json
import logging
from dotenv import load_dotenv

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig, AuthConfig, AuthType, BasicAuthConfig
from servicenow_mcp.tools.workflow_tools import (
    list_workflows,
    get_workflow_details,
    list_workflow_versions,
    get_workflow_activities,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def setup_auth_and_config():
    """Set up authentication and server configuration."""
    instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
    username = os.getenv("SERVICENOW_USERNAME")
    password = os.getenv("SERVICENOW_PASSWORD")
    
    if not all([instance_url, username, password]):
        logger.error("Missing required environment variables. Please set SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, and SERVICENOW_PASSWORD.")
        exit(1)
    
    # Create authentication configuration
    auth_config = AuthConfig(
        type=AuthType.BASIC,
        basic=BasicAuthConfig(username=username, password=password),
    )
    
    # Create server configuration
    server_config = ServerConfig(
        instance_url=instance_url,
        auth=auth_config,
    )
    
    # Create authentication manager
    auth_manager = AuthManager(auth_config)
    
    return auth_manager, server_config

def print_result(name, result):
    """Print the result of a function call."""
    logger.info(f"=== Result of {name} ===")
    if "error" in result:
        logger.error(f"Error: {result['error']}")
        return False
    else:
        logger.info(json.dumps(result, indent=2))
        return True

def run_tests():
    """Run the direct tests."""
    auth_manager, server_config = setup_auth_and_config()
    
    # Test list_workflows
    logger.info("Testing list_workflows...")
    result = list_workflows(auth_manager, server_config, {"limit": 10})
    success = print_result("list_workflows", result)
    
    if not success:
        logger.error("Failed to list workflows. Skipping remaining tests.")
        return
    
    # Get a workflow ID for further tests
    if result.get("workflows") and len(result["workflows"]) > 0:
        workflow_id = result["workflows"][0]["sys_id"]
        logger.info(f"Using workflow ID: {workflow_id}")
        
        # Test get_workflow_details
        logger.info("\nTesting get_workflow_details...")
        result = get_workflow_details(auth_manager, server_config, {"workflow_id": workflow_id})
        success = print_result("get_workflow_details", result)
        
        # Test list_workflow_versions
        logger.info("\nTesting list_workflow_versions...")
        result = list_workflow_versions(auth_manager, server_config, {"workflow_id": workflow_id})
        success = print_result("list_workflow_versions", result)
        
        # Test get_workflow_activities
        if result.get("versions") and len(result["versions"]) > 0:
            version_id = result["versions"][0]["sys_id"]
            logger.info(f"Using version ID: {version_id}")
            
            logger.info("\nTesting get_workflow_activities...")
            result = get_workflow_activities(auth_manager, server_config, {
                "workflow_id": workflow_id,
                "version": version_id
            })
            success = print_result("get_workflow_activities", result)
    else:
        logger.warning("No workflows found. Skipping remaining tests.")

if __name__ == "__main__":
    run_tests()
