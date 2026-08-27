#!/usr/bin/env python3
"""Tiny pgmpy modeling smoke check.

Builds a two-node discrete Bayesian network, validates CPDs, optionally runs one
exact inference query, and reports whether optional torch/Pyro packages are
importable. The script is deterministic, uses no network or local checkout
assumptions, and should run from any working directory with pgmpy installed.

Example:
    python check_modeling_smoke.py
    python check_modeling_smoke.py --skip-inference
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import sys
from typing import Any


def package_version(dist_name: str) -> str | None:
    """Return an installed distribution version, or None if unavailable."""
    try:
        return importlib.metadata.version(dist_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def module_available(module_name: str) -> bool:
    """Return True if a module can be found without importing it."""
    return importlib.util.find_spec(module_name) is not None


def build_tiny_model() -> tuple[Any, dict[str, Any]]:
    """Build and validate a deterministic two-node discrete BN."""
    from pgmpy.factors.discrete import TabularCPD
    from pgmpy.models import DiscreteBayesianNetwork

    model = DiscreteBayesianNetwork([("Weather", "WetGrass")])

    cpd_weather = TabularCPD(
        variable="Weather",
        variable_card=2,
        values=[[0.7], [0.3]],
        state_names={"Weather": ["sunny", "rainy"]},
    )
    cpd_wet_grass = TabularCPD(
        variable="WetGrass",
        variable_card=2,
        values=[[0.8, 0.1], [0.2, 0.9]],
        evidence=["Weather"],
        evidence_card=[2],
        state_names={"Weather": ["sunny", "rainy"], "WetGrass": ["dry", "wet"]},
    )

    if cpd_weather.get_values().shape != (2, 1):
        raise AssertionError(f"Unexpected Weather CPD shape: {cpd_weather.get_values().shape}")
    if cpd_wet_grass.get_values().shape != (2, 2):
        raise AssertionError(f"Unexpected WetGrass CPD shape: {cpd_wet_grass.get_values().shape}")

    model.add_cpds(cpd_weather, cpd_wet_grass)
    check_model = model.check_model()
    if check_model is not True:
        raise AssertionError(f"check_model returned {check_model!r}")

    details = {
        "nodes": sorted(str(node) for node in model.nodes()),
        "edges": [[str(u), str(v)] for u, v in model.edges()],
        "cpd_shapes": {
            "Weather": list(cpd_weather.get_values().shape),
            "WetGrass": list(cpd_wet_grass.get_values().shape),
        },
        "state_names": model.states,
    }
    return model, details


def run_tiny_inference(model: Any) -> dict[str, float]:
    """Run one exact inference query as an optional validation smoke."""
    from pgmpy.inference import VariableElimination

    query = VariableElimination(model).query(
        variables=["WetGrass"],
        evidence={"Weather": "sunny"},
        show_progress=False,
    )
    states = list(query.state_names["WetGrass"])
    values = [float(value) for value in query.values.tolist()]
    return dict(zip(states, values, strict=True))


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and validate a tiny pgmpy discrete Bayesian network.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--skip-inference",
        action="store_true",
        help="Only validate model construction and CPDs; do not run the tiny VariableElimination query.",
    )
    parser.add_argument(
        "--no-optional-report",
        action="store_true",
        help="Do not report optional torch/Pyro module availability.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        from pgmpy.global_vars import config

        model, model_details = build_tiny_model()
        report: dict[str, Any] = {
            "schema": "pgmpy.modeling_smoke.v1",
            "status": "ok",
            "pgmpy_version": package_version("pgmpy"),
            "backend": config.get_backend(),
            "check_model": True,
            "model": model_details,
        }

        if not args.skip_inference:
            report["posterior_WetGrass_given_Weather_sunny"] = run_tiny_inference(model)

        if not args.no_optional_report:
            report["optional_imports"] = {
                "torch": module_available("torch"),
                "pyro": module_available("pyro"),
            }

        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - failure path is for diagnostics.
        failure = {
            "schema": "pgmpy.modeling_smoke.v1",
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        print(json.dumps(failure, indent=2, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
