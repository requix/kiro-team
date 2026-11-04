"""Tests for API endpoints."""

import pytest
from src.api import get_items, get_item


def test_get_items_returns_list():
    """get_items returns a list."""
    items = get_items()
    assert isinstance(items, list)
    assert len(items) == 12


def test_get_item_found():
    """get_item returns item when found."""
    item = get_item(1)
    assert item is not None
    assert item["name"] == "Laptop"


def test_get_item_not_found():
    """get_item returns None when not found."""
    item = get_item(999)
    assert item is None


def test_items_have_required_fields():
    """All items have id, name, price."""
    items = get_items()
    for item in items:
        assert "id" in item
        assert "name" in item
        assert "price" in item
