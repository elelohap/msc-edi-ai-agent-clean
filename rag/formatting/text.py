from __future__ import annotations

import re

def normalize_inline_numbered_lists(text: str) -> str:
    """
    Fix common inline numbered lists like:
    'Steps: 1. **A** 2. **B**' -> newlines between items.
    """
    if not text:
        return text
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r":\s*(\d+\.)\s+\*\*", r":\n\n\1 **", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<!\n)\s+(\d+\.)\s+\*\*", r"\n\n\1 **", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def normalize_bullets(text: str) -> str:
    """
    Ensures each '•' bullet starts on its own line (no inline bullets).
    """
    if not text:
        return text

    t = text.replace("\r\n", "\n").replace("\r", "\n")

    # "blah. • item" -> "blah.\n• item"
    t = re.sub(r"([^\n])\s*(•\s+)", r"\1\n\2", t)

    # "• a • b" -> "• a\n• b"
    t = re.sub(r"\s+(•\s+)", r"\n\1", t)

    # Optional: blank line before list block for nicer rendering
    t = re.sub(r"\n(•\s+)", r"\n\n\1", t)

    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def format_answer_text(text: str) -> str:
    """
    One canonical place to normalize answer formatting.
    Call this once, near the final response boundary (router).
    """
    text = normalize_inline_numbered_lists(text)
    text = normalize_bullets(text)
    return text
