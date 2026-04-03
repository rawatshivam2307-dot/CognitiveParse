from __future__ import annotations

import ply.lex as lex

reserved = {
    "print": "PRINT",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
}

tokens = (
    "ID",
    "NUMBER",
    "LPAREN",
    "RPAREN",
    "COLON",
    "PLUS",
    "MINUS",
    "TIMES",
    "DIVIDE",
    "EQUALS",
    "NEWLINE",
) + tuple(reserved.values())

t_LPAREN = r"\("
t_RPAREN = r"\)"
t_COLON = r":"
t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE = r"/"
t_EQUALS = r"="

def t_ID(t):
    r"[a-zA-Z_][a-zA-Z0-9_]*"
    t.type = reserved.get(t.value, "ID")
    return t


def t_NUMBER(t):
    r"\d+"
    t.value = int(t.value)
    return t


def t_NEWLINE(t):
    r"\n+"
    t.lexer.lineno += len(t.value)
    return t


t_ignore = " \t\r"


def t_error(t):
    ch = t.value[0]
    raise SyntaxError(f"Lexical error: Illegal character '{ch}' at line {t.lexer.lineno}")


def build_lexer():
    return lex.lex()
