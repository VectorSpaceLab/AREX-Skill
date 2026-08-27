#!/usr/bin/env python3
"""Validate TaskBench fixture files without mutating them.

This helper intentionally accepts explicit file paths only. It performs local
JSON/JSONL shape checks for the TaskBench schemas used by tool descriptions,
graph descriptions, released/generated data, user requests, and predictions.
It does not call model endpoints, download data, or rewrite inputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

MAX_MESSAGES = 200


class Reporter:
    def __init__(self) -> None:
        self.checked: Dict[str, Dict[str, Any]] = {}
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self._suppressed_warnings = 0
        self._suppressed_errors = 0

    def warn(self, message: str) -> None:
        if len(self.warnings) < MAX_MESSAGES:
            self.warnings.append(message)
        else:
            self._suppressed_warnings += 1

    def error(self, message: str) -> None:
        if len(self.errors) < MAX_MESSAGES:
            self.errors.append(message)
        else:
            self._suppressed_errors += 1

    def summary(self, dependency_type: str) -> Dict[str, Any]:
        warnings = list(self.warnings)
        errors = list(self.errors)
        if self._suppressed_warnings:
            warnings.append(f"{self._suppressed_warnings} additional warnings suppressed")
        if self._suppressed_errors:
            errors.append(f"{self._suppressed_errors} additional errors suppressed")
        return {
            "ok": not errors,
            "checked": self.checked,
            "warnings": warnings,
            "errors": errors,
            "dependency_type": dependency_type,
        }


def scalar_id(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (str, int, float)):
        return str(value).strip() != ""
    return False


def context(label: str, path: Path, line: Optional[int] = None) -> str:
    if line is None:
        return f"{label} {path}"
    return f"{label} {path} line {line}"


def read_json(path: Path, label: str, reporter: Reporter) -> Optional[Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        reporter.error(f"{label}: file does not exist: {path}")
    except json.JSONDecodeError as exc:
        reporter.error(f"{label}: invalid JSON in {path}: {exc}")
    except OSError as exc:
        reporter.error(f"{label}: cannot read {path}: {exc}")
    return None


def read_rows(path: Path, label: str, reporter: Reporter) -> List[Tuple[int, Any]]:
    """Read JSONL rows, also accepting a top-level JSON array as a convenience."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        reporter.error(f"{label}: file does not exist: {path}")
        return []
    except OSError as exc:
        reporter.error(f"{label}: cannot read {path}: {exc}")
        return []

    stripped = text.strip()
    if not stripped:
        reporter.warn(f"{label}: file is empty: {path}")
        return []

    if stripped.startswith("["):
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as exc:
            reporter.error(f"{label}: invalid JSON array in {path}: {exc}")
            return []
        if not isinstance(obj, list):
            reporter.error(f"{label}: top-level JSON value in {path} must be a list when not JSONL")
            return []
        return [(idx + 1, row) for idx, row in enumerate(obj)]

    rows: List[Tuple[int, Any]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append((line_no, json.loads(line)))
        except json.JSONDecodeError as exc:
            reporter.error(f"{label}: invalid JSONL at {path} line {line_no}: {exc}")
    return rows


def infer_dependency_from_nodes(nodes: Sequence[Dict[str, Any]]) -> Optional[str]:
    if not nodes:
        return None
    all_temporal = all("parameters" in node for node in nodes)
    all_resource = all("input-type" in node and "output-type" in node for node in nodes)
    any_temporal = any("parameters" in node for node in nodes)
    any_resource = any("input-type" in node or "output-type" in node for node in nodes)

    # Some temporal fixtures carry resource-looking fields as metadata; the
    # parameters list is the decisive TaskBench temporal contract.
    if all_temporal:
        return "temporal"
    if all_resource and not any_temporal:
        return "resource"
    if any_temporal and not any_resource:
        return "temporal"
    if any_resource and not any_temporal:
        return "resource"
    if any_temporal or any_resource:
        return "mixed"
    return None


def validate_parameter_list(value: Any, label: str, reporter: Reporter) -> None:
    if not isinstance(value, list):
        reporter.error(f"{label}: temporal node must have list field 'parameters'")
        return
    for idx, parameter in enumerate(value):
        if not isinstance(parameter, dict):
            reporter.warn(f"{label}: parameters[{idx}] should be an object")
            continue
        if "name" not in parameter or "type" not in parameter:
            reporter.warn(f"{label}: parameters[{idx}] should include name and type")


def validate_nodes_document(
    obj: Any,
    *,
    label: str,
    path: Path,
    requested_dependency_type: str,
    reporter: Reporter,
    require_graph_links: bool,
) -> Optional[str]:
    checked: Dict[str, Any] = {"path": str(path)}
    reporter.checked[label] = checked

    if not isinstance(obj, dict):
        reporter.error(f"{label}: top-level JSON must be an object: {path}")
        return None

    nodes = obj.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        reporter.error(f"{label}: top-level object must contain a non-empty 'nodes' list: {path}")
        checked["nodes"] = 0
        return None

    node_ids: List[str] = []
    valid_nodes: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for idx, node in enumerate(nodes):
        node_label = f"{label}: node[{idx}]"
        if not isinstance(node, dict):
            reporter.error(f"{node_label} must be an object")
            continue
        node_id = node.get("id")
        if not scalar_id(node_id):
            reporter.error(f"{node_label} must have a non-empty scalar id")
            continue
        node_id_s = str(node_id)
        if node_id_s in seen:
            reporter.error(f"{label}: duplicate node id: {node_id_s}")
        seen.add(node_id_s)
        node_ids.append(node_id_s)
        valid_nodes.append(node)

    inferred = infer_dependency_from_nodes(valid_nodes)
    checked["nodes"] = len(valid_nodes)
    if inferred in {"resource", "temporal"}:
        checked["inferred_dependency_type"] = inferred
    elif inferred == "mixed":
        checked["inferred_dependency_type"] = "mixed"
        if requested_dependency_type == "auto":
            reporter.error(f"{label}: nodes mix resource and temporal schema clues; pass an explicit --dependency-type after normalizing the fixture")
    else:
        checked["inferred_dependency_type"] = "unknown"

    effective_type: Optional[str]
    if requested_dependency_type == "auto":
        effective_type = inferred if inferred in {"resource", "temporal"} else None
    else:
        effective_type = requested_dependency_type

    if effective_type is None:
        reporter.warn(f"{label}: could not infer dependency type; skipped resource/temporal node-field checks")
    else:
        for idx, node in enumerate(valid_nodes):
            node_name = str(node.get("id", idx))
            node_label = f"{label}: node {node_name!r}"
            if effective_type == "resource":
                for field in ("input-type", "output-type"):
                    if not isinstance(node.get(field), list):
                        reporter.error(f"{node_label} must have list field {field!r} for resource dependency")
            else:
                validate_parameter_list(node.get("parameters"), node_label, reporter)

    if require_graph_links:
        links = obj.get("links")
        if links is None:
            reporter.warn(f"{label}: graph_desc has no 'links' list")
            checked["links"] = 0
        elif not isinstance(links, list):
            reporter.error(f"{label}: 'links' must be a list")
            checked["links"] = 0
        else:
            checked["links"] = len(links)
            node_id_set = set(node_ids)
            for idx, link in enumerate(links):
                link_label = f"{label}: link[{idx}]"
                if not isinstance(link, dict):
                    reporter.error(f"{link_label} must be an object")
                    continue
                source = link.get("source")
                target = link.get("target")
                if not scalar_id(source) or not scalar_id(target):
                    reporter.error(f"{link_label} must have scalar source and target")
                    continue
                if str(source) not in node_id_set:
                    reporter.error(f"{link_label} references unknown source node {source!r}")
                if str(target) not in node_id_set:
                    reporter.error(f"{link_label} references unknown target node {target!r}")

    return inferred if inferred in {"resource", "temporal"} else None


def choose_dependency_type(requested: str, inferred_values: Iterable[Optional[str]], reporter: Reporter) -> str:
    if requested != "auto":
        return requested
    values = [value for value in inferred_values if value in {"resource", "temporal"}]
    unique = sorted(set(values))
    if not unique:
        reporter.warn("dependency type remains auto; no resource or temporal node schema was available")
        return "auto"
    if len(unique) > 1:
        reporter.error(f"conflicting dependency type clues: {', '.join(unique)}")
        return "auto"
    return unique[0]


def pick_field(row: Dict[str, Any], normalized: str, legacy: str) -> Tuple[Optional[str], Optional[Any], str]:
    if normalized in row:
        return normalized, row.get(normalized), "normalized"
    if legacy in row:
        return legacy, row.get(legacy), "legacy"
    return None, None, "missing"


def coerce_list(value: Any, *, field: str, where: str, reporter: Reporter) -> Optional[List[Any]]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("["):
            try:
                decoded = json.loads(stripped)
            except json.JSONDecodeError as exc:
                reporter.error(f"{where}: field {field!r} is a JSON string but does not decode: {exc}")
                return None
            if isinstance(decoded, list):
                reporter.warn(f"{where}: field {field!r} is a JSON-encoded string; native evaluation needs a real list")
                return decoded
    reporter.error(f"{where}: field {field!r} must be a list")
    return None


def add_list_problem(reporter: Reporter, strict: bool, message: str) -> None:
    if strict:
        reporter.error(message)
    else:
        reporter.warn(message)


def validate_task_node_list(nodes: Optional[List[Any]], *, where: str, dependency_type: str, reporter: Reporter, strict: bool = True) -> None:
    if nodes is None:
        return
    for idx, node in enumerate(nodes):
        node_where = f"{where}: task_nodes[{idx}]"
        if not isinstance(node, dict):
            add_list_problem(reporter, strict, f"{node_where} must be an object")
            continue
        task = node.get("task")
        if not isinstance(task, str) or not task.strip():
            add_list_problem(reporter, strict, f"{node_where} should contain non-empty string field 'task'")
        if "arguments" in node and not isinstance(node.get("arguments"), list):
            add_list_problem(reporter, strict, f"{node_where} field 'arguments' should be a list")
        if dependency_type == "temporal" and isinstance(node.get("arguments"), list):
            for arg_idx, argument in enumerate(node["arguments"]):
                if not isinstance(argument, dict):
                    add_list_problem(reporter, strict, f"{node_where}: temporal arguments[{arg_idx}] should be an object")
                elif "name" not in argument or "value" not in argument:
                    add_list_problem(reporter, strict, f"{node_where}: temporal arguments[{arg_idx}] should contain name and value")


def validate_link_list(links: Optional[List[Any]], *, field_name: str, where: str, reporter: Reporter, strict: bool = True) -> None:
    if links is None:
        return
    for idx, link in enumerate(links):
        link_where = f"{where}: {field_name}[{idx}]"
        if not isinstance(link, dict):
            add_list_problem(reporter, strict, f"{link_where} should be an object")
            continue
        if "source" not in link or "target" not in link:
            add_list_problem(reporter, strict, f"{link_where} should contain source and target")


def validate_data_rows(path: Path, reporter: Reporter, dependency_type: str) -> None:
    label = "data_jsonl"
    rows = read_rows(path, label, reporter)
    checked = {"path": str(path), "rows": len(rows), "normalized_rows": 0, "legacy_rows": 0}
    reporter.checked[label] = checked
    ids: set[str] = set()

    for line_no, row in rows:
        where = context(label, path, line_no)
        if not isinstance(row, dict):
            reporter.error(f"{where}: row must be an object")
            continue
        row_id = row.get("id")
        if not scalar_id(row_id):
            reporter.error(f"{where}: row must contain a non-empty scalar id")
        else:
            row_id_s = str(row_id)
            if row_id_s in ids:
                reporter.error(f"{where}: duplicate id {row_id_s!r}")
            ids.add(row_id_s)

        request_field, request_value, request_mode = pick_field(row, "user_request", "instruction")
        if request_field is None or not isinstance(request_value, str) or not request_value.strip():
            reporter.error(f"{where}: row must contain non-empty user_request or instruction")

        steps_field, steps_value, steps_mode = pick_field(row, "task_steps", "tool_steps")
        nodes_field, nodes_value, nodes_mode = pick_field(row, "task_nodes", "tool_nodes")
        links_field, links_value, links_mode = pick_field(row, "task_links", "tool_links")
        modes = {request_mode, steps_mode, nodes_mode, links_mode}
        if "legacy" in modes:
            checked["legacy_rows"] += 1
        if "normalized" in modes:
            checked["normalized_rows"] += 1

        if steps_field is None:
            reporter.error(f"{where}: row must contain task_steps or tool_steps")
            steps = None
        else:
            steps = coerce_list(steps_value, field=steps_field, where=where, reporter=reporter)
        if nodes_field is None:
            reporter.error(f"{where}: row must contain task_nodes or tool_nodes")
            nodes = None
        else:
            nodes = coerce_list(nodes_value, field=nodes_field, where=where, reporter=reporter)
        if links_field is None:
            reporter.error(f"{where}: row must contain task_links or tool_links, using [] for single-node rows")
            links = None
        else:
            links = coerce_list(links_value, field=links_field, where=where, reporter=reporter)

        if steps is not None and not steps:
            reporter.warn(f"{where}: steps list is empty")
        validate_task_node_list(nodes, where=where, dependency_type=dependency_type, reporter=reporter)
        validate_link_list(links, field_name=links_field or "task_links", where=where, reporter=reporter)

    if checked["legacy_rows"]:
        reporter.warn(f"{label}: {checked['legacy_rows']} row(s) use legacy instruction/tool_* field names; convert a temporary copy before native evaluation")


def validate_user_request_rows(path: Path, reporter: Reporter) -> None:
    label = "user_requests_jsonl"
    rows = read_rows(path, label, reporter)
    reporter.checked[label] = {"path": str(path), "rows": len(rows)}
    ids: set[str] = set()
    for line_no, row in rows:
        where = context(label, path, line_no)
        if not isinstance(row, dict):
            reporter.error(f"{where}: row must be an object")
            continue
        row_id = row.get("id")
        if not scalar_id(row_id):
            reporter.error(f"{where}: row must contain a non-empty scalar id")
        else:
            row_id_s = str(row_id)
            if row_id_s in ids:
                reporter.error(f"{where}: duplicate id {row_id_s!r}")
            ids.add(row_id_s)
        user_request = row.get("user_request")
        if not isinstance(user_request, str) or not user_request.strip():
            reporter.error(f"{where}: row must contain non-empty string field 'user_request'")


def validate_prediction_rows(path: Path, reporter: Reporter, dependency_type: str, strict: bool) -> None:
    label = "predictions_jsonl"
    rows = read_rows(path, label, reporter)
    checked = {"path": str(path), "rows": len(rows), "rows_with_result": 0, "input_style_rows": 0, "strict": strict}
    reporter.checked[label] = checked
    ids: set[str] = set()

    for line_no, row in rows:
        where = context(label, path, line_no)
        if not isinstance(row, dict):
            reporter.error(f"{where}: row must be an object")
            continue
        row_id = row.get("id")
        if not scalar_id(row_id):
            reporter.error(f"{where}: row must contain a non-empty scalar id")
        else:
            row_id_s = str(row_id)
            if row_id_s in ids:
                reporter.error(f"{where}: duplicate id {row_id_s!r}")
            ids.add(row_id_s)

        if "result" not in row:
            if not strict and isinstance(row.get("user_request"), str) and row["user_request"].strip():
                checked["input_style_rows"] += 1
                continue
            reporter.error(f"{where}: prediction row must contain result" + ("" if strict else " or be an input-style row with user_request"))
            continue

        result = row.get("result")
        if not isinstance(result, dict):
            reporter.error(f"{where}: result must be an object")
            continue
        checked["rows_with_result"] += 1

        for field in ("task_steps", "task_nodes"):
            if field not in result:
                add_list_problem(reporter, strict, f"{where}: result should contain list field {field!r}")
                value = None
            else:
                value = result.get(field)
                if not isinstance(value, list):
                    add_list_problem(reporter, strict, f"{where}: result field {field!r} should be a list")
                    value = None
            if field == "task_nodes":
                validate_task_node_list(value, where=f"{where}: result", dependency_type=dependency_type, reporter=reporter, strict=strict)

        if "task_links" in result:
            links_value = result.get("task_links")
            if not isinstance(links_value, list):
                add_list_problem(reporter, strict, f"{where}: result field 'task_links' should be a list")
                links_value = None
            validate_link_list(links_value, field_name="task_links", where=f"{where}: result", reporter=reporter, strict=strict)
        elif dependency_type == "temporal":
            add_list_problem(reporter, strict, f"{where}: temporal predictions should include result.task_links")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate TaskBench fixture JSON/JSONL files and emit a JSON summary."
    )
    parser.add_argument("--tool-desc", help="Path to tool_desc.json.")
    parser.add_argument("--graph-desc", help="Path to graph_desc.json.")
    parser.add_argument("--data-jsonl", help="Path to data JSONL/JSON-array file.")
    parser.add_argument("--user-requests-jsonl", help="Path to user_requests JSONL/JSON-array file.")
    parser.add_argument("--predictions-jsonl", help="Path to prediction JSONL/JSON-array file.")
    parser.add_argument("--dependency-type", default="auto", choices=["auto", "resource", "temporal"], help="Validate resource or temporal node/result contracts; auto infers from node schemas when available.")
    parser.add_argument("--strict", action="store_true", help="Require prediction rows to contain result objects and promote result-shape issues to errors.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    reporter = Reporter()
    inferred: List[Optional[str]] = []

    if args.tool_desc:
        path = Path(args.tool_desc)
        obj = read_json(path, "tool_desc", reporter)
        if obj is not None:
            inferred.append(
                validate_nodes_document(
                    obj,
                    label="tool_desc",
                    path=path,
                    requested_dependency_type=args.dependency_type,
                    reporter=reporter,
                    require_graph_links=False,
                )
            )

    if args.graph_desc:
        path = Path(args.graph_desc)
        obj = read_json(path, "graph_desc", reporter)
        if obj is not None:
            inferred.append(
                validate_nodes_document(
                    obj,
                    label="graph_desc",
                    path=path,
                    requested_dependency_type=args.dependency_type,
                    reporter=reporter,
                    require_graph_links=True,
                )
            )

    dependency_type = choose_dependency_type(args.dependency_type, inferred, reporter)

    if args.data_jsonl:
        validate_data_rows(Path(args.data_jsonl), reporter, dependency_type)
    if args.user_requests_jsonl:
        validate_user_request_rows(Path(args.user_requests_jsonl), reporter)
    if args.predictions_jsonl:
        validate_prediction_rows(Path(args.predictions_jsonl), reporter, dependency_type, args.strict)

    if not any([args.tool_desc, args.graph_desc, args.data_jsonl, args.user_requests_jsonl, args.predictions_jsonl]):
        reporter.warn("no input files were provided; nothing was validated")

    summary = reporter.summary(dependency_type)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
