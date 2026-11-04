"""Helper utilities."""

from src.services.user_service import get_user_data


def format_user_display(user_id: int) -> str:
    """Format user for display.
    
    Uses get_user_data to fetch the user first.
    """
    user = get_user_data(user_id)
    if not user:
        return "Unknown User"
    return f"{user['name']} <{user['email']}>"


def get_user_email(user_id: int) -> str | None:
    """Get just the user's email."""
    user = get_user_data(user_id)
    return user.get("email") if user else None
