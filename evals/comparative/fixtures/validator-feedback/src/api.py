"""API endpoints for item management."""

from typing import Any


def get_items() -> list[dict]:
    """Get all items from the database (simulated)."""
    return [
        {"id": 1, "name": "Laptop", "price": 999.99},
        {"id": 2, "name": "Mouse", "price": 29.99},
        {"id": 3, "name": "Keyboard", "price": 79.99},
        {"id": 4, "name": "Monitor", "price": 299.99},
        {"id": 5, "name": "Headphones", "price": 149.99},
        {"id": 6, "name": "Webcam", "price": 89.99},
        {"id": 7, "name": "USB Hub", "price": 39.99},
        {"id": 8, "name": "Mousepad", "price": 19.99},
        {"id": 9, "name": "Cable", "price": 9.99},
        {"id": 10, "name": "Stand", "price": 49.99},
        {"id": 11, "name": "Dock", "price": 199.99},
        {"id": 12, "name": "Speaker", "price": 129.99},
    ]


def get_item(item_id: int) -> dict | None:
    """Get a single item by ID."""
    items = get_items()
    for item in items:
        if item["id"] == item_id:
            return item
    return None


# TODO: Add paginate(items, page, page_size) function that returns:
# {
#     "items": [...],
#     "total_count": int,
#     "total_pages": int,
#     "current_page": int,
#     "has_next": bool,
#     "has_prev": bool
# }
#
# Requirements:
# - page is 1-indexed (first page is 1, not 0)
# - page_size defaults to 10, max is 100
# - Handle edge cases properly
