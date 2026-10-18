"""Tests for the keyword role-inference heuristic (labeling/rules.py)."""

import pytest

from labeling.rules import infer_role


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Main Title", "headline"),
        ("Section heading", "headline"),
        ("Brand Logo", "logo"),
        ("Shop now button", "cta"),
        ("Register", "cta"),
    ],
)
def test_matches_keywords_case_insensitively(name: str, expected: str) -> None:
    assert infer_role(name) == expected
    assert infer_role(name.upper()) == expected


def test_unmatched_and_empty_names_are_unknown() -> None:
    assert infer_role("decorative swoosh") == "unknown"
    assert infer_role("") == "unknown"
    assert infer_role(None) == "unknown"


def test_first_matching_role_wins_when_keywords_collide() -> None:
    # "title" (headline) is checked before "logo"; document the precedence.
    assert infer_role("Title logo lockup") == "headline"
