#!/usr/bin/env python3
"""Inspect M-flow ingestion pipeline capabilities without executing a pipeline.

The script imports the installed M-flow package, reports public signatures,
registered loaders, ContentType values, and basic Stage metadata. It does not
call add(), ingest(), memorize(), learn(), run_custom_pipeline(), or any workflow
executor.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from importlib import metadata, util
from pathlib import Path
from typing import Any


def _ensure_import_context() -> None:
    """Allow execution from either an installed package or a source tree."""
    if util.find_spec("m_flow") is not None:
        return

    cwd = str(Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    for parent in Path(__file__).resolve().parents:
        if (parent / "m_flow" / "__init__.py").is_file():
            parent_str = str(parent)
            if parent_str not in sys.path:
                sys.path.insert(0, parent_str)
            return


_ensure_import_context()


def _safe_distribution_version() -> str | None:
    """Return the installed distribution version when discoverable."""
    for package_name in ("mflow-ai", "m-flow", "m_flow"):
        try:
            return metadata.version(package_name)
        except metadata.PackageNotFoundError:
            continue
    return None


def _safe_signature(obj: Any) -> str:
    """Render an inspect.signature result without failing the whole script."""
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # pragma: no cover - defensive runtime inspector
        return f"<signature unavailable: {type(exc).__name__}: {exc}>"


def _public_name(obj: Any) -> str:
    module = getattr(obj, "__module__", "")
    qualname = getattr(obj, "__qualname__", getattr(obj, "__name__", type(obj).__name__))
    return f"{module}.{qualname}" if module else qualname


def _loader_inventory() -> list[dict[str, Any]]:
    """List loader engine entries and their declared capabilities."""
    try:
        from m_flow.shared.loaders.create_loader_engine import create_loader_engine
    except Exception as exc:  # pragma: no cover - depends on installed package
        return [
            {
                "name": "<registry unavailable>",
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
            }
        ]

    try:
        engine = create_loader_engine()
    except Exception as exc:  # pragma: no cover - optional dependency/runtime variance
        return [
            {
                "name": "<engine unavailable>",
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
            }
        ]

    inventory: list[dict[str, Any]] = []
    for name in sorted(engine.get_available_loaders()):
        info = engine.get_loader_info(name)
        inventory.append(
            {
                "name": info.get("name", name),
                "status": "registered",
                "extensions": list(info.get("extensions", [])),
                "mime_types": list(info.get("mime_types", [])),
            }
        )
    return inventory


def inspect_runtime() -> dict[str, Any]:
    """Collect deterministic M-flow pipeline introspection data."""
    result: dict[str, Any] = {
        "distribution_version": _safe_distribution_version(),
        "module_version": None,
        "content_type_values": [],
        "loaders": [],
        "signatures": {},
        "stage_probe": {},
        "notes": ["introspection_only", "no_pipeline_execution"],
    }

    try:
        import m_flow
        from m_flow.api.v1.add import add
        from m_flow.api.v1.ingest import ingest
        from m_flow.api.v1.learn import learn
        from m_flow.api.v1.memorize import memorize
        from m_flow.api.v1.memorize.memorize import get_default_tasks
        from m_flow.pipeline import Stage
        from m_flow.pipeline.custom import run_custom_pipeline
        from m_flow.shared.enums import ContentType
    except Exception as exc:  # pragma: no cover - depends on installed package
        result["import_error"] = f"{type(exc).__name__}: {exc}"
        return result

    result["module_version"] = getattr(m_flow, "__version__", None)
    result["content_type_values"] = [item.value for item in ContentType]
    result["loaders"] = _loader_inventory()
    result["signatures"] = {
        "add": _safe_signature(add),
        "ingest": _safe_signature(ingest),
        "memorize": _safe_signature(memorize),
        "get_default_tasks": _safe_signature(get_default_tasks),
        "learn": _safe_signature(learn),
        "run_custom_pipeline": _safe_signature(run_custom_pipeline),
        "Stage": _safe_signature(Stage),
    }

    # Constructing a Stage is safe; the wrapped callable is never invoked.
    probe = Stage(lambda x: x, task_config={"batch_size": 7})
    result["stage_probe"] = {
        "task_type": probe.task_type,
        "task_config": probe.task_config,
        "default_params": {
            "args_count": len(probe.default_params.get("args", ())),
            "kwargs": probe.default_params.get("kwargs", {}),
        },
    }

    return result


def print_text(report: dict[str, Any]) -> None:
    """Print a stable human-readable report."""
    print("M-flow ingestion pipeline inspector")
    print("Mode: introspection only; no pipelines executed")
    print(f"Distribution version: {report.get('distribution_version') or 'unknown'}")
    print(f"Module version: {report.get('module_version') or 'unknown'}")

    if report.get("import_error"):
        print(f"Import error: {report['import_error']}")
        return

    print("\nContentType values:")
    for value in report.get("content_type_values", []):
        print(f"  - {value}")

    print("\nRegistered loaders:")
    for loader in report.get("loaders", []):
        status = loader.get("status", "unknown")
        print(f"  - {loader.get('name')} ({status})")
        if loader.get("extensions"):
            print(f"      extensions: {', '.join(loader['extensions'])}")
        if loader.get("mime_types"):
            print(f"      mime types: {', '.join(loader['mime_types'])}")
        if loader.get("error"):
            print(f"      error: {loader['error']}")

    print("\nPublic signatures:")
    for name in sorted(report.get("signatures", {})):
        print(f"  - {name}{report['signatures'][name]}")

    probe = report.get("stage_probe", {})
    if probe:
        print("\nStage probe:")
        print(f"  task_type: {probe.get('task_type')}")
        print(f"  task_config: {probe.get('task_config')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect installed M-flow ingestion loaders and pipeline APIs without executing a pipeline."
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    report = inspect_runtime()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print_text(report)
    return 1 if report.get("import_error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
