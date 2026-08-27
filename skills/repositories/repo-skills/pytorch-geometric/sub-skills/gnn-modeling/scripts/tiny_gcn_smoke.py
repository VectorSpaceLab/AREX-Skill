#!/usr/bin/env python3
"""Tiny synthetic GCN training smoke test for PyTorch Geometric.

This script avoids downloads, GPUs, network access, and repository-local files. It
uses only public installed torch and torch_geometric APIs for the actual smoke
run, while keeping --help available before importing those dependencies.
"""

import argparse
import sys


def import_runtime_dependencies():
    try:
        import torch
        import torch.nn.functional as F
        from torch_geometric.data import Data
        from torch_geometric.nn import GCNConv
    except ModuleNotFoundError as exc:
        missing = exc.name or "required package"
        raise SystemExit(
            f"Missing runtime dependency '{missing}'. Install torch and torch_geometric "
            "in the active Python environment, then rerun this smoke test."
        ) from exc
    return torch, F, Data, GCNConv


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a safe synthetic PyTorch Geometric GCN training smoke test."
    )
    parser.add_argument("--epochs", type=int, default=8, help="Optimization steps to run.")
    parser.add_argument("--hidden-channels", type=int, default=8, help="Hidden feature width.")
    parser.add_argument("--lr", type=float, default=0.05, help="Adam learning rate.")
    parser.add_argument("--weight-decay", type=float, default=0.0, help="Adam weight decay.")
    parser.add_argument("--seed", type=int, default=12345, help="Deterministic torch seed.")
    parser.add_argument(
        "--loss-tolerance",
        type=float,
        default=0.05,
        help="Allowed final-loss increase over initial loss for very short runs.",
    )
    parser.add_argument(
        "--min-accuracy",
        type=float,
        default=0.80,
        help="Minimum training accuracy required on the synthetic graph.",
    )
    args = parser.parse_args(argv)
    if args.epochs < 1:
        parser.error("--epochs must be at least 1")
    if args.hidden_channels < 1:
        parser.error("--hidden-channels must be at least 1")
    if args.min_accuracy < 0.0 or args.min_accuracy > 1.0:
        parser.error("--min-accuracy must be between 0 and 1")
    return args


def run(args: argparse.Namespace) -> int:
    torch, F, Data, GCNConv = import_runtime_dependencies()

    class TinyGCN(torch.nn.Module):
        def __init__(self, in_channels: int, hidden_channels: int, out_channels: int):
            super().__init__()
            self.conv1 = GCNConv(in_channels, hidden_channels)
            self.conv2 = GCNConv(hidden_channels, out_channels)

        def forward(self, x, edge_index):
            x = self.conv1(x, edge_index).relu()
            return self.conv2(x, edge_index)

    def build_tiny_graph():
        x = torch.tensor(
            [
                [1.0, 0.0, 0.1],
                [0.9, 0.1, 0.0],
                [0.8, 0.2, 0.1],
                [0.0, 1.0, 0.9],
                [0.1, 0.8, 1.0],
                [0.2, 0.9, 0.8],
            ],
            dtype=torch.float,
        )
        edge_index = torch.tensor(
            [
                [0, 1, 1, 2, 3, 4, 4, 5, 2, 3],
                [1, 0, 2, 1, 4, 3, 5, 4, 3, 2],
            ],
            dtype=torch.long,
        )
        y = torch.tensor([0, 0, 0, 1, 1, 1], dtype=torch.long)
        train_mask = torch.tensor([True, True, True, True, True, True])
        return Data(x=x, edge_index=edge_index, y=y, train_mask=train_mask)

    def validate_graph(data) -> None:
        if data.x is None or data.edge_index is None or data.y is None:
            raise AssertionError("data must contain x, edge_index, and y")
        if data.x.dim() != 2:
            raise AssertionError(
                f"x must have shape [num_nodes, features], got {tuple(data.x.shape)}"
            )
        if data.edge_index.dtype != torch.long:
            raise AssertionError("edge_index must use dtype torch.long")
        if data.edge_index.dim() != 2 or data.edge_index.size(0) != 2:
            raise AssertionError(
                f"edge_index must have shape [2, num_edges], got {tuple(data.edge_index.shape)}"
            )
        if data.edge_index.numel() and int(data.edge_index.max()) >= data.x.size(0):
            raise AssertionError("edge_index references a node outside x")
        if data.y.dtype != torch.long:
            raise AssertionError("class labels y must use dtype torch.long")
        if data.train_mask.dtype != torch.bool or data.train_mask.numel() != data.x.size(0):
            raise AssertionError("train_mask must be boolean with one value per node")

    torch.manual_seed(args.seed)
    data = build_tiny_graph()
    validate_graph(data)

    model = TinyGCN(
        in_channels=data.num_node_features,
        hidden_channels=args.hidden_channels,
        out_channels=2,
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    losses = []
    for _ in range(args.epochs):
        model.train()
        optimizer.zero_grad()
        out = model(data.x, data.edge_index)
        if out.shape != (data.num_nodes, 2):
            raise AssertionError(f"unexpected output shape {tuple(out.shape)}")
        loss = F.cross_entropy(out[data.train_mask], data.y[data.train_mask])
        if not torch.isfinite(loss):
            raise AssertionError("loss is not finite")
        loss.backward()
        if not any(
            param.grad is not None and torch.isfinite(param.grad).all()
            for param in model.parameters()
            if param.requires_grad
        ):
            raise AssertionError("no finite gradients were produced")
        optimizer.step()
        losses.append(float(loss.detach()))

    model.eval()
    with torch.no_grad():
        logits = model(data.x, data.edge_index)
        pred = logits.argmax(dim=-1)
        accuracy = float((pred == data.y).float().mean())

    if losses[-1] > losses[0] + args.loss_tolerance:
        raise AssertionError(
            f"final loss {losses[-1]:.6f} exceeded initial loss {losses[0]:.6f} "
            f"by more than tolerance {args.loss_tolerance}"
        )
    if accuracy < args.min_accuracy:
        raise AssertionError(
            f"accuracy {accuracy:.3f} below required minimum {args.min_accuracy:.3f}"
        )

    print(f"initial_loss={losses[0]:.6f}")
    print(f"final_loss={losses[-1]:.6f}")
    print(f"accuracy={accuracy:.3f}")
    print(f"pred={pred.tolist()}")
    print("tiny_gcn_smoke: ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(parse_args(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":
    raise SystemExit(main())
