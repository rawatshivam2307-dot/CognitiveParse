from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

KEYWORDS = {
    "if",
    "else",
    "while",
    "for",
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
}


@dataclass
class ErrorDetails:
    category: str
    explanation: str


def classify_error(message: str, token: Optional[str] = None) -> ErrorDetails:
    text = (message or "").lower()
    token = (token or "").strip()

    if "indent" in text or "unindent" in text:
        return ErrorDetails(
            category="Indentation Error",
            explanation="Indentation is inconsistent or block structure is misaligned.",
        )

    if "parenthes" in text or "bracket" in text or "brace" in text:
        return ErrorDetails(
            category="Unmatched Delimiter",
            explanation="A delimiter such as (), [], or {} is unmatched or misplaced.",
        )

    if "eof" in text or "unterminated" in text:
        return ErrorDetails(
            category="Incomplete Statement",
            explanation="The statement appears unfinished (for example an open string or expression).",
        )

    if "expected" in text or "missing" in text or "invalid syntax" in text:
        return ErrorDetails(
            category="Missing or Invalid Syntax",
            explanation="Python expected different syntax at this location.",
        )

    if token and token.isalpha() and token.lower() not in KEYWORDS:
        return ErrorDetails(
            category="Potential Keyword/Identifier Issue",
            explanation="Check this token for misspelling or incorrect placement.",
        )

    return ErrorDetails(
        category="General Syntax Error",
        explanation="The code contains a Python syntax issue near the reported location.",
    )


def to_dict(details: ErrorDetails) -> Dict[str, str]:
    return {"category": details.category, "explanation": details.explanation}
