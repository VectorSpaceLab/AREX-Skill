#!/usr/bin/env python3
"""CPU-only PyG Explainer smoke test on a tiny synthetic graph."""

import argparse
import sys
from typing import Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny CPU-only torch_geometric.explain smoke test with "
            "synthetic data and GNNExplainer."
        )
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=2,
        help="GNNExplainer optimization epochs; keep small for smoke tests.",
    )
    parser.add_argument(
        "--train-epochs",
        type=int,
        default=20,
        help="Tiny base-model training epochs before explanation.",
    )
    parser.add_argument(
        "--node-index",
        type=int,
        default=0,
        help="Node output row to explain in the six-node synthetic graph.",
    )
    parser.add_argument(
        "--threshold-topk",
        type=int,
        default=None,
        help="Optional positive integer for topk_hard mask thresholding.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=12345,
        help="Torch random seed for deterministic smoke-test behavior.",
    )
    return parser.parse_args()


def import_runtime():
    try:
        import torch
        import torch.nn.functional as F
        from torch import nn
        from torch_geometric.data import Data
        from torch_geometric.explain import Explainer, GNNExplainer
        from torch_geometric.nn import GCNConv
    except ImportError as exc:
        raise SystemExit(
            "This smoke test requires installed torch and torch_geometric packages. "
            f"Import failed: {exc}"
        ) from exc

    return torch, F, nn, Data, Explainer, GNNExplainer, GCNConv


def build_graph(torch, Data):
    x = torch.tensor(
        [
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.9, 0.1],
            [0.1, 0.0, 1.0],
            [0.0, 0.1, 0.9],
        ],
        dtype=torch.float,
    )
    edge_index = torch.tensor(
        [
            [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 0, 0, 2],
            [1, 0, 2, 1, 3, 2, 4, 3, 5, 4, 0, 5, 2, 0],
        ],
        dtype=torch.long,
    )
    y = torch.tensor([0, 0, 1, 1, 2, 2], dtype=torch.long)
    return Data(x=x, edge_index=edge_index, y=y)


def build_model(nn, F, GCNConv, in_channels: int, hidden_channels: int, out_channels: int):
    class TinyGCN(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = GCNConv(in_channels, hidden_channels)
            self.conv2 = GCNConv(hidden_channels, out_channels)

        def forward(self, x, edge_index):
            x = self.conv1(x, edge_index).relu()
            x = self.conv2(x, edge_index)
            return F.log_softmax(x, dim=-1)

    return TinyGCN()


def train_model(torch, F, model, data, epochs: int) -> None:
    optimizer = torch.optim.Adam(model.parameters(), lr=0.05, weight_decay=0.0)
    model.train()
    for _ in range(max(0, epochs)):
        optimizer.zero_grad()
        out = model(data.x, data.edge_index)
        loss = F.nll_loss(out, data.y)
        loss.backward()
        optimizer.step()


def build_explainer(Explainer, GNNExplainer, model, epochs: int, threshold_topk: Optional[int]):
    threshold_config = None
    if threshold_topk is not None:
        threshold_config = ("topk_hard", threshold_topk)

    return Explainer(
        model=model,
        algorithm=GNNExplainer(epochs=epochs),
        explanation_type="model",
        node_mask_type="attributes",
        edge_mask_type="object",
        model_config=dict(
            mode="multiclass_classification",
            task_level="node",
            return_type="log_probs",
        ),
        threshold_config=threshold_config,
    )


def check_model_config_recovery(Explainer, GNNExplainer, model) -> str:
    try:
        Explainer(
            model=model,
            algorithm=GNNExplainer(epochs=1),
            explanation_type="model",
            node_mask_type="attributes",
            edge_mask_type="object",
            model_config=dict(
                mode="binary_classification",
                task_level="node",
                return_type="log_probs",
            ),
        )
    except ValueError as exc:
        return str(exc).splitlines()[0]
    raise AssertionError("expected invalid binary/log_probs model_config to fail")


def main() -> int:
    args = parse_args()
    if args.epochs <= 0:
        raise SystemExit("--epochs must be positive")
    if args.train_epochs < 0:
        raise SystemExit("--train-epochs must be non-negative")
    if args.threshold_topk is not None and args.threshold_topk <= 0:
        raise SystemExit("--threshold-topk must be positive when provided")

    torch, F, nn, Data, Explainer, GNNExplainer, GCNConv = import_runtime()
    torch.manual_seed(args.seed)

    data = build_graph(torch, Data)
    if args.node_index < 0 or args.node_index >= data.num_nodes:
        raise SystemExit(f"--node-index must be in [0, {data.num_nodes - 1}]")

    model = build_model(
        nn,
        F,
        GCNConv,
        in_channels=data.num_node_features,
        hidden_channels=8,
        out_channels=3,
    )
    train_model(torch, F, model, data, args.train_epochs)
    model.eval()

    recovery_message = check_model_config_recovery(Explainer, GNNExplainer, model)
    explainer = build_explainer(Explainer, GNNExplainer, model, args.epochs, args.threshold_topk)
    explanation = explainer(data.x, data.edge_index, index=args.node_index)
    explanation.validate_masks()

    assert "node_mask" in explanation.available_explanations
    assert "edge_mask" in explanation.available_explanations
    assert explanation.node_mask.shape == data.x.shape
    assert explanation.edge_mask.shape == (data.edge_index.size(1),)
    assert torch.isfinite(explanation.node_mask).all()
    assert torch.isfinite(explanation.edge_mask).all()
    assert explanation.node_mask.sum() >= 0
    assert explanation.edge_mask.sum() >= 0

    with torch.no_grad():
        prediction = model(data.x, data.edge_index).argmax(dim=-1)

    print(f"available_explanations={explanation.available_explanations}")
    print(f"node_mask_shape={tuple(explanation.node_mask.shape)}")
    print(f"edge_mask_shape={tuple(explanation.edge_mask.shape)}")
    print(f"node_mask_sum={float(explanation.node_mask.sum()):.6f}")
    print(f"edge_mask_sum={float(explanation.edge_mask.sum()):.6f}")
    print(f"explained_node={args.node_index}")
    print(f"predicted_class={int(prediction[args.node_index])}")
    print(f"model_config_recovery={recovery_message}")
    print("tiny_explainer_smoke: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
