#!/usr/bin/env python3
"""Smoke-test OSMnx graph validation, GDF round-trip, and GraphML I/O.

This script is intentionally self-contained: it creates a tiny in-memory graph
and writes only to a temporary directory unless --workdir is provided. It does
not read the OSMnx source checkout or make network requests.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

import networkx as nx
import osmnx as ox
from shapely import LineString


def build_tiny_graph() -> nx.MultiDiGraph:
    """Create a minimal OSMnx-compatible directed graph."""
    G = nx.MultiDiGraph(crs="epsg:4326", simplified=False)
    G.add_node(1, x=-122.0000, y=37.0000, street_count=1)
    G.add_node(2, x=-121.9990, y=37.0000, street_count=2)
    G.add_node(3, x=-121.9980, y=37.0005, street_count=1)

    G.add_edge(
        1,
        2,
        key=0,
        osmid=1001,
        length=88.8,
        highway="residential",
        oneway=False,
    )
    G.add_edge(
        2,
        1,
        key=0,
        osmid=1001,
        length=88.8,
        highway="residential",
        oneway=False,
    )
    G.add_edge(
        2,
        3,
        key=0,
        osmid=1002,
        length=104.2,
        highway="residential",
        oneway=True,
        geometry=LineString([(-121.9990, 37.0000), (-121.9985, 37.0003), (-121.9980, 37.0005)]),
    )
    return G


def run_smoke(workdir: Path) -> dict[str, Any]:
    """Run smoke checks and return a JSON-serializable summary."""
    workdir.mkdir(parents=True, exist_ok=True)

    G = build_tiny_graph()
    ox.convert.validate_graph(G)

    gdf_nodes, gdf_edges = ox.convert.graph_to_gdfs(G, fill_edge_geometry=True)
    ox.convert.validate_node_edge_gdfs(gdf_nodes, gdf_edges)

    G_roundtrip = ox.convert.graph_from_gdfs(gdf_nodes, gdf_edges, graph_attrs=G.graph.copy())
    ox.convert.validate_graph(G_roundtrip)

    D = ox.convert.to_digraph(G_roundtrip, weight="length")
    Gu = ox.convert.to_undirected(G_roundtrip)

    graphml_path = workdir / "tiny-osmnx-smoke.graphml"
    ox.io.save_graphml(G_roundtrip, graphml_path)
    G_loaded = ox.io.load_graphml(graphml_path)
    ox.convert.validate_graph(G_loaded)

    return {
        "osmnx_version": getattr(ox, "__version__", "unknown"),
        "graphml_path": str(graphml_path),
        "nodes": len(G_loaded.nodes),
        "edges": len(G_loaded.edges),
        "node_index_name": gdf_nodes.index.name,
        "edge_index_names": list(gdf_edges.index.names),
        "digraph_edges": len(D.edges),
        "undirected_edges": len(Gu.edges),
        "checks": [
            "validate_graph",
            "graph_to_gdfs",
            "validate_node_edge_gdfs",
            "graph_from_gdfs",
            "to_digraph",
            "to_undirected",
            "save_graphml",
            "load_graphml",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny no-network OSMnx graph/GDF/GraphML smoke test.",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="Directory for the temporary GraphML file. Defaults to an auto-removed temp directory.",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the auto-created temporary directory and print its path. Ignored when --workdir is set.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the success summary as JSON instead of human-readable text.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.workdir is not None:
        summary = run_smoke(args.workdir)
    elif args.keep:
        tempdir = tempfile.mkdtemp(prefix="osmnx-graph-io-smoke-")
        summary = run_smoke(Path(tempdir))
        summary["tempdir"] = tempdir
    else:
        with tempfile.TemporaryDirectory(prefix="osmnx-graph-io-smoke-") as tempdir:
            summary = run_smoke(Path(tempdir))
            # The file is intentionally temporary, so make that explicit.
            summary["graphml_path"] = "removed with temporary directory"

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "OSMnx graph I/O smoke passed: "
            f"version={summary['osmnx_version']}, "
            f"nodes={summary['nodes']}, edges={summary['edges']}, "
            f"edge_index={summary['edge_index_names']}"
        )
        if "tempdir" in summary:
            print(f"Kept temporary directory: {summary['tempdir']}")


if __name__ == "__main__":
    main()
