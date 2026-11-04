"""Data processor - needs caching added."""

import time
from typing import Any, Callable


class DataProcessor:
    """Processes data from external sources."""
    
    def __init__(self, fetcher: Callable[[], Any]):
        """
        Args:
            fetcher: Function that fetches fresh data (simulates API call)
        """
        self.fetcher = fetcher
        self._fetch_count = 0
    
    def get_data(self) -> Any:
        """Get data - currently fetches every time (no caching)."""
        self._fetch_count += 1
        return self.fetcher()
    
    @property
    def fetch_count(self) -> int:
        """Number of times fetcher was called."""
        return self._fetch_count


# TODO: Add a TimedCache class that:
# - Caches results for a configurable TTL (default 60 seconds)
# - Is thread-safe for concurrent access
# - Refreshes data after TTL expires
