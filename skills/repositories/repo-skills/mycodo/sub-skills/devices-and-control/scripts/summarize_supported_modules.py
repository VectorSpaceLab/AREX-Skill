#!/usr/bin/env python3
"""Summarize Mycodo supported module metadata without importing Mycodo.

This helper is intentionally static: it parses Python source with ``ast`` and
never imports module files, optional hardware libraries, or Mycodo itself. It is
safe to run against a checkout to obtain approximate counts, categories, and
metadata names for Inputs, Outputs, Functions, Actions, and Widgets.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

FAMILY_CONFIG = {
    "inputs": {
        "directory": "mycodo/inputs",
        "info_var": "INPUT_INFORMATION",
        "name_key": "input_name",
        "unique_key": "input_name_unique",
        "manufacturer_key": "input_manufacturer",
        "library_key": "input_library",
    },
    "outputs": {
        "directory": "mycodo/outputs",
        "info_var": "OUTPUT_INFORMATION",
        "name_key": "output_name",
        "unique_key": "output_name_unique",
        "manufacturer_key": None,
        "library_key": "output_library",
    },
    "functions": {
        "directory": "mycodo/functions",
        "info_var": "FUNCTION_INFORMATION",
        "name_key": "function_name",
        "unique_key": "function_name_unique",
        "manufacturer_key": None,
        "library_key": None,
    },
    "actions": {
        "directory": "mycodo/actions",
        "info_var": "ACTION_INFORMATION",
        "name_key": "name",
        "unique_key": "name_unique",
        "manufacturer_key": "manufacturer",
        "library_key": "library",
    },
    "widgets": {
        "directory": "mycodo/widgets",
        "info_var": "WIDGET_INFORMATION",
        "name_key": "widget_name",
        "unique_key": "widget_name_unique",
        "manufacturer_key": None,
        "library_key": "widget_library",
    },
}

FAMILY_CHOICES = tuple(["all"] + sorted(FAMILY_CONFIG))


def _title_from_key(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


def _slice_value(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant):
        return str(node.value)
    if hasattr(ast, "Index") and isinstance(node, ast.Index):  # pragma: no cover
        return _slice_value(node.value)
    return None


def static_eval(node: ast.AST, env: Mapping[str, Any]) -> Any:
    """Best-effort static evaluator for simple metadata expressions."""

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return env.get(node.id, node.id)
    if isinstance(node, ast.List):
        return [static_eval(item, env) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(static_eval(item, env) for item in node.elts)
    if isinstance(node, ast.Set):
        return sorted(static_eval(item, env) for item in node.elts)
    if isinstance(node, ast.Dict):
        result: Dict[Any, Any] = {}
        for key_node, value_node in zip(node.keys, node.values):
            key = static_eval(key_node, env) if key_node is not None else None
            result[key] = static_eval(value_node, env)
        return result
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = static_eval(node.operand, env)
        if isinstance(value, (int, float)):
            return -value
        return f"-{value}"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = static_eval(node.left, env)
        right = static_eval(node.right, env)
        if isinstance(left, list) and isinstance(right, list):
            return left + right
        return f"{left}{right}"
    if isinstance(node, ast.JoinedStr):
        parts: List[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue):
                parts.append(str(static_eval(value.value, env)))
        return "".join(parts)
    if isinstance(node, ast.Subscript):
        key = _slice_value(node.slice)
        if key == "title" and isinstance(node.value, ast.Subscript):
            return static_eval(node.value, env)
        if isinstance(node.value, ast.Name) and node.value.id in {"TRANSLATIONS", "T"}:
            return _title_from_key(key or "translation")
        container = static_eval(node.value, env)
        if isinstance(container, Mapping) and key in container:
            return container[key]
        return _title_from_key(key or "subscript")
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Attribute) and node.func.attr == "format":
            fmt = static_eval(node.func.value, env)
            args = [static_eval(arg, env) for arg in node.args]
            kwargs = {kw.arg: static_eval(kw.value, env) for kw in node.keywords if kw.arg}
            try:
                return str(fmt).format(*args, **kwargs)
            except Exception:
                return str(fmt)
        if node.args:
            first = static_eval(node.args[0], env)
            if isinstance(first, (str, int, float)):
                return first
        return "<call>"
    if isinstance(node, ast.IfExp):
        return static_eval(node.body, env)
    return "<expr>"


def extract_info(path: Path, info_var: str) -> Optional[Dict[str, Any]]:
    """Return a metadata dictionary from a source file, if statically visible."""

    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"), filename=str(path))
    except SyntaxError:
        return None

    env: MutableMapping[str, Any] = {}
    found: Optional[Dict[str, Any]] = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        value = static_eval(node.value, env)
        for target in node.targets:
            if isinstance(target, ast.Name):
                env[target.id] = value
                if target.id == info_var and isinstance(value, dict):
                    found = dict(value)
    return found


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value)
    return [value]


def module_name(info: Mapping[str, Any], config: Mapping[str, Any], fallback: str) -> str:
    for key in (config.get("name_key"), config.get("unique_key")):
        if key and info.get(key):
            return str(info[key])
    return fallback


def summarize_family(repo_root: Path, family: str) -> Dict[str, Any]:
    config = FAMILY_CONFIG[family]
    directory = repo_root / str(config["directory"])
    summary: Dict[str, Any] = {
        "family": family,
        "directory": str(config["directory"]),
        "exists": directory.is_dir(),
        "count": 0,
        "with_dependencies": 0,
        "interfaces": Counter(),
        "output_types": Counter(),
        "applications": Counter(),
        "manufacturers": Counter(),
        "libraries": Counter(),
        "measurements": Counter(),
        "options_enabled": Counter(),
        "modules": [],
    }
    if not directory.is_dir():
        return summary

    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("__") or path.name.startswith("base_"):
            continue
        info = extract_info(path, str(config["info_var"]))
        if not info:
            continue

        name = module_name(info, config, path.stem)
        unique_key = config.get("unique_key")
        unique = str(info.get(unique_key) or path.stem) if unique_key else path.stem
        manufacturer_key = config.get("manufacturer_key")
        library_key = config.get("library_key")
        manufacturer = str(info.get(manufacturer_key) or "") if manufacturer_key else ""
        library = str(info.get(library_key) or "") if library_key else ""
        interfaces = [str(item) for item in as_list(info.get("interfaces"))]
        output_types = [str(item) for item in as_list(info.get("output_types"))]
        applications = [str(item) for item in as_list(info.get("application"))]
        options_enabled = [str(item) for item in as_list(info.get("options_enabled"))]
        dependencies = as_list(info.get("dependencies_module"))

        measurements = []
        measurements_dict = info.get("measurements_dict")
        if isinstance(measurements_dict, Mapping):
            for measurement in measurements_dict.values():
                if isinstance(measurement, Mapping) and measurement.get("measurement"):
                    measurements.append(str(measurement.get("measurement")))

        summary["count"] += 1
        if dependencies:
            summary["with_dependencies"] += 1
        summary["interfaces"].update(interfaces)
        summary["output_types"].update(output_types)
        summary["applications"].update(applications)
        if manufacturer:
            summary["manufacturers"].update([manufacturer])
        if library:
            summary["libraries"].update([library])
        summary["measurements"].update(measurements)
        summary["options_enabled"].update(options_enabled)
        summary["modules"].append(
            {
                "file": path.name,
                "name": name,
                "unique": unique,
                "manufacturer": manufacturer,
                "library": library,
                "interfaces": interfaces,
                "output_types": output_types,
                "applications": applications,
                "measurements": sorted(set(measurements)),
                "has_dependencies": bool(dependencies),
            }
        )

    summary["modules"].sort(key=lambda item: (str(item["name"]).lower(), str(item["file"])))
    return summary


def counter_to_dict(counter: Counter) -> Dict[str, int]:
    return {str(key): int(value) for key, value in counter.most_common()}


def jsonable(summary: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(summary)
    for key in [
        "interfaces",
        "output_types",
        "applications",
        "manufacturers",
        "libraries",
        "measurements",
        "options_enabled",
    ]:
        result[key] = counter_to_dict(result[key])
    return result


def print_counter(title: str, counter: Counter, limit: int) -> None:
    if not counter:
        return
    rendered = ", ".join(f"{key}={value}" for key, value in counter.most_common(limit))
    print(f"  {title}: {rendered}")


def print_summary(summary: Dict[str, Any], show_modules: bool, limit: int) -> None:
    print(f"{summary['family']} ({summary['directory']}):")
    if not summary["exists"]:
        print("  directory not found")
        return
    print(f"  modules: {summary['count']}")
    print(f"  modules with dependency metadata: {summary['with_dependencies']}")
    print_counter("interfaces", summary["interfaces"], limit)
    print_counter("output types", summary["output_types"], limit)
    print_counter("applications", summary["applications"], limit)
    print_counter("manufacturers", summary["manufacturers"], limit)
    print_counter("libraries", summary["libraries"], limit)
    print_counter("measurements", summary["measurements"], limit)
    print_counter("options enabled", summary["options_enabled"], limit)
    modules = summary["modules"]
    if show_modules or limit:
        print("  module names:")
        selected = modules if show_modules else modules[:limit]
        for item in selected:
            extras = []
            if item["interfaces"]:
                extras.append("interfaces=" + "/".join(item["interfaces"]))
            if item["output_types"]:
                extras.append("types=" + "/".join(item["output_types"]))
            if item["manufacturer"]:
                extras.append("manufacturer=" + item["manufacturer"])
            if item["library"]:
                extras.append("library=" + item["library"])
            suffix = f" ({'; '.join(extras)})" if extras else ""
            print(f"    - {item['name']} [{item['unique']}] {item['file']}{suffix}")
        if not show_modules and len(modules) > limit:
            print(f"    ... {len(modules) - limit} more; rerun with --show-modules")


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Statically summarize Mycodo Input/Output/Function/Action/Widget "
            "metadata without importing Mycodo or hardware libraries."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Path to a Mycodo checkout or installed source tree (default: current directory).",
    )
    parser.add_argument(
        "--family",
        choices=FAMILY_CHOICES,
        default="all",
        help="Module family to summarize (default: all).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Number of counter entries and module names to print per family unless --show-modules is set.",
    )
    parser.add_argument(
        "--show-modules",
        action="store_true",
        help="Print every discovered module name for each selected family.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()
    families = sorted(FAMILY_CONFIG) if args.family == "all" else [args.family]
    summaries = [summarize_family(repo_root, family) for family in families]

    if args.json:
        print(json.dumps({"repo_root": str(repo_root), "families": [jsonable(item) for item in summaries]}, indent=2, sort_keys=True))
    else:
        print(f"Mycodo static module summary for: {repo_root}")
        print("No imports, hardware access, network calls, credentials, or daemon operations are performed.\n")
        for index, summary in enumerate(summaries):
            if index:
                print()
            print_summary(summary, show_modules=args.show_modules, limit=max(args.limit, 0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
