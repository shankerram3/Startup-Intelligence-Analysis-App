"""
Pytest configuration and shared fixtures
Provides reusable test fixtures for all test suites
"""

import pytest
import os
from typing import Generator, Dict, Any
from unittest.mock import Mock, MagicMock, patch
from neo4j import GraphDatabase
from faker import Faker
import json

# Set test environment variables before importing app modules
os.environ["TESTING"] = "true"
os.environ["CACHE_ENABLED"] = "false"
os.environ["ENABLE_AUTH"] = "false"
os.environ["ENABLE_RATE_LIMITING"] = "false"

fake = Faker()


# =============================================================================
# Session-scoped fixtures (run once per test session)
# =============================================================================


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """
    Test configuration dictionary

    Returns:
        Dictionary with test configuration
    """
    return {
        "neo4j_uri": os.getenv("NEO4J_TEST_URI", "bolt://localhost:7687"),
        "neo4j_user": os.getenv("NEO4J_TEST_USER", "neo4j"),
        "neo4j_password": os.getenv("NEO4J_TEST_PASSWORD", "testpassword"),
        "openai_api_key": os.getenv("OPENAI_API_KEY", "test-fake-key-not-real"),
        "redis_host": os.getenv("REDIS_TEST_HOST", "localhost"),
        "redis_port": int(os.getenv("REDIS_TEST_PORT", "6379")),
    }


# =============================================================================
# Function-scoped fixtures (run for each test)
# =============================================================================


@pytest.fixture
def mock_neo4j_driver():
    """
    Mock Neo4j driver for testing without real database

    Returns:
        Mock Neo4j driver instance

    Example:
        def test_query(mock_neo4j_driver):
            mock_neo4j_driver.session().run.return_value = [{"name": "Test"}]
    """
    driver = MagicMock()
    session = MagicMock()
    result = MagicMock()

    # Configure mock chain
    driver.session.return_value.__enter__.return_value = session
    driver.session.return_value.__exit__.return_value = None
    session.run.return_value = result

    return driver


@pytest.fixture
def mock_openai_client():
    """
    Mock OpenAI client for testing without API calls

    Returns:
        Mock OpenAI client

    Example:
        def test_extraction(mock_openai_client):
            mock_openai_client.chat.completions.create.return_value = mock_response
    """
    client = MagicMock()

    # Mock response structure
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(
        {"entities": [], "relationships": []}
    )
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50

    client.chat.completions.create.return_value = mock_response

    return client


@pytest.fixture
def sample_article() -> Dict[str, Any]:
    """
    Generate a sample article for testing

    Returns:
        Dictionary with article data

    Example:
        def test_processing(sample_article):
            result = process_article(sample_article)
            assert result is not None
    """
    return {
        "id": fake.uuid4(),
        "title": fake.sentence(),
        "content": fake.text(max_nb_chars=1000),
        "url": fake.url(),
        "published_date": fake.date_time_this_year().isoformat(),
        "author": fake.name(),
        "source": "TechCrunch",
        "metadata": {"word_count": 500, "reading_time": 3},
    }


@pytest.fixture
def sample_entities() -> list[Dict[str, Any]]:
    """
    Generate sample entities for testing

    Returns:
        List of entity dictionaries

    Example:
        def test_graph_builder(sample_entities):
            builder.add_entities(sample_entities)
    """
    return [
        {
            "name": fake.company(),
            "type": "Company",
            "description": fake.catch_phrase(),
            "properties": {"founded": "2020", "industry": "AI"},
        },
        {
            "name": fake.name(),
            "type": "Person",
            "description": fake.job(),
            "properties": {"role": "CEO"},
        },
        {
            "name": fake.company(),
            "type": "Investor",
            "description": "Venture Capital",
            "properties": {},
        },
    ]


@pytest.fixture
def sample_relationships() -> list[Dict[str, Any]]:
    """
    Generate sample relationships for testing

    Returns:
        List of relationship dictionaries
    """
    return [
        {
            "source": "Company A",
            "target": "Person X",
            "type": "FOUNDED_BY",
            "strength": 0.95,
            "context": "Founded in 2020",
        },
        {
            "source": "Company A",
            "target": "Investor Y",
            "type": "FUNDED_BY",
            "strength": 0.90,
            "context": "Series A funding",
        },
    ]


@pytest.fixture
def mock_cache():
    """
    Mock cache manager for testing

    Returns:
        Mock cache instance
    """
    cache = MagicMock()
    cache.enabled = False
    cache.get.return_value = None
    cache.set.return_value = True
    cache.delete.return_value = True
    cache.exists.return_value = False

    return cache


@pytest.fixture
def mock_logger():
    """
    Mock logger for testing

    Returns:
        Mock structlog logger
    """
    logger = MagicMock()
    return logger


# =============================================================================
# Real connection fixtures (for integration tests)
# =============================================================================


@pytest.fixture(scope="session")
@pytest.mark.requires_neo4j
def neo4j_driver(test_config):
    """
    Real Neo4j driver for integration tests

    Yields:
        Neo4j driver instance

    Note:
        Requires NEO4J_TEST_URI environment variable
        Only use with @pytest.mark.requires_neo4j
    """
    if not os.getenv("NEO4J_TEST_URI"):
        pytest.skip("NEO4J_TEST_URI not set, skipping integration test")

    driver = GraphDatabase.driver(
        test_config["neo4j_uri"],
        auth=(test_config["neo4j_user"], test_config["neo4j_password"]),
    )

    # Test connection
    try:
        driver.verify_connectivity()
    except Exception as e:
        pytest.skip(f"Cannot connect to Neo4j: {e}")

    yield driver

    driver.close()


@pytest.fixture
@pytest.mark.requires_neo4j
def neo4j_session(neo4j_driver):
    """
    Neo4j session with automatic cleanup

    Yields:
        Neo4j session

    Note:
        Automatically cleans up test data after test
    """
    with neo4j_driver.session() as session:
        yield session

        # Cleanup: Delete all test data
        session.run("MATCH (n:TestEntity) DETACH DELETE n")


# =============================================================================
# API testing fixtures
# =============================================================================


@pytest.fixture
def api_client():
    """
    FastAPI test client

    Returns:
        TestClient instance

    Example:
        def test_endpoint(api_client):
            response = api_client.get("/health")
            assert response.status_code == 200
    """
    from fastapi.testclient import TestClient

    # Import here to avoid circular imports
    from api import app

    return TestClient(app)


@pytest.fixture
def auth_headers():
    """
    Generate authentication headers for testing

    Returns:
        Dictionary with Authorization header

    Example:
        def test_protected_endpoint(api_client, auth_headers):
            response = api_client.get("/protected", headers=auth_headers)
    """
    from utils.security import generate_test_token

    token = generate_test_token("test_user", "admin")
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Parametrized test data
# =============================================================================


@pytest.fixture(params=["Company", "Person", "Investor", "Technology", "Product"])
def entity_type(request):
    """
    Parametrized fixture for different entity types

    Usage:
        def test_entity_processing(entity_type):
            # Test will run once for each entity type
            process_entity(entity_type)
    """
    return request.param


@pytest.fixture(params=["FOUNDED_BY", "FUNDED_BY", "WORKS_AT", "PARTNERS_WITH"])
def relationship_type(request):
    """
    Parametrized fixture for different relationship types
    """
    return request.param


# =============================================================================
# Helper functions for tests
# =============================================================================


def create_test_article(
    title: str = None, content: str = None, **kwargs
) -> Dict[str, Any]:
    """
    Helper function to create test articles with custom fields

    Args:
        title: Article title
        content: Article content
        **kwargs: Additional fields

    Returns:
        Article dictionary

    Example:
        article = create_test_article(title="Test Article", source="Custom")
    """
    article = {
        "id": fake.uuid4(),
        "title": title or fake.sentence(),
        "content": content or fake.text(max_nb_chars=500),
        "url": fake.url(),
        "published_date": fake.date_time_this_year().isoformat(),
        "author": fake.name(),
        "source": "TechCrunch",
    }
    article.update(kwargs)
    return article


def assert_valid_entity(entity: Dict[str, Any]):
    """
    Assert that entity has required fields

    Args:
        entity: Entity dictionary to validate

    Example:
        result = extract_entities(text)
        for entity in result:
            assert_valid_entity(entity)
    """
    assert "name" in entity, "Entity missing 'name' field"
    assert "type" in entity, "Entity missing 'type' field"
    assert entity["type"] in [
        "Company",
        "Person",
        "Investor",
        "Technology",
        "Product",
        "FundingRound",
        "Location",
        "Event",
    ], f"Invalid entity type: {entity['type']}"


def assert_valid_relationship(relationship: Dict[str, Any]):
    """
    Assert that relationship has required fields

    Args:
        relationship: Relationship dictionary to validate
    """
    assert "source" in relationship, "Relationship missing 'source' field"
    assert "target" in relationship, "Relationship missing 'target' field"
    assert "type" in relationship, "Relationship missing 'type' field"
    assert "strength" in relationship, "Relationship missing 'strength' field"
    assert 0.0 <= relationship["strength"] <= 1.0, "Invalid strength value"


# =============================================================================
# Autouse fixtures (automatically used by all tests)
# =============================================================================


@pytest.fixture(autouse=True)
def reset_environment():
    """
    Reset environment variables before each test

    This ensures tests don't interfere with each other
    """
    # Store original environment
    original_env = os.environ.copy()

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def mock_expensive_operations(monkeypatch):
    """
    Mock expensive operations in test mode

    This prevents tests from making real API calls or expensive computations
    """
    # Skip if integration test
    if "integration" in str(pytest.current_test_name):
        return

    # Mock OpenAI calls
    monkeypatch.setenv("OPENAI_API_KEY", "test-fake-key-not-real")

    # Mock sentence transformers (prevent model download)
    def mock_encode(*args, **kwargs):
        import numpy as np

        return np.random.rand(384)  # Fake embedding

    try:
        from sentence_transformers import SentenceTransformer

        monkeypatch.setattr(SentenceTransformer, "encode", mock_encode)
    except ImportError:
        pass


# =============================================================================
# Test markers and skip conditions
# =============================================================================


def pytest_configure(config):
    """Add custom markers to pytest"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers and skip conditions
    """
    for item in items:
        # Add unit marker to tests in unit/ directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Add integration marker to tests in integration/ directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add e2e marker to tests in e2e/ directory
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Skip tests requiring Neo4j if not configured
        if "requires_neo4j" in item.keywords and not os.getenv("NEO4J_TEST_URI"):
            item.add_marker(pytest.mark.skip(reason="NEO4J_TEST_URI not configured"))

        # Skip tests requiring OpenAI if not configured
        if "requires_openai" in item.keywords and not os.getenv("OPENAI_API_KEY"):
            item.add_marker(pytest.mark.skip(reason="OPENAI_API_KEY not configured"))
