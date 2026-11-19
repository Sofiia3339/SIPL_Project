from .. import ast as a
from ..runtime import Context, State, Result, primitive, OPERATIONS


def arithmetic(node: a.Aexp, ctx: Context) -> int:
    ctx.tick(node.span)
    if isinstance(node, a.Num):
        return node.value
    if isinstance(node, a.Var):
        return ctx.read(node.name, node.span)
    if isinstance(node, a.Binary):
        left = arithmetic(node.left, ctx)
        right = arithmetic(node.right, ctx)
        return primitive(OPERATIONS[node.op], [left, right])
    raise TypeError(type(node))


def boolean(node: a.Bexp, ctx: Context) -> bool:
    ctx.tick(node.span)
    if isinstance(node, a.Compare):
        return primitive(
            OPERATIONS[node.op],
            [arithmetic(node.left, ctx), arithmetic(node.right, ctx)],
        )
    if isinstance(node, a.Or):
        left = boolean(node.left, ctx)
        right = boolean(node.right, ctx)
        return primitive("or", [left, right])
    if isinstance(node, a.Not):
        return not boolean(node.operand, ctx)
    raise TypeError(type(node))


def statement(node: a.Stm, ctx: Context) -> None:
    ctx.tick(node.span)
    ctx.emit("BeforeStatement", node.span, node=type(node).__name__)
    if isinstance(node, a.Assign):
        value = arithmetic(node.value, ctx)
        old = ctx.state.get(node.name)
        ctx.state[node.name] = value
        ctx.emit("VariableChanged", node.span, name=node.name, old=old, new=value)
    elif isinstance(node, a.Seq):
        statement(node.first, ctx)
        statement(node.second, ctx)
    elif isinstance(node, a.If):
        value = boolean(node.condition, ctx)
        ctx.emit("ConditionChecked", node.condition.span, value=value, owner="If")
        statement(node.yes if value else node.no, ctx)
    elif isinstance(node, a.While):
        while True:
            value = boolean(node.condition, ctx)
            ctx.emit(
                "ConditionChecked", node.condition.span, value=value, owner="While"
            )
            if not value:
                break
            statement(node.body, ctx)
    elif isinstance(node, a.Block):
        statement(node.body, ctx)
    elif not isinstance(node, a.Skip):
        raise TypeError(type(node))
    ctx.emit("AfterStatement", node.span, node=type(node).__name__)


def run(
    program: a.Prog,
    state: State | None = None,
    *,
    max_steps: int = 10000,
    trace: bool = False
) -> Result:
    ctx = Context({} if state is None else state, max_steps, trace)
    return ctx.finish(lambda: statement(program.body, ctx))
