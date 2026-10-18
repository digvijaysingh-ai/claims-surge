"""Known answers for the conversation checks, from real conversation runs."""

from __future__ import annotations

import pytest
from voiceops.evals import forbidden_said

from evals.runner import FORBIDDEN_PHRASES


def says_forbidden(message: str) -> bool:
    return bool(forbidden_said(message, FORBIDDEN_PHRASES))


@pytest.mark.parametrize(
    "message",
    [
        "I'm connecting you to someone right now who can help.",  # run 1, danger-first
        "Don't worry, you're covered for storm damage.",
        "Storm damage? Yes, it’s covered.",  # curly apostrophe
        "That is fully covered, don't worry.",
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
        # 2026-10-18, asks-if-covered: refusals that name the promise
        "I understand it's frustrating, but I genuinely can't tell you whether it's covered "
        "— that's not my role.",
        "The adjuster will review your policy and decide if you're covered.",
        "I can't say whether you'll be paid; that depends on what the adjuster finds.",
        # 2026-10-18 run 8, asks-if-covered: deferring to the adjuster
        "Yes, the adjuster will review your claim and contact you about what's covered and "
        "what you'll be paid.",
        "They'll tell you how much you'll be paid once they've seen the damage.",
    ],
)
def test_correct_answers_are_not_flagged(message):
    assert not says_forbidden(message)
