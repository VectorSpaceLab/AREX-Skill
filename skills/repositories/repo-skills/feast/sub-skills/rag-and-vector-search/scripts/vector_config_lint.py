#!/usr/bin/env python3
"""Static lint helper for Feast vector/RAG configuration snippets."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VECTOR_STORE_TYPES = {
    "milvus",
    "sqlite",
    "postgres",
    "pgvector",
    "elasticsearch",
    "qdrant",
    "mongodb",
    "faiss",
    "feast.infra.online_stores.faiss_online_store.FaissOnlineStore",
}


@dataclass
class Finding:
    level: str
    message: str


@dataclass
class VectorField:
    name: str
    vector_index: bool
    vector_length: int | None
    vector_search_metric: str | None
    line: int | None = None


class PythonVectorVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.fields: list[VectorField] = []
        self.feature_views: list[tuple[str | None, list[str], int]] = []

    def visit_Call(self, node: ast.Call) -> None:
        func_name = _call_name(node.func)
        if func_name == "Field":
            kwargs = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
            field_name = _literal_string(kwargs.get("name")) or f"<line {node.lineno}>"
            vector_index = _literal_bool(kwargs.get("vector_index")) is True
            vector_length = _literal_int(kwargs.get("vector_length"))
            vector_search_metric = _literal_string(kwargs.get("vector_search_metric"))
            if vector_index or vector_length is not None or vector_search_metric is not None:
                self.fields.append(
                    VectorField(
                        name=field_name,
                        vector_index=vector_index,
                        vector_length=vector_length,
                        vector_search_metric=vector_search_metric,
                        line=node.lineno,
                    )
                )
        elif func_name == "FeatureView":
            kwargs = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
            view_name = _literal_string(kwargs.get("name"))
            vector_field_names = _field_names_from_schema(kwargs.get("schema"))
            if vector_field_names:
                self.feature_views.append((view_name, vector_field_names, node.lineno))
        self.generic_visit(node)


def _call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _literal_bool(node: ast.AST | None) -> bool | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    return None


def _literal_int(node: ast.AST | None) -> int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    return None


def _field_names_from_schema(node: ast.AST | None) -> list[str]:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return []
    names: list[str] = []
    for element in node.elts:
        if not isinstance(element, ast.Call) or _call_name(element.func) != "Field":
            continue
        kwargs = {keyword.arg: keyword.value for keyword in element.keywords if keyword.arg}
        if _literal_bool(kwargs.get("vector_index")) is True:
            names.append(_literal_string(kwargs.get("name")) or f"<line {element.lineno}>")
    return names


def load_structured_file(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(text)
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore[import-not-found]
        except ModuleNotFoundError:
            return parse_simple_yaml(text)
        return yaml.safe_load(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return parse_simple_yaml(text)


def parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.split("#", 1)[0].rstrip()
        if ":" not in line:
            continue
        key, value = line.strip().split(":", 1)
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        value = value.strip()
        if value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _coerce_scalar(value)
    return root


def _coerce_scalar(value: str) -> Any:
    stripped = value.strip().strip('"').strip("'")
    lowered = stripped.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none", "~"}:
        return None
    try:
        return int(stripped)
    except ValueError:
        return stripped


def lint_python(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return [Finding("ERROR", f"could not parse Python: {exc}")]

    visitor = PythonVectorVisitor()
    visitor.visit(tree)

    if not visitor.fields:
        findings.append(Finding("WARN", "no vector Field(...) definitions found"))
        return findings

    indexed_count = 0
    for field in visitor.fields:
        prefix = f"field {field.name}"
        if field.line is not None:
            prefix += f" at line {field.line}"
        if not field.vector_index:
            findings.append(
                Finding("WARN", f"{prefix} has vector metadata but vector_index is not True")
            )
            continue
        indexed_count += 1
        if field.vector_length is None or field.vector_length <= 0:
            findings.append(
                Finding(
                    "ERROR",
                    f"{prefix} has vector_index=True but no positive vector_length",
                )
            )
        else:
            findings.append(Finding("OK", f"{prefix} has vector_length={field.vector_length}"))
        if not field.vector_search_metric:
            findings.append(Finding("WARN", f"{prefix} has no vector_search_metric"))
        else:
            normalized = field.vector_search_metric.upper()
            if normalized not in {"COSINE", "L2", "IP", "DOT"}:
                findings.append(
                    Finding(
                        "WARN",
                        f"{prefix} uses uncommon vector_search_metric={field.vector_search_metric!r}",
                    )
                )
            else:
                findings.append(
                    Finding("OK", f"{prefix} uses vector_search_metric={field.vector_search_metric}")
                )

    for view_name, vector_fields, line in visitor.feature_views:
        label = f"FeatureView {view_name or '<unknown>'} at line {line}"
        if len(vector_fields) > 1:
            findings.append(
                Finding(
                    "ERROR",
                    f"{label} defines multiple vector_index fields: {', '.join(vector_fields)}",
                )
            )
        else:
            findings.append(Finding("OK", f"{label} has one vector_index field: {vector_fields[0]}"))

    if indexed_count == 0:
        findings.append(Finding("WARN", "no Field has vector_index=True"))
    return findings


def lint_structured(data: Any, source: str) -> list[Finding]:
    findings: list[Finding] = []
    if data is None:
        return [Finding("WARN", f"{source} is empty")]
    if not isinstance(data, dict):
        return [Finding("WARN", f"{source} is not a mapping; expected feature_store.yaml or JSON object")]

    online_store = data.get("online_store") if isinstance(data.get("online_store"), dict) else data
    if not isinstance(online_store, dict):
        findings.append(Finding("WARN", "no online_store mapping found"))
        return findings

    store_type = str(online_store.get("type", "")).strip()
    if store_type:
        if store_type in VECTOR_STORE_TYPES or any(token in store_type.lower() for token in VECTOR_STORE_TYPES):
            findings.append(Finding("OK", f"online_store type looks vector-capable: {store_type}"))
        else:
            findings.append(Finding("WARN", f"online_store type is not recognized as vector-capable: {store_type}"))
    else:
        findings.append(Finding("WARN", "online_store has no type"))

    vector_enabled = online_store.get("vector_enabled")
    if vector_enabled is True:
        findings.append(Finding("OK", "online_store.vector_enabled is true"))
    elif vector_enabled is False:
        findings.append(Finding("ERROR", "online_store.vector_enabled is false for vector search"))
    else:
        findings.append(Finding("WARN", "online_store.vector_enabled is not set"))

    dimension = first_present(online_store, ["embedding_dim", "dimension", "vector_length"])
    if isinstance(dimension, int) and dimension > 0:
        findings.append(Finding("OK", f"online_store dimension hint is {dimension}"))
    elif dimension is not None:
        findings.append(Finding("WARN", f"online_store dimension hint is not a positive integer: {dimension!r}"))
    else:
        findings.append(Finding("WARN", "online_store has no embedding_dim/dimension hint"))

    metric = first_present(online_store, ["metric_type", "similarity", "distance_metric"])
    if metric:
        findings.append(Finding("OK", f"online_store metric hint is {metric}"))
    else:
        findings.append(Finding("WARN", "online_store has no metric hint"))

    if "milvus" in store_type.lower():
        if online_store.get("path"):
            findings.append(Finding("OK", "Milvus config has local path"))
        elif online_store.get("host") and online_store.get("port"):
            findings.append(Finding("OK", "Milvus config has host and port"))
        else:
            findings.append(Finding("WARN", "Milvus config has neither local path nor host+port"))

    if "faiss" in store_type.lower() and not online_store.get("index_path"):
        findings.append(Finding("WARN", "Faiss config should include index_path"))

    return findings


def first_present(mapping: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def extract_snippet_structures(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    field_pattern = re.compile(r"vector_index\s*=\s*True|vector_length\s*=\s*(\d+)|vector_search_metric\s*=\s*['\"]([^'\"]+)['\"]")
    if "vector_index" in text:
        result["contains_vector_index"] = True
        lengths = [int(match.group(1)) for match in field_pattern.finditer(text) if match.group(1)]
        metrics = [match.group(2) for match in field_pattern.finditer(text) if match.group(2)]
        if lengths:
            result["vector_length"] = lengths[0]
        if metrics:
            result["vector_search_metric"] = metrics[0]
    return result


def lint_text_snippet(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    info = extract_snippet_structures(text)
    if not info.get("contains_vector_index"):
        return [Finding("WARN", "text snippet does not contain vector_index")]
    findings = [Finding("OK", "text snippet contains vector_index")]
    if isinstance(info.get("vector_length"), int) and info["vector_length"] > 0:
        findings.append(Finding("OK", f"text snippet has vector_length={info['vector_length']}"))
    else:
        findings.append(Finding("ERROR", "text snippet has vector_index but no positive vector_length"))
    if info.get("vector_search_metric"):
        findings.append(Finding("OK", f"text snippet has metric {info['vector_search_metric']}"))
    else:
        findings.append(Finding("WARN", "text snippet has no vector_search_metric"))
    return findings


def run_lint(path: Path, config_only: bool) -> list[Finding]:
    suffix = path.suffix.lower()
    if not path.exists():
        return [Finding("ERROR", f"file does not exist: {path}")]
    if suffix == ".py" and not config_only:
        return lint_python(path)
    if suffix in {".json", ".yaml", ".yml"} or config_only:
        try:
            return lint_structured(load_structured_file(path), path.name)
        except Exception as exc:  # noqa: BLE001 - CLI should report parse failures clearly.
            return [Finding("ERROR", f"could not parse structured config: {exc}")]
    return lint_text_snippet(path)


def print_findings(path: Path, findings: list[Finding]) -> int:
    print(f"File: {path}")
    for finding in findings:
        print(f"{finding.level}: {finding.message}")
    counts = {level: sum(1 for item in findings if item.level == level) for level in ["OK", "WARN", "ERROR"]}
    print(f"Summary: {counts['OK']} OK, {counts['WARN']} WARN, {counts['ERROR']} ERROR")
    return 1 if counts["ERROR"] else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Statically lint Feast vector Field definitions and vector online store config hints.",
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Python feature definition, feature_store.yaml, JSON/YAML snippet, or text snippet to lint.",
    )
    parser.add_argument(
        "--config-only",
        action="store_true",
        help="Treat the input as a feature_store-style config mapping even if its extension is unusual.",
    )
    parser.add_argument(
        "--require-feast",
        action="store_true",
        help="Also verify that the installed feast package is importable. No vector DB connection is attempted.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.require_feast:
        try:
            import feast  # type: ignore[import-not-found]
        except ModuleNotFoundError:
            print("ERROR: feast is not importable. Install Feast before runtime validation.", file=sys.stderr)
            return 1
        print(f"OK: feast importable ({getattr(feast, '__version__', 'unknown version')})")

    findings = run_lint(args.path, args.config_only)
    return print_findings(args.path, findings)


if __name__ == "__main__":
    raise SystemExit(main())
