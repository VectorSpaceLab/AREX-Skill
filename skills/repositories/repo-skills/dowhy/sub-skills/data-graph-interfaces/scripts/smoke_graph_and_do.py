#!/usr/bin/env python3
"""Smoke test for DoWhy graph parsing and pandas causal do-sampler.

This script is intentionally tiny and download-free. It can be run from any
working directory as long as DoWhy and its base dependencies are importable in
the active Python environment.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a no-download DoWhy smoke check for graph parsing and df.causal.do.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Random seed for synthetic data generation. Default: 7.",
    )
    parser.add_argument(
        "--samples",
        type=_positive_int,
        default=200,
        help="Number of synthetic rows to generate. Default: 200.",
    )
    parser.add_argument(
        "--graph-format",
        choices=["gml", "dot"],
        default="gml",
        help="Graph string format to parse. GML is the default because it avoids DOT parser dependencies.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print only a JSON result object.",
    )
    return parser


def _build_graph_string(nx: Any, graph_format: str) -> str:
    graph = nx.DiGraph([("W", "X"), ("W", "Y"), ("X", "Y")])
    if graph_format == "gml":
        return "\n".join(nx.generate_gml(graph))
    if graph_format == "dot":
        return "digraph { W -> X; W -> Y; X -> Y; }"
    raise ValueError(f"Unsupported graph format: {graph_format}")


def _run(seed: int, samples: int, graph_format: str) -> dict[str, Any]:
    import networkx as nx
    import numpy as np
    import pandas as pd

    import dowhy.api  # noqa: F401  # registers df.causal accessor
    from dowhy.graph import build_graph_from_str

    rng = np.random.default_rng(seed)

    graph_str = _build_graph_string(nx, graph_format)
    graph = build_graph_from_str(graph_str)

    expected_nodes = {"W", "X", "Y"}
    expected_edges = {("W", "X"), ("W", "Y"), ("X", "Y")}
    graph_nodes = set(graph.nodes)
    graph_edges = {(str(u), str(v)) for u, v in graph.edges}

    if graph_nodes != expected_nodes:
        raise AssertionError(f"Parsed graph nodes mismatch: {sorted(graph_nodes)}")
    if graph_edges != expected_edges:
        raise AssertionError(f"Parsed graph edges mismatch: {sorted(graph_edges)}")

    w = rng.normal(size=samples)
    treatment_prob = 1.0 / (1.0 + np.exp(-0.8 * w))
    x = rng.binomial(1, treatment_prob, size=samples)
    y = 2.0 * x + 0.5 * w + rng.normal(scale=0.25, size=samples)
    df = pd.DataFrame({"W": w, "X": x, "Y": y})

    variable_types = {"W": "c", "X": "b", "Y": "c"}
    sampled = df.causal.do(
        x={"X": 1},
        outcome="Y",
        graph=graph,
        variable_types=variable_types,
        method="weighting",
    )

    if len(sampled) != samples:
        raise AssertionError(f"Expected {samples} sampled rows, got {len(sampled)}")
    if set(sampled["X"].unique()) != {1}:
        raise AssertionError("Intervention did not force X to the requested value 1")
    if sampled["Y"].isna().any():
        raise AssertionError("Sampled outcome contains NaN values")

    return {
        "ok": True,
        "seed": seed,
        "samples": samples,
        "graph_format": graph_format,
        "graph_nodes": sorted(str(node) for node in graph.nodes),
        "graph_edges": sorted([str(edge) for edge in graph.edges]),
        "sampled_rows": int(len(sampled)),
        "intervention_values": sorted(int(value) for value in sampled["X"].unique()),
        "outcome_mean": float(sampled["Y"].mean()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = _make_parser()
    args = parser.parse_args(argv)

    try:
        result = _run(seed=args.seed, samples=args.samples, graph_format=args.graph_format)
    except Exception as exc:  # pragma: no cover - CLI diagnostic path
        failure = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "hint": (
                "If --graph-format dot failed, retry with --graph-format gml or install a DOT parser backend. "
                "If df.causal.do failed, check that DoWhy base dependencies are installed."
            ),
        }
        print(json.dumps(failure, indent=2, sort_keys=True), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("DoWhy graph + pandas do-sampler smoke check passed.")
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
