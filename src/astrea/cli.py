"""Public command line interface."""

import argparse
import sys
from importlib.metadata import version
from pathlib import Path

from .batch import generate, validate
from .catalog import listing
from .errors import AstreaError
from .jsonio import dumps
from .planning import read_plan, template


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise AstreaError("E_CONFIG", message, "arguments")


def parser():
    root = Parser(
        prog="astrea", description="Generate offline synthetic .eml test fixtures."
    )
    root.add_argument(
        "--version", action="version", version=version("astrea-fake-mail-generator")
    )
    commands = root.add_subparsers(dest="command", required=True)
    catalog = commands.add_parser(
        "list", help="Inspect supported fixtures and settings."
    )
    catalog.add_argument(
        "kind", choices=["fixtures", "profiles", "locales", "packs", "limits"]
    )
    catalog.add_argument("--json", action="store_true")
    plan = commands.add_parser(
        "plan", help="Print a template or preview an existing plan."
    )
    choice = plan.add_mutually_exclusive_group()
    choice.add_argument("--template", choices=["core", "stress"])
    choice.add_argument("--plan", type=Path)
    generation = commands.add_parser("generate", help="Generate a new fixture folder.")
    generation.add_argument("--plan", type=Path, required=True)
    generation.add_argument("--out", type=Path, required=True)
    validation = commands.add_parser(
        "validate", help="Check a generated fixture folder."
    )
    validation.add_argument("--input", type=Path, required=True)
    for command in (root, catalog, plan, generation, validation):
        command.add_argument(
            "--json-diagnostics", action="store_true", default=argparse.SUPPRESS
        )
    return root


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    json_errors = "--json-diagnostics" in argv
    try:
        args = parser().parse_args(argv)
        if args.command == "list":
            result = listing(args.kind)
            if not args.json:
                if isinstance(result, dict):
                    print("\n".join(f"{key}: {value}" for key, value in result.items()))
                else:
                    print(
                        "\n".join(
                            row["id"] if isinstance(row, dict) else row
                            for row in result
                        )
                    )
                return 0
        elif args.command == "plan":
            result = (
                read_plan(args.plan) if args.plan else template(args.template or "core")
            )
        elif args.command == "generate":
            result = generate(read_plan(args.plan), args.out)
        else:
            result = validate(args.input)
        print(dumps(result), end="")
        return 0
    except AstreaError as exc:
        print(
            dumps(exc.diagnostic()).rstrip() if json_errors else f"{exc.code}: {exc}",
            file=sys.stderr,
        )
        return exc.exit_code
    except (OSError, UnicodeError):
        error = AstreaError("E_IO", "File operation failed", exit_code=1)
        print(
            dumps(error.diagnostic()).rstrip()
            if json_errors
            else f"{error.code}: {error}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
