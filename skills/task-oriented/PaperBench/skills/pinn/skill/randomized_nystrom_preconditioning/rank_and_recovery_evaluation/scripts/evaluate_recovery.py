#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path

import numpy as np


def effective_dimension(eigenvalues, mu):
    eigenvalues = np.asarray(eigenvalues, dtype=float)
    if mu <= 0:
        raise ValueError("mu must be positive")
    return float(np.sum(eigenvalues / (eigenvalues + mu)))


def choose_rank(eigenvalues, mu, rank_cap=None, n=None):
    deff = effective_dimension(eigenvalues, mu)
    theoretical = int(2 * math.ceil(1.5 * deff) + 1)
    upper = int(n if n is not None else len(eigenvalues))
    if rank_cap is not None:
        upper = min(upper, int(rank_cap))
    rank = max(1, min(theoretical, upper))
    return {"effective_dimension": deff, "theoretical_rank": theoretical, "selected_rank": rank, "rank_cap": upper}


def evaluate_trace(cg_trace, pcg_trace, condition_stats, mechanism_checks, tolerance=1e-8):
    cg_iterations = int(cg_trace["iterations"])
    pcg_iterations = int(pcg_trace["iterations"])
    pcg_converged = bool(pcg_trace.get("converged", False))
    pcg_final_rel = float(pcg_trace.get("relative_residuals", [1.0])[-1])
    cond_reduced = condition_stats["condition_preconditioned"] < condition_stats["condition_A_mu"]
    iter_reduced = pcg_iterations < cg_iterations
    mechanism_ok = all(bool(mechanism_checks.get(key, False)) for key in [
        "randomized_nystrom_factorization_executed",
        "preconditioner_applied",
        "pcg_iterations_executed",
    ])
    ok = pcg_converged and pcg_final_rel <= tolerance and cond_reduced and iter_reduced and mechanism_ok
    return {
        "ok": bool(ok),
        "pcg_converged": pcg_converged,
        "pcg_final_relative_residual": pcg_final_rel,
        "cg_iterations": cg_iterations,
        "pcg_iterations": pcg_iterations,
        "iteration_reduction": cg_iterations - pcg_iterations,
        "condition_reduction_factor": condition_stats["condition_A_mu"] / condition_stats["condition_preconditioned"],
        "condition_reduced": bool(cond_reduced),
        "iteration_reduced": bool(iter_reduced),
        "mechanism_ok": bool(mechanism_ok),
    }


def _self_test():
    vals = np.array([100.0, 10.0, 1.0, 0.1])
    rank = choose_rank(vals, 0.5, rank_cap=3)
    assert rank["selected_rank"] == 3
    decision = evaluate_trace(
        {"iterations": 50},
        {"iterations": 12, "converged": True, "relative_residuals": [1.0, 1e-9]},
        {"condition_A_mu": 1000.0, "condition_preconditioned": 20.0},
        {"randomized_nystrom_factorization_executed": True, "preconditioner_applied": True, "pcg_iterations_executed": True},
    )
    assert decision["ok"]
    rejected = evaluate_trace(
        {"iterations": 10},
        {"iterations": 12, "converged": True, "relative_residuals": [1.0, 1e-9]},
        {"condition_A_mu": 1000.0, "condition_preconditioned": 20.0},
        {"randomized_nystrom_factorization_executed": True, "preconditioner_applied": True, "pcg_iterations_executed": True},
    )
    assert not rejected["ok"]
    return {"ok": True, "rank": rank, "decision": decision}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        print(json.dumps(_self_test(), indent=2))
        return 0
    if args.input is None or args.output is None:
        parser.error("--input and --output are required unless --self-test is used")
    payload = json.loads(args.input.read_text())
    result = evaluate_trace(payload["cg_trace"], payload["pcg_trace"], payload["condition_stats"], payload["mechanism_checks"], payload.get("tolerance", 1e-8))
    args.output.write_text(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
