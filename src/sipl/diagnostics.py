from dataclasses import dataclass
from .ast import SourceSpan, to_data


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    span: SourceSpan | None = None

    def to_data(self):
        return {"code": self.code, "message": self.message, "span": to_data(self.span)}


class SiplError(Exception):
    def __init__(self, code, message, span=None):
        self.diagnostic = Diagnostic(code, message, span)
        super().__init__(message)
