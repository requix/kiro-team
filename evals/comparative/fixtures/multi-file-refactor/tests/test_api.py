"""Tests for API endpoints."""

import pytest
from src.api.users import get_user_endpoint, list_users_endpoint


def test_get_user_endpoint_existing():
    """Test getting existing user via API."""
    result = get_user_endpoint(1)
    assert "user" in result
    assert result["user"]["name"] == "Alice"


def test_get_user_endpoint_nonexistent():
    """Test getting non-existent user via API."""
    result = get_user_endpoint(999)
    assert "error" in result
    assert result["error"] == "User not found"


def test_list_users_endpoint():
    """Test listing users."""
    result = list_users_endpoint()
    assert "users" in result
