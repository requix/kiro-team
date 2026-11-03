"""Item catalog management."""

from datetime import datetime
from typing import Optional
from .models import Item, Category


class ItemCatalog:
    """Manages a catalog of items."""
    
    def __init__(self):
        self._items: dict[int, Item] = {}
        self._categories: dict[int, Category] = {}
        self._next_item_id = 1
        self._next_category_id = 1
    
    def add_item(
        self,
        name: str,
        description: str,
        category: str,
        price: float,
        tags: Optional[list[str]] = None,
    ) -> Item:
        """Add a new item to the catalog."""
        item = Item(
            id=self._next_item_id,
            name=name,
            description=description,
            category=category,
            price=price,
            created_at=datetime.now(),
            tags=tags or [],
        )
        self._items[item.id] = item
        self._next_item_id += 1
        return item
    
    def get_item(self, item_id: int) -> Optional[Item]:
        """Get an item by ID."""
        return self._items.get(item_id)
    
    def list_items(self) -> list[Item]:
        """List all items."""
        return list(self._items.values())
    
    def get_items_by_category(self, category: str) -> list[Item]:
        """Get all items in a category."""
        return [item for item in self._items.values() if item.category == category]
    
    def delete_item(self, item_id: int) -> bool:
        """Delete an item. Returns True if deleted."""
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False
    
    def add_category(self, name: str, parent_id: Optional[int] = None) -> Category:
        """Add a new category."""
        category = Category(
            id=self._next_category_id,
            name=name,
            parent_id=parent_id,
        )
        self._categories[category.id] = category
        self._next_category_id += 1
        return category
    
    def list_categories(self) -> list[Category]:
        """List all categories."""
        return list(self._categories.values())
