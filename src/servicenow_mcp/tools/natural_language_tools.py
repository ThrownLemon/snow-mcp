"""
Natural Language tools for the ServiceNow MCP server.

This module provides tools for interacting with ServiceNow using natural language.
"""

import logging
import re
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel, Field, field_validator

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

class NaturalLanguageSearchParams(BaseModel):
    """Parameters for natural language search."""
    
    query: str = Field(
        ..., description="Natural language search query (e.g., 'find all incidents about SAP')"
    )
    table: str = Field("incident", description="Table to search in (default: incident)")
    limit: int = Field(10, description="Maximum number of results to return", ge=1, le=100)
    
    @field_validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()


class NaturalLanguageUpdateParams(BaseModel):
    """Parameters for natural language update."""
    
    query: str = Field(
        ...,
        description=(
            "Natural language update instruction (e.g., 'Update incident INC0010001 "
            "saying I'm working on it')"
        ),
    )
    
    @field_validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError("Update query cannot be empty")
        return v.strip()


class UpdateScriptParams(BaseModel):
    """Parameters for updating a script."""
    
    script_id: str = Field(..., description="ID or name of the script to update")
    script_type: str = Field(
        ..., description="Type of script (e.g., 'business_rule', 'script_include', 'ui_action')"
    )
    script: str = Field(..., description="The script content")
    description: Optional[str] = Field(None, description="Description of the script")
    active: bool = Field(True, description="Whether the script should be active")


class NaturalLanguageResponse(BaseModel):
    """Response for natural language operations."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    results: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of matching records"
    )
    query_used: Optional[str] = Field(None, description="The actual query used for the search")


def natural_language_search(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: NaturalLanguageSearchParams,
) -> Dict[str, Any]:
    """
    Search for records using natural language.
    
    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for the natural language search.
        
    Returns:
        Dictionary with search results.
    """
    try:
        # Simple keyword extraction (in a real implementation, use NLP here)
        keywords = re.findall(r'\b\w+\b', params.query.lower())
        
        # Build a simple query (this is a basic implementation)
        query_parts = []
        for keyword in keywords:
            if len(keyword) > 3:  # Only include meaningful keywords
                query_parts.append(f"LIKE{keyword}")
        
        if not query_parts:
            return {
                "success": False,
                "message": "No valid search terms found in the query",
                "results": []
            }
            
        query = "^OR".join(query_parts)
        
        # Get the records
        url = f"{config.instance_url}/api/now/table/{params.table}"
        headers = auth_manager.get_headers()
        
        response = requests.get(
            url,
            headers=headers,
            params={
                "sysparm_query": query,
                "sysparm_limit": params.limit,
                "sysparm_display_value": "all"
            },
            timeout=30
        )
        response.raise_for_status()
        
        results = response.json().get("result", [])
        
        return NaturalLanguageResponse(
            success=True,
            message=f"Found {len(results)} matching records",
            results=results,
            query_used=query
        ).model_dump()
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to perform search: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "results": []
        }
    except Exception as e:
        error_msg = f"Unexpected error during search: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "results": []
        }


def natural_language_update(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: NaturalLanguageUpdateParams,
) -> Dict[str, Any]:
    """
    Update records using natural language.
    
    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for the natural language update.
        
    Returns:
        Dictionary with update results.
    """
    try:
        # Simple pattern matching for updates (in a real implementation, use NLP)
        # Example: "Update incident INC0010001 priority to high"
        match = re.match(r"update\s+(\w+)\s+([A-Z0-9]+)(?:\s+(?:saying|with|setting)?\s*(.*))?", 
                        params.query, re.IGNORECASE)
        
        if not match:
            return {
                "success": False,
                "message": (
                    "Could not parse update command. Format: 'Update [table] [record_id] "
                    "[changes]'"
                ),
                "updated": False
            }
            
        table = match.group(1).lower()
        record_id = match.group(2)
        changes_text = match.group(3).strip() if match.group(3) else ""
        
        # Parse changes (simple implementation)
        changes = {}
        if "saying" in params.query.lower():
            # Handle comment/description updates
            comment_match = re.search(r"saying\s+(.*?)(?:\s+and\s+|$)", params.query, re.IGNORECASE)
            if comment_match:
                changes["comments"] = comment_match.group(1)
        else:
            # Handle field updates (e.g., "priority to high")
            field_updates = re.findall(r"(\w+)\s+(?:to|as)\s+([^,]+)", changes_text, re.IGNORECASE)
            for field, value in field_updates:
                changes[field.strip()] = value.strip()
        
        if not changes:
            return {
                "success": False,
                "message": "No valid changes specified in the update command",
                "updated": False
            }
        
        # Perform the update
        url = f"{config.instance_url}/api/now/table/{table}/{record_id}"
        headers = auth_manager.get_headers()
        
        response = requests.patch(
            url,
            headers=headers,
            json=changes,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json().get("result", {})
        
        return {
            "success": True,
            "message": f"Successfully updated {table} {record_id}",
            "updated": True,
            "result": result
        }
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to perform update: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "updated": False
        }
    except Exception as e:
        error_msg = f"Unexpected error during update: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "updated": False
        }


def update_script(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateScriptParams,
) -> Dict[str, Any]:
    """
    Update a ServiceNow script.
    
    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for updating the script.
        
    Returns:
        Dictionary with update results.
    """
    try:
        # Map script types to their corresponding API endpoints
        script_type_map = {
            "business_rule": "sys_script",
            "script_include": "sys_script_include",
            "ui_action": "sys_ui_action",
            "ui_script": "sys_ui_script"
        }
        
        if params.script_type not in script_type_map:
            return {
                "success": False,
                "message": f"Unsupported script type: {params.script_type}",
                "updated": False
            }
            
        table = script_type_map[params.script_type]
        url = f"{config.instance_url}/api/now/table/{table}"
        headers = auth_manager.get_headers()
        
        # First, try to find the script by name or ID
        query = f"name={params.script_id}^ORsys_id={params.script_id}"
        
        response = requests.get(
            f"{url}?sysparm_query={query}",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        scripts = response.json().get("result", [])
        
        if not scripts:
            return {
                "success": False,
                "message": f"No {params.script_type} found with name or ID: {params.script_id}",
                "updated": False
            }
            
        script = scripts[0]
        script_id = script["sys_id"]
        
        # Prepare the update payload
        update_data = {
            "script": params.script,
            "active": "true" if params.active else "false"
        }
        
        if params.description is not None:
            update_data["description"] = params.description
        
        # Update the script
        response = requests.patch(
            f"{url}/{script_id}",
            headers=headers,
            json=update_data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json().get("result", {})
        
        return {
            "success": True,
            "message": f"Successfully updated {params.script_type} {params.script_id}",
            "updated": True,
            "result": result
        }
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to update script: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "updated": False
        }
    except Exception as e:
        error_msg = f"Unexpected error during script update: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "updated": False
        }