#!/usr/bin/env python3
"""Download-free synthetic smoke for OGB-shaped model contracts.

This is intentionally self-contained and does not import the repository,
construct an OGB dataset, read a checkpoint, or perform network I/O. It checks
small node, graph, link, and reversible tensor contracts with PyTorch only.
"""
from __future__ import annotations

import argparse
import sys
from typing import Iterable, Optional


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run a tiny, download-free OGB model-contract smoke."
    )
    p.add_argument(
        "--task",
        choices=("node", "graph", "link", "reversible", "all"),
        default="all",
        help="synthetic contract to check (default: all)",
    )
    p.add_argument(
        "--aggregator",
        choices=("max", "mean", "add", "softmax", "power"),
        default="softmax",
        help="tiny GENConv-style aggregation (default: softmax)",
    )
    p.add_argument("--seed", type=int, default=7, help="random seed")
    return p


def require_torch():
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("PyTorch is required for the tiny smoke") from exc
    return torch


def aggregate(torch, messages, dst, n_nodes, name):
    out = torch.zeros(n_nodes, messages.size(1), dtype=messages.dtype)
    if name == "add":
        out.index_add_(0, dst, messages)
        return out
    if name == "mean":
        out.index_add_(0, dst, messages)
        degree = torch.bincount(dst, minlength=n_nodes).clamp_min(1).view(-1, 1)
        return out / degree
    if name == "max":
        rows = []
        for node in range(n_nodes):
            selected = messages[dst == node]
            rows.append(
                selected.max(dim=0).values
                if selected.numel()
                else torch.zeros(messages.size(1), dtype=messages.dtype)
            )
        return torch.stack(rows, dim=0)
    if name == "softmax":
        weights = torch.zeros(messages.size(0), dtype=messages.dtype)
        for node in range(n_nodes):
            mask = dst == node
            if mask.any():
                weights[mask] = torch.softmax(messages[mask].mean(dim=1), dim=0)
        out.index_add_(0, dst, messages * weights.view(-1, 1))
        return out
    if name == "power":
        out.index_add_(0, dst, messages.abs().pow(2.0))
        degree = torch.bincount(dst, minlength=n_nodes).clamp_min(1).view(-1, 1)
        return (out / degree).sqrt()
    raise ValueError(name)


def graph_layer(torch, x, edge_index, aggregator, edge_attr=None):
    src, dst = edge_index
    messages = x[src]
    if edge_attr is not None:
        messages = messages + edge_attr
    return x + aggregate(torch, messages, dst, x.size(0), aggregator)


def finite(torch, tensor, label):
    if tensor.numel() == 0 or not bool(torch.isfinite(tensor).all()):
        raise AssertionError(f"{label} contains a non-finite or empty tensor")


def run_node(torch, aggregator):
    x = torch.randn(5, 8, requires_grad=True)
    edges = torch.tensor([[0, 1, 2, 3, 4, 0], [1, 2, 3, 4, 0, 2]])
    h = graph_layer(torch, x, edges, aggregator)
    logits = torch.nn.Linear(8, 3)(h)
    loss = logits.square().mean()
    loss.backward()
    finite(torch, logits, "node logits")
    return tuple(logits.shape)


def run_graph(torch, aggregator):
    x = torch.randn(6, 8)
    edges = torch.tensor([[0, 1, 2, 3, 4, 5, 0, 3], [1, 2, 0, 4, 5, 3, 2, 0]])
    edge_attr = torch.randn(edges.size(1), 8)
    h = graph_layer(torch, x, edges, aggregator, edge_attr)
    batch = torch.tensor([0, 0, 0, 1, 1, 1])
    pooled = torch.stack([h[batch == i].mean(0) for i in range(2)])
    logits = torch.nn.Linear(8, 2)(pooled)
    finite(torch, logits, "graph logits")
    return tuple(logits.shape)


def run_link(torch, aggregator):
    x = torch.randn(5, 8)
    edges = torch.tensor([[0, 1, 2, 3, 4], [1, 2, 3, 4, 0]])
    h = graph_layer(torch, x, edges, aggregator)
    pairs = torch.tensor([[0, 2], [1, 4], [3, 0]])
    pair = h[pairs[:, 0]] * h[pairs[:, 1]]
    score = torch.sigmoid(torch.nn.Linear(8, 1)(pair))
    finite(torch, score, "link scores")
    return tuple(score.shape)


def run_reversible(torch, aggregator):
    # Additive coupling with two feature groups; the branch is deterministic.
    x = torch.randn(4, 8)
    edges = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]])
    x0, x1 = x.chunk(2, dim=-1)
    delta0 = graph_layer(torch, x1, edges, aggregator)
    y0 = x0 + delta0
    delta1 = graph_layer(torch, y0, edges, aggregator)
    y1 = x1 + delta1
    z0, z1 = y0, y1
    recovered_x1 = z1 - graph_layer(torch, z0, edges, aggregator)
    recovered_x0 = z0 - graph_layer(torch, recovered_x1, edges, aggregator)
    recovered = torch.cat((recovered_x0, recovered_x1), dim=-1)
    if not bool(torch.allclose(x, recovered, atol=1e-5, rtol=1e-5)):
        raise AssertionError("reversible additive round-trip failed")
    finite(torch, recovered, "reversible state")
    return tuple(recovered.shape)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parser().parse_args(argv)
    torch = require_torch()
    torch.manual_seed(args.seed)
    runners = {
        "node": run_node,
        "graph": run_graph,
        "link": run_link,
        "reversible": run_reversible,
    }
    selected = runners.keys() if args.task == "all" else (args.task,)
    results = []
    for name in selected:
        shape = runners[name](torch, args.aggregator)
        results.append(f"{name}:{shape}")
    print("OK tiny synthetic smoke (no OGB data or checkpoints): " + ", ".join(results))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, RuntimeError, ValueError) as exc:
        print(f"SMOKE_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
