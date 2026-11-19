from dataclasses import replace
from . import ast as a
from .lexer import tokenize
from .diagnostics import SiplError


def join(first, last):
    return a.SourceSpan(
        first.start, last.end, first.line, first.column, last.end_line, last.end_column
    )


class Parser:
    def __init__(self, source):
        self.tokens = tokenize(source)
        self.index = 0

    @property
    def current(self):
        return self.tokens[self.index]

    def take(self, kind):
        token = self.current
        if token.kind != kind:
            raise SiplError(
                "E_SYNTAX",
                f'Очікується {kind!r}, отримано {token.text or "кінець файлу"!r}.',
                token.span,
            )
        self.index += 1
        return token

    def program(self):
        start = self.take("begin").span
        body = self.sequence()
        end = self.take("end").span
        self.take("EOF")
        return a.Prog(join(start, end), body)

    def sequence(self):
        result = self.statement()
        while self.current.kind == ";":
            self.take(";")
            right = self.statement()
            result = a.Seq(join(result.span, right.span), result, right)
        return result

    def statement(self):
        start = self.current.span
        kind = self.current.kind
        if kind == "VAR":
            name = self.take("VAR").text
            self.take(":=")
            value = self.arithmetic()
            return a.Assign(join(start, value.span), name, value)
        if kind == "skip":
            return a.Skip(self.take("skip").span)
        if kind == "begin":
            self.take("begin")
            body = self.sequence()
            end = self.take("end").span
            return a.Block(join(start, end), body)
        if kind == "if":
            self.take("if")
            condition = self.boolean()
            self.take("then")
            yes = self.statement()
            self.take("else")
            no = self.statement()
            return a.If(join(start, no.span), condition, yes, no)
        if kind == "while":
            self.take("while")
            condition = self.boolean()
            self.take("do")
            body = self.statement()
            return a.While(join(start, body.span), condition, body)
        raise SiplError("E_SYNTAX", "Очікується оператор SIPL.", start)

    def boolean(self):
        result = self.negation()
        while self.current.kind == "∨":
            self.take("∨")
            right = self.negation()
            result = a.Or(join(result.span, right.span), result, right)
        return result

    def negation(self):
        if self.current.kind == "¬":
            start = self.take("¬").span
            operand = self.negation()
            return a.Not(join(start, operand.span), operand)
        saved = self.index
        try:
            left = self.arithmetic()
            op = self.current.kind
            if op not in ("=", ">"):
                raise SiplError(
                    "E_SYNTAX", "Очікується порівняння = або >.", self.current.span
                )
            self.take(op)
            right = self.arithmetic()
            return a.Compare(join(left.span, right.span), op, left, right)
        except SiplError as relation_error:
            self.index = saved
            if self.current.kind != "(":
                raise relation_error
            start = self.take("(").span
            try:
                condition = self.boolean()
                end = self.take(")").span
            except SiplError as grouped_error:
                if (
                    relation_error.diagnostic.span.start
                    > grouped_error.diagnostic.span.start
                ):
                    raise relation_error
                raise
            return replace(condition, span=join(start, end))

    def arithmetic(self):
        result = self.product()
        while self.current.kind in ("+", "-"):
            op = self.current.kind
            self.take(op)
            right = self.product()
            result = a.Binary(join(result.span, right.span), op, result, right)
        return result

    def product(self):
        result = self.atom()
        while self.current.kind == "*":
            self.take("*")
            right = self.atom()
            result = a.Binary(join(result.span, right.span), "*", result, right)
        return result

    def atom(self):
        token = self.current
        if token.kind == "NUMBER":
            self.take("NUMBER")
            return a.Num(token.span, int(token.text))
        if token.kind == "-":
            self.take("-")
            number = self.take("NUMBER")
            return a.Num(join(token.span, number.span), -int(number.text))
        if token.kind == "VAR":
            self.take("VAR")
            return a.Var(token.span, token.text)
        if token.kind == "(":
            self.take("(")
            value = self.arithmetic()
            end = self.take(")").span
            return replace(value, span=join(token.span, end))
        raise SiplError(
            "E_SYNTAX",
            "Очікується число, змінна або арифметичний вираз у дужках.",
            token.span,
        )


def parse(source: str) -> a.Prog:
    if len(source) > 100_000:
        raise SiplError("E_RESOURCE", "Текст перевищує 100000 символів.")
    try:
        return Parser(source).program()
    except RecursionError:
        raise SiplError(
            "E_RESOURCE", "Перевищено допустиму вкладеність програми."
        ) from None
