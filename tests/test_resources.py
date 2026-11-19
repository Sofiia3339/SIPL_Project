import unittest
from sipl import parse, run, sem_P, evaluate
from sipl.diagnostics import SiplError
from sipl.ast import Seq, Skip
from sipl.runtime import primitive


class ResourceTests(unittest.TestCase):
    def test_integer_bound(self):
        p = parse("begin X:=X*X end")
        for engine, arg in [(run, p), (evaluate, sem_P(p))]:
            result = engine(arg, {"X": 2**5000}, trace=True)
            self.assertEqual(result.status, "resource_exceeded")
            self.assertEqual(result.diagnostic.code, "E_RESOURCE")
            with self.assertRaises(SiplError):
                engine(arg, {"X": 2**9000})

    def test_deep_execution(self):
        p = parse("begin skip end")
        body = p.body
        for _ in range(1500):
            body = Seq(p.span, body, Skip(p.span))
        result = run(type(p)(p.span, body), max_steps=5000, trace=True)
        self.assertEqual(result.status, "resource_exceeded")

    def test_invalid_primitive(self):
        with self.assertRaises(ValueError):
            primitive("invalid", [])
