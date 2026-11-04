"""Tests for data processor."""

import pytest
from src.processor import DataProcessor


@pytest.fixture
def counter_fetcher():
    """Fetcher that returns incrementing numbers."""
    count = [0]
    def fetch():
        count[0] += 1
        return {"value": count[0]}
    return fetch


def test_processor_fetches_data(counter_fetcher):
    """Basic fetch works."""
    processor = DataProcessor(counter_fetcher)
    result = processor.get_data()
    assert result["value"] == 1


def test_processor_fetches_every_call(counter_fetcher):
    """Without cache, each call fetches fresh data."""
    processor = DataProcessor(counter_fetcher)
    r1 = processor.get_data()
    r2 = processor.get_data()
    r3 = processor.get_data()
    
    assert r1["value"] == 1
    assert r2["value"] == 2
    assert r3["value"] == 3
    assert processor.fetch_count == 3


def test_fetch_count_tracked(counter_fetcher):
    """Fetch count is accurately tracked."""
    processor = DataProcessor(counter_fetcher)
    assert processor.fetch_count == 0
    processor.get_data()
    assert processor.fetch_count == 1
    processor.get_data()
    assert processor.fetch_count == 2
