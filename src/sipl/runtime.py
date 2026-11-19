from dataclasses import dataclass, field
from typing import Any
from .ast import SourceSpan, to_data
from .diagnostics import Diagnostic, SiplError
from .lexer import VARIABLE

State = dict[str, int]
MAX_INTEGER_BITS = 8192


@dataclass(frozen=True)
class Event:
    index: int
    kind: str
    span: SourceSpan | None
    state: State
    details: dict[str, Any]

    def to_data(self):
        return {
            "index": self.index,
            "kind": self.kind,
            "span": to_data(self.span),
            "state": self.state,
            "details": self.details,
        }


@dataclass
class Result:
    status: str
    state: State
    steps: int
    events: list[Event] = field(default_factory=list)
    diagnostic: Diagnostic | None = None

    def to_data(self):
        return {
            "status": self.status,
            "state": self.state,
            "steps": self.steps,
            "events": [event.to_data() for event in self.events],
            "diagnostic": self.diagnostic.to_data() if self.diagnostic else None,
        }


class Context:
    def __init__(self, state, max_steps, trace):
        if type(max_steps) is not int or max_steps <= 0:
            raise SiplError("E_INPUT", "Ліміт кроків має бути додатним цілим числом.")
        if not isinstance(state, dict) or any(
            not isinstance(k, str) or not VARIABLE.fullmatch(k) or type(v) is not int
            for k, v in state.items()
        ):
            raise SiplError(
                "E_INPUT",
                "Стан має бути об’єктом: ім’я змінної → ціле число (не bool).",
            )
        self.state = dict(state)
        if any(v.bit_length() > MAX_INTEGER_BITS for v in state.values()):
            raise SiplError("E_RESOURCE", "Значення стану перевищує 8192 біти.")
        self.max_steps = max_steps
        self.steps = 0
        self.trace = trace
        self.events = []

    def tick(self, span):
        if self.steps >= self.max_steps:
            raise SiplError(
                "E_LIMIT", "Вичерпано ліміт кроків; завершення не встановлено.", span
            )
        self.steps += 1

    def emit(self, kind, span, **details):
        if self.trace:
            self.events.append(
                Event(len(self.events), kind, span, dict(self.state), details)
            )

    def read(self, name, span):
        if name not in self.state:
            raise SiplError("E_UNDEFINED", f"Змінна {name} не визначена у стані.", span)
        return self.state[name]

    def finish(self, action):
        try:
            action()
        except SiplError as error:
            status = {
                "E_LIMIT": "limit_exceeded",
                "E_RESOURCE": "resource_exceeded",
            }.get(error.diagnostic.code, "undefined")
            self.emit(
                "Failed",
                error.diagnostic.span,
                diagnostic=error.diagnostic.to_data(),
                status=status,
            )
            return Result(
                status, dict(self.state), self.steps, self.events, error.diagnostic
            )
        except RecursionError:
            diagnostic = Diagnostic(
                "E_RESOURCE", "Перевищено допустиму вкладеність обчислення."
            )
            self.emit(
                "Failed",
                None,
                diagnostic=diagnostic.to_data(),
                status="resource_exceeded",
            )
            return Result(
                "resource_exceeded",
                dict(self.state),
                self.steps,
                self.events,
                diagnostic,
            )
        self.emit("Finished", None)
        return Result("finished", dict(self.state), self.steps, self.events)


def primitive(name, values):
    if name == "add":
        result = values[0] + values[1]
    elif name == "sub":
        result = values[0] - values[1]
    elif name == "mult":
        result = values[0] * values[1]
    else:
        return predicate(name, values)
    if result.bit_length() > MAX_INTEGER_BITS:
        raise SiplError("E_RESOURCE", "Результат арифметики перевищує 8192 біти.")
    return result


def predicate(name, values):
    if name == "eq":
        return values[0] == values[1]
    if name == "gr":
        return values[0] > values[1]
    if name == "or":
        return values[0] or values[1]
    if name == "neg":
        return not values[0]
    raise ValueError(f"Unknown primitive: {name}")


OPERATIONS = {"+": "add", "-": "sub", "*": "mult", "=": "eq", ">": "gr"}
