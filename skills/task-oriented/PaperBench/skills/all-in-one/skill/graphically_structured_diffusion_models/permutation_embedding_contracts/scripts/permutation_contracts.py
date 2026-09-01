#!/usr/bin/env python3
"""Permutation and embedding checks for GSDM masks."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


NODE_RE = re.compile(r"^(?P<array>[A-Za-z_][A-Za-z0-9_]*)\[(?P<indices>[0-9,]+)\]$")


def validate_permutation(permutation: list[int], size: int) -> None:
    if len(permutation) != size:
        raise ValueError("permutation length does not match mask size")
    if sorted(permutation) != list(range(size)):
        raise ValueError("permutation must be a bijection over node indices")


def preserves_mask(mask: list[list[bool]], permutation: list[int]) -> dict:
    size = len(mask)
    validate_permutation(permutation, size)
    for i in range(size):
        for j in range(size):
            if bool(mask[i][j]) != bool(mask[permutation[i]][permutation[j]]):
                return {
                    "preserves_mask": False,
                    "mismatch": {
                        "source": [i, j],
                        "permuted": [permutation[i], permutation[j]],
                        "source_value": bool(mask[i][j]),
                        "permuted_value": bool(mask[permutation[i]][permutation[j]]),
                    },
                }
    return {"preserves_mask": True, "mismatch": None}


def array_name(node: str) -> str:
    match = NODE_RE.match(node)
    if not match:
        return node
    return match.group("array")


def embedding_groups(nodes: list[str], mode: str, arrays: dict[str, str] | None = None, exchangeable_groups: dict[str, str] | None = None) -> dict[str, str]:
    if mode == "independent":
        return {node: f"node:{idx}" for idx, node in enumerate(nodes)}
    if mode == "array":
        arrays = arrays or {node: array_name(node) for node in nodes}
        return {node: f"array:{arrays[node]}" for node in nodes}
    if mode == "exchangeable":
        if not exchangeable_groups:
            raise ValueError("exchangeable mode requires explicit exchangeable_groups")
        missing = [node for node in nodes if node not in exchangeable_groups]
        if missing:
            raise ValueError("exchangeable_groups missing nodes: " + ", ".join(missing[:5]))
        return {node: f"exchangeable:{exchangeable_groups[node]}" for node in nodes}
    raise ValueError(f"unknown embedding mode: {mode}")


def bcmf_swap_i_permutation(nodes: list[str], first: int, second: int) -> list[int]:
    destination_by_node = {}
    for node in nodes:
        match = NODE_RE.match(node)
        if not match:
            destination_by_node[node] = node
            continue
        arr = match.group("array")
        indices = [int(value) for value in match.group("indices").split(",")]
        if arr in {"A", "C", "E"} and indices[0] == first:
            indices[0] = second
        elif arr in {"A", "C", "E"} and indices[0] == second:
            indices[0] = first
        destination_by_node[node] = f"{arr}[{','.join(str(value) for value in indices)}]"
    index = {node: idx for idx, node in enumerate(nodes)}
    return [index[destination_by_node[node]] for node in nodes]


def partial_swap_permutation(nodes: list[str], left_node: str, right_node: str) -> list[int]:
    index = {node: idx for idx, node in enumerate(nodes)}
    perm = list(range(len(nodes)))
    left = index[left_node]
    right = index[right_node]
    perm[left], perm[right] = perm[right], perm[left]
    return perm


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph-json", required=True)
    parser.add_argument("--swap-i", nargs=2, type=int, metavar=("FIRST", "SECOND"))
    parser.add_argument("--partial-swap", nargs=2, metavar=("LEFT_NODE", "RIGHT_NODE"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    graph = json.loads(Path(args.graph_json).read_text(encoding="utf-8"))
    nodes = graph["nodes"]
    if args.swap_i:
        permutation = bcmf_swap_i_permutation(nodes, args.swap_i[0], args.swap_i[1])
    elif args.partial_swap:
        permutation = partial_swap_permutation(nodes, args.partial_swap[0], args.partial_swap[1])
    else:
        permutation = list(range(len(nodes)))
    check = preserves_mask(graph["mask"], permutation)
    groups = embedding_groups(nodes, "array", arrays=graph.get("arrays"))
    result = {"permutation": permutation, **check, "embedding_groups": groups}
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "preserves_mask": check["preserves_mask"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
