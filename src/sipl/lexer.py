from dataclasses import dataclass
import re
from .ast import SourceSpan
from .diagnostics import SiplError

VARIABLE = re.compile(r"[A-Z][A-Z0-9_]*\Z")
_PATTERN = re.compile(r"\s+|:=|[0-9]+|[A-Za-z_][A-Za-z_0-9]*|[;()+*=>¬∨-]")
_KEYWORDS = {"begin", "end", "skip", "if", "then", "else", "while", "do"}


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    span: SourceSpan


def tokenize(source: str) -> list[Token]:
    result = []
    offset, line, column = 0, 1, 1
    while offset < len(source):
        match = _PATTERN.match(source, offset)
        if match is None:
            span = SourceSpan(offset, offset + 1, line, column, line, column + 1)
            raise SiplError("E_LEX", f"Невідомий символ {source[offset]!r}.", span)
        text = match.group()
        end_line = line + text.count("\n")
        end_column = (
            len(text.rsplit("\n", 1)[-1]) + 1 if "\n" in text else column + len(text)
        )
        span = SourceSpan(offset, match.end(), line, column, end_line, end_column)
        offset, line, column = match.end(), end_line, end_column
        if text.isspace():
            continue
        if text.isascii() and text.isdigit():
            if len(text) > 1000:
                raise SiplError(
                    "E_RESOURCE", "Числовий літерал довший за 1000 цифр.", span
                )
            kind = "NUMBER"
        elif VARIABLE.fullmatch(text):
            kind = "VAR"
        elif text in _KEYWORDS or len(text) == 1 or text == ":=":
            kind = text
        else:
            raise SiplError(
                "E_LEX", f"Некоректне ім’я або ключове слово {text!r}.", span
            )
        result.append(Token(kind, text, span))
    result.append(
        Token("EOF", "", SourceSpan(offset, offset, line, column, line, column))
    )
    return result
