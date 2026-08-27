#!/usr/bin/env python3
"""Tiny deterministic smoke check for pgmpy structure and parameter learning.

The script creates an in-memory pandas DataFrame, runs one or more safe learning
operations, and prints concise results. It performs no network access and does
not read files from the current working directory.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Iterable

import pandas as pd

from pgmpy import logger
from pgmpy.causal_discovery import HillClimbSearch, PC
from pgmpy.global_vars import config
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.parameter_estimator import DiscreteBayesianEstimator


def build_fixture() -> pd.DataFrame:
    """Return a tiny categorical fixture with a stable A/B association."""
    return pd.DataFrame(
        {
            "A": [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1],
            "B": [0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1],
            "C": [0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1],
        }
    )


def sorted_edges(edges: Iterable[tuple]) -> list[tuple]:
    return sorted((str(u), str(v)) for u, v in edges)


def run_pc(data: pd.DataFrame, significance_level: float) -> str:
    est = PC(
        variant="stable",
        ci_test="chi_square",
        return_type="dag",
        significance_level=significance_level,
        max_cond_vars=1,
        show_progress=False,
    ).fit(data)
    return f"pc_edges={sorted_edges(est.causal_graph_.edges())} adjacency_shape={tuple(est.adjacency_matrix_.shape)}"


def run_hillclimb(data: pd.DataFrame) -> str:
    est = HillClimbSearch(
        scoring_method="bic-d",
        max_indegree=1,
        max_iter=50,
        return_type="dag",
        show_progress=False,
    ).fit(data)
    return f"hillclimb_edges={sorted_edges(est.causal_graph_.edges())} adjacency_shape={tuple(est.adjacency_matrix_.shape)}"


def run_parameters(data: pd.DataFrame) -> str:
    state_names = {column: [0, 1] for column in data.columns}
    model = DiscreteBayesianNetwork([("A", "B"), ("A", "C")])
    model.fit(
        data,
        estimator=DiscreteBayesianEstimator(
            state_names=state_names,
            prior_type="BDeu",
            equivalent_sample_size=2,
        ),
    )
    cpd_b = model.get_cpds("B").get_values().round(3).tolist()
    return f"parameter_cpds={len(model.get_cpds())} check_model={model.check_model()} cpd_B_given_A={cpd_b}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny deterministic pgmpy learning smoke check.")
    parser.add_argument(
        "--mode",
        choices=["all", "pc", "hillclimb", "parameters"],
        default="all",
        help="Which smoke operation to run. Default: all.",
    )
    parser.add_argument(
        "--significance-level",
        type=float,
        default=0.2,
        help="PC chi-square significance level for the tiny fixture. Default: 0.2.",
    )
    parser.add_argument("--show-data", action="store_true", help="Print the tiny input fixture before results.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config.set_show_progress(False)
    logger.setLevel(logging.ERROR)

    data = build_fixture()
    print(f"fixture_shape={tuple(data.shape)} columns={list(data.columns)}")
    if args.show_data:
        print(data.to_string(index=False))

    modes = ["pc", "hillclimb", "parameters"] if args.mode == "all" else [args.mode]
    for mode in modes:
        if mode == "pc":
            print(run_pc(data, args.significance_level))
        elif mode == "hillclimb":
            print(run_hillclimb(data))
        elif mode == "parameters":
            print(run_parameters(data))
        else:  # pragma: no cover - argparse prevents this.
            raise ValueError(f"Unknown mode: {mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
