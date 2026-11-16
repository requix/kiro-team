"""Database utilities."""

# Mock database
USERS_DB = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
}


def query_user(user_id: int) -> dict | None:
    """Query user from database."""
    return USERS_DB.get(user_id)


def query_all_users() -> list:
    """Query all users."""
    return list(USERS_DB.values())
