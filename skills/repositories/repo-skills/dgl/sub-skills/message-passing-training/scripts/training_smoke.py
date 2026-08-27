#!/usr/bin/env python3
"""CPU-safe smoke test for DGL message passing and PyTorch full-graph training."""

from __future__ import annotations

import argparse
import json
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic tiny DGL/PyTorch full-graph training smoke. "
            "No datasets are downloaded."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print a machine-readable JSON summary instead of a text summary",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        import dgl
        import dgl.function as fn
        import dgl.nn.pytorch as dglnn
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"ERROR: failed to import DGL/PyTorch: {exc}", file=sys.stderr)
        return 2

    torch.manual_seed(7)

    src = torch.tensor([0, 1, 2, 3, 0, 2], dtype=torch.int64)
    dst = torch.tensor([1, 2, 3, 0, 2, 1], dtype=torch.int64)
    graph = dgl.graph((src, dst), num_nodes=4)
    graph = dgl.add_self_loop(graph)
    features = torch.arange(16, dtype=torch.float32).reshape(4, 4) / 10.0
    labels = torch.tensor([0, 1, 0, 1], dtype=torch.int64)
    train_mask = torch.tensor([True, True, True, False])

    with graph.local_scope():
        graph.ndata["h"] = features
        graph.edata["w"] = torch.ones(graph.num_edges(), 1)
        graph.update_all(fn.u_mul_e("h", "w", "m"), fn.sum("m", "h_sum"))
        message_shape = tuple(graph.ndata["h_sum"].shape)

    class TinyModel(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.conv1 = dglnn.GraphConv(4, 5)
            self.conv2 = dglnn.SAGEConv(5, 2, "mean")

        def forward(self, g, x):
            h = F.relu(self.conv1(g, x))
            return self.conv2(g, h)

    model = TinyModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    logits = model(graph, features)
    loss = F.cross_entropy(logits[train_mask], labels[train_mask])
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    gat = dglnn.GATConv(4, 2, num_heads=2, allow_zero_in_degree=True)
    gat_shape = tuple(gat(graph, features).shape)

    graph_a = dgl.graph((torch.tensor([0, 1]), torch.tensor([1, 0])), num_nodes=2)
    graph_b = dgl.graph((torch.tensor([0, 1]), torch.tensor([1, 2])), num_nodes=3)
    batched = dgl.batch([graph_a, graph_b])
    batched.ndata["h"] = torch.ones(batched.num_nodes(), 2)
    readout_shape = tuple(dgl.mean_nodes(batched, "h").shape)

    hetero = dgl.heterograph(
        {
            ("user", "follows", "user"): (
                torch.tensor([0, 1], dtype=torch.int64),
                torch.tensor([1, 2], dtype=torch.int64),
            ),
            ("user", "plays", "game"): (
                torch.tensor([0, 2], dtype=torch.int64),
                torch.tensor([0, 1], dtype=torch.int64),
            ),
        },
        num_nodes_dict={"user": 3, "game": 2},
    )
    hetero_conv = dglnn.HeteroGraphConv(
        {
            ("user", "follows", "user"): dglnn.SAGEConv((4, 4), 3, "mean"),
            ("user", "plays", "game"): dglnn.SAGEConv((4, 4), 3, "mean"),
        },
        aggregate="sum",
    )
    hetero_out = hetero_conv(
        hetero,
        {
            "user": torch.randn(3, 4),
            "game": torch.randn(2, 4),
        },
    )
    hetero_shapes = {key: tuple(value.shape) for key, value in hetero_out.items()}

    checks = {
        "message_shape": message_shape,
        "logits_shape": tuple(logits.shape),
        "loss": float(loss.detach()),
        "gat_shape": gat_shape,
        "readout_shape": readout_shape,
        "hetero_shapes": hetero_shapes,
    }

    if not torch.isfinite(loss):
        print("ERROR: training loss is not finite", file=sys.stderr)
        return 1
    if checks["logits_shape"] != (4, 2):
        print(f"ERROR: unexpected logits shape {checks['logits_shape']}", file=sys.stderr)
        return 1
    if checks["message_shape"] != (4, 4):
        print(f"ERROR: unexpected message shape {checks['message_shape']}", file=sys.stderr)
        return 1
    if checks["gat_shape"] != (4, 2, 2):
        print(f"ERROR: unexpected GAT shape {checks['gat_shape']}", file=sys.stderr)
        return 1
    if checks["readout_shape"] != (2, 2):
        print(f"ERROR: unexpected readout shape {checks['readout_shape']}", file=sys.stderr)
        return 1
    if checks["hetero_shapes"].get("user") != (3, 3) or checks["hetero_shapes"].get("game") != (2, 3):
        print(f"ERROR: unexpected heterograph shapes {checks['hetero_shapes']}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"ok": True, "checks": checks}, sort_keys=True))
    else:
        print("OK: DGL message passing training smoke passed")
        for key, value in checks.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
