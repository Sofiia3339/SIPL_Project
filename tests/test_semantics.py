import json
from pathlib import Path
import unittest
from sipl import parse, sem_P, evaluate, format_term
from sipl.semantics import sem_A, sem_B, sem_S, term_data
from sipl import ast as a


class SemanticsTests(unittest.TestCase):
    def test_golden(self):
        for case in json.loads(
            (Path(__file__).parent / "golden_terms.json").read_text()
        ):
            with self.subTest(source=case["source"]):
                self.assertEqual(
                    format_term(sem_P(parse(case["source"]))), case["term"]
                )

    def test_rule_trace(self):
        t = sem_P(
            parse(
                "begin R:=0;while R=0 do begin if ¬ R>1 ∨ R=0 then R:=R+1 else skip end end"
            )
        )
        r = evaluate(t, trace=True)
        self.assertEqual(r.state, {"R": 1})
        rules = {e.details["rule"] for e in r.events if "rule" in e.details}
        self.assertTrue(
            {"AF_CONST", "AF_AS", "AF_DNM", "AF_SEQ", "AF_IF", "AF_WH", "AF_S"} <= rules
        )
        self.assertIn(
            "AF_ID",
            {
                e.details.get("rule")
                for e in evaluate(sem_P(parse("begin skip end")), trace=True).events
            },
        )
        self.assertEqual(term_data(t)["type"], "Compose")
        self.assertTrue(
            all(
                "arguments" in e.details
                for e in r.events
                if e.details.get("rule") == "AF_S"
            )
        )

    def test_course_gcd(self):
        r = evaluate(
            sem_P(parse("begin while ¬ M=N do if M>N then M:=M-N else N:=N-M end")),
            {"M": 8, "N": 16},
            trace=True,
        )
        changes = [e for e in r.events if e.details.get("rule") == "AF_AS"]
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].details["before"], {"M": 8, "N": 16})
        self.assertEqual(changes[0].state, {"M": 8, "N": 8})

    def test_wrong_nodes(self):
        for function in [sem_A, sem_B, sem_S, format_term]:
            with self.assertRaises(TypeError):
                function(a.Node(parse("begin skip end").span))
