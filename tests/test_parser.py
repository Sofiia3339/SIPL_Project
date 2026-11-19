import unittest
from sipl import parse, run
from sipl import ast as a
from sipl.ast import to_data
from sipl.diagnostics import SiplError
from sipl.lexer import tokenize

POSITIVE = [
    "begin skip end",
    "begin X:=0 end",
    "begin X:=-12 end",
    "begin X:=1;Y:=2 end",
    "begin begin skip end end",
    "begin if X=0 then skip else X:=1 end",
    "begin while X>0 do X:=X-1 end",
    "begin X:=2+3*4 end",
    "begin X:=(2+3)*4 end",
    "begin if ¬ X=0 ∨ Y>1 then skip else skip end",
    "begin if (X+1)>0 then skip else skip end",
    "begin if ((X=1) ∨ ¬(Y>2)) then skip else skip end",
    "begin if (X)=(1) then skip else skip end",
    "begin X1_A:=5--2 end",
    "begin if X=1 then if Y=2 then skip else skip else skip end",
    "begin while X>0 do begin X:=X-1;skip end end",
]
NEGATIVE = [
    "",
    "skip",
    "begin end",
    "begin skip; end",
    "begin ;skip end",
    "begin X=1 end",
    "begin X:= end",
    "begin X:=1",
    "begin if X=1 then skip end",
    "begin while X>0 X:=0 end",
    "begin X:=(1+2 end",
    "begin skip end skip",
    "begin X:=1/2 end",
    "begin x:=1 end",
    "begin if X<1 then skip else skip end",
    "begin X:=-Y end",
    "begin X:=1;;skip end",
    "begin if X then skip else skip end",
    "begin if (X=) then skip else skip end",
    "begin if (X=1 then skip else skip end",
    "begin if (X+1) then skip else skip end",
    "begin X:=1.5 end",
    "begin X:=1 # comment\nend",
]


class ParserTests(unittest.TestCase):
    def test_positive(self):
        for source in POSITIVE:
            with self.subTest(source=source):
                self.assertIsInstance(parse(source), a.Prog)

    def test_negative(self):
        for source in NEGATIVE:
            with self.subTest(source=source), self.assertRaises(SiplError) as error:
                parse(source)
            self.assertIsNotNone(error.exception.diagnostic.span)

    def test_precedence(self):
        for expr, expected in {
            "10-3-2": 5,
            "2+3*4": 14,
            "(2+3)*4": 20,
            "-2*3+7": 1,
            "5--2": 7,
            "2*3*4": 24,
        }.items():
            self.assertEqual(run(parse(f"begin X:={expr} end")).state["X"], expected)
        node = parse("begin X:=1;Y:=2;Z:=3 end").body
        self.assertIsInstance(node.first, a.Seq)

    def test_sequence_scope(self):
        source = "begin X:=0;while X>0 do X:=X-1;if X=1 then skip else skip;R:=8 end"
        self.assertEqual(run(parse(source)).state, {"X": 0, "R": 8})

    def test_spans(self):
        source = "begin\n  X := (1 + 2)\nend"
        program = parse(source)
        span = program.body.span
        self.assertEqual((span.line, span.column), (2, 3))
        self.assertEqual(source[span.start : span.end], "X := (1 + 2)")
        self.assertEqual((span.end_line, span.end_column), (2, 15))
        self.assertEqual(to_data(program)["body"]["type"], "Assign")
        self.assertIsNone(to_data(None))

    def test_errors_and_limits(self):
        with self.assertRaises(SiplError) as error:
            parse("begin\n X := @\nend")
        d = error.exception.diagnostic
        self.assertEqual((d.code, d.span.line, d.span.column), ("E_LEX", 2, 7))
        with self.assertRaises(SiplError) as error:
            parse("begin X := 1")
        self.assertEqual(error.exception.diagnostic.span.start, 12)
        self.assertEqual(tokenize(" \n\t")[0].span.line, 2)
        for source in [
            "begin unknown:=1 end",
            "begin X:=" + "9" * 1001 + " end",
            " " * 100001,
            "begin X:=" + "(" * 2000 + "1" + ")" * 2000 + " end",
        ]:
            with self.assertRaises(SiplError):
                parse(source)
