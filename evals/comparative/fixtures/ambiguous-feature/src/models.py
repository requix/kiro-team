"""Data models for item catalog."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Item:
    """An item in the catalog."""
    id: int
    name: str
    description: str
    category: str
    price: float
    created_at: datetime
    tags: list[str]
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "price": self.price,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags,
        }


@dataclass
class Category:
    """A category for items."""
    id: int
    name: str
    parent_id: Optional[int] = None
