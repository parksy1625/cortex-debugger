"""Validation shared by CLI, API, and model adapters."""

from __future__ import annotations


def validate_pair_lengths(clean_length: int, corrupted_length: int, *, max_tokens: int = 128) -> None:
    if not (0 < clean_length <= max_tokens and 0 < corrupted_length <= max_tokens):
        raise ValueError(f"Tokenized prompts must contain 1–{max_tokens} tokens")
    if clean_length != corrupted_length:
        raise ValueError("v0.1 requires equal tokenized prompt lengths")


def validate_patch_coordinate(layer: int, token_index: int, *, n_layers: int, n_tokens: int) -> None:
    if not 0 <= layer < n_layers:
        raise ValueError(f"layer must be between 0 and {n_layers - 1}")
    if not 0 <= token_index < n_tokens:
        raise ValueError(f"token_index must be between 0 and {n_tokens - 1}")
