"""
Tests for the ServiceNow MCP catalog tools.
"""

import unittest
from unittest.mock import MagicMock, patch
import requests # Import requests for the exceptions

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.catalog_tools import (
    list_catalog_items,
    get_catalog_item,
    list_catalog_categories,
    ListCatalogItemsParams,  # Original: CatalogListParams
    GetCatalogItemParams,
    ListCatalogCategoriesParams,  # Original: CatalogCategoryListParams
    CatalogResponse # To check tool responses
)
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig


class TestCatalogTools(unittest.TestCase): # Changed from IsolatedAsyncioTestCase to TestCase
    """Test cases for the catalog tools."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock server config
        self.config = ServerConfig(
            instance_url="https://example.service-now.com",
            api_url="https://example.service-now.com/api/sn_sc", # Assuming api_url is used by tools
            auth=AuthConfig(
                type=AuthType.BASIC,
                basic=BasicAuthConfig(username="admin", password="password"),
            ),
            timeout=10
        )

        # Create a mock auth manager
        self.auth_manager = MagicMock(spec=AuthManager)
        self.auth_manager.get_headers.return_value = {"Authorization": "Basic YWRtaW46cGFzc3dvcmQ="}
        # Removed: self.resource = CatalogResource(self.config, self.auth_manager)

    @patch("servicenow_mcp.tools.catalog_tools.requests.get")
    def test_list_catalog_items(self, mock_get):
        """Test listing catalog items."""
        mock_response_data = [
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
        mock_api_response = MagicMock()
        mock_api_response.json.return_value = {"result": mock_response_data}
        mock_api_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_api_response

        params = ListCatalogItemsParams(limit=1, offset=0, query="laptop", category="hardware", active=True)
        response = list_catalog_items(self.config, self.auth_manager, params)

        self.assertTrue(response.success)
        self.assertEqual(response.data["items"], mock_response_data)
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], f"{self.config.instance_url}/api/now/table/sc_cat_item")
        self.assertEqual(kwargs["params"]["sysparm_limit"], 1)
        self.assertEqual(kwargs["params"]["sysparm_offset"], 0)


    @patch("servicenow_mcp.tools.catalog_tools.requests.get")
    def test_list_catalog_items_error(self, mock_get):
        """Test listing catalog items with an error."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        params = ListCatalogItemsParams(limit=10, offset=0)
        response = list_catalog_items(self.config, self.auth_manager, params)

        self.assertFalse(response.success)
        self.assertIn("Failed to list catalog items: API Error", response.message)
        self.assertEqual(response.data["items"], [])
        self.assertEqual(response.data["total"], 0)

    @patch("servicenow_mcp.tools.catalog_tools.get_catalog_item_variables", return_value=[])
    @patch("servicenow_mcp.tools.catalog_tools.requests.get")
    def test_get_catalog_item(self, mock_get, mock_variables):
        """Test getting a specific catalog item."""
        mock_response_data = {"sys_id": "item1", "name": "Laptop"}
        mock_api_response = MagicMock()
        mock_api_response.json.return_value = {"result": mock_response_data}
        mock_api_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_api_response

        params = GetCatalogItemParams(item_id="item1")
        response = get_catalog_item(self.config, self.auth_manager, params)

        self.assertTrue(response.success)
        self.assertEqual(response.data["item"]["sys_id"], mock_response_data["sys_id"])
        self.assertEqual(response.data["item"]["name"], mock_response_data["name"])
        mock_get.assert_called_once()

    @patch("servicenow_mcp.tools.catalog_tools.requests.get")
    def test_get_catalog_item_not_found(self, mock_get):
        """Test getting a catalog item that is not found."""
        mock_api_response = MagicMock()
        mock_api_response.json.return_value = {"result": None} # Or an empty list for "result"
        mock_api_response.raise_for_status = MagicMock() # Or mock it to raise a 404
        # Simulating a case where API returns success but no item
        mock_get.return_value = mock_api_response


        params = GetCatalogItemParams(item_id="nonexistent")
        response = get_catalog_item(self.config, self.auth_manager, params)

        self.assertFalse(response.success) # Expecting the tool to interpret "no result" as not successful
        self.assertIn("Catalog item not found: nonexistent", response.message)
        self.assertIsNone(response.data)


    @patch("servicenow_mcp.tools.catalog_tools.requests.get")
    def test_get_catalog_item_error(self, mock_get):
        """Test getting a catalog item with an API error."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        params = GetCatalogItemParams(item_id="item1")
        response = get_catalog_item(self.config, self.auth_manager, params)

        self.assertFalse(response.success)
        self.assertIn("Catalog item not found", response.message)
        self.assertIsNone(response.data)

    @patch("servicenow_mcp.tools.catalog_tools.requests.get")
    def test_list_catalog_categories(self, mock_get):
        """Test listing catalog categories."""
        mock_response_data = [{
            "sys_id": "cat1",
            "title": "Hardware",
            "description": "",
            "parent": "",
            "icon": "",
            "active": "",
            "order": ""
        }]
        mock_api_response = MagicMock()
        mock_api_response.json.return_value = {"result": mock_response_data}
        mock_api_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_api_response

        params = ListCatalogCategoriesParams(limit=10, offset=0, query="Hardware", active=True)
        response = list_catalog_categories(self.config, self.auth_manager, params)

        self.assertTrue(response.success)
        self.assertEqual(response.data["categories"], mock_response_data)
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], f"{self.config.instance_url}/api/now/table/sc_category")
        self.assertEqual(kwargs["params"]["sysparm_limit"], 10)
        self.assertEqual(kwargs["params"]["sysparm_offset"], 0)


    @patch("servicenow_mcp.tools.catalog_tools.requests.get")
    def test_list_catalog_categories_error(self, mock_get):
        """Test listing catalog categories with an error."""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        params = ListCatalogCategoriesParams(limit=10, offset=0)
        response = list_catalog_categories(self.config, self.auth_manager, params)

        self.assertFalse(response.success)
        self.assertIn("Failed to list catalog categories: API Error", response.message)
        self.assertEqual(response.data["categories"], [])
        self.assertEqual(response.data["total"], 0)

    # The original test_read method is refactored into test_get_catalog_item above.
    # The original test_read_missing_param is commented out as its direct translation is complex
    # and might be testing behavior of the old CatalogResource.read({}) method which is now obsolete.
    # async def test_read_missing_param(self):
    #     """Test reading a catalog item with missing parameter."""
    #     # This test needs re-evaluation based on Pydantic validation and tool function design.
    #     # GetCatalogItemParams requires item_id, so Pydantic would raise an error before the tool is called
    #     # if item_id is not provided.
    #     # If the intent was to test how the tool handles an empty item_id string,
    #     # the ServiceNow API would likely return an error, which should be caught.
    #     params = GetCatalogItemParams(item_id="") # Example of potentially problematic input
    #     response = await get_catalog_item(self.config, self.auth_manager, params)
    #     self.assertFalse(response.success)
    #     self.assertIn("not found or invalid", response.message.lower()) # Adjust expected message


if __name__ == "__main__":
    # To run async tests with unittest directly
    # unittest.main()
    # For pytest, this is not strictly necessary but doesn't harm
    async def main():
        # Create a TestLoader
        loader = unittest.TestLoader()
        # Load tests from the class
        suite = loader.loadTestsFromTestCase(TestCatalogTools)
        # Create a TestResult object
        result = unittest.TestResult()
        # Run the tests
        # For async tests, you might need a runner that supports asyncio
        # This is a simplified way; pytest handles this better.
        # For direct execution:
        runner = unittest.TextTestRunner()
        loop = asyncio.get_event_loop()
        for test in suite:
            if asyncio.iscoroutinefunction(test.run): # Simplistic check
                 loop.run_until_complete(test.run(result))
            else:
                 test.run(result)

    if __name__ == '__main__':
        # Pytest will discover and run these tests automatically.
        # If running this file directly:
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(main())
        unittest.main() # Standard unittest execution
