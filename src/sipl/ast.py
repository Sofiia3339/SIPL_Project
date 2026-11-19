from dataclasses import dataclass, fields
from typing import Any


@dataclass(frozen=True)
class SourceSpan:
    start: int
    end: int
    line: int
    column: int
    end_line: int
    end_column: int


@dataclass(frozen=True)
class Node:
    span: SourceSpan


class Aexp(Node):
    pass


class Bexp(Node):
    pass


class Stm(Node):
    pass


@dataclass(frozen=True)
class Num(Aexp):
    value: int


@dataclass(frozen=True)
class Var(Aexp):
    name: str


@dataclass(frozen=True)
class Binary(Aexp):
    op: str
    left: Aexp
    right: Aexp


@dataclass(frozen=True)
class Compare(Bexp):
    op: str
    left: Aexp
    right: Aexp


@dataclass(frozen=True)
class Or(Bexp):
    left: Bexp
    right: Bexp


@dataclass(frozen=True)
class Not(Bexp):
    operand: Bexp


@dataclass(frozen=True)
class Assign(Stm):
    name: str
    value: Aexp


@dataclass(frozen=True)
class Seq(Stm):
    first: Stm
    second: Stm


@dataclass(frozen=True)
class If(Stm):
    condition: Bexp
    yes: Stm
    no: Stm


@dataclass(frozen=True)
class While(Stm):
    condition: Bexp
    body: Stm


@dataclass(frozen=True)
class Block(Stm):
    body: Stm


@dataclass(frozen=True)
class Skip(Stm):
    pass


@dataclass(frozen=True)
class Prog(Node):
    body: Stm


def to_data(value: Any) -> Any:
    if isinstance(value, Node):
        return {
            "type": type(value).__name__,
            **{f.name: to_data(getattr(value, f.name)) for f in fields(value)},
        }
    if isinstance(value, SourceSpan):
        return {f.name: getattr(value, f.name) for f in fields(value)}
    return value
