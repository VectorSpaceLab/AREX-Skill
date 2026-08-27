#!/usr/bin/env python3
"""Safe smoke checks for PyTorch Geometric loaders on tiny synthetic data."""

import argparse
import json
import sys
import traceback
from typing import Any, Dict


def _tensor_to_list(value: Any):
    if hasattr(value, "detach"):
        return value.detach().cpu().tolist()
    return value


def check_dataloader(verbose: bool = False) -> Dict[str, Any]:
    import torch
    from torch_geometric.data import Data
    from torch_geometric.loader import DataLoader

    graph_a = Data(
        x=torch.tensor([[1.0], [2.0], [3.0]]),
        edge_index=torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]], dtype=torch.long),
        y=torch.tensor([0]),
    )
    graph_b = Data(
        x=torch.tensor([[4.0], [5.0]]),
        edge_index=torch.tensor([[0, 1], [1, 0]], dtype=torch.long),
        y=torch.tensor([1]),
    )

    batch = next(iter(DataLoader([graph_a, graph_b], batch_size=2, shuffle=False)))

    assert batch.num_graphs == 2, f"expected 2 graphs, got {batch.num_graphs}"
    assert batch.num_nodes == 5, f"expected 5 nodes, got {batch.num_nodes}"
    assert batch.batch.tolist() == [0, 0, 0, 1, 1]
    assert batch.ptr.tolist() == [0, 3, 5]
    assert batch.edge_index.tolist() == [[0, 1, 1, 2, 3, 4], [1, 0, 2, 1, 4, 3]]
    assert batch.y.tolist() == [0, 1]

    result = {
        "ok": True,
        "num_graphs": int(batch.num_graphs),
        "num_nodes": int(batch.num_nodes),
        "batch": batch.batch.tolist(),
        "ptr": batch.ptr.tolist(),
        "edge_index": batch.edge_index.tolist() if verbose else "validated",
    }
    return result


def check_follow_batch() -> Dict[str, Any]:
    import torch
    from torch_geometric.data import Data
    from torch_geometric.loader import DataLoader

    data = Data(
        x=torch.randn(3, 2),
        pos=torch.randn(3, 2),
        edge_index=torch.tensor([[0, 1], [1, 2]], dtype=torch.long),
        y=torch.tensor([0]),
    )

    batch = next(iter(DataLoader([data, data], batch_size=2, follow_batch=["pos"])))

    assert batch.pos_batch.tolist() == [0, 0, 0, 1, 1, 1]
    assert batch.pos_ptr.tolist() == [0, 3, 6]

    return {
        "ok": True,
        "pos_batch": batch.pos_batch.tolist(),
        "pos_ptr": batch.pos_ptr.tolist(),
    }


def check_neighbor_loader(verbose: bool = False) -> Dict[str, Any]:
    import torch
    from torch_geometric.data import Data
    from torch_geometric.loader import NeighborLoader

    data = Data(
        x=torch.arange(8, dtype=torch.float).view(-1, 1),
        edge_index=torch.tensor(
            [[2, 3, 3, 4, 5, 6, 7], [0, 0, 1, 1, 2, 3, 4]],
            dtype=torch.long,
        ),
    )

    loader = NeighborLoader(
        data,
        input_nodes=torch.tensor([0, 1], dtype=torch.long),
        num_neighbors=[2, 1],
        batch_size=1,
        replace=False,
        shuffle=False,
    )

    try:
        batch = next(iter(loader))
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report backend failures.
        message = str(exc)
        lower_message = message.lower()
        backend_hint = any(token in lower_message for token in ("pyg-lib", "pyg_lib", "torch-sparse", "torch_sparse", "neighborsampler"))
        return {
            "ok": False,
            "skipped": backend_hint,
            "reason": "NeighborLoader iteration failed. Install a compatible pyg-lib or torch-sparse backend if neighbor sampling is required.",
            "error_type": type(exc).__name__,
            "error": message,
        }

    assert int(batch.batch_size) == 1
    assert batch.n_id[: batch.batch_size].tolist() == [0]
    assert int(batch.edge_index.max()) < int(batch.num_nodes)

    return {
        "ok": True,
        "batch_size": int(batch.batch_size),
        "n_id": batch.n_id.tolist(),
        "edge_index": batch.edge_index.tolist() if verbose else "validated",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run safe PyTorch Geometric loader smoke checks on tiny synthetic graphs."
    )
    parser.add_argument(
        "--check-neighbor",
        action="store_true",
        help="Also try to iterate a tiny NeighborLoader; reports missing optional sampler backends without failing unless --strict-neighbor is set.",
    )
    parser.add_argument(
        "--strict-neighbor",
        action="store_true",
        help="Exit non-zero if the NeighborLoader check cannot run because an optional sampler backend is unavailable.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include validated tensor contents in JSON output where practical.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output: Dict[str, Any] = {"checks": {}}

    try:
        output["checks"]["dataloader"] = check_dataloader(verbose=args.verbose)
        output["checks"]["follow_batch"] = check_follow_batch()
        if args.check_neighbor:
            output["checks"]["neighbor_loader"] = check_neighbor_loader(verbose=args.verbose)
            if args.strict_neighbor and not output["checks"]["neighbor_loader"].get("ok", False):
                output["ok"] = False
                print(json.dumps(output, indent=2, sort_keys=True))
                return 2
        output["ok"] = True
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except ModuleNotFoundError as exc:
        output["ok"] = False
        output["error_type"] = type(exc).__name__
        output["error"] = str(exc)
        output["reason"] = "Install torch and torch_geometric in the active Python environment before running PyG loader checks."
        print(json.dumps(output, indent=2, sort_keys=True), file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - produce clear CLI diagnostics.
        output["ok"] = False
        output["error_type"] = type(exc).__name__
        output["error"] = str(exc)
        output["reason"] = "A loader smoke assertion or runtime check failed; rerun with --verbose after fixing the reported issue."
        print(json.dumps(output, indent=2, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
