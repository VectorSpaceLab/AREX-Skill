#!/usr/bin/env python3
"""Safely inspect Feast feature definition files.

The script imports a Python definitions module, discovers common Feast definition
objects, and runs local validation hooks when available. It never applies a repo,
materializes features, starts servers, pushes data, or calls retrieval APIs.
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable


@dataclass
class Finding:
    level: str
    subject: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import a Feast definitions file and report discovered objects plus local validation findings.",
    )
    parser.add_argument(
        "definitions_file",
        type=Path,
        help="Path to a Python file containing Feast definition objects.",
    )
    parser.add_argument(
        "--module-name",
        default="_feast_definitions_under_validation",
        help="Temporary module name used during import. Defaults to an isolated private name.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of human-readable text.",
    )
    parser.add_argument(
        "--include-private",
        action="store_true",
        help="Inspect variables whose names start with an underscore.",
    )
    parser.add_argument(
        "--skip-to-proto",
        action="store_true",
        help="Skip to_proto() serialization checks for discovered objects.",
    )
    return parser.parse_args()


def import_feast() -> tuple[ModuleType | None, str | None]:
    try:
        import feast  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - depends on user environment
        return None, f"Unable to import installed feast package: {exc}"
    return feast, None


def import_definitions(path: Path, module_name: str) -> tuple[ModuleType | None, str | None]:
    if not path.exists():
        return None, f"Definitions file does not exist: {path}"
    if path.suffix != ".py":
        return None, f"Definitions file must be a .py file: {path}"

    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None, f"Could not build import spec for: {path}"

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None, traceback.format_exc(limit=8)
    return module, None


def flatten_values(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        for item in value.values():
            yield from flatten_values(item)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from flatten_values(item)
    else:
        yield value


def object_name(obj: Any) -> str:
    return str(getattr(obj, "name", "<unnamed>"))


def load_feast_classes() -> dict[str, type[Any]]:
    classes: dict[str, type[Any]] = {}
    imports = [
        ("Entity", "feast", "Entity"),
        ("Field", "feast", "Field"),
        ("FeatureView", "feast", "FeatureView"),
        ("FeatureService", "feast", "FeatureService"),
        ("DataSource", "feast.data_source", "DataSource"),
        ("RequestSource", "feast.data_source", "RequestSource"),
        ("PushSource", "feast.data_source", "PushSource"),
        ("OnDemandFeatureView", "feast.on_demand_feature_view", "OnDemandFeatureView"),
        ("BatchFeatureView", "feast.batch_feature_view", "BatchFeatureView"),
        ("StreamFeatureView", "feast.stream_feature_view", "StreamFeatureView"),
    ]
    for label, module_name, attr in imports:
        try:
            module = __import__(module_name, fromlist=[attr])
            classes[label] = getattr(module, attr)
        except Exception:
            continue
    return classes


def classify_object(obj: Any, feast_classes: dict[str, type[Any]]) -> str | None:
    for label in [
        "FeatureService",
        "OnDemandFeatureView",
        "BatchFeatureView",
        "StreamFeatureView",
        "FeatureView",
        "Entity",
        "Field",
        "RequestSource",
        "PushSource",
        "DataSource",
    ]:
        cls = feast_classes.get(label)
        if cls is not None and isinstance(obj, cls):
            return label

    module_name = getattr(type(obj), "__module__", "")
    class_name = type(obj).__name__
    if module_name.startswith("feast.") and class_name in {
        "LabelView",
        "Permission",
        "SavedDataset",
        "ValidationReference",
    }:
        return class_name
    return None


def discover_objects(module: ModuleType, include_private: bool) -> list[tuple[str, str, Any]]:
    feast_classes = load_feast_classes()
    discovered: list[tuple[str, str, Any]] = []
    seen: set[int] = set()

    for var_name, value in vars(module).items():
        if not include_private and var_name.startswith("_"):
            continue
        if inspect.ismodule(value) or inspect.isfunction(value) or inspect.isclass(value):
            continue
        for item in flatten_values(value):
            item_id = id(item)
            if item_id in seen:
                continue
            kind = classify_object(item, feast_classes)
            if kind is None:
                continue
            seen.add(item_id)
            discovered.append((kind, var_name, item))

    discovered.sort(key=lambda row: (row[0], object_name(row[2]), row[1]))
    return discovered


def check_field(kind: str, obj: Any) -> list[Finding]:
    findings: list[Finding] = []
    if kind != "Field":
        return findings

    subject = f"Field:{object_name(obj)}"
    vector_index = bool(getattr(obj, "vector_index", False))
    vector_length = int(getattr(obj, "vector_length", 0) or 0)
    vector_metric = getattr(obj, "vector_search_metric", None)
    dtype = getattr(obj, "dtype", None)
    dtype_text = repr(dtype)

    if vector_index and vector_length <= 0:
        findings.append(
            Finding("ERROR", subject, "vector_index=True requires vector_length > 0."),
        )
    if vector_index and "Array" not in dtype_text and "List" not in dtype_text and "VECTOR" not in dtype_text.upper():
        findings.append(
            Finding(
                "WARN",
                subject,
                f"vector_index=True usually expects an array/list dtype; observed dtype {dtype_text}.",
            ),
        )
    if vector_length > 0 and not vector_index:
        findings.append(
            Finding("WARN", subject, "vector_length is set but vector_index is False."),
        )
    if vector_index and not vector_metric:
        findings.append(
            Finding("WARN", subject, "vector_search_metric is not set; confirm target vector store default."),
        )
    return findings


def check_feature_view_like(kind: str, obj: Any) -> list[Finding]:
    findings: list[Finding] = []
    if kind not in {"FeatureView", "BatchFeatureView", "StreamFeatureView"}:
        return findings

    subject = f"{kind}:{object_name(obj)}"
    ttl = getattr(obj, "ttl", None)
    online = bool(getattr(obj, "online", False))
    offline = bool(getattr(obj, "offline", False))
    source = getattr(obj, "data_source", None) or getattr(obj, "source", None)

    if ttl is None:
        findings.append(Finding("WARN", subject, "ttl is None; confirm whether this is intentional for the view type."))
    elif str(ttl) in {"0:00:00", "0"}:
        findings.append(Finding("WARN", subject, "ttl is zero, meaning feature values live forever."))
    if not online and not offline:
        findings.append(Finding("WARN", subject, "both online and offline flags are False."))
    if kind == "FeatureView" and source is None and not getattr(obj, "source_views", None):
        findings.append(Finding("WARN", subject, "no source or source feature views are attached."))
    return findings


def run_safe_validation(kind: str, obj: Any, skip_to_proto: bool) -> list[Finding]:
    findings: list[Finding] = []
    subject = f"{kind}:{object_name(obj)}"

    if hasattr(obj, "ensure_valid"):
        try:
            obj.ensure_valid()
        except Exception as exc:
            findings.append(Finding("ERROR", subject, f"ensure_valid() failed: {exc}"))

    if kind == "FeatureService" and hasattr(obj, "validate"):
        try:
            obj.validate()
        except Exception as exc:
            findings.append(Finding("ERROR", subject, f"validate() failed: {exc}"))

    if not skip_to_proto and hasattr(obj, "to_proto"):
        try:
            obj.to_proto()
        except Exception as exc:
            findings.append(Finding("ERROR", subject, f"to_proto() failed: {exc}"))

    return findings


def emit_human(module: ModuleType, discovered: list[tuple[str, str, Any]], findings: list[Finding]) -> None:
    print(f"Imported definitions module: {module.__name__}")
    print(f"Discovered Feast objects: {len(discovered)}")
    for kind, var_name, obj in discovered:
        print(f"- {kind}: {object_name(obj)} (variable: {var_name})")

    if findings:
        print("\nFindings:")
        for finding in findings:
            print(f"{finding.level}: {finding.subject}: {finding.message}")
    else:
        print("No blocking validation errors found.")


def emit_json(module: ModuleType, discovered: list[tuple[str, str, Any]], findings: list[Finding]) -> None:
    import json

    payload = {
        "module": module.__name__,
        "objects": [
            {"kind": kind, "name": object_name(obj), "variable": var_name}
            for kind, var_name, obj in discovered
        ],
        "findings": [finding.__dict__ for finding in findings],
        "has_errors": any(finding.level == "ERROR" for finding in findings),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> int:
    args = parse_args()
    feast_module, feast_error = import_feast()
    if feast_error:
        print(f"ERROR: {feast_error}", file=sys.stderr)
        return 2

    module, import_error = import_definitions(args.definitions_file.resolve(), args.module_name)
    if import_error:
        print("ERROR: Failed to import definitions file.", file=sys.stderr)
        print(import_error, file=sys.stderr)
        return 2
    assert module is not None
    assert feast_module is not None

    discovered = discover_objects(module, args.include_private)
    findings: list[Finding] = []
    for kind, _var_name, obj in discovered:
        findings.extend(check_field(kind, obj))
        findings.extend(check_feature_view_like(kind, obj))
        findings.extend(run_safe_validation(kind, obj, args.skip_to_proto))

    if args.json:
        emit_json(module, discovered, findings)
    else:
        emit_human(module, discovered, findings)

    return 1 if any(finding.level == "ERROR" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
