from pathlib import Path
import unittest
from math import gcd
from sipl import parse, run, sem_P, evaluate
from sipl.diagnostics import SiplError

ROOT = Path(__file__).resolve().parents[1]


class ExecutionTests(unittest.TestCase):
    def both(self, source, state=None, **kwargs):
        p = parse(source)
        return run(p, state, **kwargs), evaluate(sem_P(p), state, **kwargs)

    def test_examples(self):
        cases = [
            ("power", {"X": 5, "Y": 2}, {"X": 5, "Y": 0, "R": 25}),
            ("gcd", {"M": 8, "N": 16}, {"M": 8, "N": 8}),
            ("sum_even", {"N": 3}, {"N": 3, "R": 12, "I": 4}),
            ("branch", {"X": -7}, {"X": -7, "R": 7}),
            ("branch", {"X": 0}, {"X": 0, "R": 0}),
        ]
        for name, state, expected in cases:
            for result in self.both(
                (ROOT / "examples" / f"{name}.sipl").read_text(), state
            ):
                self.assertEqual(result.status, "finished")
                self.assertEqual(result.state, expected)

    def test_new_inputs(self):
        power = (ROOT / "examples/power.sipl").read_text()
        euclid = (ROOT / "examples/gcd.sipl").read_text()
        for x in range(-3, 4):
            for y in range(6):
                for r in self.both(power, {"X": x, "Y": y}):
                    self.assertEqual(r.state["R"], x**y)
        for x in range(1, 8):
            for y in range(1, 8):
                for r in self.both(euclid, {"M": x, "N": y}):
                    self.assertEqual(r.state["M"], gcd(x, y))

    def test_conditions_and_blocks(self):
        for r in self.both(
            "begin begin X:=2 end;if ¬ X>3 ∨ X=0 then R:=1 else R:=0;skip end"
        ):
            self.assertEqual(r.state, {"X": 2, "R": 1})

    def test_undefined_and_strict_or(self):
        for source in [
            "begin R:=X+1 end",
            "begin if 1=1 ∨ X=0 then skip else skip end",
            "begin while X>0 do skip end",
        ]:
            for r in self.both(source, trace=True):
                self.assertEqual(r.status, "undefined")
                self.assertEqual(r.diagnostic.code, "E_UNDEFINED")
                self.assertEqual(r.events[-1].kind, "Failed")
                self.assertIsNotNone(r.diagnostic.span)

    def test_unselected_branch(self):
        for source in [
            "begin if 1=1 then R:=3 else R:=X end",
            "begin if 1=0 then R:=X else R:=3 end",
        ]:
            for r in self.both(source):
                self.assertEqual(r.state, {"R": 3})

    def test_limits(self):
        for r in self.both("begin while 1=1 do skip end", max_steps=25, trace=True):
            self.assertEqual(r.status, "limit_exceeded")
            self.assertEqual(r.steps, 25)
        for r in self.both("begin X:=1 end", max_steps=1):
            self.assertEqual(r.state, {})
        for r in self.both("begin skip end", max_steps=1):
            self.assertEqual(r.status, "finished")

    def test_invalid_inputs(self):
        for state in [[], {"X": True}, {"x": 1}, {"X": 1.5}, {1: 3}]:
            for engine in [run, lambda p, s: evaluate(sem_P(p), s)]:
                with self.assertRaises(SiplError):
                    engine(parse("begin skip end"), state)
        for limit in [0, -1, True, 1.5]:
            with self.assertRaises(SiplError):
                run(parse("begin skip end"), max_steps=limit)
        with self.assertRaises(TypeError):
            evaluate(parse("begin skip end").span)

    def test_trace_copy(self):
        initial = {"X": 0}
        r = run(
            parse("begin X:=1;X:=2;if X>0 then skip else skip end"), initial, trace=True
        )
        self.assertEqual(initial, {"X": 0})
        changes = [e for e in r.events if e.kind == "VariableChanged"]
        self.assertEqual([e.state["X"] for e in changes], [1, 2])
        self.assertEqual(changes[0].details, {"name": "X", "old": 0, "new": 1})
        self.assertEqual(r.events[-1].kind, "Finished")
        self.assertEqual(
            sum(e.kind == "BeforeStatement" for e in r.events),
            sum(e.kind == "AfterStatement" for e in r.events),
        )
        self.assertEqual([e.index for e in r.events], list(range(len(r.events))))
        self.assertEqual(r.to_data()["events"][0]["kind"], "BeforeStatement")
        self.assertEqual(run(parse("begin skip end")).events, [])
