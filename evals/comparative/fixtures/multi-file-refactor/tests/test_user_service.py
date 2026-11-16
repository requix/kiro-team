"""Tests for user service."""

import pytest
from src.services.user_service import get_user_data, create_user


def test_get_user_data_existing():
    """Test fetching existing user."""
    user = get_user_data(1)
    assert user is not None
    assert user["name"] == "Alice"
    assert user["email"] == "alice@example.com"


def test_get_user_data_nonexistent():
    """Test fetching non-existent user."""
    user = get_user_data(999)
    assert user is None


def test_create_user():
    """Test creating a user."""
    user = create_user("Charlie", "charlie@example.com")
    assert user["name"] == "Charlie"
    assert user["email"] == "charlie@example.com"
