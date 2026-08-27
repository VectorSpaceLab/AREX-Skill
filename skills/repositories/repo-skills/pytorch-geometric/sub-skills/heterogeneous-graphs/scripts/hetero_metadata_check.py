#!/usr/bin/env python3
"""Validate tiny PyG HeteroData metadata and optional reverse-edge expectations."""

from __future__ import annotations

import argparse
import sys
from typing import Any, Iterable

EdgeType = tuple[str, str, str]


class DependencyError(RuntimeError):
    """Raised when public PyG runtime dependencies are unavailable."""


def load_dependencies() -> tuple[Any, Any]:
    try:
        import torch
        from torch_geometric.data import HeteroData
    except Exception as exc:  # pragma: no cover - depends on runtime environment.
        raise DependencyError(
            "this check requires installed public packages 'torch' and "
            "'torch_geometric'"
        ) from exc
    return torch, HeteroData


def build_tiny_hetero_data(
    *,
    include_reverse: bool,
    forward_relation: str,
    reverse_relation: str,
) -> Any:
    torch, HeteroData = load_dependencies()
    data = HeteroData()
    data["user"].x = torch.tensor(
        [[1.0, 0.0, 0.5], [0.0, 1.0, 0.5], [0.5, 0.5, 1.0]],
        dtype=torch.float,
    )
    data["movie"].x = torch.tensor(
        [[1.0, 0.2, 0.0], [0.1, 0.8, 1.0]],
        dtype=torch.float,
    )

    forward_edge_index = torch.tensor([[0, 1, 2, 0], [0, 1, 1, 0]], dtype=torch.long)
    data["user", forward_relation, "movie"].edge_index = forward_edge_index

    if include_reverse:
        data["movie", reverse_relation, "user"].edge_index = forward_edge_index.flip(0)

    return data


def validate_edge_type(edge_type: object) -> EdgeType:
    if not isinstance(edge_type, tuple) or len(edge_type) != 3:
        raise ValueError(f"edge type must be a 3-tuple, got {edge_type!r}")
    src, relation, dst = edge_type
    if not all(isinstance(part, str) and part for part in edge_type):
        raise ValueError(f"edge type parts must be non-empty strings, got {edge_type!r}")
    return src, relation, dst


def validate_data(data: Any, *, require_reverse: bool, forward_type: EdgeType, reverse_type: EdgeType) -> list[str]:
    torch, _ = load_dependencies()
    messages: list[str] = []
    node_types, edge_types = data.metadata()

    if not node_types:
        raise ValueError("metadata has no node types")
    if not edge_types:
        raise ValueError("metadata has no edge types")

    for node_type in node_types:
        store = data[node_type]
        if "x" not in store and store.num_nodes is None:
            raise ValueError(f"node type {node_type!r} has neither x nor num_nodes")
        messages.append(f"node type {node_type!r}: num_nodes={store.num_nodes}")

    for raw_edge_type in edge_types:
        edge_type = validate_edge_type(raw_edge_type)
        src_type, _, dst_type = edge_type
        if src_type not in node_types:
            raise ValueError(f"edge type {edge_type!r} references missing source node type {src_type!r}")
        if dst_type not in node_types:
            raise ValueError(f"edge type {edge_type!r} references missing destination node type {dst_type!r}")

        edge_index = data[edge_type].edge_index
        if edge_index.dtype != torch.long:
            raise ValueError(f"edge_index for {edge_type!r} must use torch.long dtype")
        if edge_index.dim() != 2 or edge_index.size(0) != 2:
            raise ValueError(f"edge_index for {edge_type!r} must have shape [2, num_edges]")
        if edge_index.numel() == 0:
            messages.append(f"edge type {edge_type!r}: empty edge_index")
            continue

        src_count = data[src_type].num_nodes
        dst_count = data[dst_type].num_nodes
        if src_count is None or dst_count is None:
            raise ValueError(f"cannot infer node counts for edge type {edge_type!r}")
        if int(edge_index[0].max()) >= src_count or int(edge_index[0].min()) < 0:
            raise ValueError(f"source indices for {edge_type!r} are outside [0, {src_count})")
        if int(edge_index[1].max()) >= dst_count or int(edge_index[1].min()) < 0:
            raise ValueError(f"target indices for {edge_type!r} are outside [0, {dst_count})")
        messages.append(f"edge type {edge_type!r}: num_edges={edge_index.size(1)}")

    if forward_type not in edge_types:
        raise ValueError(f"expected forward edge type {forward_type!r} is missing")
    if require_reverse:
        if reverse_type not in edge_types:
            raise ValueError(f"expected reverse edge type {reverse_type!r} is missing")
        forward_edge_index = data[forward_type].edge_index
        reverse_edge_index = data[reverse_type].edge_index
        if not torch.equal(forward_edge_index.flip(0), reverse_edge_index):
            raise ValueError("reverse edge_index is not the flipped forward edge_index")
        messages.append(f"reverse edge type {reverse_type!r}: matches flipped forward edges")

    return messages


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and validate a tiny synthetic PyG HeteroData object.",
    )
    parser.add_argument(
        "--require-reverse",
        action="store_true",
        help="Require a reverse edge type and verify it flips the forward edge_index.",
    )
    parser.add_argument(
        "--drop-reverse",
        action="store_true",
        help="Omit the synthetic reverse edge store to demonstrate failure handling.",
    )
    parser.add_argument(
        "--expect-failure",
        action="store_true",
        help="Exit successfully only if validation fails; useful for negative smoke checks.",
    )
    parser.add_argument(
        "--forward-relation",
        default="rates",
        help="Relation name for the synthetic ('user', relation, 'movie') edge type.",
    )
    parser.add_argument(
        "--reverse-relation",
        default="rev_rates",
        help="Relation name for the synthetic ('movie', relation, 'user') reverse edge type.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    forward_type = ("user", args.forward_relation, "movie")
    reverse_type = ("movie", args.reverse_relation, "user")
    try:
        data = build_tiny_hetero_data(
            include_reverse=not args.drop_reverse,
            forward_relation=args.forward_relation,
            reverse_relation=args.reverse_relation,
        )
        messages = validate_data(
            data,
            require_reverse=args.require_reverse,
            forward_type=forward_type,
            reverse_type=reverse_type,
        )
    except DependencyError as exc:
        print(f"dependency check failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        if args.expect_failure:
            print(f"expected validation failure: {exc}")
            return 0
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1

    if args.expect_failure:
        print("validation succeeded but --expect-failure was set", file=sys.stderr)
        return 1

    node_types, edge_types = data.metadata()
    print("validation passed")
    print(f"node_types={node_types}")
    print(f"edge_types={edge_types}")
    for message in messages:
        print(f"- {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
