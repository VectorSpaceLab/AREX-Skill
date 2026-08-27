#!/usr/bin/env python3
"""Read-only Metaflow dependency environment preflight.

Example:
  python environment_preflight.py --json --strict
"""
import argparse
import importlib.util
import json
import shutil


def main() -> int:
    parser = argparse.ArgumentParser(description="Report Metaflow environment/dependency tooling readiness without installing packages.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Fail if Metaflow cannot be imported.")
    args = parser.parse_args()
    report = {"metaflow_import": False, "tools": {}, "plugins": {}, "warnings": []}
    try:
        import metaflow
        from metaflow import plugins
        report["metaflow_import"] = True
        report["version"] = getattr(metaflow, "__version__", None)
        def plugin_names(value):
            if hasattr(value, "keys"):
                return sorted(value.keys())
            names = []
            for item in value:
                names.append(getattr(item, "name", getattr(item, "__name__", str(item))))
            return sorted(names)

        report["plugins"] = {
            "environments": plugin_names(plugins.ENVIRONMENTS),
            "datastores": plugin_names(plugins.DATASTORES),
            "step_decorators": plugin_names(plugins.STEP_DECORATORS),
            "flow_decorators": plugin_names(plugins.FLOW_DECORATORS),
        }
    except Exception as exc:  # pragma: no cover
        report["warnings"].append(f"Metaflow import failed: {exc!r}")
    for tool in ["conda", "micromamba", "uv", "metaflow", "metaflow-dev"]:
        report["tools"][tool] = bool(shutil.which(tool))
    for module in ["boto3", "kubernetes", "azure.identity", "google.cloud.storage"]:
        try:
            found = importlib.util.find_spec(module) is not None
        except ModuleNotFoundError:
            found = False
        report.setdefault("optional_modules", {})[module] = found
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else report)
    return 0 if report["metaflow_import"] or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
