import json
from pathlib import Path
import unittest

from tests import test_cli

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None


@unittest.skipIf(
    Draft202012Validator is None,
    "Install requirements-dev.txt for JSON Schema validation",
)
class SchemaTests(unittest.TestCase):
    def test_all_payloads(self):
        schema = json.loads(
            (Path(__file__).parents[1] / "docs/cli.schema.json").read_text()
        )
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        harness = test_cli.CliTests()
        for command in ["parse", "check", "run", "trace", "term", "eval-term"]:
            for source in ["begin X:=1 end", "begin end"]:
                _, payload = harness.invoke(command, source)
                validator.validate(payload)
        for source, extra in [
            ("begin X:=Y end", []),
            ("begin while 1=1 do skip end", ["--max-steps", "5"]),
        ]:
            _, payload = harness.invoke("trace", source, extra)
            validator.validate(payload)
