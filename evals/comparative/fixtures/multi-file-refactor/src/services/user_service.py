"""User service layer."""

from src.utils.database import query_user


def get_user_data(user_id: int) -> dict | None:
    """Fetch user data from the database.
    
    Args:
        user_id: The user's ID
        
    Returns:
        User data dict or None if not found
    """
    return query_user(user_id)


def create_user(name: str, email: str) -> dict:
    """Create a new user."""
    return {"id": 1, "name": name, "email": email}
