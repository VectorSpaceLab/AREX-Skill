#!/usr/bin/env python3
"""Self-contained CPU smoke for graph-layer shape and dependency contracts.

This helper intentionally does not import the repository checkout. It probes
only the installed PyTorch/PyG compiled operations and implements tiny local
shape checks for sparse, dense, aggregation, and reversible patterns.
"""
from __future__ import annotations

import argparse
import sys
from typing import Iterable


def _finite(name: str, value) -> None:
    import torch

    if not torch.isfinite(value).all().item():
        raise RuntimeError(f"{name} produced non-finite values")


def _check_sparse(torch, scatter, scatter_softmax, knn_graph) -> list[str]:
    n, c = 8, 4
    x = torch.arange(n * c, dtype=torch.float32).reshape(n, c) / 10
    # Source row -> target row; this is a deliberately tiny explicit graph.
    src = torch.tensor([0, 1, 2, 3, 4, 5, 6, 7, 1, 2, 3, 4], dtype=torch.long)
    dst = torch.tensor([1, 2, 3, 4, 5, 6, 7, 0, 0, 1, 2, 3], dtype=torch.long)
    edge_index = torch.stack((src, dst))
    msg = x[src]
    for reduce in ("add", "mean", "max"):
        out = scatter(msg, dst, dim=0, dim_size=n, reduce=reduce)
        if tuple(out.shape) != (n, c):
            raise RuntimeError(f"sparse {reduce} shape: {tuple(out.shape)}")
        _finite(f"sparse {reduce}", out)
    weights = scatter_softmax(msg[:, :1], dst, dim=0)
    softmax_out = scatter(msg * weights, dst, dim=0, dim_size=n, reduce="sum")
    _finite("sparse softmax", softmax_out)
    knn_edges = knn_graph(x, k=2, batch=torch.zeros(n, dtype=torch.long), loop=False)
    if knn_edges.ndim != 2 or knn_edges.shape[0] != 2:
        raise RuntimeError(f"sparse KNN shape: {tuple(knn_edges.shape)}")
    _finite("sparse features", x)
    return [f"sparse explicit edge_index={tuple(edge_index.shape)}", f"sparse knn={tuple(knn_edges.shape)}"]


def _check_dense(torch) -> list[str]:
    b, c, n, k = 2, 4, 8, 2
    x = torch.arange(b * c * n, dtype=torch.float32).reshape(b, c, n, 1) / 10
    points = x.squeeze(-1).transpose(1, 2).contiguous()
    distances = (points.unsqueeze(2) - points.unsqueeze(1)).square().sum(-1)
    neighbors = distances.topk(k=k, dim=-1, largest=False).indices
    centers = torch.arange(n).view(1, n, 1).expand(b, n, k)
    edge_index = torch.stack((neighbors, centers))
    if tuple(edge_index.shape) != (2, b, n, k):
        raise RuntimeError(f"dense KNN shape: {tuple(edge_index.shape)}")
    base = torch.arange(b, dtype=torch.long).view(b, 1, 1) * n
    flat = x.squeeze(-1).transpose(1, 2).reshape(b * n, c)
    neighbor_features = flat[(neighbors + base).reshape(-1)].reshape(b, n, k, c)
    center_features = x.squeeze(-1).transpose(1, 2).unsqueeze(2)
    relative = (neighbor_features - center_features).amax(dim=2)
    out = relative.transpose(1, 2).unsqueeze(-1)
    if tuple(out.shape) != (b, c, n, 1):
        raise RuntimeError(f"dense output shape: {tuple(out.shape)}")
    _finite("dense relative output", out)
    return [f"dense x={tuple(x.shape)}", f"dense edge_index={tuple(edge_index.shape)}"]


def _check_reversible(torch, nn) -> list[str]:
    n, channels, group = 5, 6, 2
    torch.manual_seed(7)
    x = torch.randn(n, channels, requires_grad=True)
    chunks = torch.chunk(x, group, dim=-1)
    fms = nn.ModuleList(nn.Linear(channels // group, channels // group) for _ in range(group))

    def forward(value):
        xs = torch.chunk(value, group, dim=-1)
        y_in = sum(xs[1:])
        ys = []
        for i, fm in enumerate(fms):
            y = xs[i] + fm(y_in)
            ys.append(y)
            y_in = y
        return torch.cat(ys, dim=-1)

    def inverse(value):
        ys = torch.chunk(value, group, dim=-1)
        recovered = []
        for i in range(group - 1, -1, -1):
            y_in = ys[i - 1] if i else sum(recovered)
            recovered.append(ys[i] - fms[i](y_in))
        return torch.cat(recovered[::-1], dim=-1)

    y = forward(x)
    restored = inverse(y)
    error = (restored - x).abs().max()
    if error.item() > 1e-5:
        raise RuntimeError(f"reversible round-trip error: {error.item():.3g}")
    y.square().mean().backward()
    if x.grad is None or not torch.isfinite(x.grad).all().item():
        raise RuntimeError("reversible backward produced invalid gradients")
    return [f"reversible group={group} max_error={error.item():.3g}"]


def run_tiny() -> int:
    try:
        import torch
        from torch_scatter import scatter, scatter_softmax
        from torch_cluster import knn_graph
    except Exception as exc:  # pragma: no cover - environment-dependent
        print(f"BLOCKED: compatible torch/PyG compiled stack unavailable: {exc}", file=sys.stderr)
        return 2

    try:
        results: list[str] = []
        results.extend(_check_sparse(torch, scatter, scatter_softmax, knn_graph))
        results.extend(_check_dense(torch))
        results.extend(_check_reversible(torch, torch.nn))
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"OK: CPU tiny graph-layer smoke; torch={torch.__version__}")
    for result in results:
        print(f"- {result}")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run self-contained CPU shape, KNN, aggregation, and reversible checks."
    )
    parser.add_argument(
        "--tiny",
        action="store_true",
        help="run the bounded CPU smoke (without this flag, print usage)",
    )
    args = parser.parse_args(argv)
    if not args.tiny:
        parser.print_help()
        return 0
    return run_tiny()


if __name__ == "__main__":
    raise SystemExit(main())
