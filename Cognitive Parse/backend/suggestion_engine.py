from __future__ import annotations

import difflib
import re
from typing import List, Optional

KEYWORDS = [
    "if",
    "elif",
    "else",
    "for",
    "while",
    "print",
    "def",
    "return",
    "in",
    "class",
    "try",
    "except",
    "finally",
    "with",
    "async",
    "await",
    "match",
    "case",
    "lambda",
]
COMMON_SYMBOLS = [":", "(", ")", "[", "]", "{", "}", "=", "+", "-", "*", "/", ",", "."]
BLOCK_KEYWORDS = {
    "if",
    "elif",
    "else",
    "for",
    "while",
    "def",
    "class",
    "try",
    "except",
    "finally",
    "with",
    "match",
    "case",
}


def _keyword_typo_candidates(line_text: str) -> List[str]:
    candidates: List[str] = []
    for word in re.findall(r"[A-Za-z_][A-Za-z_0-9]*", line_text):
        lower = word.lower()
        if lower in KEYWORDS:
            continue
        matches = difflib.get_close_matches(lower, KEYWORDS, n=1, cutoff=0.75)
        if matches:
            candidates.append(f"Replace '{word}' with keyword '{matches[0]}'.")
    return candidates


def _missing_colon_candidate(line_text: str) -> Optional[str]:
    stripped = line_text.strip()
    if not stripped:
        return None
    first = stripped.split()[0].rstrip("(").lower()
    if first in BLOCK_KEYWORDS and not stripped.endswith(":"):
        return f"Add ':' at the end of the '{first}' statement."
    return None


def suggest(token: Optional[str], message: str = "", line_text: str = "") -> str:
    token = (token or "").strip()
    msg = message.lower()
    line_text = (line_text or "").rstrip("\n")
    suggestions: List[str] = []

    if "indent" in msg or "unindent" in msg:
        suggestions.append("Fix indentation to match the surrounding block (typically 4 spaces).")

    if "unterminated" in msg or "eof" in msg:
        suggestions.append("Complete the unfinished string, expression, or block before running again.")

    if "parenthes" in msg or "bracket" in msg or "brace" in msg:
        suggestions.append("Balance all delimiters: (), [], and {}.")

    if "expected ':'" in msg:
        suggestions.append("Add ':' at the end of the current block statement.")

    if "invalid syntax" in msg and line_text:
        colon_fix = _missing_colon_candidate(line_text)
        if colon_fix:
            suggestions.append(colon_fix)

    if token in COMMON_SYMBOLS:
        suggestions.append(f"Review usage near '{token}' and ensure surrounding syntax is valid.")

    if token.isalpha():
        matches = difflib.get_close_matches(token.lower(), KEYWORDS, n=1, cutoff=0.7)
        if matches:
            suggestions.append(f"Did you mean '{matches[0]}'?")

    if line_text:
        suggestions.extend(_keyword_typo_candidates(line_text))

    if not suggestions:
        suggestions.append(
            "Check the reported line and the previous line; Python syntax errors often originate just before the highlighted point."
        )

    deduped: List[str] = []
    seen = set()
    for item in suggestions:
        if item not in seen:
            deduped.append(item)
            seen.add(item)

    return "Possible fixes: " + " ".join(deduped[:3])
