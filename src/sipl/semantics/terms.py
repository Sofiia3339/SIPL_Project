from dataclasses import dataclass, fields
from ..ast import SourceSpan, to_data


@dataclass(frozen=True)
class Term:
    span: SourceSpan


class TFA(Term):
    pass


class TFB(Term):
    pass


class TFS(Term):
    pass


@dataclass(frozen=True)
class Const(TFA):
    value: int


@dataclass(frozen=True)
class Dnm(TFA):
    name: str


@dataclass(frozen=True)
class SuperA(TFA):
    function: str
    args: tuple[TFA, TFA]


@dataclass(frozen=True)
class SuperB(TFB):
    function: str
    args: tuple[TFA | TFB, ...]


@dataclass(frozen=True)
class AS(TFS):
    name: str
    value: TFA


@dataclass(frozen=True)
class Compose(TFS):
    first: TFS
    second: TFS


@dataclass(frozen=True)
class IF(TFS):
    condition: TFB
    yes: TFS
    no: TFS


@dataclass(frozen=True)
class WH(TFS):
    condition: TFB
    body: TFS


@dataclass(frozen=True)
class Id(TFS):
    pass


def term_data(term: Term):
    def encode(value):
        if isinstance(value, Term):
            return term_data(value)
        if isinstance(value, tuple):
            return [encode(item) for item in value]
        return to_data(value)

    return {
        "type": type(term).__name__,
        **{f.name: encode(getattr(term, f.name)) for f in fields(term)},
    }


def format_term(term: Term) -> str:
    if isinstance(term, Const):
        return str(term.value)
    if isinstance(term, Dnm):
        return term.name + "⇒"
    if isinstance(term, (SuperA, SuperB)):
        power = "¹" if len(term.args) == 1 else "²"
        return (
            f"S{power}({term.function}, " + ", ".join(map(format_term, term.args)) + ")"
        )
    if isinstance(term, AS):
        return f"AS^{term.name}({format_term(term.value)})"
    if isinstance(term, Compose):
        return f"({format_term(term.first)} · {format_term(term.second)})"
    if isinstance(term, IF):
        return f"IF({format_term(term.condition)}, {format_term(term.yes)}, {format_term(term.no)})"
    if isinstance(term, WH):
        return f"WH({format_term(term.condition)}, {format_term(term.body)})"
    if isinstance(term, Id):
        return "id"
    raise TypeError(type(term))
