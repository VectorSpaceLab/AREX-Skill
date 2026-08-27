#!/usr/bin/env python3
"""Tiny pgmpy inference/simulation smoke check.

Builds a self-contained discrete Bayesian network, validates it, runs exact
posterior and MAP queries, compares BeliefPropagation with VariableElimination,
and simulates a few rows. It requires only an installed pgmpy package.
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np

from pgmpy.factors.discrete import TabularCPD
from pgmpy.global_vars import config
from pgmpy.inference import BeliefPropagation, VariableElimination
from pgmpy.models import DiscreteBayesianNetwork


def build_tiny_model() -> DiscreteBayesianNetwork:
    """Return a two-node BN with named states."""
    model = DiscreteBayesianNetwork([("Disease", "Test")])
    disease = TabularCPD(
        variable="Disease",
        variable_card=2,
        values=[[0.7], [0.3]],
        state_names={"Disease": ["absent", "present"]},
    )
    test = TabularCPD(
        variable="Test",
        variable_card=2,
        values=[[0.95, 0.20], [0.05, 0.80]],
        evidence=["Disease"],
        evidence_card=[2],
        state_names={"Disease": ["absent", "present"], "Test": ["negative", "positive"]},
    )
    model.add_cpds(disease, test)
    return model


def positive_posterior_expected() -> float:
    numerator = 0.3 * 0.80
    denominator = numerator + 0.7 * 0.05
    return numerator / denominator


def run_smoke(samples: int, seed: int) -> dict[str, object]:
    if samples <= 0:
        raise ValueError("--samples must be a positive integer")

    config.set_show_progress(False)
    model = build_tiny_model()
    if model.check_model() is not True:
        raise AssertionError("model.check_model() did not return True")

    evidence = {"Test": "positive"}
    ve = VariableElimination(model)
    posterior = ve.query(variables=["Disease"], evidence=evidence, show_progress=False)
    present_prob = float(posterior.get_value(Disease="present"))
    expected = positive_posterior_expected()
    if not np.isclose(present_prob, expected, atol=1e-12):
        raise AssertionError(f"unexpected posterior: got {present_prob}, expected {expected}")

    map_result = ve.map_query(variables=["Disease"], evidence=evidence, show_progress=False)
    if map_result != {"Disease": "present"}:
        raise AssertionError(f"unexpected MAP result: {map_result}")

    bp = BeliefPropagation(model)
    bp_posterior = bp.query(variables=["Disease"], evidence=evidence, show_progress=False)
    bp_present_prob = float(bp_posterior.get_value(Disease="present"))
    if not np.isclose(bp_present_prob, present_prob, atol=1e-12):
        raise AssertionError("BeliefPropagation posterior differed from VariableElimination")

    simulated = model.simulate(n_samples=samples, seed=seed, show_progress=False)
    expected_columns = {"Disease", "Test"}
    if set(simulated.columns) != expected_columns:
        raise AssertionError(f"unexpected simulated columns: {list(simulated.columns)}")
    if simulated.shape[0] != samples:
        raise AssertionError(f"unexpected simulated row count: {simulated.shape[0]}")
    if not set(simulated["Disease"].astype(str)).issubset({"absent", "present"}):
        raise AssertionError("simulated Disease states are outside the CPD state names")
    if not set(simulated["Test"].astype(str)).issubset({"negative", "positive"}):
        raise AssertionError("simulated Test states are outside the CPD state names")

    return {
        "model_valid": True,
        "query": "P(Disease | Test=positive)",
        "posterior_present": round(present_prob, 12),
        "expected_present": round(expected, 12),
        "map_query": map_result,
        "belief_propagation_present": round(bp_present_prob, 12),
        "simulation_shape": list(simulated.shape),
        "simulation_columns": list(simulated.columns),
        "simulation_preview": simulated.astype(str).head(min(samples, 5)).to_dict(orient="records"),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a tiny pgmpy Bayesian network, validate it, run exact inference "
            "and MAP checks, and simulate a few rows."
        )
    )
    parser.add_argument("--samples", type=int, default=6, help="number of rows to simulate; default: 6")
    parser.add_argument("--seed", type=int, default=42, help="random seed for simulation; default: 42")
    parser.add_argument("--json", action="store_true", help="emit compact JSON instead of a readable summary")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = run_smoke(samples=args.samples, seed=args.seed)
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("pgmpy inference smoke passed")
        print(f"  {result['query']}: present={result['posterior_present']}")
        print(f"  MAP: {result['map_query']}")
        print(f"  simulated shape: {tuple(result['simulation_shape'])}")
        print("  simulation preview:")
        for row in result["simulation_preview"]:
            print(f"    {row}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
