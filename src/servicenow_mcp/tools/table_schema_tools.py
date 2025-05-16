"""
Table Schema tools for the ServiceNow MCP server.

This module provides tools for working with ServiceNow table schemas.
"""

import logging
from typing import Dict, Any, List, Optional, Union

import requests
from pydantic import BaseModel, Field, field_validator

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


class FieldType(BaseModel):
    """Represents a field type which can be either a string or a reference."""
    value: str
    link: Optional[str] = None
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, str):
            return cls(value=v)
        elif isinstance(v, dict):
            return cls(
                value=v.get('value', ''),
                link=v.get('link')
            )
        raise ValueError("Field type must be a string or a dictionary with 'value' and optional 'link'")
    
    def __str__(self):
        return self.value


class FieldInfo(BaseModel):
    """Information about a field in a ServiceNow table."""
    
    name: str = Field(..., description="System name of the field")
    label: str = Field(..., description="Display label of the field")
    type: Union[str, FieldType] = Field(..., description="Data type of the field")
    max_length: Optional[int] = Field(None, description="Maximum length for string fields")
    reference: Optional[Union[str, FieldType]] = Field(
        None, 
        description="Reference to another table, if applicable"
    )
    mandatory: bool = Field(False, description="Whether the field is required")
    read_only: bool = Field(False, description="Whether the field is read-only")
    default_value: Any = Field(None, description="Default value for the field")
    choices: Optional[Dict[str, str]] = Field(None, description="Allowed values for choice fields")
    description: str = Field("", description="Description of the field")
    
    @field_validator('type', 'reference', mode='before')
    def validate_field_type(cls, v, info):
        field_name = info.field_name
        if v is None and field_name == 'reference':
            return None
        if isinstance(v, (str, dict)):
            return v
        raise ValueError(f"Field {field_name} must be a string or a dictionary")


class TableSchemaResponse(BaseModel):
    """Response for getting a table schema."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    name: str = Field(..., description="Name of the table")
    label: str = Field(..., description="Display label of the table")
    description: str = Field("", description="Description of the table")
    sys_created_on: Optional[str] = Field(None, description="Creation timestamp")
    sys_updated_on: Optional[str] = Field(None, description="Last update timestamp")
    fields: Dict[str, FieldInfo] = Field(..., description="Dictionary of field information keyed by field name")


class GetTableSchemaParams(BaseModel):
    """Parameters for getting a table schema."""
    
    table_name: str = Field(..., description="Name of the table to get the schema for")
    include_all_fields: bool = Field(False, description="Include all fields, including system and read-only fields")
    

class TableSchemaListResponse(BaseModel):
    """Response for listing table schemas."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    tables: List[Dict[str, str]] = Field(..., description="List of table names and labels")


def get_table_schema(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetTableSchemaParams,
) -> Dict[str, Any]:
    """
    Get the schema for a ServiceNow table.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for getting the table schema.

    Returns:
        Dictionary with the table schema information.
    """
    try:
        # Get authentication headers
        headers = auth_manager.get_headers()
        
        # First, get the table metadata
        table_url = f"{config.instance_url}/api/now/table/sys_db_object"
        table_params = {
            "sysparm_query": f"name={params.table_name}",
            "sysparm_fields": "name,label,description,sys_created_on,sys_updated_on"
        }
        
        table_response = requests.get(
            table_url,
            headers=headers,
            params=table_params,
            timeout=30
        )
        table_response.raise_for_status()
        
        table_data = table_response.json().get("result", [{}])[0]
        if not table_data:
            return {
                "success": False,
                "message": f"Table '{params.table_name}' not found",
                "error": "Table not found"
            }
        
        # Get the field schema
        schema_url = f"{config.instance_url}/api/now/table/sys_dictionary"
        # Build the query to get all fields for the table
        schema_params = {
            "sysparm_query": f"name={params.table_name}",
            "sysparm_fields": "element,column_label,internal_type,max_length,reference,mandatory,read_only,default_value,choices,description"
        }
        
        # Add filter for non-system fields if needed
        if not params.include_all_fields:
            schema_params["sysparm_query"] += "^column_label!="
        
        schema_response = requests.get(
            schema_url,
            headers=headers,
            params=schema_params,
            timeout=30
        )
        schema_response.raise_for_status()
        
        # Process the fields
        fields = {}
        for field in schema_response.json().get("result", []):
            field_name = field.get("element")
            if not field_name:
                continue
                
            # Parse choices if available
            choices = None
            if field.get("choices"):
                try:
                    choices = {}
                    for choice in field["choices"].split("\n"):
                        if "|--" in choice:
                            key, value = choice.split("|--", 1)
                            choices[key.strip()] = value.strip()
                except Exception as e:
                    logger.warning(f"Failed to parse choices for field {field_name}: {e}")
            
            fields[field_name] = FieldInfo(
                name=field_name,
                label=field.get("column_label", field_name),
                type=field.get("internal_type", "string"),
                max_length=field.get("max_length"),
                reference=field.get("reference"),
                mandatory=field.get("mandatory", "false").lower() == "true",
                read_only=field.get("read_only", "false").lower() == "true",
                default_value=field.get("default_value"),
                choices=choices,
                description=field.get("description", "")
            )
        
        # Create the response
        response = TableSchemaResponse(
            success=True,
            name=table_data.get("name", ""),
            label=table_data.get("label", ""),
            description=table_data.get("description", ""),
            sys_created_on=table_data.get("sys_created_on"),
            sys_updated_on=table_data.get("sys_updated_on"),
            fields=fields
        )
        
        return response.model_dump()
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to get schema for table '{params.table_name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        error_msg = f"Unexpected error getting schema for table '{params.table_name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }


class ListTableSchemasParams(BaseModel):
    """Parameters for listing table schemas."""
    
    include_system_tables: bool = Field(
        False, 
        description="Include system tables (prefixed with 'sys_', 'ZZ_', or 'v_')"
    )


def list_table_schemas(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    List all available table schemas in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Optional parameters for filtering the results.
            - include_system_tables (bool): Include system tables (default: False)

    Returns:
        Dictionary with list of table names and labels.
    """
    try:
        # Parse parameters
        params_model = ListTableSchemasParams(**(params or {}))
        
        # Get authentication headers
        headers = auth_manager.get_headers()
        
        # Build query parameters
        url = f"{config.instance_url}/api/now/table/sys_db_object"
        query_params = {
            "sysparm_fields": "name,label",
            "sysparm_limit": 1000
        }
        
        # Add query filter to exclude system tables if needed
        if not params_model.include_system_tables:
            query_params["sysparm_query"] = "nameNOT LIKEsys_^nameNOT LIKEZZ_^nameNOT LIKEv_^"
        
        response = requests.get(
            url,
            headers=headers,
            params=query_params,
            timeout=30
        )
        response.raise_for_status()
        
        tables = response.json().get("result", [])
        
        return TableSchemaListResponse(
            success=True,
            tables=[{"name": t.get("name"), "label": t.get("label", t.get("name"))} for t in tables]
        ).model_dump()
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to list table schemas: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }
    except Exception as e:
        error_msg = f"Unexpected error listing table schemas: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "error": str(e)
        }
