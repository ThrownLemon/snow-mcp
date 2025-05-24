"""Tests for the ServiceNow MCP catalog tools."""

import pytest
from unittest.mock import MagicMock

import requests

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.catalog_tools import (
    GetCatalogItemParams,
    ListCatalogCategoriesParams,
    ListCatalogItemsParams,
    CreateCatalogCategoryParams,
    UpdateCatalogCategoryParams,
    MoveCatalogItemsParams,
    get_catalog_item,
    get_catalog_item_variables,
    list_catalog_categories,
    list_catalog_items,
    create_catalog_category,
    update_catalog_category,
    move_catalog_items,
)
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig


@pytest.fixture
def config():
    """Fixture to provide a ServerConfig for testing."""
    # Create a mock server config
    return ServerConfig(
        instance_url="https://example.service-now.com",
        auth=AuthConfig(
            type=AuthType.BASIC,
            basic=BasicAuthConfig(username="admin", password="password"),
        ),
    )


@pytest.fixture
def auth_manager():
    """Fixture to provide a mock AuthManager for testing."""
    # Create a mock auth manager
    manager = MagicMock(spec=AuthManager)
    manager.get_headers.return_value = {"Authorization": "Basic YWRtaW46cGFzc3dvcmQ="}
    return manager


def test_list_catalog_items(monkeypatch, config, auth_manager):
    """Test listing catalog items."""
    # Import the module to patch
    import servicenow_mcp.tools.catalog_tools
    
    # Mock the response from ServiceNow
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": [
            {
                "sys_id": "item1",
                "name": "Laptop",
                "short_description": "Request a new laptop",
                "category": "Hardware",
                "price": "1000",
                "picture": "laptop.jpg",
                "active": "true",
                "order": "100",
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()
    
    # Setup monkeypatch
    def mock_get(*args, **kwargs):
        assert args[0] == "https://example.service-now.com/api/now/table/sc_cat_item"
        assert kwargs["params"]["sysparm_limit"] == 10
        assert kwargs["params"]["sysparm_offset"] == 0
        assert "sysparm_query" in kwargs["params"]
        assert "active=true" in kwargs["params"]["sysparm_query"]
        assert "category=Hardware" in kwargs["params"]["sysparm_query"]
        assert "short_descriptionLIKElaptop^ORnameLIKElaptop" in kwargs["params"]["sysparm_query"]
        return mock_response
    
    monkeypatch.setattr(servicenow_mcp.tools.catalog_tools.requests, 'get', mock_get)
    
    # Call the function
    params = ListCatalogItemsParams(
        limit=10,
        offset=0,
        category="Hardware",
        query="laptop",
        active=True,
    )
    result = list_catalog_items(config, auth_manager, params)
    
    # Check the result
    assert result.success is True
    assert len(result.data["items"]) == 1
    assert result.data["items"][0]["name"] == "Laptop"
    assert result.data["items"][0]["category"] == "Hardware"


def test_list_catalog_items_error(monkeypatch, config, auth_manager):
    """Test listing catalog items with an error."""
    # Import the module to patch
    import servicenow_mcp.tools.catalog_tools
    
    # Setup monkeypatch to simulate an error
    def mock_get(*args, **kwargs):
        raise requests.exceptions.RequestException("API Error")
    
    monkeypatch.setattr(servicenow_mcp.tools.catalog_tools.requests, 'get', mock_get)
    
    # Call the function
    params = ListCatalogItemsParams()
    result = list_catalog_items(config, auth_manager, params)
    
    # Check the result
    assert result.success is False
    assert "Failed to list catalog items" in result.message
    assert "API Error" in result.message


def test_get_catalog_item(monkeypatch, config, auth_manager):
    """Test getting a specific catalog item."""
    # Import the module to patch
    import servicenow_mcp.tools.catalog_tools
    from servicenow_mcp.utils import tool_utils
    
    # Mock the get_record_by_id_or_name response
    mock_record_result = {
        "success": True,
        "record": {
            "sys_id": "item1",
            "name": "Laptop",
            "short_description": "Request a new laptop",
            "description": "Request a new laptop for work",
            "category": "Hardware",
            "price": "1000",
            "picture": "laptop.jpg",
            "active": "true",
            "order": "100",
            "delivery_time": "3 days",
            "availability": "In Stock",
        }
    }
    
    # Mock the variables list
    mock_variables = [
        {
            "sys_id": "var1",
            "name": "model",
            "label": "Model",
            "type": "string",
            "mandatory": True,
            "default_value": "MacBook Pro",
            "help_text": "Select the laptop model",
            "order": "100",
        },
        {
            "sys_id": "var2",
            "name": "color",
            "label": "Color",
            "type": "string",
            "mandatory": False,
            "default_value": "Silver",
            "help_text": "Select the laptop color",
            "order": "200",
        }
    ]
    
    # Setup monkeypatch for get_record_by_id_or_name
    def mock_get_record(*args, **kwargs):
        return mock_record_result
    
    # Setup monkeypatch for get_catalog_item_variables
    def mock_get_variables(*args, **kwargs):
        return mock_variables
    
    monkeypatch.setattr(tool_utils, 'get_record_by_id_or_name', mock_get_record)
    monkeypatch.setattr(servicenow_mcp.tools.catalog_tools, 'get_catalog_item_variables', mock_get_variables)
    
    # Call the function
    params = GetCatalogItemParams(item_id="item1")
    result = get_catalog_item(config, auth_manager, params)
    
    # Check the result
    assert result.success is True
    assert result.data["item"]["sys_id"] == "item1"
    assert result.data["item"]["name"] == "Laptop"
    assert "variables" in result.data["item"]


def test_get_catalog_item_variables(monkeypatch, config, auth_manager):
    """Test getting catalog item variables."""
    # Import the module to patch
    import servicenow_mcp.tools.catalog_tools
    from servicenow_mcp.utils import tool_utils
    
    # Mock the get_record_by_id_or_name response
    mock_record_result = {
        "success": True,
        "record": {
            "sys_id": "item1",
            "name": "Laptop",
        }
    }
    
    # Mock the response from ServiceNow for variables
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": [
            {
                "sys_id": "var1",
                "name": "model",
                "question_text": "Model",
                "type": "string",
                "mandatory": "true",
            },
            {
                "sys_id": "var2",
                "name": "color",
                "question_text": "Color",
                "type": "string",
                "mandatory": "false",
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()
    
    # Setup monkeypatch for get_record_by_id_or_name
    def mock_get_record(*args, **kwargs):
        return mock_record_result
    
    # Setup monkeypatch for requests.get
    def mock_get(*args, **kwargs):
        assert "item_option_new" in args[0]
        return mock_response
    
    monkeypatch.setattr(tool_utils, 'get_record_by_id_or_name', mock_get_record)
    monkeypatch.setattr(servicenow_mcp.tools.catalog_tools.requests, 'get', mock_get)
    
    # Call the function
    variables = get_catalog_item_variables(config, auth_manager, "item1")
    
    # Check the result
    assert isinstance(variables, list)
    assert len(variables) == 2
    assert variables[0]["name"] == "model"
    assert variables[0]["mandatory"] == "true"
    assert variables[1]["name"] == "color"
    assert variables[1]["mandatory"] == "false"


def test_list_catalog_categories(monkeypatch, config, auth_manager):
    """Test listing catalog categories."""
    # Import the module to patch
    import servicenow_mcp.tools.catalog_tools
    
    # Mock the response from ServiceNow
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": [
            {
                "sys_id": "cat1",
                "title": "Hardware",
                "description": "Hardware items",
                "parent": "",
                "active": "true",
            },
            {
                "sys_id": "cat2",
                "title": "Software",
                "description": "Software items",
                "parent": "",
                "active": "true",
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()
    
    # Setup monkeypatch
    def mock_get(*args, **kwargs):
        assert "sc_category" in args[0]
        return mock_response
    
    monkeypatch.setattr(servicenow_mcp.tools.catalog_tools.requests, 'get', mock_get)
    
    # Call the function
    params = ListCatalogCategoriesParams(limit=10, offset=0, active=True)
    result = list_catalog_categories(config, auth_manager, params)
    
    # Check the result
    assert result.success is True
    assert len(result.data["categories"]) == 2
    assert result.data["categories"][0]["title"] == "Hardware"
    assert result.data["categories"][1]["title"] == "Software"


def test_create_catalog_category(monkeypatch, config, auth_manager):
    """Test creating a catalog category."""
    # Import the module to patch
    import servicenow_mcp.tools.catalog_tools
    
    # Mock the response from ServiceNow
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": {
            "sys_id": "new_cat",
            "title": "New Category",
            "description": "New category description",
            "parent": "parent_cat",
            "active": "true",
        }
    }
    mock_response.raise_for_status = MagicMock()
    
    # Setup monkeypatch
    def mock_post(*args, **kwargs):
        assert "sc_category" in args[0]
        assert kwargs["json"]["title"] == "New Category"
        assert kwargs["json"]["description"] == "New category description"
        # The parent_id is mapped to 'parent' in the JSON body
        if 'parent_id' in params.__dict__:
            assert kwargs["json"].get("parent") == params.parent_id
        return mock_response
    
    monkeypatch.setattr(servicenow_mcp.tools.catalog_tools.requests, 'post', mock_post)
    
    # Call the function
    params = CreateCatalogCategoryParams(
        title="New Category",
        description="New category description",
        parent_id="parent_cat",
        active=True
    )
    result = create_catalog_category(config, auth_manager, params)
    
    # Check the result
    assert result.success is True
    assert result.data["sys_id"] == "new_cat"
    assert result.data["title"] == "New Category"


def test_update_catalog_category(monkeypatch, config, auth_manager):
    """Test updating a catalog category."""
    # Import the module to patch
    import servicenow_mcp.tools.catalog_tools
    from servicenow_mcp.utils import tool_utils
    
    # Mock the get_record_by_id_or_name response
    mock_record_result = {
        "success": True,
        "record": {
            "sys_id": "cat1",
            "title": "Old Category",
            "description": "Old description",
            "parent": "",
            "active": "true",
        }
    }
    
    # Mock the response from ServiceNow
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "result": {
            "sys_id": "cat1",
            "title": "Updated Category",
            "description": "Updated description",
            "parent": "",
            "active": "true",
        }
    }
    
    # Setup monkeypatch for get_record_by_id_or_name
    def mock_get_record(*args, **kwargs):
        return mock_record_result
    
    # Setup monkeypatch for requests.patch
    def mock_patch(*args, **kwargs):
        assert "sc_category/cat1" in args[0]
        assert kwargs["json"]["title"] == "Updated Category"
        assert kwargs["json"]["description"] == "Updated description"
        return mock_response
    
    monkeypatch.setattr(tool_utils, 'get_record_by_id_or_name', mock_get_record)
    monkeypatch.setattr(servicenow_mcp.tools.catalog_tools.requests, 'patch', mock_patch)
    
    # Call the function
    params = UpdateCatalogCategoryParams(
        category_id="cat1",
        title="Updated Category",
        description="Updated description",
    )
    result = update_catalog_category(config, auth_manager, params)
    
    # Check the result
    assert result.success is True
    assert result.data["category"]["sys_id"] == "cat1"
    assert result.data["category"]["title"] == "Updated Category"


def test_move_catalog_items(monkeypatch, config, auth_manager):
    """Test moving catalog items to a different category."""
    # Import the module to patch
    import servicenow_mcp.tools.catalog_tools
    from servicenow_mcp.utils import tool_utils
    
    # Mock the get_record_by_id_or_name response for category
    mock_category_result = {
        "success": True,
        "record": {
            "sys_id": "target_category_id",
            "title": "Target Category",
        }
    }
    
    # Mock the get_record_by_id_or_name response for item
    mock_item_result = {
        "success": True,
        "record": {
            "sys_id": "item1",
            "name": "Laptop",
            "category": "old_category_id",
        }
    }
    
    # Mock the response from ServiceNow for the update
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "result": {
            "sys_id": "item1",
            "name": "Laptop",
            "category": "target_category_id",
        }
    }
    mock_response.raise_for_status = MagicMock()
    
    # Setup monkeypatch for get_record_by_id_or_name
    def mock_get_record(*args, **kwargs):
        if kwargs.get('table_name') == 'sc_category':
            return mock_category_result
        else:  # sc_cat_item
            return mock_item_result
    
    # Setup monkeypatch for requests.patch
    def mock_patch(*args, **kwargs):
        assert "sc_cat_item/item1" in args[0]
        assert kwargs["json"]["category"] == "target_category_id"
        return mock_response
    
    monkeypatch.setattr(tool_utils, 'get_record_by_id_or_name', mock_get_record)
    monkeypatch.setattr(servicenow_mcp.tools.catalog_tools.requests, 'patch', mock_patch)
    
    # Call the function
    params = MoveCatalogItemsParams(
        item_ids=["item1"],
        target_category_id="target_category_id"
    )
    result = move_catalog_items(config, auth_manager, params)
    
    # Check the result
    assert result.success is True
    assert result.data["moved_items_count"] == 1
    assert result.data["target_category_id"] == "target_category_id"
    assert result.data["target_category_name"] == "Target Category"
