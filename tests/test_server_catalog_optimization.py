"""
Tests for the ServiceNow MCP server integration with catalog optimization tools.
"""

import pytest
from unittest.mock import MagicMock, patch

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.catalog_optimization import (
    OptimizationRecommendationsParams,
    UpdateCatalogItemParams,
    get_optimization_recommendations,
    update_catalog_item,
)
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig


class TestCatalogOptimizationToolParameters:
    """Test cases for the catalog optimization tool parameters."""

    def test_tool_parameter_classes(self):
        """Test that the parameter classes for the tools are properly defined."""
        # Test OptimizationRecommendationsParams
        params = OptimizationRecommendationsParams(
            recommendation_types=["inactive_items", "low_usage"],
            category_id="hardware"
        )
        assert params.recommendation_types == ["inactive_items", "low_usage"]
        assert params.category_id == "hardware"

        # Test with default values
        params = OptimizationRecommendationsParams(
            recommendation_types=["inactive_items"]
        )
        assert params.recommendation_types == ["inactive_items"]
        assert params.category_id is None

        # Test UpdateCatalogItemParams
        params = UpdateCatalogItemParams(
            item_id="item1",
            name="Updated Laptop",
            short_description="High-performance laptop",
            description="Detailed description of the laptop",
            category="hardware",
            price="1099.99",
            active=True,
            order=100
        )
        assert params.item_id == "item1"
        assert params.name == "Updated Laptop"
        assert params.short_description == "High-performance laptop"
        assert params.description == "Detailed description of the laptop"
        assert params.category == "hardware"
        assert params.price == "1099.99"
        assert params.active
        assert params.order == 100

        # Test with only required parameters
        params = UpdateCatalogItemParams(
            item_id="item1"
        )
        assert params.item_id == "item1"
        assert params.name is None
        assert params.short_description is None
        assert params.description is None
        assert params.category is None
        assert params.price is None
        assert params.active is None
        assert params.order is None


if __name__ == "__main__":
    pytest.main([__file__]) 