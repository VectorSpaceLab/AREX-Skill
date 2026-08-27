#!/usr/bin/env python3
"""Tiny CPU smoke checks for attention and heterogeneous PGT layers.

The script is deterministic, uses synthetic tensors only, performs no downloads,
and is safe to run from any working directory after PyTorch Geometric Temporal
and its PyG dependencies are importable.

Examples:
    python scripts/attention_hetero_smoke.py --help
    python scripts/attention_hetero_smoke.py
    python scripts/attention_hetero_smoke.py --checks temporalconv heterogclstm
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable


def _shape(tensor: Any) -> list[int]:
    return list(tensor.shape)


def run_temporalconv() -> dict[str, Any]:
    import torch
    from torch_geometric_temporal.nn.attention import TemporalConv

    torch.manual_seed(7)
    batch_size, time_steps, num_nodes, in_channels = 2, 5, 4, 3
    out_channels, kernel_size = 2, 3
    x = torch.arange(
        batch_size * time_steps * num_nodes * in_channels, dtype=torch.float32
    ).reshape(batch_size, time_steps, num_nodes, in_channels)
    x = x / x.abs().max().clamp_min(1.0)

    model = TemporalConv(
        in_channels=in_channels,
        out_channels=out_channels,
        kernel_size=kernel_size,
    ).eval()
    with torch.no_grad():
        y = model(x)

    expected = (batch_size, time_steps - (kernel_size - 1), num_nodes, out_channels)
    assert tuple(y.shape) == expected, f"TemporalConv shape {tuple(y.shape)} != {expected}"
    assert torch.isfinite(y).all(), "TemporalConv produced non-finite values"
    return {"output_shape": _shape(y), "expected_shape": list(expected)}


def run_stconv() -> dict[str, Any]:
    import torch
    from torch_geometric_temporal.nn.attention import STConv

    torch.manual_seed(11)
    batch_size, time_steps, num_nodes, in_channels = 2, 5, 4, 3
    hidden_channels, out_channels, kernel_size = 5, 2, 2
    x = torch.randn(batch_size, time_steps, num_nodes, in_channels)
    edge_index = torch.tensor(
        [[0, 1, 2, 3, 0, 2, 1, 3], [1, 2, 3, 0, 2, 0, 3, 1]],
        dtype=torch.long,
    )
    edge_weight = torch.ones(edge_index.size(1), dtype=torch.float32)

    model = STConv(
        num_nodes=num_nodes,
        in_channels=in_channels,
        hidden_channels=hidden_channels,
        out_channels=out_channels,
        kernel_size=kernel_size,
        K=2,
        normalization="sym",
    ).eval()
    with torch.no_grad():
        y = model(x, edge_index, edge_weight)

    expected = (
        batch_size,
        time_steps - 2 * (kernel_size - 1),
        num_nodes,
        out_channels,
    )
    assert tuple(y.shape) == expected, f"STConv shape {tuple(y.shape)} != {expected}"
    assert torch.isfinite(y).all(), "STConv produced non-finite values"
    return {"output_shape": _shape(y), "expected_shape": list(expected)}


def run_heterogclstm() -> dict[str, Any]:
    import torch
    from torch_geometric_temporal.nn.hetero import HeteroGCLSTM

    torch.manual_seed(13)
    x_dict = {
        "author": torch.randn(3, 2),
        "paper": torch.randn(4, 3),
    }
    edge_index_dict = {
        ("author", "writes", "paper"): torch.tensor(
            [[0, 1, 2, 0], [1, 2, 3, 0]], dtype=torch.long
        ),
        ("paper", "rev_writes", "author"): torch.tensor(
            [[1, 2, 3, 0], [0, 1, 2, 0]], dtype=torch.long
        ),
    }
    in_channels_dict = {node_type: x.shape[-1] for node_type, x in x_dict.items()}
    out_channels = 4
    metadata = (list(x_dict.keys()), list(edge_index_dict.keys()))

    layer = HeteroGCLSTM(
        in_channels_dict=in_channels_dict,
        out_channels=out_channels,
        metadata=metadata,
    ).eval()

    h_dict, c_dict = layer(x_dict, edge_index_dict)
    h_dict, c_dict = layer(x_dict, edge_index_dict, h_dict, c_dict)

    for node_type, x in x_dict.items():
        expected = (x.shape[0], out_channels)
        assert tuple(h_dict[node_type].shape) == expected, (
            f"HeteroGCLSTM h[{node_type!r}] shape {tuple(h_dict[node_type].shape)} "
            f"!= {expected}"
        )
        assert tuple(c_dict[node_type].shape) == expected, (
            f"HeteroGCLSTM c[{node_type!r}] shape {tuple(c_dict[node_type].shape)} "
            f"!= {expected}"
        )
        assert torch.isfinite(h_dict[node_type]).all(), f"h[{node_type!r}] has non-finite values"
        assert torch.isfinite(c_dict[node_type]).all(), f"c[{node_type!r}] has non-finite values"

    return {
        "node_types": list(x_dict.keys()),
        "hidden_shapes": {key: _shape(value) for key, value in h_dict.items()},
        "cell_shapes": {key: _shape(value) for key, value in c_dict.items()},
        "edge_types": ["|".join(edge_type) for edge_type in edge_index_dict],
    }


CHECKS: dict[str, Callable[[], dict[str, Any]]] = {
    "temporalconv": run_temporalconv,
    "stconv": run_stconv,
    "heterogclstm": run_heterogclstm,
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run tiny CPU-only smoke checks for TemporalConv, STConv, and "
            "HeteroGCLSTM using synthetic tensors and no downloads."
        )
    )
    parser.add_argument(
        "--checks",
        nargs="+",
        choices=sorted(CHECKS),
        default=sorted(CHECKS),
        help="Subset of checks to run (default: all).",
    )
    parser.add_argument(
        "--allow-stconv-skip",
        action="store_true",
        help=(
            "Report STConv as skipped instead of failing if a PyG optional operation "
            "or compatible ChebConv dependency is unavailable."
        ),
    )
    parser.add_argument(
        "--json-indent",
        type=int,
        default=2,
        help="Indentation for the JSON result payload (default: 2).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    results: dict[str, Any] = {"status": "ok", "checks": {}}

    for name in args.checks:
        try:
            results["checks"][name] = {"status": "ok", **CHECKS[name]()}
        except Exception as exc:  # noqa: BLE001 - diagnostic script should summarize failures.
            if name == "stconv" and args.allow_stconv_skip:
                results["checks"][name] = {
                    "status": "skipped",
                    "reason": f"{type(exc).__name__}: {exc}",
                }
                continue
            results["status"] = "failed"
            results["checks"][name] = {
                "status": "failed",
                "reason": f"{type(exc).__name__}: {exc}",
            }
            print(json.dumps(results, indent=args.json_indent, sort_keys=True))
            return 1

    print(json.dumps(results, indent=args.json_indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
