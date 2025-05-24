"""
Tests for the knowledge base tools.

This module contains tests for the knowledge base tools in the ServiceNow MCP server.
"""

import pytest
from unittest.mock import MagicMock, patch

import requests

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.knowledge_base import (
    CreateArticleParams,
    CreateCategoryParams,
    CreateKnowledgeBaseParams,
    GetArticleParams,
    ListArticlesParams,
    ListKnowledgeBasesParams,
    PublishArticleParams,
    UpdateArticleParams,
    ListCategoriesParams,
    KnowledgeBaseResponse,
    CategoryResponse,
    ArticleResponse,
    create_article,
    create_category,
    create_knowledge_base,
    get_article,
    list_articles,
    list_knowledge_bases,
    publish_article,
    update_article,
    list_categories,
)
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig


class TestKnowledgeBaseTools:
    """Tests for the knowledge base tools."""

    def setup_method(self):
        """Set up test fixtures."""
        auth_config = AuthConfig(
            type=AuthType.BASIC,
            basic=BasicAuthConfig(
                username="test_user",
                password="test_password"
            )
        )
        self.server_config = ServerConfig(
            instance_url="https://test.service-now.com",
            auth=auth_config,
        )
        self.auth_manager = MagicMock(spec=AuthManager)
        self.auth_manager.get_headers.return_value = {
            "Authorization": "Bearer test",
            "Content-Type": "application/json",
        }

    @patch("servicenow_mcp.tools.knowledge_base.requests.post")
    def test_create_knowledge_base(self, mock_post):
        """Test creating a knowledge base."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "kb001",
                "title": "Test Knowledge Base",
                "description": "Test Description",
                "owner": "admin",
                "kb_managers": "it_managers",
                "workflow_publish": "Knowledge - Instant Publish",
                "workflow_retire": "Knowledge - Instant Retire",
            }
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Call the method
        params = CreateKnowledgeBaseParams(
            title="Test Knowledge Base",
            description="Test Description",
            owner="admin",
            managers="it_managers"
        )
        result = create_knowledge_base(self.server_config, self.auth_manager, params)

        # Verify the result
        assert result.success
        assert "kb001" == result.kb_id
        assert "Test Knowledge Base" == result.kb_name

        # Verify the request
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert f"{self.server_config.api_url}/table/kb_knowledge_base" == args[0]
        assert self.auth_manager.get_headers() == kwargs["headers"]
        assert "Test Knowledge Base" == kwargs["json"]["title"]
        assert "Test Description" == kwargs["json"]["description"]
        assert "admin" == kwargs["json"]["owner"]
        assert "it_managers" == kwargs["json"]["kb_managers"]

    @patch("servicenow_mcp.tools.knowledge_base.requests.post")
    def test_create_category(self, mock_post):
        """Test creating a category."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "cat001",
                "label": "Test Category",
                "description": "Test Category Description",
                "kb_knowledge_base": "kb001",
                "parent": "",
                "active": "true",
            }
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Call the method
        params = CreateCategoryParams(
            title="Test Category",
            description="Test Category Description",
            knowledge_base="kb001",
            active=True
        )
        result = create_category(self.server_config, self.auth_manager, params)

        # Verify the result
        assert result.success
        assert "cat001" == result.category_id
        assert "Test Category" == result.category_name

        # Verify the request
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert f"{self.server_config.api_url}/table/kb_category" == args[0]
        assert self.auth_manager.get_headers() == kwargs["headers"]
        assert "Test Category" == kwargs["json"]["label"]
        assert "Test Category Description" == kwargs["json"]["description"]
        assert "kb001" == kwargs["json"]["kb_knowledge_base"]
        assert "true" == kwargs["json"]["active"]

    @patch("servicenow_mcp.tools.knowledge_base.requests.post")
    def test_create_article(self, mock_post):
        """Test creating a knowledge article."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "art001",
                "short_description": "Test Article",
                "text": "This is a test article content",
                "kb_knowledge_base": "kb001",
                "kb_category": "cat001",
                "article_type": "text",
                "keywords": "test,article,knowledge",
                "workflow_state": "draft",
            }
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Call the method
        params = CreateArticleParams(
            title="Test Article",
            short_description="Test Article",
            text="This is a test article content",
            knowledge_base="kb001",
            category="cat001",
            keywords="test,article,knowledge",
            article_type="text"
        )
        result = create_article(self.server_config, self.auth_manager, params)

        # Verify the result
        assert result.success
        assert "art001" == result.article_id
        assert "Test Article" == result.article_title

        # Verify the request
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert f"{self.server_config.api_url}/table/kb_knowledge" == args[0]
        assert self.auth_manager.get_headers() == kwargs["headers"]
        assert "Test Article" == kwargs["json"]["short_description"]
        assert "This is a test article content" == kwargs["json"]["text"]
        assert "kb001" == kwargs["json"]["kb_knowledge_base"]
        assert "cat001" == kwargs["json"]["kb_category"]
        assert "text" == kwargs["json"]["article_type"]
        assert "test,article,knowledge" == kwargs["json"]["keywords"]

    @patch("servicenow_mcp.tools.knowledge_base.requests.patch")
    def test_update_article(self, mock_patch):
        """Test updating a knowledge article."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "art001",
                "short_description": "Updated Article",
                "text": "This is an updated article content",
                "kb_category": "cat002",
                "keywords": "updated,article,knowledge",
                "workflow_state": "draft",
            }
        }
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        # Call the method
        params = UpdateArticleParams(
            article_id="art001",
            title="Updated Article",
            text="This is an updated article content",
            category="cat002",
            keywords="updated,article,knowledge"
        )
        result = update_article(self.server_config, self.auth_manager, params)

        # Verify the result
        assert result.success
        assert "art001" == result.article_id
        assert "Updated Article" == result.article_title

        # Verify the request
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        assert f"{self.server_config.api_url}/table/kb_knowledge/art001" == args[0]
        assert self.auth_manager.get_headers() == kwargs["headers"]
        assert "Updated Article" == kwargs["json"]["short_description"]
        assert "This is an updated article content" == kwargs["json"]["text"]
        assert "cat002" == kwargs["json"]["kb_category"]
        assert "updated,article,knowledge" == kwargs["json"]["keywords"]

    @patch("servicenow_mcp.tools.knowledge_base.requests.patch")
    def test_publish_article(self, mock_patch):
        """Test publishing a knowledge article."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "art001",
                "short_description": "Test Article",
                "workflow_state": "published",
            }
        }
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        # Call the method
        params = PublishArticleParams(
            article_id="art001",
            workflow_state="published"
        )
        result = publish_article(self.server_config, self.auth_manager, params)

        # Verify the result
        assert result.success
        assert "art001" == result.article_id
        assert "Test Article" == result.article_title
        assert "published" == result.workflow_state

        # Verify the request
        mock_patch.assert_called_once()
        args, kwargs = mock_patch.call_args
        assert f"{self.server_config.api_url}/table/kb_knowledge/art001" == args[0]
        assert self.auth_manager.get_headers() == kwargs["headers"]
        assert "published" == kwargs["json"]["workflow_state"]

    @patch("servicenow_mcp.tools.knowledge_base.requests.get")
    def test_list_articles(self, mock_get):
        """Test listing knowledge articles."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {
                    "sys_id": "art001",
                    "short_description": "Test Article 1",
                    "kb_knowledge_base": {"display_value": "IT Knowledge Base"},
                    "kb_category": {"display_value": "Network"},
                    "workflow_state": {"display_value": "Published"},
                    "sys_created_on": "2023-01-01 00:00:00",
                    "sys_updated_on": "2023-01-02 00:00:00",
                },
                {
                    "sys_id": "art002",
                    "short_description": "Test Article 2",
                    "kb_knowledge_base": {"display_value": "IT Knowledge Base"},
                    "kb_category": {"display_value": "Software"},
                    "workflow_state": {"display_value": "Draft"},
                    "sys_created_on": "2023-01-03 00:00:00",
                    "sys_updated_on": "2023-01-04 00:00:00",
                }
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Call the method
        params = ListArticlesParams(
            limit=10,
            offset=0,
            knowledge_base="kb001",
            category="cat001",
            workflow_state="published",
            query="network"
        )
        result = list_articles(self.server_config, self.auth_manager, params)

        # Verify the result
        assert result["success"]
        assert 2 == len(result["articles"])
        assert "art001" == result["articles"][0]["id"]
        assert "Test Article 1" == result["articles"][0]["title"]
        assert "IT Knowledge Base" == result["articles"][0]["knowledge_base"]
        assert "Network" == result["articles"][0]["category"]
        assert "Published" == result["articles"][0]["workflow_state"]

        # Verify the request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert f"{self.server_config.api_url}/table/kb_knowledge" == args[0]
        assert self.auth_manager.get_headers() == kwargs["headers"]
        assert 10 == kwargs["params"]["sysparm_limit"]
        assert 0 == kwargs["params"]["sysparm_offset"]
        assert "all" == kwargs["params"]["sysparm_display_value"]
        
        # Verify the query syntax contains the correct pattern
        assert "sysparm_query" in kwargs["params"]
        query = kwargs["params"]["sysparm_query"]
        assert "kb_knowledge_base.sys_id=kb001" in query
        assert "kb_category.sys_id=cat001" in query

    @patch("servicenow_mcp.tools.knowledge_base.requests.get")
    def test_get_article(self, mock_get):
        """Test getting a knowledge article."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "sys_id": "art001",
                "short_description": "Test Article",
                "text": "This is a test article content",
                "kb_knowledge_base": {"display_value": "IT Knowledge Base"},
                "kb_category": {"display_value": "Network"},
                "workflow_state": {"display_value": "Published"},
                "sys_created_on": "2023-01-01 00:00:00",
                "sys_updated_on": "2023-01-02 00:00:00",
                "author": {"display_value": "admin"},
                "keywords": "test,article,knowledge",
                "article_type": "text",
                "view_count": "42"
            }
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Call the method
        params = GetArticleParams(article_id="art001")
        result = get_article(self.server_config, self.auth_manager, params)

        # Verify the result
        assert result["success"]
        assert "art001" == result["article"]["id"]
        assert "Test Article" == result["article"]["title"]
        assert "This is a test article content" == result["article"]["text"]
        assert "IT Knowledge Base" == result["article"]["knowledge_base"]
        assert "Network" == result["article"]["category"]
        assert "Published" == result["article"]["workflow_state"]
        assert "admin" == result["article"]["author"]
        assert "test,article,knowledge" == result["article"]["keywords"]
        assert "text" == result["article"]["article_type"]
        assert "42" == result["article"]["views"]

        # Verify the request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert f"{self.server_config.api_url}/table/kb_knowledge/art001" == args[0]
        assert self.auth_manager.get_headers() == kwargs["headers"]
        assert "true" == kwargs["params"]["sysparm_display_value"]

    @patch("servicenow_mcp.tools.knowledge_base.requests.post")
    def test_create_knowledge_base_error(self, mock_post):
        """Test error handling when creating a knowledge base."""
        # Mock error response
        mock_post.side_effect = requests.RequestException("API error")

        # Call the method
        params = CreateKnowledgeBaseParams(title="Test Knowledge Base")
        result = create_knowledge_base(self.server_config, self.auth_manager, params)

        # Verify the result
        assert not result.success
        assert "Failed to create knowledge base" in result.message

    @patch("servicenow_mcp.tools.knowledge_base.requests.get")
    def test_get_article_not_found(self, mock_get):
        """Test getting a non-existent article."""
        # Mock empty response
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": {}}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Call the method
        params = GetArticleParams(article_id="nonexistent")
        result = get_article(self.server_config, self.auth_manager, params)

        # Verify the result
        assert not result["success"]
        assert "not found" in result["message"]

    @patch("servicenow_mcp.tools.knowledge_base.requests.get")
    def test_list_knowledge_bases(self, mock_get):
        """Test listing knowledge bases."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {
                    "sys_id": "kb001",
                    "title": "IT Knowledge Base",
                    "description": "Knowledge base for IT resources",
                    "owner": {"display_value": "admin"},
                    "kb_managers": {"display_value": "it_managers"},
                    "active": "true",
                    "sys_created_on": "2023-01-01 00:00:00",
                    "sys_updated_on": "2023-01-02 00:00:00",
                },
                {
                    "sys_id": "kb002",
                    "title": "HR Knowledge Base",
                    "description": "Knowledge base for HR resources",
                    "owner": {"display_value": "hr_admin"},
                    "kb_managers": {"display_value": "hr_managers"},
                    "active": "true",
                    "sys_created_on": "2023-01-03 00:00:00",
                    "sys_updated_on": "2023-01-04 00:00:00",
                }
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Call the method
        params = ListKnowledgeBasesParams(
            limit=10,
            offset=0,
            active=True,
            query="IT"
        )
        result = list_knowledge_bases(self.server_config, self.auth_manager, params)

        # Verify the result
        assert result["success"]
        assert 2 == len(result["knowledge_bases"])
        assert "kb001" == result["knowledge_bases"][0]["id"]
        assert "IT Knowledge Base" == result["knowledge_bases"][0]["title"]
        assert "Knowledge base for IT resources" == result["knowledge_bases"][0]["description"]
        assert "admin" == result["knowledge_bases"][0]["owner"]
        assert "it_managers" == result["knowledge_bases"][0]["managers"]
        assert result["knowledge_bases"][0]["active"]

        # Verify the request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert f"{self.server_config.api_url}/table/kb_knowledge_base" == args[0]
        assert self.auth_manager.get_headers() == kwargs["headers"]
        assert 10 == kwargs["params"]["sysparm_limit"]
        assert 0 == kwargs["params"]["sysparm_offset"]
        assert "true" == kwargs["params"]["sysparm_display_value"]
        assert "active=true^titleLIKEIT^ORdescriptionLIKEIT" == kwargs["params"]["sysparm_query"]

    @patch("servicenow_mcp.tools.knowledge_base.requests.get")
    def test_list_categories(self, mock_get):
        """Test listing categories in a knowledge base."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {
                    "sys_id": "cat001",
                    "label": "Network Troubleshooting",
                    "description": "Articles for network troubleshooting",
                    "kb_knowledge_base": {"display_value": "IT Knowledge Base"},
                    "parent": {"display_value": ""},
                    "active": "true",
                    "sys_created_on": "2023-01-01 00:00:00",
                    "sys_updated_on": "2023-01-02 00:00:00",
                },
                {
                    "sys_id": "cat002",
                    "label": "Software Setup",
                    "description": "Articles for software installation",
                    "kb_knowledge_base": {"display_value": "IT Knowledge Base"},
                    "parent": {"display_value": ""},
                    "active": "true",
                    "sys_created_on": "2023-01-03 00:00:00",
                    "sys_updated_on": "2023-01-04 00:00:00",
                }
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Call the method
        params = ListCategoriesParams(
            knowledge_base="kb001",
            active=True,
            query="Network"
        )
        result = list_categories(self.server_config, self.auth_manager, params)

        # Verify the result
        assert result["success"]
        assert 2 == len(result["categories"])
        assert "cat001" == result["categories"][0]["id"]
        assert "Network Troubleshooting" == result["categories"][0]["title"]
        assert "Articles for network troubleshooting" == result["categories"][0]["description"]
        assert "IT Knowledge Base" == result["categories"][0]["knowledge_base"]
        assert "" == result["categories"][0]["parent_category"]
        assert result["categories"][0]["active"]

        # Verify the request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert f"{self.server_config.api_url}/table/kb_category" == args[0]
        assert self.auth_manager.get_headers() == kwargs["headers"]
        assert 10 == kwargs["params"]["sysparm_limit"]
        assert 0 == kwargs["params"]["sysparm_offset"]
        assert "all" == kwargs["params"]["sysparm_display_value"]
        
        # Verify the query syntax contains the correct pattern
        assert "sysparm_query" in kwargs["params"]
        query = kwargs["params"]["sysparm_query"]
        assert "kb_knowledge_base.sys_id=kb001" in query
        assert "active=true" in query
        assert "labelLIKENetwork" in query


class TestKnowledgeBaseParams:
    """Tests for the knowledge base parameter classes."""

    def test_create_knowledge_base_params(self):
        """Test CreateKnowledgeBaseParams validation."""
        # Minimal required parameters
        params = CreateKnowledgeBaseParams(title="Test Knowledge Base")
        assert "Test Knowledge Base" == params.title
        assert "Knowledge - Instant Publish" == params.publish_workflow

        # All parameters
        params = CreateKnowledgeBaseParams(
            title="Test Knowledge Base",
            description="Test Description",
            owner="admin",
            managers="it_managers",
            publish_workflow="Custom Workflow",
            retire_workflow="Custom Retire Workflow"
        )
        assert "Test Knowledge Base" == params.title
        assert "Test Description" == params.description
        assert "admin" == params.owner
        assert "it_managers" == params.managers
        assert "Custom Workflow" == params.publish_workflow
        assert "Custom Retire Workflow" == params.retire_workflow

    def test_create_category_params(self):
        """Test CreateCategoryParams validation."""
        # Required parameters
        params = CreateCategoryParams(
            title="Test Category",
            knowledge_base="kb001"
        )
        assert "Test Category" == params.title
        assert "kb001" == params.knowledge_base
        assert params.active

        # All parameters
        params = CreateCategoryParams(
            title="Test Category",
            description="Test Description",
            knowledge_base="kb001",
            parent_category="parent001",
            active=False
        )
        assert "Test Category" == params.title
        assert "Test Description" == params.description
        assert "kb001" == params.knowledge_base
        assert "parent001" == params.parent_category
        assert not params.active

    def test_create_article_params(self):
        """Test CreateArticleParams validation."""
        # Required parameters
        params = CreateArticleParams(
            title="Test Article",
            text="Test content",
            short_description="Test short description",
            knowledge_base="kb001",
            category="cat001"
        )
        assert "Test Article" == params.title
        assert "Test content" == params.text
        assert "Test short description" == params.short_description
        assert "kb001" == params.knowledge_base
        assert "cat001" == params.category
        assert "text" == params.article_type

        # All parameters
        params = CreateArticleParams(
            title="Test Article",
            text="Test content",
            short_description="Test short description",
            knowledge_base="kb001",
            category="cat001",
            keywords="test,article",
            article_type="html"
        )
        assert "Test Article" == params.title
        assert "Test content" == params.text
        assert "Test short description" == params.short_description
        assert "kb001" == params.knowledge_base
        assert "cat001" == params.category
        assert "test,article" == params.keywords
        assert "html" == params.article_type


if __name__ == "__main__":
    pytest.main([__file__]) 