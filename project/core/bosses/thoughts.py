"""Presentation helpers for boss thought cards."""

import re


def format_boss_thoughts(thoughts):
    """Split authored identifiers into emphasis spans without trusting HTML."""
    formatted = []
    for thought in thoughts:
        terms = sorted(set(thought.get("identifiers", [])), key=len, reverse=True)
        pattern = r"(?<!\w)(?:" + "|".join(re.escape(term) for term in terms) + r")(?!\w)"
        parts, start = [], 0
        for match in re.finditer(pattern, thought["text"]) if terms else []:
            parts.append({"text": thought["text"][start:match.start()], "bold": False})
            parts.append({"text": match.group(), "bold": True})
            start = match.end()
        parts.append({"text": thought["text"][start:], "bold": False})
        formatted.append({**thought, "parts": parts})
    return formatted
