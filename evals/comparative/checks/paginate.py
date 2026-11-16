#!/usr/bin/env python3
"""Behavioral checks for the validator-feedback scenario.

Run from the scenario workspace: python3 paginate.py <check>
Exit 0 means the check passed. Any other exit code means it failed.

The task asks for paginate(items, page=1, page_size=10) in src/api.py. Where
the task leaves a choice open (empty list, page out of range, bad input), each
reasonable behavior is accepted: an empty page, clamping, or a ValueError.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

KEYS = {"items", "total_count", "total_pages", "current_page", "has_next", "has_prev"}


def _paginate():
    from src.api import paginate  # noqa: PLC0415

    return paginate


def _items(n: int) -> list[dict]:
    return [{"id": i} for i in range(1, n + 1)]


def check_metadata() -> None:
    r = _paginate()(_items(12), 1, 10)
    missing = KEYS - set(r)
    assert not missing, f"missing keys: {sorted(missing)}"
    assert r["total_count"] == 12, r
    assert r["total_pages"] == 2, r
    assert r["current_page"] == 1, r


def check_page_bounds() -> None:
    paginate = _paginate()
    first = paginate(_items(12), 1, 10)
    last = paginate(_items(12), 2, 10)
    assert [i["id"] for i in first["items"]] == list(range(1, 11)), first
    assert [i["id"] for i in last["items"]] == [11, 12], last
    assert first["has_next"] is True and first["has_prev"] is False, first
    assert last["has_next"] is False and last["has_prev"] is True, last
    exact = paginate(_items(20), 2, 10)
    assert exact["has_next"] is False, f"last full page reports has_next: {exact}"


def check_defaults_and_max() -> None:
    paginate = _paginate()
    r = paginate(_items(25))
    assert r["current_page"] == 1 and len(r["items"]) == 10, f"defaults wrong: {r}"
    big = paginate(_items(250), 1, 500)
    assert len(big["items"]) == 100, f"page_size not capped at 100: {len(big['items'])} items"


def check_empty() -> None:
    r = _paginate()(_items(0), 1, 10)
    assert r["items"] == [], r
    assert r["total_count"] == 0, r
    assert r["total_pages"] in (0, 1), r
    assert r["has_next"] is False and r["has_prev"] is False, r


def check_out_of_range_and_invalid() -> None:
    paginate = _paginate()
    try:
        r = paginate(_items(12), 5, 10)
        assert r["items"] == [] or r["current_page"] == 2, f"page 5 of 2: {r}"
        assert r["has_next"] is False, r
    except ValueError:
        pass
    for page, size in ((0, 10), (-1, 10), (1, 0), (1, -5)):
        try:
            r = paginate(_items(12), page, size)
        except ValueError:
            continue
        assert r["current_page"] >= 1, f"page={page} size={size}: {r}"
        assert 0 < len(r["items"]) <= 100, f"page={page} size={size}: {r}"


CHECKS = {
    "metadata": check_metadata,
    "page-bounds": check_page_bounds,
    "defaults-and-max": check_defaults_and_max,
    "empty": check_empty,
    "out-of-range": check_out_of_range_and_invalid,
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in CHECKS:
        print(f"usage: {sys.argv[0]} {{{','.join(CHECKS)}}}", file=sys.stderr)
        return 2
    try:
        CHECKS[sys.argv[1]]()
    except Exception as exc:
        print(f"FAIL {sys.argv[1]}: {exc!r}")
        return 1
    print(f"PASS {sys.argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
