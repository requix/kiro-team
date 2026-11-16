"""Counter module with an intentional off-by-one bug."""


def count_items(items: list) -> int:
    """Count the number of items in a list.
    
    Args:
        items: List of items to count
        
    Returns:
        Number of items
    """
    # BUG: Returns n+1 instead of n
    return len(items) + 1


def main():
    sample = [1, 2, 3, 4, 5]
    print(f"Count: {count_items(sample)}")


if __name__ == "__main__":
    main()
