#!/usr/bin/env python3
"""Safely inspect a CrewAI Flow graph without executing kickoff, LLMs, or tools.

The script can parse a Python file with --ast-only or import an explicitly named
module/file and Flow class to read CrewAI's static FlowDefinition metadata. It
never calls kickoff(), kickoff_async(), plot(), crews, tools, network, or LLMs.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any


Condition = str | dict[str, list["Condition"]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect CrewAI Flow starts, listeners, routers, and route labels without running the flow.",
        epilog=(
            "Targets: path/to/file.py:FlowClass, package.module:FlowClass, "
            "or path/to/file.py with --ast-only."
        ),
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Flow target. Use file.py:ClassName or module.name:ClassName. Required unless using --help.",
    )
    parser.add_argument(
        "--ast-only",
        action="store_true",
        help="Parse decorators from source with ast and do not import user code.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text report.",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit with status 2 when graph warnings are found.",
    )
    return parser.parse_args()


def split_target(target: str) -> tuple[str, str | None]:
    if ":" in target:
        module_or_path, class_name = target.rsplit(":", 1)
        return module_or_path, class_name or None
    return target, None


def load_module(module_or_path: str) -> ModuleType:
    path = Path(module_or_path)
    if path.suffix == ".py" or path.exists():
        resolved = path.expanduser().resolve()
        module_name = f"_crewai_flow_validation_{resolved.stem}"
        spec = importlib.util.spec_from_file_location(module_name, resolved)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load module from {module_or_path!r}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(module_or_path)


def get_attr_path(module: ModuleType, attr_path: str) -> Any:
    value: Any = module
    for part in attr_path.split("."):
        value = getattr(value, part)
    return value


def condition_to_data(value: Any) -> Condition | None:
    if value is None or value is False:
        return None
    if value is True:
        return {"unconditional": []}
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if "and" in value:
            return {"and": [condition_to_data(item) for item in value.get("and", []) if condition_to_data(item) is not None]}
        if "or" in value:
            return {"or": [condition_to_data(item) for item in value.get("or", []) if condition_to_data(item) is not None]}
    return str(value)


def extract_condition_names(condition: Condition | None) -> list[str]:
    if condition is None:
        return []
    if isinstance(condition, str):
        return [condition]
    names: list[str] = []
    for values in condition.values():
        for value in values:
            names.extend(extract_condition_names(value))
    return names


def extract_direct_or_names(condition: Condition | None) -> list[str]:
    if condition is None:
        return []
    if isinstance(condition, str):
        return [condition]
    if "and" in condition:
        return []
    names: list[str] = []
    for value in condition.get("or", []):
        names.extend(extract_direct_or_names(value))
    return names


def normalize_method_definition(name: str, method: Any) -> dict[str, Any]:
    human_feedback = getattr(method, "human_feedback", None)
    human_emit = list(getattr(human_feedback, "emit", None) or []) if human_feedback is not None else []
    start = condition_to_data(getattr(method, "start", None))
    listen = condition_to_data(getattr(method, "listen", None))
    emit = list(getattr(method, "emit", None) or [])
    is_router = bool(getattr(method, "router", False))
    if human_emit:
        is_router = True
    return {
        "name": name,
        "is_start": bool(getattr(method, "is_start", False)),
        "start": start,
        "listen": listen,
        "is_router": is_router,
        "emit": emit,
        "human_feedback_emit": human_emit,
        "persist": getattr(method, "persist", None) is not None,
    }


def inspect_flow_definition(target: str) -> dict[str, Any]:
    module_or_path, class_name = split_target(target)
    if not class_name:
        raise ValueError("Import-based inspection requires an explicit class target such as file.py:MyFlow")

    module = load_module(module_or_path)
    flow_class = get_attr_path(module, class_name)

    try:
        from crewai.flow.flow import Flow
    except Exception as exc:  # pragma: no cover - depends on caller environment
        raise RuntimeError(f"Could not import crewai.flow.flow.Flow: {exc}") from exc

    if not isinstance(flow_class, type) or not issubclass(flow_class, Flow):
        raise TypeError(f"{class_name!r} is not a CrewAI Flow subclass")

    definition = flow_class.flow_definition()
    methods = [
        normalize_method_definition(method_name, method_definition)
        for method_name, method_definition in definition.methods.items()
    ]
    state = getattr(definition, "state", None)
    return {
        "mode": "flow_definition",
        "flow_name": definition.name,
        "target": target,
        "state": state.__class__.__name__ if state is not None else None,
        "methods": methods,
    }


def decorator_name(node: ast.AST) -> str:
    if isinstance(node, ast.Call):
        return decorator_name(node.func)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = decorator_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def ast_condition(node: ast.AST | None) -> Condition | None:
    if node is None:
        return None
    if isinstance(node, ast.Call):
        name = decorator_name(node.func).split(".")[-1]
        if name in {"and_", "or_"}:
            key = "and" if name == "and_" else "or"
            return {key: [item for arg in node.args if (item := ast_condition(arg)) is not None]}
        if node.args:
            return ast_condition(node.args[0])
        return None
    value = literal_string(node)
    return value if value is not None else ast.unparse(node) if hasattr(ast, "unparse") else None


def ast_emit_from_call(node: ast.Call) -> list[str]:
    labels: list[str] = []
    for keyword in node.keywords:
        if keyword.arg != "emit":
            continue
        value = keyword.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            labels.append(value.value)
        elif isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            for element in value.elts:
                item = literal_string(element)
                if item is not None:
                    labels.append(item)
    return list(dict.fromkeys(labels))


def inspect_ast(target: str) -> dict[str, Any]:
    module_or_path, selected_class = split_target(target)
    path = Path(module_or_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"AST mode requires an existing Python file: {module_or_path}")

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    if selected_class:
        classes = [node for node in classes if node.name == selected_class]
    if not classes:
        raise ValueError(f"No matching class found in {path.name}")
    if len(classes) > 1 and not selected_class:
        raise ValueError(
            "AST mode found multiple classes; specify one as file.py:ClassName. "
            f"Candidates: {', '.join(node.name for node in classes)}"
        )

    class_node = classes[0]
    methods: list[dict[str, Any]] = []
    for node in class_node.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        method: dict[str, Any] = {
            "name": node.name,
            "is_start": False,
            "start": None,
            "listen": None,
            "is_router": False,
            "emit": [],
            "human_feedback_emit": [],
            "persist": False,
        }
        for decorator in node.decorator_list:
            name = decorator_name(decorator).split(".")[-1]
            call = decorator if isinstance(decorator, ast.Call) else None
            if name == "start":
                method["is_start"] = True
                method["start"] = ast_condition(call.args[0]) if call and call.args else {"unconditional": []}
            elif name == "listen":
                method["listen"] = ast_condition(call.args[0]) if call and call.args else None
            elif name == "router":
                method["is_router"] = True
                method["listen"] = ast_condition(call.args[0]) if call and call.args else None
                method["emit"] = ast_emit_from_call(call) if call else []
            elif name == "human_feedback":
                method["human_feedback_emit"] = ast_emit_from_call(call) if call else []
                if method["human_feedback_emit"]:
                    method["is_router"] = True
            elif name == "persist":
                method["persist"] = True
        if method["is_start"] or method["listen"] is not None or method["is_router"] or method["persist"]:
            methods.append(method)

    return {
        "mode": "ast",
        "flow_name": class_node.name,
        "target": target,
        "state": None,
        "methods": methods,
    }


def analyze(report: dict[str, Any]) -> dict[str, Any]:
    methods = report["methods"]
    method_names = {method["name"] for method in methods}
    starts = [method for method in methods if method["is_start"]]
    unconditional_starts = [method for method in starts if method["start"] == {"unconditional": []}]
    routers = [method for method in methods if method["is_router"]]
    listeners = [method for method in methods if method["listen"] is not None]

    router_labels: set[str] = set()
    dynamic_routers: list[str] = []
    for method in routers:
        labels = list(method.get("emit") or []) + list(method.get("human_feedback_emit") or [])
        if labels:
            router_labels.update(str(label) for label in labels)
        else:
            dynamic_routers.append(method["name"])

    listener_direct_labels: set[str] = set()
    all_trigger_names: set[str] = set()
    for method in methods:
        for condition_key in ("start", "listen"):
            condition = method.get(condition_key)
            all_trigger_names.update(extract_condition_names(condition))
            listener_direct_labels.update(extract_direct_or_names(condition))

    consumed_labels = listener_direct_labels - method_names
    warnings: dict[str, list[str]] = {
        "no_start_methods": [],
        "multiple_unconditional_starts": [],
        "router_labels_without_listeners": [],
        "listener_triggers_without_known_source": [],
        "dynamic_router_labels": [],
        "methods_marked_start_and_listener": [],
    }

    if not starts:
        warnings["no_start_methods"].append("No @start methods were found.")
    if len(unconditional_starts) > 1:
        warnings["multiple_unconditional_starts"].append(
            "Multiple unconditional starts: " + ", ".join(method["name"] for method in unconditional_starts)
        )

    missing_consumers = sorted(label for label in router_labels if label not in consumed_labels)
    if missing_consumers:
        warnings["router_labels_without_listeners"].extend(missing_consumers)

    known_trigger_sources = method_names | router_labels
    unknown_triggers = sorted(
        trigger for trigger in all_trigger_names
        if trigger not in known_trigger_sources and trigger != "unconditional"
    )
    if unknown_triggers:
        warnings["listener_triggers_without_known_source"].extend(unknown_triggers)

    if dynamic_routers:
        warnings["dynamic_router_labels"].extend(dynamic_routers)

    for method in methods:
        if method["is_start"] and method.get("listen") is not None:
            warnings["methods_marked_start_and_listener"].append(method["name"])

    report["summary"] = {
        "method_count": len(methods),
        "start_methods": [method["name"] for method in starts],
        "listener_methods": [method["name"] for method in listeners if not method["is_router"]],
        "router_methods": [method["name"] for method in routers],
        "declared_router_labels": sorted(router_labels),
        "consumed_route_labels": sorted(consumed_labels),
    }
    report["warnings"] = {key: value for key, value in warnings.items() if value}
    return report


def print_text(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print(f"Flow: {report['flow_name']} ({report['mode']})")
    print(f"Target: {report['target']}")
    if report.get("state"):
        print(f"State: {report['state']}")
    print()
    print("Starts:")
    for name in summary["start_methods"]:
        print(f"  - {name}")
    if not summary["start_methods"]:
        print("  - none")
    print("Listeners:")
    for name in summary["listener_methods"]:
        print(f"  - {name}")
    if not summary["listener_methods"]:
        print("  - none")
    print("Routers:")
    for name in summary["router_methods"]:
        print(f"  - {name}")
    if not summary["router_methods"]:
        print("  - none")
    print("Declared router labels:")
    for label in summary["declared_router_labels"]:
        print(f"  - {label}")
    if not summary["declared_router_labels"]:
        print("  - none or dynamic")
    print()
    if report["warnings"]:
        print("Warnings:")
        for key, values in report["warnings"].items():
            print(f"  {key}:")
            for value in values:
                print(f"    - {value}")
    else:
        print("Warnings: none")


def main() -> int:
    args = parse_args()
    if not args.target:
        print("error: target is required unless using --help", file=sys.stderr)
        return 2

    try:
        report = inspect_ast(args.target) if args.ast_only else inspect_flow_definition(args.target)
        report = analyze(report)
    except Exception as exc:
        error = {"ok": False, "error": str(exc), "target": args.target}
        if args.json:
            print(json.dumps(error, indent=2, sort_keys=True))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1

    report["ok"] = not bool(report["warnings"])
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print_text(report)

    if args.fail_on_warning and report["warnings"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
