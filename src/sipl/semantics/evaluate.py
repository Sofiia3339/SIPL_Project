from ..runtime import Context, State, Result, primitive
from .terms import Const, Dnm, SuperA, SuperB, AS, Compose, IF, WH, Id, Term, TFS


def value(term: Term, ctx: Context):
    ctx.tick(term.span)
    if isinstance(term, Const):
        result, rule = term.value, "AF_CONST"
    elif isinstance(term, Dnm):
        result, rule = ctx.read(term.name, term.span), "AF_DNM"
    elif isinstance(term, (SuperA, SuperB)):
        args = [value(arg, ctx) for arg in term.args]
        result, rule = primitive(term.function, args), "AF_S"
    else:
        raise TypeError(type(term))
    details = {"rule": rule, "term_type": type(term).__name__, "result": result}
    if isinstance(term, (SuperA, SuperB)):
        details.update(function=term.function, arguments=args)
    elif isinstance(term, Dnm):
        details["name"] = term.name
    ctx.emit("RuleApplied", term.span, **details)
    return result


def apply(term: TFS, ctx: Context):
    ctx.tick(term.span)
    before = dict(ctx.state)
    if isinstance(term, AS):
        result = value(term.value, ctx)
        ctx.state[term.name] = result
        ctx.emit(
            "RuleApplied",
            term.span,
            rule="AF_AS",
            before=before,
            name=term.name,
            value=result,
        )
    elif isinstance(term, Compose):
        ctx.emit("RuleEnter", term.span, rule="AF_SEQ")
        apply(term.first, ctx)
        apply(term.second, ctx)
        ctx.emit("RuleApplied", term.span, rule="AF_SEQ", before=before)
    elif isinstance(term, IF):
        condition = value(term.condition, ctx)
        ctx.emit(
            "RuleEnter",
            term.span,
            rule="AF_IF",
            condition=condition,
            selected="yes" if condition else "no",
        )
        apply(term.yes if condition else term.no, ctx)
        ctx.emit("RuleApplied", term.span, rule="AF_IF", before=before)
    elif isinstance(term, WH):
        iteration = 0
        while True:
            condition = value(term.condition, ctx)
            ctx.emit(
                "RuleEnter",
                term.span,
                rule="AF_WH",
                condition=condition,
                iteration=iteration,
            )
            if not condition:
                break
            apply(term.body, ctx)
            iteration += 1
        ctx.emit(
            "RuleApplied", term.span, rule="AF_WH", before=before, iterations=iteration
        )
    elif isinstance(term, Id):
        ctx.emit("RuleApplied", term.span, rule="AF_ID", before=before)
    else:
        raise TypeError(type(term))


def evaluate(
    term: TFS,
    state: State | None = None,
    *,
    max_steps: int = 10000,
    trace: bool = False
) -> Result:
    if not isinstance(term, TFS):
        raise TypeError("evaluate очікує терм типу TFS.")
    ctx = Context({} if state is None else state, max_steps, trace)
    return ctx.finish(lambda: apply(term, ctx))
