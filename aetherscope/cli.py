from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from . import __version__
from .reports import build_report, to_json, to_markdown
from .scope import Scope

VERDICT_EXIT = {
    "in-scope": 0,
    "out-of-scope": 1,
    "unknown": 2,
    "error": 3,
}


def _load_scope(path: Optional[str]) -> Scope:
    if path is None or path == "-":
        return Scope.from_text(sys.stdin.read())
    return Scope.from_file(path)


def _read_targets(path: Optional[str]) -> List[str]:
    if path is None or path == "-":
        return [line.strip() for line in sys.stdin if line.strip()]
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return [line.strip() for line in handle if line.strip()]


def cmd_check(args: argparse.Namespace) -> int:
    scope = _load_scope(args.scope)
    targets = args.targets or _read_targets(args.targets_file)
    worst = 0
    output = []
    for target in targets:
        verdict, rule = scope.classify(target)
        if args.json:
            output.append(
                {
                    "target": target,
                    "verdict": verdict,
                    "rule": rule.raw if rule else None,
                }
            )
        else:
            matched = f"  [{rule.raw}]" if rule else ""
            output.append(f"{target}: {verdict}{matched}")
        worst = max(worst, VERDICT_EXIT.get(verdict, 3))
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print("\n".join(output))
    return worst


def cmd_filter(args: argparse.Namespace) -> int:
    scope = _load_scope(args.scope)
    targets = _read_targets(args.targets_file)
    kept = [t for t in targets if scope.classify(t)[0] == "in-scope"]
    for target in kept:
        print(target)
    return 0


def cmd_parse(args: argparse.Namespace) -> int:
    scope = _load_scope(args.scope)
    for rule in scope.rules:
        flags = "excluded" if rule.excluded else "included"
        print(f"{rule.raw}\t{rule.kind}\t{flags}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    scope = _load_scope(args.scope)
    targets = _read_targets(args.targets_file)
    report = build_report(scope, targets)
    if args.format == "json":
        content = to_json(report)
    else:
        content = to_markdown(report, scope)
    if args.output and args.output != "-":
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(content)
    else:
        print(content)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aetherscope",
        description="Scope enforcement for authorized security testing.",
    )
    parser.add_argument("--version", action="version", version=f"aetherscope {__version__}")
    parser.add_argument("-s", "--scope", help="scope file (or - for stdin)")
    parser.add_argument("-f", "--targets-file", help="file of targets (or - for stdin)")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-s", "--scope", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    common.add_argument(
        "-f", "--targets-file", default=argparse.SUPPRESS, help=argparse.SUPPRESS
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", parents=[common], help="classify targets against the scope")
    p_check.add_argument("targets", nargs="*", help="targets to classify")
    p_check.add_argument("--json", action="store_true", help="JSON output")
    p_check.set_defaults(func=cmd_check)

    p_filter = sub.add_parser("filter", parents=[common], help="keep only in-scope targets")
    p_filter.set_defaults(func=cmd_filter)

    p_parse = sub.add_parser("parse", parents=[common], help="show parsed scope rules")
    p_parse.set_defaults(func=cmd_parse)

    p_report = sub.add_parser("report", parents=[common], help="build a scope report")
    p_report.add_argument("--format", choices=["json", "markdown"], default="markdown")
    p_report.add_argument("-o", "--output", help="output file (or stdout)")
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
