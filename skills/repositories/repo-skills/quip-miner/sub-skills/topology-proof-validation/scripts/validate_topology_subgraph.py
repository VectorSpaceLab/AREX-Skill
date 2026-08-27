#!/usr/bin/env python3
"""Validate that a candidate topology JSON(.gz) is a subgraph of a reference topology."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as fh:  # type: ignore[arg-type]
        return json.load(fh)


def _nodes_edges(data: dict[str, Any]) -> tuple[set[int], set[tuple[int, int]]]:
    nodes = {int(n) for n in data.get("nodes", [])}
    edges = set()
    for edge in data.get("edges", []):
        if len(edge) < 2:
            continue
        u, v = int(edge[0]), int(edge[1])
        edges.add((min(u, v), max(u, v)))
    return nodes, edges


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True, help="Reference hardware topology JSON or JSON.GZ.")
    parser.add_argument("--candidate", type=Path, required=True, help="Candidate/mined topology JSON or JSON.GZ.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    ref_nodes, ref_edges = _nodes_edges(_load(args.reference))
    cand_nodes, cand_edges = _nodes_edges(_load(args.candidate))
    missing_nodes = sorted(cand_nodes - ref_nodes)
    missing_edges = sorted(cand_edges - ref_edges)
    result = {
        "reference": str(args.reference),
        "candidate": str(args.candidate),
        "reference_nodes": len(ref_nodes),
        "reference_edges": len(ref_edges),
        "candidate_nodes": len(cand_nodes),
        "candidate_edges": len(cand_edges),
        "valid": not missing_nodes and not missing_edges,
        "missing_nodes_count": len(missing_nodes),
        "missing_edges_count": len(missing_edges),
        "missing_nodes_sample": missing_nodes[:10],
        "missing_edges_sample": missing_edges[:10],
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Reference: {result['reference_nodes']} nodes / {result['reference_edges']} edges")
        print(f"Candidate: {result['candidate_nodes']} nodes / {result['candidate_edges']} edges")
        print("VALID" if result["valid"] else "INVALID")
        if missing_nodes:
            print(f"Missing nodes ({len(missing_nodes)}): {missing_nodes[:10]}")
        if missing_edges:
            print(f"Missing edges ({len(missing_edges)}): {missing_edges[:10]}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
