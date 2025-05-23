---
trigger: always_on
---

# ServiceNow MCP Tool Creation Prompt

Use this prompt to guide the development of new tools for the ServiceNow MCP project. This structured approach ensures consistency in implementation, testing, and documentation.

## Background

The ServiceNow MCP (Model Completion Protocol) server allows Claude to interact with ServiceNow instances, retrieving data and performing actions through the ServiceNow API. Adding new tools expands the capabilities of this bridge.

## Required Files to Create/Modify

For each new tool, you need to:

1. Create/modify a tool module in `src/servicenow_mcp/tools/`
2. Update the tools `__init__.py` to expose the new tool
3. Update `server.py` to register the tool with the MCP server
4. Add unit tests in the `tests/` directory
5. Update documentation in the `docs/` directory
6. Update the `README.md` to include the new tool

## Implementation Steps

Please implement the following ServiceNow tool capability: {DESCRIBE_CAPABILITY_HERE}

Follow these steps to ensure a complete implementation:

### 1. Tool Module Implementation

```python
# Create a new file or modify an existing module in src/servicenow_mcp/tools/

"""
{TOOL_NAME} tools for the ServiceNow MCP server.

This module provides tools for {TOOL_DESCRIPTION}.
"""

import logging
from typing import Optional, List

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


class {ToolName}Params(BaseModel):
    """Parameters for {tool_name}."""

    # Define parameters with type annotations and descriptions
    param1: str = Field(..., description="Description of parameter 1")
    param2: Optional[str] = Field(None, description="Description of parameter 2")
    # Add more parameters as needed


class {ToolName}Response(BaseModel):
    """Response from {tool_name} operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    # Add more response fields as needed


def {tool_name}(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: {ToolName}Params,
) -> {ToolName}Response:
    """
    {Tool description with detailed explanation}.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for {tool_name}.

    Returns:
        Response with {description of response}.
    """
    api_url = f"{config.api_url}/table/{table_name}"

    # Build request data
    data = {
        # Map parameters to API request fields
        "field1": params.param1,
    }

    if params.param2:
        data["field2"] = params.param2
    # Add conditional fields as needed

    # Make request
    try:
        response = requests.post(  # or get, patch, delete as appropriate
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return {ToolName}Response(
            success=True,
            message="{Tool name} completed successfully",
            # Add more response fields from result as needed
        )

    except requests.RequestException as e:
        logger.error(f"Failed to {tool_name}: {e}")
        return {ToolName}Response(
            success=False,
            message=f"Failed to {tool_name}: {str(e)}",
        )
```

### 2. Update tools/__init__.py

```python
# Add import for new tool
from servicenow_mcp.tools.{tool_module} import (
    {tool_name},
)

# Add to __all__ list
__all__ = [
    # Existing tools...
    
    # New tools
    "{tool_name}",
]
```

### 3. Update server.py

```python
# Add imports for the tool parameters and function
from servicenow_mcp.tools.{tool_module} import (
    {ToolName}Params,
)
from servicenow_mcp.tools.{tool_module} import (
    {tool_name} as {tool_name}_tool,
)

# In the _register_tools method, add:
@self.mcp_server.tool()
def {tool_name}(params: {ToolName}Params) -> Dict[str, Any]:
    return {tool_name}_tool(
        self.config,
        self.auth_manager,
        params,
    )
```

### 4. Add Unit Tests

```python
# Add to existing test file or create a new one in tests/test_{tool_module}.py

@patch("requests.post")  # Or appropriate HTTP method
def test_{tool_name}(self, mock_post):
    """Test {tool_name} function."""
    # Configure mock
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "result": {
            # Mocked response data
        }
    }
    mock_post.return_value = mock_response
    
    # Create test params
    params = {ToolName}Params(
        param1="value1",
        param2="value2",
    )
    
    # Call function
    result = {tool_name}(self.config, self.auth_manager, params)
    
    # Verify result
    self.assertTrue(result.success)
    # Add more assertions
    
    # Verify mock was called correctly
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    self.assertEqual(call_args[0][0], f"{self.config.api_url}/table/{table_name}")
    # Add more assertions for request data
```

### 5. Update Documentation

Create or update a markdown file in `docs/` that explains the tool:

```markdown
# {Tool Category} in ServiceNow MCP

## {Tool Name}

{Detailed description of the tool}

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| param1 | string | Yes | Description of parameter 1 |
| param2 | string | No | Description of parameter 2 |
| ... | ... | ... | ... |

### Example

```python
# Example usage of {tool_name}
result = {tool_name}({
    "param1": "value1",
    "param2": "value2"
})
```
