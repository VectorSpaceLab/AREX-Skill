#!/usr/bin/env python3
"""Validate deterministic GraphRAG graph-helper behavior on tiny edge lists."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run offline graph-helper checks for degree and connected components."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of a human-readable summary.",
    )
    return parser.parse_args()


def load_dependencies() -> dict[str, Any]:
    try:
        import networkx as nx
        import pandas as pd
        from graphrag.graphs.compute_degree import compute_degree
        from graphrag.graphs.connected_components import connected_components
        from graphrag.graphs.stable_lcc import stable_lcc
    except ImportError as exc:
        raise SystemExit(
            "GraphRAG graph dependencies are not importable. Install GraphRAG before "
            "running this helper, or use --help to inspect options."
        ) from exc

    return {
        "nx": nx,
        "pd": pd,
        "compute_degree": compute_degree,
        "connected_components": connected_components,
        "stable_lcc": stable_lcc,
    }


def run_checks(symbols: dict[str, Any]) -> dict[str, Any]:
    pd = symbols["pd"]
    compute_degree = symbols["compute_degree"]
    connected_components = symbols["connected_components"]
    stable_lcc = symbols["stable_lcc"]

    relationships = pd.DataFrame(
        [
            {"source": " A ", "target": "b", "weight": 1.0},
            {"source": "B", "target": "c", "weight": 2.0},
            {"source": "D", "target": "E", "weight": 3.0},
        ]
    )
    normalized_relationships = relationships.assign(
        source=relationships["source"].str.strip().str.upper(),
        target=relationships["target"].str.strip().str.upper(),
    )

    degree = compute_degree(normalized_relationships)
    components = connected_components(normalized_relationships)
    lcc = stable_lcc(relationships)

    degree_map = dict(zip(degree["title"], degree["degree"], strict=True))
    expected_degree = {"A": 1, "B": 2, "C": 1, "D": 1, "E": 1}
    lcc_nodes = sorted(set(lcc["source"]).union(lcc["target"]))
    component_sizes = sorted([len(component) for component in components], reverse=True)

    checks = [
        {
            "name": "degree_counts",
            "ok": degree_map == expected_degree,
            "observed": degree_map,
            "expected": expected_degree,
        },
        {
            "name": "component_sizes",
            "ok": component_sizes == [3, 2],
            "observed": component_sizes,
            "expected": [3, 2],
        },
        {
            "name": "stable_lcc_nodes",
            "ok": lcc_nodes == ["A", "B", "C"],
            "observed": lcc_nodes,
            "expected": ["A", "B", "C"],
        },
    ]
    return {"ok": all(check["ok"] for check in checks), "checks": checks}


def main() -> int:
    args = parse_args()
    report = run_checks(load_dependencies())
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for check in report["checks"]:
            status = "ok" if check["ok"] else "failed"
            print(f"{check['name']}: {status}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
