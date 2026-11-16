"""Tests for counter module."""

import pytest
from src.counter import count_items


def test_count_items_basic():
    """Test basic counting."""
    assert count_items([1, 2, 3]) == 3


def test_count_items_empty():
    """Test empty list."""
    assert count_items([]) == 0


def test_count_items_single():
    """Test single item."""
    assert count_items(["a"]) == 1


def test_count_items_strings():
    """Test with strings."""
    assert count_items(["apple", "banana", "cherry"]) == 3
