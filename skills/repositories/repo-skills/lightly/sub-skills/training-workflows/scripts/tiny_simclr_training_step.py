#!/usr/bin/env python3
"""Run one synthetic SimCLR training step without downloads."""

from __future__ import annotations

import argparse

import torch
from lightly.loss import NTXentLoss
from lightly.models.modules import SimCLRProjectionHead
from torch import nn


class TinyBackbone(nn.Module):
    """A small CNN that maps synthetic images to feature vectors."""

    def __init__(self, feature_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(32, feature_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class TinySimCLR(nn.Module):
    """A minimal SimCLR-style network for one-step smoke tests."""

    def __init__(self, feature_dim: int) -> None:
        super().__init__()
        self.backbone = TinyBackbone(feature_dim)
        hidden_dim = max(64, feature_dim * 2)
        projection_dim = max(32, feature_dim // 2)
        self.projection_head = SimCLRProjectionHead(
            input_dim=feature_dim,
            hidden_dim=hidden_dim,
            output_dim=projection_dim,
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        features = self.backbone(x)
        projections = self.projection_head(features)
        return features, projections


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one synthetic SimCLR training step on random tensors."
        )
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Choose the execution device.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Synthetic batch size for the two-view step.",
    )
    parser.add_argument(
        "--feature-dim",
        type=int,
        default=64,
        help="Output dimension of the tiny backbone features.",
    )
    parser.add_argument(
        "--image-size",
        type=int,
        default=32,
        help="Synthetic square image size.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for the synthetic batch.",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=0.1,
        help="Learning rate for the one-step SGD update.",
    )
    return parser.parse_args()


def resolve_device(choice: str) -> torch.device:
    if choice == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if choice == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but is not available.")
    return torch.device(choice)


def build_synthetic_views(
    batch_size: int,
    image_size: int,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    view_0 = torch.rand(batch_size, 3, image_size, image_size, device=device)
    noise = 0.05 * torch.randn_like(view_0)
    view_1 = (view_0 + noise).clamp(0.0, 1.0)
    return view_0, view_1


def main() -> None:
    args = parse_args()
    if args.batch_size < 2:
        raise SystemExit("--batch-size must be at least 2 for SimCLR.")
    if args.feature_dim < 1:
        raise SystemExit("--feature-dim must be positive.")
    if args.image_size < 8:
        raise SystemExit("--image-size must be at least 8.")

    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    device = resolve_device(args.device)
    model = TinySimCLR(args.feature_dim).to(device)
    criterion = NTXentLoss().to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=args.lr, momentum=0.9)

    model.train()
    view_0, view_1 = build_synthetic_views(
        batch_size=args.batch_size,
        image_size=args.image_size,
        device=device,
    )
    features_0, projections_0 = model(view_0)
    _, projections_1 = model(view_1)
    loss = criterion(projections_0, projections_1)
    loss.backward()
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)

    print(f"device={device.type}")
    print(f"input_shape={tuple(view_0.shape)}")
    print(f"features_shape={tuple(features_0.shape)}")
    print(f"projection_shape={tuple(projections_0.shape)}")
    print(f"loss={loss.item():.6f}")


if __name__ == "__main__":
    main()
