#!/usr/bin/env python3
"""Validate tiny PyTorch Geometric graph fixtures and print a JSON summary."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Tuple


def require_pyg() -> Tuple[Any, Any, Any, Any]:
    try:
        import torch
        from torch_geometric.data import Batch, Data, HeteroData
    except ModuleNotFoundError as exc:
        missing = exc.name or "torch/torch_geometric"
        raise RuntimeError(
            f"Missing required package '{missing}'. Install torch and "
            "torch_geometric before running validation fixtures."
        ) from exc
    return torch, Batch, Data, HeteroData


def make_homogeneous(torch: Any, Data: Any) -> Any:
    data = Data(
        x=torch.tensor(
            [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [0.5, 0.5]],
            dtype=torch.float,
        ),
        edge_index=torch.tensor(
            [[0, 1, 2, 3], [1, 2, 3, 0]],
            dtype=torch.long,
        ),
        y=torch.tensor([0, 1, 0, 1], dtype=torch.long),
    )
    data.train_mask = torch.tensor([True, True, False, False])
    data.val_mask = torch.tensor([False, False, True, False])
    data.test_mask = torch.tensor([False, False, False, True])
    return data


def make_hetero(torch: Any, HeteroData: Any) -> Any:
    data = HeteroData()
    data["paper"].x = torch.tensor(
        [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
        dtype=torch.float,
    )
    data["author"].x = torch.tensor(
        [[0.2, 0.8], [0.8, 0.2]],
        dtype=torch.float,
    )
    data[("author", "writes", "paper")].edge_index = torch.tensor(
        [[0, 1, 1], [0, 1, 2]],
        dtype=torch.long,
    )
    data[("paper", "written_by", "author")].edge_index = torch.tensor(
        [[0, 1, 2], [0, 1, 1]],
        dtype=torch.long,
    )
    return data


def make_invalid(torch: Any, Data: Any) -> Any:
    return Data(
        x=torch.randn(3, 2),
        edge_index=torch.tensor(
            [[0, 1], [1, 2], [2, 3]],
            dtype=torch.long,
        ),
    )


def validate_masks(torch: Any, data: Any) -> None:
    for key in ("train_mask", "val_mask", "test_mask"):
        if key not in data:
            continue
        mask = data[key]
        if mask.dtype != torch.bool:
            raise ValueError(f"{key} must have dtype torch.bool")
        if data.num_nodes is None or mask.numel() != data.num_nodes:
            raise ValueError(
                f"{key} length {mask.numel()} does not match num_nodes "
                f"{data.num_nodes}"
            )


def validate_homogeneous(torch: Any, Batch: Any, data: Any) -> Dict[str, Any]:
    data.validate(raise_on_error=True)
    if data.edge_index.dtype != torch.long:
        raise ValueError("edge_index must use torch.long dtype")
    if data.x is not None and data.num_nodes is not None:
        if data.x.size(0) != data.num_nodes:
            raise ValueError("x.size(0) must match num_nodes")
    validate_masks(torch, data)
    batch = Batch.from_data_list([data, data.clone()])
    return {
        "type": "Data",
        "num_nodes": int(data.num_nodes or 0),
        "num_edges": int(data.num_edges),
        "keys": sorted(data.keys()),
        "batch_num_graphs": int(batch.num_graphs),
        "batch_num_nodes": int(batch.num_nodes),
    }


def validate_hetero(data: Any) -> Dict[str, Any]:
    data.validate(raise_on_error=True)
    node_types, edge_types = data.metadata()
    return {
        "type": "HeteroData",
        "node_types": list(node_types),
        "edge_types": [list(edge_type) for edge_type in edge_types],
        "num_nodes_by_type": {
            node_type: int(data[node_type].num_nodes or 0)
            for node_type in node_types
        },
        "num_edges_by_type": {
            "__".join(edge_type): int(data[edge_type].num_edges)
            for edge_type in edge_types
        },
    }


def build_fixture(name: str, torch: Any, Data: Any, HeteroData: Any) -> Tuple[Any, str]:
    if name == "homogeneous":
        return make_homogeneous(torch, Data), "valid"
    if name == "hetero":
        return make_hetero(torch, HeteroData), "valid"
    if name == "invalid":
        return make_invalid(torch, Data), "invalid"
    raise ValueError(f"Unsupported fixture: {name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate tiny PyTorch Geometric Data or HeteroData fixtures and "
            "print a JSON summary."
        )
    )
    parser.add_argument(
        "--fixture",
        choices=("homogeneous", "hetero", "invalid"),
        default="homogeneous",
        help="Fixture to validate. The invalid fixture is expected to fail.",
    )
    parser.add_argument(
        "--expect-invalid",
        action="store_true",
        help="Treat validation failure as success; intended for the invalid fixture.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        torch, Batch, Data, HeteroData = require_pyg()
    except RuntimeError as exc:
        print(json.dumps({
            "ok": False,
            "fixture": args.fixture,
            "error": str(exc),
        }, indent=2, sort_keys=True), file=sys.stderr)
        return 1

    try:
        fixture, expected_state = build_fixture(args.fixture, torch, Data, HeteroData)
        if isinstance(fixture, HeteroData):
            summary = validate_hetero(fixture)
        else:
            summary = validate_homogeneous(torch, Batch, fixture)
    except Exception as exc:
        if args.expect_invalid:
            print(json.dumps({
                "ok": True,
                "fixture": args.fixture,
                "validation_failed_as_expected": True,
                "error": str(exc),
            }, indent=2, sort_keys=True))
            return 0
        print(json.dumps({
            "ok": False,
            "fixture": args.fixture,
            "error": str(exc),
        }, indent=2, sort_keys=True), file=sys.stderr)
        return 1

    if args.expect_invalid:
        print(json.dumps({
            "ok": False,
            "fixture": args.fixture,
            "expected_state": expected_state,
            "error": "fixture passed validation but --expect-invalid was set",
            "summary": summary,
        }, indent=2, sort_keys=True), file=sys.stderr)
        return 1

    print(json.dumps({
        "ok": True,
        "fixture": args.fixture,
        "expected_state": expected_state,
        "summary": summary,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
