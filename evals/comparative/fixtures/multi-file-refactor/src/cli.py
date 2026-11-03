"""Command-line interface."""

from src.services.user_service import get_user_data


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: cli.py <user_id>")
        return
    
    user_id = int(sys.argv[1])
    user = get_user_data(user_id)
    
    if user:
        print(f"User: {user['name']} ({user['email']})")
    else:
        print("User not found")


if __name__ == "__main__":
    main()
