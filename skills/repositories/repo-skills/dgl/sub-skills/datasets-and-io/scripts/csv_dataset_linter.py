#!/usr/bin/env python3
"""Validate a DGL CSVDataset folder without importing DGL.

Checks meta.yaml, referenced CSV files, required ID columns, heterograph
ntype/etype structure, duplicate raw node IDs, edge endpoints, and empty
feature cells. The script is read-only and deterministic.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover - depends on caller environment
    yaml = None


DEFAULT_NTYPE = "_V"
DEFAULT_ETYPE = ["_V", "_E", "_V"]
DEFAULT_GRAPH_ID = "graph_id"
DEFAULT_NODE_ID = "node_id"
DEFAULT_SRC_ID = "src_id"
DEFAULT_DST_ID = "dst_id"


@dataclass
class Finding:
    level: str
    message: str


class LintState:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def error(self, message: str) -> None:
        self.findings.append(Finding("ERROR", message))

    def warn(self, message: str) -> None:
        self.findings.append(Finding("WARN", message))

    @property
    def error_count(self) -> int:
        return sum(1 for finding in self.findings if finding.level == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for finding in self.findings if finding.level == "WARN")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint a DGL CSVDataset directory containing meta.yaml and CSV files."
    )
    parser.add_argument("dataset_dir", help="Directory containing meta.yaml.")
    parser.add_argument(
        "--max-endpoint-errors",
        type=int,
        default=20,
        help="Maximum missing edge endpoint examples to report per edge CSV (default: 20).",
    )
    parser.add_argument(
        "--allow-empty-features",
        action="store_true",
        help="Do not warn on empty non-ID feature cells.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only the summary and errors/warnings, not successful checks.",
    )
    return parser.parse_args()


def strip_yaml_comment(line: str) -> str:
    in_single = False
    in_double = False
    previous = ""
    for index, character in enumerate(line):
        if character == "'" and not in_double:
            in_single = not in_single
        elif character == '"' and not in_single and previous != "\\":
            in_double = not in_double
        elif character == "#" and not in_single and not in_double:
            return line[:index]
        previous = character
    return line


def split_key_value(text: str) -> tuple[str, str] | None:
    in_single = False
    in_double = False
    previous = ""
    for index, character in enumerate(text):
        if character == "'" and not in_double:
            in_single = not in_single
        elif character == '"' and not in_single and previous != "\\":
            in_double = not in_double
        elif character == ":" and not in_single and not in_double:
            return text[:index].strip(), text[index + 1 :].strip()
        previous = character
    return None


def split_flow_list(text: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    previous = ""
    for character in text:
        if character == "'" and not in_double:
            in_single = not in_single
        elif character == '"' and not in_single and previous != "\\":
            in_double = not in_double
        elif character == "," and not in_single and not in_double:
            items.append("".join(current).strip())
            current = []
            previous = character
            continue
        current.append(character)
        previous = character
    items.append("".join(current).strip())
    return items


def parse_yaml_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_yaml_scalar(item) for item in split_flow_list(inner)]
    lowered = value.lower()
    if lowered in {"null", "none", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return value


def load_yaml_subset(path: Path, state: LintState) -> dict[str, Any] | None:
    data: dict[str, Any] = {}
    current_key: str | None = None
    current_list_item: dict[str, Any] | None = None
    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:  # noqa: BLE001 - report parser detail to caller
        state.error(f"failed to read {path.name}: {exc}")
        return None
    for line_number, raw_line in enumerate(raw_lines, start=1):
        without_comment = strip_yaml_comment(raw_line).rstrip()
        if not without_comment.strip():
            continue
        indent = len(without_comment) - len(without_comment.lstrip(" "))
        stripped = without_comment.strip()
        if indent == 0:
            pair = split_key_value(stripped)
            if pair is None:
                state.error(f"unsupported YAML syntax at {path.name}:{line_number}: {stripped}")
                return None
            key, value = pair
            if not key:
                state.error(f"empty YAML key at {path.name}:{line_number}")
                return None
            if value == "":
                data[key] = None
                current_key = key
                current_list_item = None
            else:
                data[key] = parse_yaml_scalar(value)
                current_key = None
                current_list_item = None
            continue
        if current_key is None:
            state.error(f"unexpected indented YAML content at {path.name}:{line_number}: {stripped}")
            return None
        if indent >= 2 and stripped.startswith("- "):
            if data[current_key] is None:
                data[current_key] = []
            if not isinstance(data[current_key], list):
                state.error(f"mixed YAML list/mapping content under {current_key!r} at {path.name}:{line_number}")
                return None
            item_text = stripped[2:].strip()
            item: dict[str, Any] = {}
            if item_text:
                pair = split_key_value(item_text)
                if pair is None:
                    state.error(f"unsupported YAML list item at {path.name}:{line_number}: {stripped}")
                    return None
                key, value = pair
                item[key] = parse_yaml_scalar(value)
            data[current_key].append(item)
            current_list_item = item
            continue
        pair = split_key_value(stripped)
        if pair is None:
            state.error(f"unsupported YAML nested content at {path.name}:{line_number}: {stripped}")
            return None
        key, value = pair
        if isinstance(data[current_key], list):
            if current_list_item is None:
                state.error(f"YAML property without list item at {path.name}:{line_number}: {stripped}")
                return None
            current_list_item[key] = parse_yaml_scalar(value)
        else:
            if data[current_key] is None:
                data[current_key] = {}
            if not isinstance(data[current_key], dict):
                state.error(f"mixed YAML scalar/mapping content under {current_key!r} at {path.name}:{line_number}")
                return None
            data[current_key][key] = parse_yaml_scalar(value)
    return data


def load_yaml(path: Path, state: LintState) -> dict[str, Any] | None:
    if yaml is not None:
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
        except Exception as exc:  # noqa: BLE001 - report parser detail to caller
            state.error(f"failed to parse {path.name}: {exc}")
            return None
    else:
        state.warn("PyYAML is not installed; using the built-in parser for simple CSVDataset meta.yaml files.")
        data = load_yaml_subset(path, state)
    if not isinstance(data, dict):
        state.error("meta.yaml must contain a YAML mapping at the top level.")
        return None
    return data


def as_list(value: Any, field: str, state: LintState) -> list[Any]:
    if isinstance(value, list):
        return value
    state.error(f"{field} must be a list.")
    return []


def as_mapping(value: Any, field: str, state: LintState) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    state.error(f"{field} entries must be mappings.")
    return None


def rel_path(dataset_dir: Path, file_name: Any, field: str, state: LintState) -> Path | None:
    if not isinstance(file_name, str) or not file_name:
        state.error(f"{field} requires non-empty string file_name.")
        return None
    path = Path(file_name)
    if path.is_absolute():
        state.warn(f"{field} uses an absolute file_name; portable CSVDataset folders should use relative paths: {file_name}")
        return path
    if ".." in path.parts:
        state.warn(f"{field} file_name traverses parent directories; keep dataset files under the dataset folder: {file_name}")
    return dataset_dir / path


def read_csv(path: Path, separator: str, state: LintState) -> tuple[list[str], list[dict[str, str]]] | None:
    if not path.exists():
        state.error(f"CSV file does not exist: {path}")
        return None
    if not path.is_file():
        state.error(f"CSV path is not a file: {path}")
        return None
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=separator)
            if reader.fieldnames is None:
                state.error(f"CSV file has no header: {path}")
                return None
            rows = list(reader)
    except Exception as exc:  # noqa: BLE001 - surface CSV detail
        state.error(f"failed to read CSV {path}: {exc}")
        return None
    headers = [header if header is not None else "" for header in reader.fieldnames]
    if any(header == "" for header in headers):
        state.warn(f"CSV file has empty header cells: {path}")
    unnamed = [header for header in headers if "Unnamed" in header]
    if unnamed:
        state.warn(f"CSV file contains pandas index-like columns ignored by DGL default parser: {path}: {unnamed}")
    return headers, rows


def require_columns(headers: Iterable[str], columns: Iterable[str], label: str, state: LintState) -> None:
    header_set = set(headers)
    for column in columns:
        if column not in header_set:
            state.error(f"{label} missing required column: {column}")


def check_empty_features(
    rows: list[dict[str, str]],
    headers: list[str],
    id_columns: set[str],
    label: str,
    allow_empty: bool,
    state: LintState,
) -> None:
    if allow_empty:
        return
    feature_headers = [header for header in headers if header not in id_columns and "Unnamed" not in header]
    for header in feature_headers:
        empty_rows = [index + 2 for index, row in enumerate(rows) if row.get(header, "") == ""]
        if empty_rows:
            preview = ", ".join(str(row) for row in empty_rows[:5])
            suffix = "" if len(empty_rows) <= 5 else f" and {len(empty_rows) - 5} more"
            state.warn(f"{label} feature column {header!r} has empty cells at CSV rows {preview}{suffix}; DGL's default parser does not support missing feature values.")


def normalize_scalar(value: Any) -> str:
    return "" if value is None else str(value)


def lint(dataset_dir: Path, max_endpoint_errors: int, allow_empty_features: bool, quiet: bool) -> LintState:
    state = LintState()
    dataset_dir = dataset_dir.expanduser().resolve()
    if not dataset_dir.exists():
        state.error(f"dataset directory does not exist: {dataset_dir}")
        return state
    if not dataset_dir.is_dir():
        state.error(f"dataset path is not a directory: {dataset_dir}")
        return state

    meta_path = dataset_dir / "meta.yaml"
    if not meta_path.exists():
        state.error(f"meta.yaml not found under dataset directory: {dataset_dir}")
        return state

    meta = load_yaml(meta_path, state)
    if meta is None:
        return state

    version = meta.get("version", "1.0.0")
    if str(version) != "1.0.0":
        state.error(f"unsupported CSVDataset version {version!r}; expected '1.0.0'.")

    dataset_name = meta.get("dataset_name")
    if not isinstance(dataset_name, str) or not dataset_name:
        state.error("dataset_name is required and must be a non-empty string.")

    separator = meta.get("separator", ",")
    if not isinstance(separator, str) or len(separator) != 1:
        state.error("separator must be a one-character string.")
        separator = ","

    node_entries = as_list(meta.get("node_data"), "node_data", state)
    edge_entries = as_list(meta.get("edge_data"), "edge_data", state)
    if not node_entries:
        state.error("node_data must contain at least one node CSV entry.")
    if not edge_entries:
        state.error("edge_data must contain at least one edge CSV entry.")

    node_ids_by_type_graph: dict[tuple[str, str], set[str]] = {}
    node_types: set[str] = set()
    seen_node_types: set[str] = set()

    for index, raw_entry in enumerate(node_entries):
        entry = as_mapping(raw_entry, f"node_data[{index}]", state)
        if entry is None:
            continue
        ntype = normalize_scalar(entry.get("ntype", DEFAULT_NTYPE)) or DEFAULT_NTYPE
        if ntype in seen_node_types:
            state.error(f"duplicate node type in node_data: {ntype}")
        seen_node_types.add(ntype)
        node_types.add(ntype)

        node_id_field = normalize_scalar(entry.get("node_id_field", DEFAULT_NODE_ID)) or DEFAULT_NODE_ID
        graph_id_field = normalize_scalar(entry.get("graph_id_field", DEFAULT_GRAPH_ID)) or DEFAULT_GRAPH_ID
        path = rel_path(dataset_dir, entry.get("file_name"), f"node_data[{index}]", state)
        if path is None:
            continue
        csv_data = read_csv(path, separator, state)
        if csv_data is None:
            continue
        headers, rows = csv_data
        require_columns(headers, [node_id_field], f"node_data[{index}] {path.name}", state)
        id_columns = {node_id_field, graph_id_field}
        check_empty_features(rows, headers, id_columns, f"node_data[{index}] {path.name}", allow_empty_features, state)

        seen_by_graph: dict[str, set[str]] = {}
        duplicate_examples: list[str] = []
        for row_number, row in enumerate(rows, start=2):
            raw_node_id = row.get(node_id_field, "")
            if raw_node_id == "":
                state.error(f"node_data[{index}] {path.name} row {row_number} has empty node id in column {node_id_field!r}.")
                continue
            graph_id = row.get(graph_id_field, "0") or "0"
            key = (ntype, graph_id)
            node_ids_by_type_graph.setdefault(key, set()).add(raw_node_id)
            graph_seen = seen_by_graph.setdefault(graph_id, set())
            if raw_node_id in graph_seen and len(duplicate_examples) < 10:
                duplicate_examples.append(f"graph_id={graph_id} node_id={raw_node_id} row={row_number}")
            graph_seen.add(raw_node_id)
        if duplicate_examples:
            state.error(f"node_data[{index}] {path.name} has duplicate node IDs within a graph/type: {duplicate_examples}")

    seen_etypes: set[tuple[str, str, str]] = set()
    for index, raw_entry in enumerate(edge_entries):
        entry = as_mapping(raw_entry, f"edge_data[{index}]", state)
        if entry is None:
            continue
        raw_etype = entry.get("etype", DEFAULT_ETYPE)
        if not isinstance(raw_etype, list) or len(raw_etype) != 3 or not all(isinstance(item, str) and item for item in raw_etype):
            state.error(f"edge_data[{index}] etype must be a three-item string list like [src_ntype, relation, dst_ntype].")
            etype = tuple(DEFAULT_ETYPE)
        else:
            etype = tuple(raw_etype)
        if etype in seen_etypes:
            state.error(f"duplicate edge type in edge_data: {etype}")
        seen_etypes.add(etype)
        src_type, _, dst_type = etype
        if src_type not in node_types:
            state.error(f"edge_data[{index}] source node type {src_type!r} is not declared in node_data.")
        if dst_type not in node_types:
            state.error(f"edge_data[{index}] destination node type {dst_type!r} is not declared in node_data.")

        src_field = normalize_scalar(entry.get("src_id_field", DEFAULT_SRC_ID)) or DEFAULT_SRC_ID
        dst_field = normalize_scalar(entry.get("dst_id_field", DEFAULT_DST_ID)) or DEFAULT_DST_ID
        graph_id_field = normalize_scalar(entry.get("graph_id_field", DEFAULT_GRAPH_ID)) or DEFAULT_GRAPH_ID
        path = rel_path(dataset_dir, entry.get("file_name"), f"edge_data[{index}]", state)
        if path is None:
            continue
        csv_data = read_csv(path, separator, state)
        if csv_data is None:
            continue
        headers, rows = csv_data
        require_columns(headers, [src_field, dst_field], f"edge_data[{index}] {path.name}", state)
        id_columns = {src_field, dst_field, graph_id_field}
        check_empty_features(rows, headers, id_columns, f"edge_data[{index}] {path.name}", allow_empty_features, state)

        missing_endpoint_examples: list[str] = []
        for row_number, row in enumerate(rows, start=2):
            graph_id = row.get(graph_id_field, "0") or "0"
            src = row.get(src_field, "")
            dst = row.get(dst_field, "")
            if src == "":
                state.error(f"edge_data[{index}] {path.name} row {row_number} has empty src id in column {src_field!r}.")
                continue
            if dst == "":
                state.error(f"edge_data[{index}] {path.name} row {row_number} has empty dst id in column {dst_field!r}.")
                continue
            src_ids = node_ids_by_type_graph.get((src_type, graph_id), set())
            dst_ids = node_ids_by_type_graph.get((dst_type, graph_id), set())
            if src not in src_ids and len(missing_endpoint_examples) < max_endpoint_errors:
                missing_endpoint_examples.append(f"row {row_number}: src_id={src!r} missing from ntype={src_type!r}, graph_id={graph_id!r}")
            if dst not in dst_ids and len(missing_endpoint_examples) < max_endpoint_errors:
                missing_endpoint_examples.append(f"row {row_number}: dst_id={dst!r} missing from ntype={dst_type!r}, graph_id={graph_id!r}")
        if missing_endpoint_examples:
            state.error(f"edge_data[{index}] {path.name} has endpoints absent from node CSVs: {missing_endpoint_examples}")

    graph_entry = meta.get("graph_data")
    graph_ids_in_graph_csv: set[str] | None = None
    if graph_entry is not None:
        entry = as_mapping(graph_entry, "graph_data", state)
        if entry is not None:
            graph_id_field = normalize_scalar(entry.get("graph_id_field", DEFAULT_GRAPH_ID)) or DEFAULT_GRAPH_ID
            path = rel_path(dataset_dir, entry.get("file_name"), "graph_data", state)
            if path is not None:
                csv_data = read_csv(path, separator, state)
                if csv_data is not None:
                    headers, rows = csv_data
                    require_columns(headers, [graph_id_field], f"graph_data {path.name}", state)
                    check_empty_features(rows, headers, {graph_id_field}, f"graph_data {path.name}", allow_empty_features, state)
                    graph_ids_in_graph_csv = {row.get(graph_id_field, "") for row in rows if row.get(graph_id_field, "") != ""}

    if graph_ids_in_graph_csv is not None:
        graph_ids_from_nodes = {graph_id for (_, graph_id) in node_ids_by_type_graph.keys()}
        missing_graph_ids = sorted(graph_ids_from_nodes - graph_ids_in_graph_csv)
        if missing_graph_ids:
            state.error(f"graph_data is missing graph IDs present in node/edge CSVs: {missing_graph_ids[:20]}")

    if not quiet and state.error_count == 0:
        state.findings.insert(0, Finding("OK", f"{dataset_dir} looks structurally compatible with dgl.data.CSVDataset."))
    return state


def main() -> int:
    args = parse_args()
    state = lint(
        Path(args.dataset_dir),
        max_endpoint_errors=max(args.max_endpoint_errors, 0),
        allow_empty_features=args.allow_empty_features,
        quiet=args.quiet,
    )
    for finding in state.findings:
        print(f"{finding.level}: {finding.message}")
    print(f"Summary: {state.error_count} error(s), {state.warning_count} warning(s)")
    return 1 if state.error_count else 0


if __name__ == "__main__":
    sys.exit(main())
