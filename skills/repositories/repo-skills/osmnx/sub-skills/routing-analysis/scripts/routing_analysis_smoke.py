#!/usr/bin/env python3
"""Deterministic smoke test for OSMnx routing-analysis helpers.

The script builds a tiny in-memory graph, prepares edge lengths, speeds,
travel times, routes, stats, bearings, and optional nearest-match checks, then
prints a compact JSON summary.
"""

from __future__ import annotations

import argparse
import json
import math
from importlib.metadata import PackageNotFoundError
from typing import Any

import networkx as nx
import numpy as np


def build_toy_graph() -> nx.MultiDiGraph:
    """Create a tiny directed street graph with known route weights."""
    G = nx.MultiDiGraph(crs="epsg:4326")
    for node_id, attrs in {
        1: {"x": 0.0, "y": 0.0, "street_count": 2},
        2: {"x": 0.001, "y": 0.0, "street_count": 2},
        3: {"x": 0.001, "y": 0.001, "street_count": 2},
        4: {"x": 0.0, "y": 0.001, "street_count": 2},
    }.items():
        G.add_node(node_id, **attrs)

    for u, v, osmid, highway in (
        (1, 2, 101, "residential"),
        (2, 1, 102, "residential"),
        (2, 3, 103, "residential"),
        (3, 2, 104, "residential"),
        (1, 4, 105, "service"),
        (4, 1, 106, "service"),
        (4, 3, 107, "service"),
        (3, 4, 108, "service"),
    ):
        G.add_edge(u, v, osmid=osmid, highway=highway)

    return G


def build_projected_toy_graph() -> nx.MultiDiGraph:
    """Create a tiny projected graph for nearest-match checks."""
    G = nx.MultiDiGraph(crs="epsg:3857")
    for node_id, attrs in {
        1: {"x": 0.0, "y": 0.0},
        2: {"x": 100.0, "y": 0.0},
        3: {"x": 100.0, "y": 100.0},
        4: {"x": 0.0, "y": 100.0},
    }.items():
        G.add_node(node_id, **attrs)

    for u, v, osmid, highway in (
        (1, 2, 201, "residential"),
        (2, 1, 202, "residential"),
        (2, 3, 203, "residential"),
        (3, 2, 204, "residential"),
        (1, 4, 205, "service"),
        (4, 1, 206, "service"),
        (4, 3, 207, "service"),
        (3, 4, 208, "service"),
    ):
        G.add_edge(u, v, osmid=osmid, highway=highway)

    return G


def _as_list(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, tuple):
        return list(value)
    return value


def _round_float(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def run_smoke(cpus: int | None) -> dict[str, Any]:
    try:
        import osmnx as ox
    except (ModuleNotFoundError, PackageNotFoundError) as exc:  # pragma: no cover
        msg = f"osmnx import failed: {exc}"
        raise RuntimeError(msg) from exc

    G = build_toy_graph()

    # Distance helpers.
    great_circle_m = ox.distance.great_circle(0, 0, 1, 1)
    euclidean = ox.distance.euclidean(0, 0, 1, 1)
    assert math.isclose(great_circle_m, 157_249.6034105, rel_tol=1e-9)
    assert math.isclose(euclidean, math.sqrt(2), rel_tol=1e-9)

    # Edge lengths, speeds, and travel times.
    G = ox.distance.add_edge_lengths(G)
    lengths = [float(data["length"]) for _, _, data in G.edges(data=True)]
    assert all(length > 0 for length in lengths)

    G = ox.routing.add_edge_speeds(
        G,
        hwy_speeds={"residential": 30.0, "service": 10.0},
        fallback=20.0,
    )
    speeds = [float(data["speed_kph"]) for _, _, data in G.edges(data=True)]
    assert all(speed > 0 for speed in speeds)

    G = ox.routing.add_edge_travel_times(G)
    travel_times = [float(data["travel_time"]) for _, _, data in G.edges(data=True)]
    assert all(tt > 0 for tt in travel_times)

    # Route solving and route GeoDataFrame output.
    shortest = ox.routing.shortest_path(G, 1, 3, weight="travel_time")
    assert shortest == [1, 2, 3]

    route_gdf = ox.routing.route_to_gdf(G, shortest, weight="travel_time")
    route_index = [list(idx) for idx in route_gdf.index.to_list()]
    assert route_index == [[1, 2, 0], [2, 3, 0]]
    assert len(route_gdf) == 2

    batch_paths = ox.routing.shortest_path(
        G,
        [1, 3],
        [3, 1],
        weight="travel_time",
        cpus=cpus,
    )
    assert batch_paths == [[1, 2, 3], [3, 2, 1]]

    k_paths = list(ox.routing.k_shortest_paths(G, 1, 3, k=2, weight="travel_time"))
    assert k_paths[0] == shortest
    assert k_paths[1] == [1, 4, 3]

    # Statistics.
    count_streets = ox.stats.count_streets_per_node(G)
    assert count_streets == {1: 2, 2: 2, 3: 2, 4: 2}

    stats = ox.stats.basic_stats(G, area=1_000_000)
    assert stats["n"] == 4
    assert stats["m"] == 8
    assert math.isclose(float(stats["k_avg"]), 4.0, rel_tol=1e-9)
    assert stats["intersection_count"] == 4
    assert stats["street_segment_count"] == 4
    assert stats["edge_length_total"] > stats["street_length_total"] > 0
    assert stats["street_length_avg"] > 0
    assert math.isclose(float(stats["circuity_avg"]), 1.0, rel_tol=0.05)

    # Bearings and orientation entropy.
    G = ox.bearing.add_edge_bearings(G)
    assert math.isclose(float(G.edges[1, 2, 0]["bearing"]), 90.0, abs_tol=1e-6)
    assert math.isclose(float(G.edges[1, 4, 0]["bearing"]), 0.0, abs_tol=1e-6)

    entropy: float | None
    if ox.bearing.scipy is not None:
        Gu = ox.convert.to_undirected(G)
        entropy = ox.bearing.orientation_entropy(Gu, weight="length")
        assert math.isfinite(entropy)
        assert entropy >= 0
    else:
        entropy = None

    # Optional nearest-node / nearest-edge checks.
    nearest_summary: dict[str, Any] = {"unprojected": None, "projected": None}

    if ox.distance.BallTree is not None:
        nn_scalar = ox.distance.nearest_nodes(G, 0.001, 0.0)
        nn_vector = ox.distance.nearest_nodes(
            G,
            np.array([0.0, 0.001]),
            np.array([0.0, 0.0]),
        )
        assert nn_scalar == 2
        assert _as_list(nn_vector) == [1, 2]
        nearest_summary["unprojected"] = {
            "scalar": int(nn_scalar),
            "vector": _as_list(nn_vector),
        }
    else:
        nearest_summary["unprojected"] = "skipped: scikit-learn not installed"

    Gp = build_projected_toy_graph()
    if ox.distance.scipy is not None:
        node_2 = Gp.nodes[2]
        nn_projected = ox.distance.nearest_nodes(Gp, float(node_2["x"]), float(node_2["y"]))
        edge_mid_x = (float(Gp.nodes[1]["x"]) + float(Gp.nodes[2]["x"])) / 2
        edge_mid_y = (float(Gp.nodes[1]["y"]) + float(Gp.nodes[2]["y"])) / 2
        ne_projected, ne_dist = ox.distance.nearest_edges(
            Gp,
            edge_mid_x,
            edge_mid_y,
            return_dist=True,
        )
        assert nn_projected == 2
        assert ne_projected in {(1, 2, 0), (2, 1, 0)}
        assert math.isclose(float(ne_dist), 0.0, abs_tol=1e-6)
        nearest_summary["projected"] = {
            "node": int(nn_projected),
            "edge": list(ne_projected),
            "distance": _round_float(float(ne_dist)),
        }
    else:
        nearest_summary["projected"] = "skipped: scipy not installed"

    summary = {
        "helpers": {
            "great_circle_m": _round_float(float(great_circle_m), 6),
            "euclidean": _round_float(float(euclidean), 6),
        },
        "weights": {
            "lengths_m": [_round_float(length) for length in lengths],
            "speed_kph": [_round_float(speed) for speed in speeds],
            "travel_time_s": [_round_float(tt) for tt in travel_times],
        },
        "route": {
            "shortest_path": shortest,
            "route_index": route_index,
            "batch_paths": batch_paths,
            "k_shortest_paths": k_paths,
        },
        "stats": {
            "n": stats["n"],
            "m": stats["m"],
            "k_avg": _round_float(float(stats["k_avg"])),
            "intersection_count": stats["intersection_count"],
            "street_segment_count": stats["street_segment_count"],
            "street_length_total": _round_float(float(stats["street_length_total"])),
            "edge_length_total": _round_float(float(stats["edge_length_total"])),
            "circuity_avg": _round_float(float(stats["circuity_avg"])),
        },
        "bearings": {
            "1->2": _round_float(float(G.edges[1, 2, 0]["bearing"])),
            "1->4": _round_float(float(G.edges[1, 4, 0]["bearing"])),
            "entropy": None if entropy is None else _round_float(float(entropy)),
        },
        "nearest": nearest_summary,
    }
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny deterministic smoke test for OSMnx routing, nearest-match, "
            "stats, and bearing helpers."
        ),
    )
    parser.add_argument(
        "--cpus",
        type=int,
        default=1,
        help="CPU count for the batch shortest_path check; use 0 to auto-detect all CPUs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cpus = None if args.cpus == 0 else args.cpus
    try:
        summary = run_smoke(cpus=cpus)
    except RuntimeError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
