from .. import ast as a
from ..runtime import OPERATIONS
from .terms import Const, Dnm, SuperA, SuperB, AS, Compose, IF, WH, Id


def sem_A(node: a.Aexp):
    if isinstance(node, a.Num):
        return Const(node.span, node.value)
    if isinstance(node, a.Var):
        return Dnm(node.span, node.name)
    if isinstance(node, a.Binary):
        return SuperA(
            node.span, OPERATIONS[node.op], (sem_A(node.left), sem_A(node.right))
        )
    raise TypeError(type(node))


def sem_B(node: a.Bexp):
    if isinstance(node, a.Compare):
        return SuperB(
            node.span, OPERATIONS[node.op], (sem_A(node.left), sem_A(node.right))
        )
    if isinstance(node, a.Or):
        return SuperB(node.span, "or", (sem_B(node.left), sem_B(node.right)))
    if isinstance(node, a.Not):
        return SuperB(node.span, "neg", (sem_B(node.operand),))
    raise TypeError(type(node))


def sem_S(node: a.Stm):
    if isinstance(node, a.Assign):
        return AS(node.span, node.name, sem_A(node.value))
    if isinstance(node, a.Seq):
        return Compose(node.span, sem_S(node.first), sem_S(node.second))
    if isinstance(node, a.If):
        return IF(node.span, sem_B(node.condition), sem_S(node.yes), sem_S(node.no))
    if isinstance(node, a.While):
        return WH(node.span, sem_B(node.condition), sem_S(node.body))
    if isinstance(node, a.Block):
        return sem_S(node.body)
    if isinstance(node, a.Skip):
        return Id(node.span)
    raise TypeError(type(node))


def sem_P(program: a.Prog):
    return sem_S(program.body)
