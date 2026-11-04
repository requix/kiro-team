"""Tests for helper utilities."""

import pytest
from src.utils.helpers import format_user_display, get_user_email


def test_format_user_display_existing():
    """Test formatting existing user."""
    result = format_user_display(1)
    assert result == "Alice <alice@example.com>"


def test_format_user_display_nonexistent():
    """Test formatting non-existent user."""
    result = format_user_display(999)
    assert result == "Unknown User"


def test_get_user_email_existing():
    """Test getting email for existing user."""
    email = get_user_email(1)
    assert email == "alice@example.com"


def test_get_user_email_nonexistent():
    """Test getting email for non-existent user."""
    email = get_user_email(999)
    assert email is None
