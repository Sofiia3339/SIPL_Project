from .parser import parse
from .interpreter import run
from .semantics import sem_P, evaluate, format_term

__version__ = "1.0.0"
__all__ = ["parse", "run", "sem_P", "evaluate", "format_term"]
