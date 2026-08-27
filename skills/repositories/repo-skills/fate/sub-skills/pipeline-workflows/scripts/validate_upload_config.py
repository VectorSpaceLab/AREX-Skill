#!/usr/bin/env python3
"""Validate FATE Pipeline upload-config YAML without contacting FateFlow.

The checker is intentionally local and conservative. It validates the shape
observed in FATE 2.2 example upload configs: top-level ``data`` list, per-item
``file``/``meta``/``table_name``/``namespace`` fields, upload booleans, partition
count, and common dense CSV metadata. It never imports fate_client and never
opens a network connection.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover - depends on caller env
    yaml = None
    YAML_IMPORT_ERROR = exc
else:
    YAML_IMPORT_ERROR = None

ROLE_RE = re.compile(r"^(guest|host|arbiter|local)(?:_\d+)?$")
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def load_yaml(path: Path) -> Any:
    if yaml is None:
        raise RuntimeError(
            "PyYAML is required to parse upload configs; install pyyaml or run in the FATE inspection env"
        ) from YAML_IMPORT_ERROR
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def as_path(base_dir: Path, file_value: str) -> Path:
    candidate = Path(file_value)
    if candidate.is_absolute():
        return candidate
    return base_dir / candidate


def add(levels: dict[str, list[str]], level: str, message: str) -> None:
    levels[level].append(message)


def validate_item(
    item: Any,
    idx: int,
    source: Path,
    base_dir: Path,
    check_files: bool,
    seen_exact: Counter,
    table_roles: defaultdict[tuple[str, str], set[str]],
) -> dict[str, Any]:
    levels: dict[str, list[str]] = {"errors": [], "warnings": []}
    summary: dict[str, Any] = {
        "index": idx,
        "file": None,
        "namespace": None,
        "table_name": None,
        "role": None,
        "partition_count": None,
        "meta_keys": [],
    }

    prefix = f"{source}:{idx}"
    if not isinstance(item, dict):
        add(levels, "errors", f"{prefix}: data item must be a mapping")
        summary.update(levels)
        return summary

    file_value = item.get("file")
    if not is_nonempty_str(file_value):
        add(levels, "errors", f"{prefix}: missing non-empty 'file'")
    else:
        summary["file"] = file_value
        if check_files:
            candidate = as_path(base_dir, file_value)
            if not candidate.exists():
                add(levels, "errors", f"{prefix}: file does not exist under base dir: {candidate}")

    namespace = item.get("namespace")
    if not is_nonempty_str(namespace):
        add(levels, "errors", f"{prefix}: missing non-empty 'namespace'")
    else:
        summary["namespace"] = namespace
        if not SAFE_NAME_RE.match(namespace):
            add(levels, "warnings", f"{prefix}: namespace contains unusual characters: {namespace!r}")

    table_name = item.get("table_name")
    if table_name is None and is_nonempty_str(item.get("name")):
        table_name = item.get("name")
        add(levels, "warnings", f"{prefix}: used 'name'; upload YAML examples use 'table_name'")
    if not is_nonempty_str(table_name):
        add(levels, "errors", f"{prefix}: missing non-empty 'table_name'")
    else:
        summary["table_name"] = table_name
        if not SAFE_NAME_RE.match(table_name):
            add(levels, "warnings", f"{prefix}: table_name contains unusual characters: {table_name!r}")
        if is_nonempty_str(file_value):
            stem = Path(file_value).stem
            if stem and stem != table_name:
                add(
                    levels,
                    "warnings",
                    f"{prefix}: table_name {table_name!r} does not match file stem {stem!r}; examples usually match them",
                )

    role = item.get("role")
    if role is None:
        add(levels, "warnings", f"{prefix}: missing optional 'role' label such as guest_0 or host_0")
    elif not is_nonempty_str(role):
        add(levels, "errors", f"{prefix}: role must be a non-empty string when present")
    else:
        summary["role"] = role
        if not ROLE_RE.match(role):
            add(levels, "warnings", f"{prefix}: role {role!r} does not match guest_0/host_0/local style")
        if table_name and namespace:
            exact_key = (str(namespace), str(table_name), str(role))
            seen_exact[exact_key] += 1
            table_roles[(str(namespace), str(table_name))].add(str(role))
            if seen_exact[exact_key] > 1:
                add(levels, "warnings", f"{prefix}: duplicate namespace/table/role mapping {exact_key}")
        if is_nonempty_str(file_value):
            lower_file = Path(file_value).name.lower()
            lower_role = role.lower()
            if "_host" in lower_file and lower_role.startswith("guest"):
                add(levels, "warnings", f"{prefix}: host-looking file is mapped to guest role {role!r}")
            if "_guest" in lower_file and lower_role.startswith("host"):
                add(levels, "warnings", f"{prefix}: guest-looking file is mapped to host role {role!r}")

    has_partitions = "partitions" in item
    has_partition = "partition" in item
    if has_partitions and has_partition:
        add(levels, "warnings", f"{prefix}: both 'partitions' and 'partition' are present; normalize to one spelling")
    part_value = item.get("partitions", item.get("partition"))
    if part_value is None:
        add(levels, "warnings", f"{prefix}: missing partition count ('partitions' or 'partition')")
    elif not is_positive_int(part_value):
        add(levels, "errors", f"{prefix}: partition count must be a positive integer, got {part_value!r}")
    else:
        summary["partition_count"] = part_value

    for bool_key in ("head", "extend_sid"):
        if bool_key not in item:
            add(levels, "warnings", f"{prefix}: missing recommended boolean '{bool_key}'")
        elif not isinstance(item[bool_key], bool):
            add(levels, "errors", f"{prefix}: '{bool_key}' must be a boolean")

    meta = item.get("meta")
    if not isinstance(meta, dict):
        add(levels, "errors", f"{prefix}: missing mapping 'meta'")
    else:
        summary["meta_keys"] = sorted(str(k) for k in meta.keys())
        input_format = meta.get("input_format")
        if input_format is None:
            add(levels, "warnings", f"{prefix}: meta missing 'input_format' (dense examples set it)")
        elif not is_nonempty_str(input_format):
            add(levels, "errors", f"{prefix}: meta.input_format must be a non-empty string")

        if input_format in (None, "dense") and "delimiter" not in meta:
            add(levels, "warnings", f"{prefix}: dense CSV meta usually includes 'delimiter'")
        if "match_id_name" not in meta and "match_id_list" not in meta:
            add(levels, "warnings", f"{prefix}: PSI/pipeline examples usually include 'match_id_name'")
        if item.get("extend_sid") is False and "sample_id_name" not in meta:
            add(levels, "warnings", f"{prefix}: extend_sid is false but meta has no 'sample_id_name'")
        if "label_name" in meta and "label_type" not in meta:
            add(levels, "warnings", f"{prefix}: meta has label_name but no label_type")
        if "label_type" in meta and "label_name" not in meta:
            add(levels, "warnings", f"{prefix}: meta has label_type but no label_name")
        if meta.get("tag_with_value") is True and "tag_value_delimiter" not in meta:
            add(levels, "warnings", f"{prefix}: tag_with_value is true but tag_value_delimiter is missing")

    summary.update(levels)
    return summary


def validate_config(path: Path, base_dir: Path, check_files: bool) -> dict[str, Any]:
    source = path.resolve()
    data = load_yaml(source)
    result: dict[str, Any] = {
        "path": str(source),
        "items": [],
        "errors": [],
        "warnings": [],
        "summary": {},
    }

    if not isinstance(data, dict):
        result["errors"].append(f"{source}: root document must be a mapping with top-level 'data'")
        return result
    items = data.get("data")
    if not isinstance(items, list):
        result["errors"].append(f"{source}: top-level 'data' must be a list")
        return result

    seen_exact: Counter = Counter()
    table_roles: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    for idx, item in enumerate(items):
        item_result = validate_item(item, idx, source, base_dir, check_files, seen_exact, table_roles)
        result["items"].append(item_result)
        result["errors"].extend(item_result["errors"])
        result["warnings"].extend(item_result["warnings"])

    namespaces = Counter(i.get("namespace") for i in result["items"] if i.get("namespace"))
    roles = Counter(i.get("role") for i in result["items"] if i.get("role"))
    tables = Counter(i.get("table_name") for i in result["items"] if i.get("table_name"))
    multi_role_tables = {
        f"{namespace}/{table}": sorted(roles_for_table)
        for (namespace, table), roles_for_table in table_roles.items()
        if len(roles_for_table) > 1
    }
    result["summary"] = {
        "item_count": len(items),
        "namespace_counts": dict(sorted(namespaces.items())),
        "role_counts": dict(sorted(roles.items())),
        "unique_table_count": len(tables),
        "multi_role_tables": multi_role_tables,
    }
    return result


def print_text(results: list[dict[str, Any]]) -> None:
    for result in results:
        summary = result["summary"]
        print(f"{result['path']}")
        if summary:
            print(f"  items: {summary['item_count']}")
            print(f"  namespaces: {summary['namespace_counts']}")
            print(f"  roles: {summary['role_counts']}")
            print(f"  unique tables: {summary['unique_table_count']}")
            if summary["multi_role_tables"]:
                print(f"  tables mapped to multiple roles: {summary['multi_role_tables']}")
        print(f"  errors: {len(result['errors'])}")
        for message in result["errors"]:
            print(f"    ERROR: {message}")
        print(f"  warnings: {len(result['warnings'])}")
        for message in result["warnings"]:
            print(f"    WARN: {message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("configs", nargs="+", type=Path, help="upload_config YAML file(s) to validate")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path.cwd(),
        help="base directory for relative file paths when --check-files is enabled (default: current directory)",
    )
    parser.add_argument("--check-files", action="store_true", help="also require referenced local data files to exist")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--strict-warnings", action="store_true", help="return nonzero if warnings are present")
    args = parser.parse_args(argv)

    results: list[dict[str, Any]] = []
    fatal_errors: list[str] = []
    for config in args.configs:
        try:
            results.append(validate_config(config, args.base_dir.resolve(), args.check_files))
        except Exception as exc:
            fatal = {"path": str(config), "items": [], "errors": [str(exc)], "warnings": [], "summary": {}}
            results.append(fatal)
            fatal_errors.append(str(exc))

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print_text(results)

    error_count = sum(len(r["errors"]) for r in results)
    warning_count = sum(len(r["warnings"]) for r in results)
    if error_count:
        return 1
    if args.strict_warnings and warning_count:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
