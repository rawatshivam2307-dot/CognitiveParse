from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ParseResult:
    valid: bool
    ast: Dict[str, Any]
    message: str


class CognitiveParser:
    """Parser wrapper that uses Python's native parser.

    This supports broad Python syntax coverage for the interpreter version
    currently running this application.
    """

    @staticmethod
    def _count_nodes(tree: ast.AST) -> int:
        return sum(1 for _ in ast.walk(tree))

    def parse_code(self, code: str) -> ParseResult:
        source = code if code.endswith("\n") else f"{code}\n"
        tree = ast.parse(source, mode="exec")
        node_count = self._count_nodes(tree)

        ast_payload: Dict[str, Any] = {
            "root": type(tree).__name__,
            "node_count": node_count,
            "tree": ast.dump(tree, include_attributes=False, indent=2),
        }
        return ParseResult(valid=True, ast=ast_payload, message="Valid Python syntax")


cognitive_parser = CognitiveParser()
