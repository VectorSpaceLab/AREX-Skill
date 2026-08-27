#!/usr/bin/env python3
"""Safe ai-data-science-team environment checker.

This helper performs import, version, signature, and optional dependency checks.
It never calls an LLM provider, launches Streamlit/MLflow/H2O services, downloads
artifacts, trains models, mutates databases, or writes outside stdout.

Example:
    python scripts/check_env.py --json
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from importlib import metadata

PUBLIC_OBJECTS = {
    "DataCleaningAgent": "ai_data_science_team.agents",
    "DataLoaderToolsAgent": "ai_data_science_team.agents",
    "DataVisualizationAgent": "ai_data_science_team.agents",
    "SQLDatabaseAgent": "ai_data_science_team.agents",
    "DataWranglingAgent": "ai_data_science_team.agents",
    "FeatureEngineeringAgent": "ai_data_science_team.agents",
    "WorkflowPlannerAgent": "ai_data_science_team.agents",
    "EDAToolsAgent": "ai_data_science_team.ds_agents",
    "H2OMLAgent": "ai_data_science_team.ml_agents",
    "MLflowToolsAgent": "ai_data_science_team.ml_agents",
    "ModelEvaluationAgent": "ai_data_science_team.ml_agents",
    "PandasDataAnalyst": "ai_data_science_team.multiagents",
    "SQLDataAnalyst": "ai_data_science_team.multiagents",
}

OPTIONAL_MODULES = {
    "openai_provider": "langchain_openai",
    "ollama_provider": "langchain_ollama",
    "streamlit_apps": "streamlit",
    "h2o_automl": "h2o",
    "mlflow_tools": "mlflow",
    "missingno_report": "missingno",
    "pytimetk_correlation_funnel": "pytimetk",
    "sweetviz_report": "sweetviz",
    "dtale_report": "dtale",
}


def check_import(module_name: str):
    try:
        mod = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "version": getattr(mod, "__version__", None)}


def inspect_public_objects():
    out = {}
    for object_name, module_name in PUBLIC_OBJECTS.items():
        try:
            module = importlib.import_module(module_name)
            obj = getattr(module, object_name)
            sig_target = obj.__init__ if inspect.isclass(obj) else obj
            out[object_name] = {"ok": True, "module": module_name, "signature": str(inspect.signature(sig_target))}
        except Exception as exc:  # noqa: BLE001 - diagnostic helper
            out[object_name] = {"ok": False, "module": module_name, "error": f"{type(exc).__name__}: {exc}"}
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check ai-data-science-team imports and optional dependency visibility.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    result = {
        "python": sys.version.split()[0],
        "distribution": {},
        "package_import": check_import("ai_data_science_team"),
        "public_objects": inspect_public_objects(),
        "optional_modules": {name: check_import(module) for name, module in OPTIONAL_MODULES.items()},
        "notes": [
            "Optional module failures are informational unless the selected workflow needs that optional surface.",
            "This checker does not call LLM providers, train models, launch services, or mutate databases."
        ],
    }

    try:
        result["distribution"] = {"ok": True, "name": "ai-data-science-team", "version": metadata.version("ai-data-science-team")}
    except Exception as exc:  # noqa: BLE001
        result["distribution"] = {"ok": False, "name": "ai-data-science-team", "error": f"{type(exc).__name__}: {exc}"}

    required_ok = result["distribution"].get("ok") and result["package_import"].get("ok") and all(v.get("ok") for v in result["public_objects"].values())
    result["required_ok"] = bool(required_ok)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python']}")
        print(f"Distribution: {result['distribution']}")
        print(f"Package import: {result['package_import']}")
        print("Public objects:")
        for name, info in result["public_objects"].items():
            status = "OK" if info.get("ok") else "FAIL"
            print(f"  {status} {name}: {info.get('signature') or info.get('error')}")
        print("Optional modules:")
        for name, info in result["optional_modules"].items():
            status = "OK" if info.get("ok") else "missing/failed"
            detail = info.get("version") if info.get("ok") else info.get("error")
            print(f"  {status} {name}: {detail}")
    return 0 if required_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
