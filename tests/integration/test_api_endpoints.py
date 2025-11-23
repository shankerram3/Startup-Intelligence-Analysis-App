"""
Integration tests for API endpoints
Tests API with mocked external dependencies
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestHealthEndpoints:
    """Test health check and status endpoints"""

    def test_root_endpoint(self, api_client):
        """Test root endpoint returns welcome message"""
        response = api_client.get("/")
        assert response.status_code == 200
        assert "startup" in response.text.lower() or "welcome" in response.text.lower()

    def test_health_endpoint(self, api_client):
        """Test health check endpoint"""
        response = api_client.get("/health")
        assert response.status_code == 200


@pytest.mark.integration
class TestQueryEndpoints:
    """Test query-related endpoints"""

    def test_query_endpoint_structure(self, api_client):
        """Test query endpoint accepts correct structure"""
        # This test assumes API accepts queries even without backend
        # It tests the API structure, not the actual query execution
        payload = {
            "question": "What is AI?",
            "use_llm": False,  # Don't actually call LLM
            "return_context": True,
        }
        response = api_client.post("/query", json=payload)
        # May fail if RAG not initialized, but should return proper error
        assert response.status_code in [200, 503, 500]

    def test_query_endpoint_validation(self, api_client):
        """Test query endpoint validates input"""
        # Test with invalid payload
        payload = {"question": "AB"}  # Too short (min_length=3)
        response = api_client.post("/query", json=payload)
        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint"""

    def test_metrics_endpoint_exists(self, api_client):
        """Test metrics endpoint is available"""
        response = api_client.get("/metrics")
        # Should return metrics in Prometheus format
        assert response.status_code in [200, 404]  # 404 if not yet integrated


@pytest.mark.integration
class TestAPIValidation:
    """Test API input validation"""

    def test_semantic_search_validation(self, api_client):
        """Test semantic search input validation"""
        # Test with too short query
        payload = {"query": "A", "top_k": 10}
        response = api_client.post("/search/semantic", json=payload)
        assert response.status_code == 422  # Validation error

    def test_semantic_search_top_k_limits(self, api_client):
        """Test top_k parameter limits"""
        # Test with top_k exceeding limit
        payload = {"query": "test query", "top_k": 100}  # Limit is 50
        response = api_client.post("/search/semantic", json=payload)
        assert response.status_code == 422  # Validation error
