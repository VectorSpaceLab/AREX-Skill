#!/usr/bin/env python3
"""Safe optional-dependency checker for ai-data-science-team ML workflows.

Default behavior is read-only and side-effect free:
- no H2O cluster startup
- no MLflow UI launch
- no model training
- no downloads
- no file writes
- no LLM calls
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.util
import inspect
import json
import os
import shutil
import sys
from typing import Any

MODULES: dict[str, dict[str, str]] = {
    "ai_data_science_team": {"distribution": "ai-data-science-team", "label": "ai-data-science-team package"},
    "IPython": {"distribution": "ipython", "label": "IPython display helpers"},
    "h2o": {"distribution": "h2o", "label": "H2O AutoML optional dependency"},
    "mlflow": {"distribution": "mlflow", "label": "MLflow optional dependency"},
    "pandas": {"distribution": "pandas", "label": "pandas"},
    "numpy": {"distribution": "numpy", "label": "NumPy"},
    "sklearn": {"distribution": "scikit-learn", "label": "scikit-learn"},
    "plotly": {"distribution": "plotly", "label": "Plotly"},
    "psutil": {"distribution": "psutil", "label": "psutil"},
    "langchain": {"distribution": "langchain", "label": "LangChain"},
    "langgraph": {"distribution": "langgraph", "label": "LangGraph"},
}

REQUIRE_ALIASES = {
    "ai-data-science-team": "ai_data_science_team",
    "ai_data_science_team": "ai_data_science_team",
    "ipython": "IPython",
    "IPython": "IPython",
    "h2o": "h2o",
    "mlflow": "mlflow",
    "pandas": "pandas",
    "numpy": "numpy",
    "sklearn": "sklearn",
    "scikit-learn": "sklearn",
    "plotly": "plotly",
    "psutil": "psutil",
    "langchain": "langchain",
    "langgraph": "langgraph",
    "java": "java",
}


def sanitize(value: Any) -> Any:
    """Remove likely local path details from strings before printing."""
    if isinstance(value, str):
        text = value
        home = os.path.expanduser("~")
        cwd = os.getcwd()
        for needle, replacement in ((home, "~"), (cwd, ".")):
            if needle and needle in text:
                text = text.replace(needle, replacement)
        if len(text) > 500:
            text = text[:497] + "..."
        return text
    if isinstance(value, dict):
        return {str(k): sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return value


def version_for(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None
    except Exception as exc:  # defensive; metadata should normally be safe
        return f"unavailable: {type(exc).__name__}: {sanitize(str(exc))}"


def module_status(module_name: str, spec: dict[str, str]) -> dict[str, Any]:
    try:
        found = importlib.util.find_spec(module_name) is not None
    except Exception as exc:
        return {
            "available": False,
            "label": spec["label"],
            "distribution": spec["distribution"],
            "version": version_for(spec["distribution"]),
            "error": f"{type(exc).__name__}: {sanitize(str(exc))}",
        }
    return {
        "available": bool(found),
        "label": spec["label"],
        "distribution": spec["distribution"],
        "version": version_for(spec["distribution"]),
    }


def java_status() -> dict[str, Any]:
    return {
        "available": shutil.which("java") is not None,
        "method": "PATH lookup only; java was not executed",
    }


def safe_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:
        return f"<signature unavailable: {type(exc).__name__}: {sanitize(str(exc))}>"


def inspect_public_apis() -> dict[str, Any]:
    """Import public ML APIs and inspect signatures without constructing agents."""
    result: dict[str, Any] = {"attempted": True, "imports": {}, "signatures": {}, "errors": []}
    imports = {
        "ml_agents": "ai_data_science_team.ml_agents",
        "h2o_tools": "ai_data_science_team.tools.h2o",
        "mlflow_tools": "ai_data_science_team.tools.mlflow",
    }

    loaded: dict[str, Any] = {}
    for key, module_name in imports.items():
        try:
            loaded[key] = importlib.import_module(module_name)
            result["imports"][module_name] = "ok"
        except Exception as exc:
            result["imports"][module_name] = f"failed: {type(exc).__name__}: {sanitize(str(exc))}"
            result["errors"].append({"module": module_name, "error": result["imports"][module_name]})

    ml_agents = loaded.get("ml_agents")
    if ml_agents is not None:
        for name in ("H2OMLAgent", "ModelEvaluationAgent", "MLflowToolsAgent", "make_h2o_ml_agent", "make_mlflow_tools_agent"):
            obj = getattr(ml_agents, name, None)
            if obj is not None:
                target = getattr(obj, "__init__", obj) if inspect.isclass(obj) else obj
                result["signatures"][name] = safe_signature(target)

    h2o_tools = loaded.get("h2o_tools")
    if h2o_tools is not None:
        tool_obj = getattr(h2o_tools, "train_h2o_automl", None)
        if tool_obj is not None:
            result["signatures"]["train_h2o_automl"] = {
                "tool_name": getattr(tool_obj, "name", "train_h2o_automl"),
                "args_schema": sanitize(getattr(tool_obj, "args", None)),
                "callable_signature": safe_signature(getattr(tool_obj, "func", tool_obj)),
            }

    mlflow_tools = loaded.get("mlflow_tools")
    if mlflow_tools is not None:
        for name in (
            "mlflow_tracking_info",
            "mlflow_search_experiments",
            "mlflow_search_runs",
            "mlflow_create_experiment",
            "mlflow_get_run_details",
            "mlflow_list_artifacts",
            "mlflow_predict_from_run_id",
            "mlflow_launch_ui",
            "mlflow_stop_ui",
            "mlflow_ui_status",
        ):
            tool_obj = getattr(mlflow_tools, name, None)
            if tool_obj is not None:
                result["signatures"][name] = {
                    "tool_name": getattr(tool_obj, "name", name),
                    "args_schema": sanitize(getattr(tool_obj, "args", None)),
                    "callable_signature": safe_signature(getattr(tool_obj, "func", tool_obj)),
                }

    return sanitize(result)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    modules = {name: module_status(name, spec) for name, spec in MODULES.items()}
    java = java_status()
    required = [REQUIRE_ALIASES.get(item, item) for item in (args.require or [])]
    missing_required: list[str] = []
    unknown_required: list[str] = []

    for req in required:
        if req == "java":
            if not java["available"]:
                missing_required.append("java")
        elif req in modules:
            if not modules[req]["available"]:
                missing_required.append(req)
        else:
            unknown_required.append(req)

    report: dict[str, Any] = {
        "status": "missing_required" if missing_required else "ok",
        "safe_default": True,
        "side_effects_avoided": [
            "no H2O cluster startup",
            "no MLflow UI launch or stop",
            "no model training or inference",
            "no downloads",
            "no file writes",
            "no LLM calls",
        ],
        "modules": modules,
        "java": java,
        "required": required,
        "missing_required": missing_required,
        "unknown_required": unknown_required,
        "public_api_inspection": {"attempted": False},
    }
    if args.inspect_public_apis:
        report["public_api_inspection"] = inspect_public_apis()
    return sanitize(report)


def emit_text(report: dict[str, Any]) -> None:
    print(f"status: {report['status']}")
    print("side effects: none (import/spec checks only)")
    print("\nmodules:")
    for name, info in report["modules"].items():
        available = "ok" if info.get("available") else "missing"
        version = info.get("version") or "unknown"
        print(f"  - {name}: {available}; version={version}; {info.get('label')}")
        if info.get("error"):
            print(f"    error: {info['error']}")
    print(f"\njava: {'ok' if report['java']['available'] else 'missing'} ({report['java']['method']})")
    if report.get("missing_required"):
        print("\nmissing required: " + ", ".join(report["missing_required"]))
    if report.get("unknown_required"):
        print("\nunknown required names: " + ", ".join(report["unknown_required"]))
    inspection = report.get("public_api_inspection", {})
    if inspection.get("attempted"):
        print("\npublic API inspection:")
        for module, status in inspection.get("imports", {}).items():
            print(f"  - {module}: {status}")
        if inspection.get("errors"):
            print("  errors were reported; see JSON output for structured details")
        if inspection.get("signatures"):
            print("  signatures:")
            for name, sig in inspection["signatures"].items():
                print(f"    - {name}: {sig}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require",
        nargs="*",
        default=[],
        help="Optional names that must be available (e.g. h2o mlflow java ai-data-science-team).",
    )
    parser.add_argument(
        "--inspect-public-apis",
        action="store_true",
        help="Import public ai-data-science-team ML modules and inspect signatures without constructing agents.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format. JSON is the default for automation.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = build_report(args)
    if args.format == "text":
        emit_text(report)
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 2 if report.get("missing_required") else 0


if __name__ == "__main__":
    raise SystemExit(main())
