"""
Shared pytest fixtures for BC-RAO backend tests.

Provides mock Supabase client, mock Redis client, FastAPI test client,
and helper fixtures for creating test data.
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Any, Dict, List
from uuid import uuid4


@pytest.fixture
def mock_supabase_response():
    """Factory for creating mock Supabase responses."""
    def _create_response(data: List[Dict[str, Any]] = None, count: int = None):
        mock_response = Mock()
        mock_response.data = data if data is not None else []
        mock_response.count = count if count is not None else len(mock_response.data)
        return mock_response
    return _create_response


@pytest.fixture
def mock_supabase(mock_supabase_response):
    """
    Mock Supabase client with configurable table responses.

    Usage:
        mock_supabase.set_table_data("campaigns", [{"id": "123", "name": "Test"}])
        mock_supabase.table("campaigns").select("*").execute()
        # Returns mock response with data
    """
    class MockSupabaseClient:
        def __init__(self):
            self._table_data = {}
            self._response_factory = mock_supabase_response

        def set_table_data(self, table_name: str, data: List[Dict[str, Any]]):
            """Set mock data for a specific table."""
            self._table_data[table_name] = data

        def table(self, table_name: str):
            """Return mock table query builder."""
            mock_table = Mock()
            mock_table._table_name = table_name
            mock_table._filters = {}
            mock_table._data = self._table_data.get(table_name, [])

            def select(columns="*", count=None):
                mock_table._count = count
                return mock_table

            def eq(field, value):
                # Filter data based on field=value
                filtered = [
                    row for row in mock_table._data
                    if row.get(field) == value
                ]
                mock_table._data = filtered
                return mock_table

            def neq(field, value):
                filtered = [
                    row for row in mock_table._data
                    if row.get(field) != value
                ]
                mock_table._data = filtered
                return mock_table

            def gte(field, value):
                filtered = [
                    row for row in mock_table._data
                    if row.get(field) is not None and row.get(field) >= value
                ]
                mock_table._data = filtered
                return mock_table

            def lte(field, value):
                filtered = [
                    row for row in mock_table._data
                    if row.get(field) is not None and row.get(field) <= value
                ]
                mock_table._data = filtered
                return mock_table

            def order(field, desc=False):
                reverse = desc
                try:
                    mock_table._data = sorted(
                        mock_table._data,
                        key=lambda x: x.get(field, ""),
                        reverse=reverse
                    )
                except:
                    pass
                return mock_table

            def limit(n):
                mock_table._data = mock_table._data[:n]
                return mock_table

            def execute():
                return self._response_factory(mock_table._data, len(mock_table._data))

            def insert(data):
                # Mock insert - add id if not present
                if isinstance(data, dict):
                    data["id"] = data.get("id", str(uuid4()))
                    mock_table._insert_data = [data]
                elif isinstance(data, list):
                    for item in data:
                        item["id"] = item.get("id", str(uuid4()))
                    mock_table._insert_data = data
                return mock_table

            def update(data):
                mock_table._update_data = data
                return mock_table

            def upsert(data, on_conflict=None, ignore_duplicates=False):
                if isinstance(data, dict):
                    data["id"] = data.get("id", str(uuid4()))
                    mock_table._insert_data = [data]
                elif isinstance(data, list):
                    for item in data:
                        item["id"] = item.get("id", str(uuid4()))
                    mock_table._insert_data = data
                return mock_table

            def delete():
                return mock_table

            # Attach methods to mock_table
            mock_table.select = select
            mock_table.eq = eq
            mock_table.neq = neq
            mock_table.gte = gte
            mock_table.lte = lte
            mock_table.order = order
            mock_table.limit = limit
            mock_table.execute = execute
            mock_table.insert = insert
            mock_table.update = update
            mock_table.upsert = upsert
            mock_table.delete = delete

            # For insert/update operations
            execute_with_insert = lambda: self._response_factory(
                getattr(mock_table, "_insert_data", []) or
                getattr(mock_table, "_update_data", []) or
                mock_table._data
            )
            mock_table.execute = execute_with_insert

            return mock_table

    return MockSupabaseClient()


@pytest.fixture
def mock_redis():
    """
    Mock Redis client for testing task state management.

    Usage:
        mock_redis.set("key", "value")
        assert mock_redis.get("key") == "value"
    """
    class MockRedis:
        def __init__(self):
            self._data = {}

        def set(self, key: str, value: str, ex: int = None):
            self._data[key] = value
            return True

        def get(self, key: str):
            return self._data.get(key)

        def delete(self, key: str):
            return self._data.pop(key, None) is not None

        def exists(self, key: str):
            return key in self._data

        def keys(self, pattern: str = "*"):
            # Simple pattern matching for testing
            if pattern == "*":
                return list(self._data.keys())
            # Basic wildcard support
            import re
            regex_pattern = pattern.replace("*", ".*")
            return [k for k in self._data.keys() if re.match(regex_pattern, k)]

        def close(self):
            pass

    return MockRedis()


@pytest.fixture
def test_user_id():
    """Generate a consistent test user UUID."""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def test_campaign_id():
    """Generate a consistent test campaign UUID."""
    return "660e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def test_profile_id():
    """Generate a consistent test profile UUID."""
    return "770e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def mock_campaign(test_user_id, test_campaign_id):
    """Create a mock campaign object."""
    return {
        "id": test_campaign_id,
        "user_id": test_user_id,
        "campaign_name": "Test Campaign",
        "target_subreddits": ["python", "programming", "coding"],
        "keywords": ["django", "flask", "fastapi"],
        "brand_voice": "Professional and helpful",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_profile(test_user_id, test_campaign_id, test_profile_id):
    """Create a mock community profile object."""
    return {
        "id": test_profile_id,
        "campaign_id": test_campaign_id,
        "user_id": test_user_id,
        "subreddit": "python",
        "isc_score": 5.0,
        "avg_formality": 0.6,
        "avg_vulnerability": 0.4,
        "rhythm_data": {"avg_sentence_length": 20, "avg_paragraph_length": 3},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_draft(test_user_id, test_campaign_id):
    """Create a mock draft object."""
    return {
        "id": str(uuid4()),
        "campaign_id": test_campaign_id,
        "user_id": test_user_id,
        "subreddit": "python",
        "archetype": "Feedback",
        "title": "Need feedback on my API design",
        "body": "I've been working on a REST API and would love some feedback...",
        "vulnerability_score": 0.75,
        "rhythm_match_score": 0.85,
        "blacklist_violations": 0,
        "model_used": "anthropic/claude-3-5-sonnet",
        "token_count": 500,
        "token_cost_usd": 0.0075,
        "generation_params": {"temperature": 0.7},
        "status": "generated",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_jwt_token(test_user_id):
    """Create a mock JWT token for testing authenticated endpoints."""
    return f"Bearer mock_jwt_token_{test_user_id}"


@pytest.fixture
def forbidden_patterns():
    """Sample forbidden patterns for blacklist validation testing."""
    return [
        {
            "regex_pattern": r"\bclick here\b",
            "category": "Promotional",
            "pattern_description": "Click here CTA"
        },
        {
            "regex_pattern": r"\bbuy now\b",
            "category": "Promotional",
            "pattern_description": "Buy now CTA"
        },
        {
            "regex_pattern": r"\blimited time offer\b",
            "category": "Spam",
            "pattern_description": "Limited time urgency"
        },
        {
            "regex_pattern": r"\bcheck out my\b",
            "category": "Promotional",
            "pattern_description": "Self-promotion phrase"
        }
    ]
