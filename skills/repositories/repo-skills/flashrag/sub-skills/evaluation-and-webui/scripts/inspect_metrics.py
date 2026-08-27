#!/usr/bin/env python3
"""List FlashRAG evaluator metrics without launching services.

Default mode parses ``flashrag/evaluator/metrics.py`` with AST and does not import
FlashRAG or optional metric dependencies. Optional ``--import`` mode imports the
installed package to show runtime-discovered ``BaseMetric`` descendants.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import json
import pathlib
import sys
from typing import Any


DEFAULT_METRICS_PATH = pathlib.Path("flashrag/evaluator/metrics.py")


def literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def base_names(class_def: ast.ClassDef) -> list[str]:
    names: list[str] = []
    for base in class_def.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
        elif isinstance(base, ast.Attribute):
            names.append(base.attr)
        elif isinstance(base, ast.Subscript):
            value = base.value
            if isinstance(value, ast.Name):
                names.append(value.id)
            elif isinstance(value, ast.Attribute):
                names.append(value.attr)
    return names


def class_docstring(class_def: ast.ClassDef) -> str:
    doc = ast.get_docstring(class_def) or ""
    return " ".join(doc.split())


def list_metrics_static(metrics_path: pathlib.Path) -> list[dict[str, Any]]:
    tree = ast.parse(metrics_path.read_text(encoding="utf-8"), filename=str(metrics_path))
    rows: list[dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        metric_name = None
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == "metric_name":
                        metric_name = literal_string(stmt.value)
            elif isinstance(stmt, ast.AnnAssign):
                target = stmt.target
                if isinstance(target, ast.Name) and target.id == "metric_name":
                    metric_name = literal_string(stmt.value)
        if metric_name and metric_name != "base":
            rows.append(
                {
                    "metric_name": metric_name,
                    "class_name": node.name,
                    "bases": base_names(node),
                    "doc": class_docstring(node),
                    "line": node.lineno,
                }
            )
    return sorted(rows, key=lambda row: row["metric_name"])


def list_metrics_import() -> list[dict[str, Any]]:
    metrics_mod = importlib.import_module("flashrag.evaluator.metrics")
    base_cls = metrics_mod.BaseMetric

    def descendants(cls: type, seen: set[type] | None = None) -> set[type]:
        if seen is None:
            seen = set()
        for sub_cls in cls.__subclasses__():
            if sub_cls not in seen:
                seen.add(sub_cls)
                descendants(sub_cls, seen)
        return seen

    rows = []
    for cls in descendants(base_cls):
        metric_name = getattr(cls, "metric_name", None)
        if metric_name and metric_name != "base":
            rows.append(
                {
                    "metric_name": metric_name,
                    "class_name": cls.__name__,
                    "module": cls.__module__,
                    "doc": " ".join((cls.__doc__ or "").split()),
                }
            )
    return sorted(rows, key=lambda row: row["metric_name"])


def render_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No metrics found."
    headers = ["metric_name", "class_name", "bases", "line", "doc"]
    present_headers = [header for header in headers if any(header in row for row in rows)]
    lines = ["\t".join(present_headers)]
    for row in rows:
        values = []
        for header in present_headers:
            value = row.get(header, "")
            if isinstance(value, list):
                value = ",".join(str(item) for item in value)
            values.append(str(value).replace("\t", " "))
        lines.append("\t".join(values))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect FlashRAG evaluator metric classes safely.")
    parser.add_argument(
        "--metrics-path",
        type=pathlib.Path,
        default=DEFAULT_METRICS_PATH,
        help="Path to flashrag/evaluator/metrics.py for static AST mode.",
    )
    parser.add_argument(
        "--import",
        dest="use_import",
        action="store_true",
        help="Import flashrag.evaluator.metrics and list runtime BaseMetric descendants.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a tab-separated table.")
    args = parser.parse_args()

    try:
        if args.use_import:
            rows = list_metrics_import()
        else:
            if not args.metrics_path.exists():
                parser.error(f"metrics file not found: {args.metrics_path}")
            rows = list_metrics_static(args.metrics_path)
    except Exception as exc:  # pragma: no cover - diagnostic script
        print(f"inspect_metrics failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print(render_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
