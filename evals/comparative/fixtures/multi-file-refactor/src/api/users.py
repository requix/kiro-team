"""User API endpoints."""

from src.services.user_service import get_user_data


def get_user_endpoint(user_id: int) -> dict:
    """Get user by ID endpoint."""
    user = get_user_data(user_id)
    if not user:
        return {"error": "User not found"}
    return {"user": user}


def list_users_endpoint() -> dict:
    """List all users endpoint."""
    # This endpoint doesn't use get_user_data
    return {"users": []}
