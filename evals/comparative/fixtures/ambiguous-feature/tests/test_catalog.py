"""Tests for item catalog."""

import pytest
from src.catalog import ItemCatalog


@pytest.fixture
def catalog():
    """Create a catalog with sample data."""
    cat = ItemCatalog()
    cat.add_item("Laptop", "High-performance laptop", "Electronics", 999.99, ["tech", "computer"])
    cat.add_item("Desk Chair", "Ergonomic office chair", "Furniture", 299.99, ["office", "comfort"])
    cat.add_item("Coffee Mug", "Large ceramic mug", "Kitchen", 14.99, ["kitchen", "drinkware"])
    cat.add_item("Keyboard", "Mechanical keyboard", "Electronics", 149.99, ["tech", "computer"])
    cat.add_item("Desk Lamp", "LED desk lamp", "Furniture", 49.99, ["office", "lighting"])
    return cat


def test_add_item(catalog):
    item = catalog.add_item("Test Item", "A test", "Test", 10.00)
    assert item.name == "Test Item"
    assert item.id == 6  # 5 items in fixture + 1


def test_get_item(catalog):
    item = catalog.get_item(1)
    assert item is not None
    assert item.name == "Laptop"


def test_get_item_not_found(catalog):
    item = catalog.get_item(999)
    assert item is None


def test_list_items(catalog):
    items = catalog.list_items()
    assert len(items) == 5


def test_get_items_by_category(catalog):
    electronics = catalog.get_items_by_category("Electronics")
    assert len(electronics) == 2
    assert all(item.category == "Electronics" for item in electronics)


def test_delete_item(catalog):
    assert catalog.delete_item(1) is True
    assert catalog.get_item(1) is None
    assert len(catalog.list_items()) == 4


def test_delete_item_not_found(catalog):
    assert catalog.delete_item(999) is False


def test_add_category(catalog):
    cat = catalog.add_category("New Category")
    assert cat.name == "New Category"
    assert cat.id == 1


def test_item_tags(catalog):
    item = catalog.get_item(1)
    assert "tech" in item.tags
    assert "computer" in item.tags
