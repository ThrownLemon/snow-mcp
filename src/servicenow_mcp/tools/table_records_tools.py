"""
Table Records tools for the ServiceNow MCP server.

This module provides tools for working with records in ServiceNow tables.
"""

import logging
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel, Field, field_validator

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


class GetRecordsParams(BaseModel):
    """Parameters for getting records from a table."""
    
    table_name: str = Field(..., description="Name of the table to query")
    query: Optional[str] = Field(None, description="Encoded query string for filtering records")
    fields: Optional[List[str]] = Field(
        None,
        description=(
            "List of fields to include in the results. If not provided, all fields will be "
            "returned."
        ),
    )
    limit: int = Field(10, description="Maximum number of records to return", ge=1, le=1000)
    offset: int = Field(0, description="Offset for pagination", ge=0)
    order_by: Optional[str] = Field(None, description="Field to order results by")
    order_direction: str = Field("desc", description="Sort order (asc or desc)")
    
    @field_validator('order_direction')
    @classmethod
    def validate_order_direction(cls, v):
        if v.lower() not in ["asc", "desc"]:
            raise ValueError("order_direction must be 'asc' or 'desc'")
        return v.lower()


class GetRecordParams(BaseModel):
    """Parameters for getting a single record from a table."""
    
    table_name: str = Field(..., description="Name of the table containing the record")
    sys_id: str = Field(..., description="System ID of the record to retrieve")
    fields: Optional[List[str]] = Field(
        None,
        description=(
            "List of fields to include in the results. If not provided, all fields will be "
            "returned."
        ),
    )


class RecordResponse(BaseModel):
    """Response for a single record."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    record: Dict[str, Any] = Field(..., description="The record data")


class RecordsResponse(BaseModel):
    """Response for multiple records."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    records: List[Dict[str, Any]] = Field(..., description="List of records")
    count: int = Field(..., description="Total number of records matching the query")
    offset: int = Field(0, description="Offset for pagination")
    limit: int = Field(10, description="Maximum number of records returned")


def get_records(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetRecordsParams,
) -> Dict[str, Any]:
    """
    Get records from a ServiceNow table.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for getting records.

    Returns:
        Dictionary with list of records and metadata.
    """
    try:
        # Get authentication headers
        headers = auth_manager.get_headers()
        
        # Build query parameters
        query_params = {}
        if params.query:
            query_params["sysparm_query"] = params.query
            
        if params.fields:
            query_params["sysparm_fields"] = ",".join(params.fields)
            
        query_params["sysparm_limit"] = params.limit
        query_params["sysparm_offset"] = params.offset
        
        if params.order_by:
            direction = "" if params.order_direction.lower() == "asc" else "DESC"
            query_params["sysparm_order_by"] = f"{params.order_by}{direction}"
        
        # Make the API request
        url = f"{config.instance_url}/api/now/table/{params.table_name}"
        response = requests.get(
            url,
            headers=headers,
            params=query_params,
            timeout=30
        )
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        records = result.get("result", [])
        
        # Get total count
        count = result.get("headers", {}).get("x-total-count", len(records))
        
        return RecordsResponse(
            success=True,
            records=records,
            count=count,
            offset=params.offset,
            limit=params.limit
        ).model_dump()
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to get records from table '{params.table_name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        error_msg = f"Unexpected error getting records from table '{params.table_name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }


def get_record(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetRecordParams,
) -> Dict[str, Any]:
    """
    Get a single record by sys_id from a ServiceNow table.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for getting the record.

    Returns:
        Dictionary with the record data.
    """
    # Get authentication headers
    headers = auth_manager.get_headers()

    # Build the URL
    url = f"{config.instance_url}/api/now/table/{params.table_name}/{params.sys_id}"
    
    # Add fields parameter if provided
    request_params = {}
    if params.fields:
        request_params["sysparm_fields"] = ",".join(params.fields)

    try:
        response = requests.get(url, headers=headers, params=request_params)
        response.raise_for_status()
        
        result = response.json().get("result", {})
        
        if not result:
            return {
                "success": False,
                "message": (
                    f"Record with sys_id '{params.sys_id}' not found in table "
                    f"'{params.table_name}'"
                ),
                "error": "Record not found"
            }
            
        return {
            "success": True,
            "record": result
        }
    except requests.exceptions.HTTPError as http_err:
        error_msg = f"HTTP error occurred: {http_err}"
        if hasattr(http_err, 'response') and http_err.response.status_code == 404:
            error_msg = (
                f"Record with sys_id '{params.sys_id}' not found in table "
                f"'{params.table_name}'"
            )
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "status_code": http_err.response.status_code if hasattr(http_err, 'response') else None
        }
    except Exception as e:
        error_msg = f"Unexpected error getting record from table '{params.table_name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }
