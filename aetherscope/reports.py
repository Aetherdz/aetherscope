from __future__ import annotations

import json
from collections import Counter
from typing import Dict, List

from .scope import Scope


def build_results(scope: Scope, targets: List[str]) -> List[Dict[str, object]]:
    entries = []
    for target in targets:
        verdict, rule = scope.classify(target)
        entries.append(
            {
                "target": target,
                "verdict": verdict,
                "rule": rule.raw if rule else None,
                "rule_kind": rule.kind if rule else None,
                "excluded": bool(rule and rule.excluded),
            }
        )
    return entries


def summarize(results: List[Dict[str, object]]) -> Dict[str, int]:
    return dict(Counter(entry["verdict"] for entry in results))


def to_json(report: Dict[str, object]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False)


def to_markdown(report: Dict[str, object], scope: Scope) -> str:
    lines: List[str] = []
    lines.append("# AetherScope Report")
    lines.append("")
    lines.append(f"**Scope rules:** {len(scope.rules)}")
    lines.append("")
    lines.append("## Rules")
    lines.append("")
    lines.append("| Rule | Kind | Excluded |")
    lines.append("| --- | --- | --- |")
    for rule in scope.rules:
        kind = rule.kind
        lines.append(f"| `{rule.raw}` | {kind} | {'yes' if rule.excluded else 'no'} |")
    lines.append("")

    summary = report.get("summary", {})
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- in-scope: {summary.get('in-scope', 0)}")
    lines.append(f"- out-of-scope: {summary.get('out-of-scope', 0)}")
    lines.append(f"- unknown: {summary.get('unknown', 0)}")
    lines.append(f"- error: {summary.get('error', 0)}")
    lines.append("")

    results = report.get("results", [])
    lines.append("## Targets")
    lines.append("")
    lines.append("| Target | Verdict | Matched Rule |")
    lines.append("| --- | --- | --- |")
    for entry in results:
        matched = entry.get("rule") or "-"
        lines.append(
            f"| `{entry['target']}` | {entry['verdict']} | {matched} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_report(scope: Scope, targets: List[str]) -> Dict[str, object]:
    results = build_results(scope, targets)
    return {
        "tool": "aetherscope",
        "version": "1.0.0",
        "summary": summarize(results),
        "results": results,
    }
