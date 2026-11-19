import contextlib, io, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from sipl.cli import main

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def invoke(self, command, source="begin X:=1 end", extra=()):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "program.sipl"
            path.write_text(source, encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = main([command, str(path), *extra, "--json"])
            p = json.loads(out.getvalue())
            self.assertEqual(p["schema_version"], "1.0")
            self.assertEqual(p["command"], command)
            return code, p

    def test_commands(self):
        for command in ["parse", "check", "run", "trace", "term", "eval-term"]:
            code, p = self.invoke(command)
            self.assertEqual(code, 0)
            self.assertTrue(p["ok"])
        self.assertEqual(
            self.invoke("trace")[1]["data"]["events"][-1]["kind"], "Finished"
        )

    def test_exit_codes(self):
        self.assertEqual(self.invoke("check", "begin end")[0], 2)
        self.assertEqual(self.invoke("run", "begin X:=Y end")[0], 3)
        self.assertEqual(
            self.invoke("trace", "begin while 1=1 do skip end", ["--max-steps", "5"])[
                0
            ],
            4,
        )
        for state in ["null", "[]", '{"X":true}', "{"]:
            self.assertEqual(self.invoke("run", extra=["--state", state])[0], 2)
        for limit in ["0", "x"]:
            self.assertEqual(self.invoke("run", extra=["--max-steps", limit])[0], 2)
        self.assertEqual(self.invoke("check", " " * 100001)[0], 5)

    def test_invalid_arguments_io(self):
        for args in [
            ["bad", "--json"],
            ["run", "missing.sipl", "--json"],
            ["check", "--json"],
            ["--json"],
        ]:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(args), 2)
            self.assertFalse(json.loads(out.getvalue())["ok"])

    def test_text_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "p.sipl"
            for command in ["check", "run", "parse", "term", "trace", "eval-term"]:
                p.write_text("begin skip end")
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self.assertEqual(main([command, str(p)]), 0)
                self.assertTrue(out.getvalue())
            for source, command in [("begin end", "check"), ("begin X:=Y end", "run")]:
                p.write_text(source)
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    self.assertNotEqual(main([command, str(p)]), 0)
                self.assertIn("E_", err.getvalue())

    def test_real_process(self):
        p = subprocess.run(
            [
                sys.executable,
                "-m",
                "sipl",
                "run",
                str(ROOT / "examples/power.sipl"),
                "--state",
                '{"X":3,"Y":4}',
                "--json",
            ],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)["data"]["state"]["R"], 81)
