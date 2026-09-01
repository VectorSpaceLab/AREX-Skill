#!/usr/bin/env python3
"""Graph-to-attention helpers for GSDM-style sparse masks."""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path


def bcmf_graph(m: int, n: int, k: int) -> dict:
    if min(m, n, k) <= 0:
        raise ValueError("m, n, and k must be positive")
    nodes = []
    arrays = {}
    for i in range(m):
        for kk in range(k):
            node = f"A[{i},{kk}]"
            nodes.append(node)
            arrays[node] = "A"
    for kk in range(k):
        for j in range(n):
            node = f"R[{kk},{j}]"
            nodes.append(node)
            arrays[node] = "R"
    for i in range(m):
        for kk in range(k):
            for j in range(n):
                node = f"C[{i},{kk},{j}]"
                nodes.append(node)
                arrays[node] = "C"
    for i in range(m):
        for j in range(n):
            node = f"E[{i},{j}]"
            nodes.append(node)
            arrays[node] = "E"

    edges = []
    for i in range(m):
        for kk in range(k):
            for j in range(n):
                c = f"C[{i},{kk},{j}]"
                edges.append((f"A[{i},{kk}]", c))
                edges.append((f"R[{kk},{j}]", c))
                edges.append((c, f"E[{i},{j}]"))
    return {"nodes": nodes, "edges": edges, "factors": [], "arrays": arrays, "dims": {"m": m, "n": n, "k": k}}


def build_attention_mask(nodes: list[str], edges: list[tuple[str, str]] | list[list[str]], factors: list[list[str]] | None = None) -> list[list[bool]]:
    index = {node: pos for pos, node in enumerate(nodes)}
    if len(index) != len(nodes):
        raise ValueError("nodes must be unique")
    mask = [[False for _ in nodes] for _ in nodes]
    for i in range(len(nodes)):
        mask[i][i] = True
    for left, right in edges:
        if left not in index or right not in index:
            raise ValueError(f"edge references unknown node: {left}, {right}")
        i, j = index[left], index[right]
        mask[i][j] = True
        mask[j][i] = True
    for factor in factors or []:
        for node in factor:
            if node not in index:
                raise ValueError(f"factor references unknown node: {node}")
        for left, right in combinations(factor, 2):
            i, j = index[left], index[right]
            mask[i][j] = True
            mask[j][i] = True
    return mask


def pack_mask(mask: list[list[bool]]) -> dict:
    if not mask:
        return {"attendable_indices": [], "valid_indices_mask": [], "max_attendable": 0}
    width = max(sum(1 for value in row if value) for row in mask)
    attendable_indices = []
    valid_indices_mask = []
    for row in mask:
        indices = [idx for idx, value in enumerate(row) if value]
        valid = [1] * len(indices)
        if indices:
            pad_value = indices[-1]
        else:
            pad_value = 0
        while len(indices) < width:
            indices.append(pad_value)
            valid.append(0)
        attendable_indices.append(indices)
        valid_indices_mask.append(valid)
    return {
        "attendable_indices": attendable_indices,
        "valid_indices_mask": valid_indices_mask,
        "max_attendable": width,
    }


def unpack_mask(packed: dict, node_count: int) -> list[list[bool]]:
    mask = [[False for _ in range(node_count)] for _ in range(node_count)]
    for row, (indices, valid) in enumerate(zip(packed["attendable_indices"], packed["valid_indices_mask"])):
        for idx, is_valid in zip(indices, valid):
            if is_valid:
                mask[row][idx] = True
    return mask


def mask_stats(mask: list[list[bool]]) -> dict:
    row_counts = [sum(1 for value in row if value) for row in mask]
    return {
        "node_count": len(mask),
        "allowed_pairs": sum(row_counts),
        "max_attendable": max(row_counts) if row_counts else 0,
        "min_attendable": min(row_counts) if row_counts else 0,
    }


def build_bcmf_attention(m: int, n: int, k: int) -> dict:
    graph = bcmf_graph(m, n, k)
    mask = build_attention_mask(graph["nodes"], graph["edges"], graph["factors"])
    packed = pack_mask(mask)
    return {
        **graph,
        "mask": mask,
        "packed": packed,
        "stats": mask_stats(mask),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bcmf", nargs=3, type=int, metavar=("M", "N", "K"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not args.bcmf:
        parser.error("--bcmf M N K is required")
    m, n, k = args.bcmf
    result = build_bcmf_attention(m, n, k)
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "stats": result["stats"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
