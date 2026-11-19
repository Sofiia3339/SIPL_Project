import argparse
import json
from pathlib import Path
import sys
from . import parse, run, sem_P, evaluate, format_term
from .ast import to_data
from .diagnostics import SiplError
from .semantics import term_data

SCHEMA_VERSION = "1.0"


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise SiplError("E_INPUT", message)


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    json_mode = "--json" in arguments
    commands = ("parse", "check", "run", "trace", "term", "eval-term")
    command = arguments[0] if arguments and arguments[0] in commands else None
    try:
        parser = ArgumentParser(prog="sipl", description="SIPL Language Toolkit")
        subparsers = parser.add_subparsers(
            dest="command", required=True, parser_class=ArgumentParser
        )
        for name in ("parse", "check", "run", "trace", "term", "eval-term"):
            sub = subparsers.add_parser(name)
            sub.add_argument("file", help="UTF-8 файл SIPL")
            sub.add_argument("--json", action="store_true")
            if name in ("run", "trace", "eval-term"):
                sub.add_argument(
                    "--state", default="{}", help="JSON-об’єкт початкового стану"
                )
                sub.add_argument("--max-steps", type=int, default=10000)
        args = parser.parse_args(arguments)
        command = args.command
        source = Path(args.file).read_text(encoding="utf-8")
        program = parse(source)
        if command == "parse":
            data = {"ast": to_data(program)}
        elif command == "check":
            data = {"valid": True}
        elif command == "term":
            term = sem_P(program)
            data = {"text": format_term(term), "term": term_data(term)}
        else:
            try:
                state = json.loads(args.state)
            except ValueError as error:
                raise SiplError(
                    "E_INPUT", f"Некоректний JSON стану: {error}."
                ) from None
            if not isinstance(state, dict):
                raise SiplError("E_INPUT", "Початковий стан має бути JSON-об’єктом.")
            if command == "eval-term":
                result = evaluate(
                    sem_P(program), state, max_steps=args.max_steps, trace=True
                )
            else:
                result = run(
                    program, state, max_steps=args.max_steps, trace=command == "trace"
                )
            data = result.to_data()
        ok = data.get("status", "finished") == "finished"
        if ok:
            code = 0
        else:
            code = {"undefined": 3, "limit_exceeded": 4, "resource_exceeded": 5}[
                data["status"]
            ]
        payload = {
            "schema_version": SCHEMA_VERSION,
            "command": command,
            "ok": ok,
            "data": data,
            "diagnostic": data.get("diagnostic"),
        }
    except SiplError as error:
        code = 5 if error.diagnostic.code == "E_RESOURCE" else 2
        payload = {
            "schema_version": SCHEMA_VERSION,
            "command": command,
            "ok": False,
            "data": None,
            "diagnostic": error.diagnostic.to_data(),
        }
    except (OSError, UnicodeError) as error:
        code = 2
        payload = {
            "schema_version": SCHEMA_VERSION,
            "command": command,
            "ok": False,
            "data": None,
            "diagnostic": {"code": "E_IO", "message": str(error), "span": None},
        }
    except RecursionError:
        code = 5
        payload = {
            "schema_version": SCHEMA_VERSION,
            "command": command,
            "ok": False,
            "data": None,
            "diagnostic": {
                "code": "E_RESOURCE",
                "message": "Перевищено допустиму вкладеність структури.",
                "span": None,
            },
        }
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False))
    elif payload["data"] is not None and payload["ok"]:
        if command == "check":
            print("Синтаксис: коректний")
        elif command == "term":
            print(payload["data"]["text"])
        else:
            print(json.dumps(payload["data"], ensure_ascii=False, indent=2))
    else:
        diagnostic = payload["diagnostic"]
        span = diagnostic["span"]
        location = f"{span['line']}:{span['column']}: " if span else ""
        print(
            f"{location}{diagnostic['code']}: {diagnostic['message']}", file=sys.stderr
        )
        if payload["data"] is not None:
            print(json.dumps(payload["data"], ensure_ascii=False, indent=2))
    return code
