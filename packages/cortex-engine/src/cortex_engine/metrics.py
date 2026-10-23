"""Experiment scores. These values must never be presented as a full causal explanation."""

from __future__ import annotations

import math


def logit_margin(correct_logit: float, incorrect_logit: float) -> float:
    """Logit(correct next token) - logit(incorrect next token)."""
    if not math.isfinite(correct_logit) or not math.isfinite(incorrect_logit):
        raise ValueError("Logits must be finite")
    return correct_logit - incorrect_logit


def recovery_score(
    clean_score: float, corrupted_score: float, patched_score: float, *, epsilon: float = 1e-8
) -> float | None:
    """Return normalized score recovery; None if the clean/corrupted gap is too small.

    Values are intentionally not clamped: a patch can worsen or overshoot the score.
    """
    if not all(map(math.isfinite, (clean_score, corrupted_score, patched_score))):
        raise ValueError("Scores must be finite")
    if not math.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("epsilon must be positive and finite")
    denominator = clean_score - corrupted_score
    if abs(denominator) <= epsilon:
        return None
    return (patched_score - corrupted_score) / denominator
