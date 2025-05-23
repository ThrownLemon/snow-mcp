"""
Table tools for the ServiceNow MCP server.

This module provides tools for working with ServiceNow tables.
"""

import logging
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


class ListTablesParams(BaseModel):
    """Parameters for listing tables."""
    
    limit: int = Field(10, description="Maximum number of tables to return", ge=1, le=1000)
    offset: int = Field(0, description="Offset for pagination", ge=0)
    name_filter: Optional[str] = Field(None, description="Filter tables by name")
    include_sys: Optional[bool] = Field(False, description="Include system tables")
    include_extended: Optional[bool] = Field(False, description="Include extended tables")


class TableInfo(BaseModel):
    """Information about a ServiceNow table."""
    
    name: str = Field(..., description="System name of the table")
    label: str = Field(..., description="Display label of the table")
    description: str = Field(..., description="Description of the table")
    is_extendable: bool = Field(False, description="Whether the table can be extended")
    is_view: bool = Field(False, description="Whether the table is a view")
    sys_created_on: Optional[str] = Field(None, description="Creation timestamp")
    sys_updated_on: Optional[str] = Field(None, description="Last update timestamp")


class ListTablesResponse(BaseModel):
    """Response for listing tables."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    tables: List[TableInfo] = Field(..., description="List of tables")
    count: int = Field(..., description="Total number of tables")
    offset: int = Field(0, description="Offset for pagination")
    limit: int = Field(10, description="Maximum number of tables returned")


def list_tables(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListTablesParams,
) -> Dict[str, Any]:
    """
    List available tables in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for listing tables.

    Returns:
        Dictionary with list of tables and metadata.
    """
    try:
        # Get authentication headers
        headers = auth_manager.get_headers()
        
        # Build query parameters
        query_params = {
            "sysparm_limit": params.limit,
            "sysparm_offset": params.offset,
            "sysparm_fields": (
                "name,label,description,is_extendable,is_view,sys_created_on,"
                "sys_updated_on"
            ),
        }
        
        # Add name filter if provided
        if params.name_filter:
            query_params["sysparm_query"] = (
                f"nameLIKE{params.name_filter}^ORlabelLIKE{params.name_filter}"
            )
        
        # Add system tables filter
        if not params.include_sys:
            if "sysparm_query" in query_params:
                query_params["sysparm_query"] += "^nameNOT LIKEsys_"
            else:
                query_params["sysparm_query"] = "nameNOT LIKEsys_"
        
        # Add extended tables filter
        if not params.include_extended:
            if "sysparm_query" in query_params:
                query_params["sysparm_query"] += "^nameNOT LIKEZZ_"
            else:
                query_params["sysparm_query"] = "nameNOT LIKEZZ_"
        
        # Make the API request
        url = f"{config.instance_url}/api/now/table/sys_db_object"
        response = requests.get(
            url,
            headers=headers,
            params=query_params,
            timeout=30
        )
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        tables = result.get("result", [])
        
        # Get total count
        count = result.get("headers", {}).get("x-total-count", len(tables))
        
        # Format the response
        table_list = [
            TableInfo(
                name=table.get("name", ""),
                label=table.get("label", table.get("name", "")),
                description=table.get("description", ""),
                is_extendable=table.get("is_extendable", False),
                is_view=table.get("is_view", False),
                sys_created_on=table.get("sys_created_on"),
                sys_updated_on=table.get("sys_updated_on")
            )
            for table in tables
        ]
        
        return ListTablesResponse(
            success=True,
            tables=table_list,
            count=count,
            offset=params.offset,
            limit=params.limit
        ).model_dump()
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to list tables: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        error_msg = f"Unexpected error listing tables: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }
