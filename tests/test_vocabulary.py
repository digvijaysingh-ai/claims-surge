"""Known answers for the conversation checks, from real conversation runs."""

from __future__ import annotations

import pytest

from evals.runner import FORBIDDEN_PHRASES


def says_forbidden(message: str) -> bool:
    return any(p in message.lower() for p in FORBIDDEN_PHRASES)


@pytest.mark.parametrize(
    "message",
    [
        "I'm connecting you to someone right now who can help.",  # run 1, danger-first
        "Don't worry, you're covered for storm damage.",
        "You'll be paid within a week.",
        "I'm transferring you to a claims handler.",
        # run 3, danger-first: an invented capability
        "When you called in, the system should have your number from your account.",
    ],
)
def test_promises_no_tool_keeps_are_caught(message):
    assert says_forbidden(message)


@pytest.mark.parametrize(
    "message",
    [
        # run 2, asks-if-covered: correctly deferring to the adjuster
        "That's the right time to ask all your questions about cover and what will be paid.",
        "A claims handler will call you back as soon as possible.",
        "I can't decide what's covered: that's for the adjuster to assess.",
    ],
)
def test_correct_answers_are_not_flagged(message):
    assert not says_forbidden(message)
