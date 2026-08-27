#!/usr/bin/env python3
"""Check that an installed pgmpy package can run core safe workflows.

This helper is bundled with the generated pgmpy skill. It does not require the
original repository checkout, does not download data, and does not need optional
extras. Example:

    python check_pgmpy_environment.py --json
"""

from __future__ import annotations

import argparse
import importlib
import json
from importlib.metadata import PackageNotFoundError, version


def optional_import(module: str) -> dict[str, object]:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostic helper reports any import failure.
        return {"available": False, "error": type(exc).__name__, "message": str(exc)[:240]}
    return {"available": True, "module": getattr(imported, "__name__", module)}


def run_core_smoke() -> dict[str, object]:
    from pgmpy.factors.discrete import TabularCPD
    from pgmpy.inference import VariableElimination
    from pgmpy.models import DiscreteBayesianNetwork

    model = DiscreteBayesianNetwork([("A", "B")])
    model.add_cpds(
        TabularCPD("A", 2, [[0.6], [0.4]], state_names={"A": ["no", "yes"]}),
        TabularCPD(
            "B",
            2,
            [[0.9, 0.2], [0.1, 0.8]],
            evidence=["A"],
            evidence_card=[2],
            state_names={"B": ["low", "high"], "A": ["no", "yes"]},
        ),
    )
    check_model = bool(model.check_model())
    posterior = VariableElimination(model).query(["B"], evidence={"A": "yes"}, show_progress=False)
    return {
        "check_model": check_model,
        "edges": [list(edge) for edge in model.edges()],
        "posterior_B_given_A_yes": {
            "low": round(float(posterior.values[0]), 6),
            "high": round(float(posterior.values[1]), 6),
        },
    }


def _registry_names(registry: object, max_items: int) -> list[str]:
    if isinstance(registry, list):
        return [str(name) for name in registry[:max_items]]
    if hasattr(registry, "index") and not callable(getattr(registry, "index")):
        return [str(name) for name in list(getattr(registry, "index"))[:max_items]]
    if hasattr(registry, "iloc"):
        return [str(name) for name in registry.iloc[:max_items].index.tolist()]
    return [str(name) for name in list(registry)[:max_items]]


def run_registry_smoke(max_items: int) -> dict[str, object]:
    from pgmpy.datasets import list_datasets
    from pgmpy.example_models import list_models

    datasets = list_datasets()
    models = list_models()
    return {
        "dataset_count": int(len(datasets)),
        "model_count": int(len(models)),
        "dataset_sample": _registry_names(datasets, max_items),
        "model_sample": _registry_names(models, max_items),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe installed-package smoke check for pgmpy.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    parser.add_argument("--check-optional", action="store_true", help="Report optional torch/pyro/litellm/plotting imports.")
    parser.add_argument("--max-registry-items", type=int, default=5, help="Maximum dataset/model names to print.")
    args = parser.parse_args()

    report: dict[str, object] = {"schema": "pgmpy.environment_smoke.v1", "status": "ok"}
    try:
        report["pgmpy_version"] = version("pgmpy")
    except PackageNotFoundError:
        report.update({"status": "failed", "error": "pgmpy distribution metadata not found"})
        print(json.dumps(report, indent=2, sort_keys=True)) if args.json else print(report["error"])
        return 2

    try:
        report["core"] = run_core_smoke()
        report["registries"] = run_registry_smoke(args.max_registry_items)
    except Exception as exc:  # noqa: BLE001 - diagnostic helper reports any smoke failure.
        report.update({"status": "failed", "error": type(exc).__name__, "message": str(exc)})

    if args.check_optional:
        report["optional_imports"] = {
            "torch": optional_import("torch"),
            "pyro": optional_import("pyro"),
            "litellm": optional_import("litellm"),
            "daft": optional_import("daft"),
            "pygraphviz": optional_import("pygraphviz"),
        }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"pgmpy environment smoke: {report['status']}")
        print(f"  version: {report.get('pgmpy_version')}")
        if report["status"] == "ok":
            core = report["core"]
            registries = report["registries"]
            print(f"  check_model: {core['check_model']}")
            print(f"  P(B=high | A=yes): {core['posterior_B_given_A_yes']['high']}")
            print(f"  registries: {registries['dataset_count']} datasets, {registries['model_count']} models")
        else:
            print(f"  {report.get('error')}: {report.get('message', '')}")
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
