#!/usr/bin/env python3
"""Plot LatentSync SyncNet train/validation loss curves from checkpoints."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import torch  # noqa: E402

REQUIRED_KEYS = ("train_step_list", "train_loss_list")
OPTIONAL_VAL_KEYS = ("val_step_list", "val_loss_list")


def resolve_path(path: str, repo_root: Path) -> Path:
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else (repo_root / candidate)


def torch_load_checkpoint(path: Path) -> dict[str, Any]:
    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    except TypeError:
        return torch.load(path, map_location="cpu")


def load_curve(checkpoint_path: Path) -> dict[str, Any]:
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    checkpoint = torch_load_checkpoint(checkpoint_path)
    missing = [key for key in REQUIRED_KEYS if key not in checkpoint]
    if missing:
        raise KeyError(f"{checkpoint_path} is missing SyncNet curve keys: {missing}")
    return {
        "train_steps": checkpoint["train_step_list"],
        "train_loss": checkpoint["train_loss_list"],
        "val_steps": checkpoint.get("val_step_list", []),
        "val_loss": checkpoint.get("val_loss_list", []),
    }


def plot_curves(checkpoints: list[Path], labels: list[str], output_path: Path, *, plot_val: bool, title: str | None) -> None:
    plt.rcParams["font.size"] = 14
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Lucida Grande"]
    plt.rcParams["font.serif"] = ["Times New Roman", "DejaVu Serif"]

    plt.figure(figsize=(7.766, 4.8))
    for checkpoint_path, label in zip(checkpoints, labels):
        curve = load_curve(checkpoint_path)
        (line,) = plt.plot(
            curve["train_steps"],
            curve["train_loss"],
            label=f"{label} train",
            linewidth=0.8,
            alpha=0.65,
        )
        if plot_val and curve["val_steps"] and curve["val_loss"]:
            plt.plot(
                curve["val_steps"],
                curve["val_loss"],
                label=f"{label} val",
                linewidth=1.6,
                color=line.get_color(),
            )

    if title:
        plt.title(title)
    plt.xlabel("Step")
    plt.ylabel("Loss")
    legend = plt.legend()
    for line in legend.get_lines():
        line.set_linewidth(2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, transparent=True)
    plt.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plot SyncNet training and validation loss curves from checkpoints")
    parser.add_argument("checkpoints", nargs="+", help="Checkpoints containing SyncNet curve lists")
    parser.add_argument("--repo-root", default=".", help="Resolve relative checkpoint/output paths against this root")
    parser.add_argument("--labels", nargs="*", default=None, help="Optional labels, one per checkpoint")
    parser.add_argument("--output", default="syncnet_curves.png", help="Output image/pdf path")
    parser.add_argument("--no-val", action="store_true", help="Plot only training loss")
    parser.add_argument("--title", default=None, help="Optional plot title")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    checkpoints = [resolve_path(path, repo_root) for path in args.checkpoints]
    output_path = resolve_path(args.output, repo_root)

    labels = args.labels or [path.parent.parent.name or path.stem for path in checkpoints]
    if len(labels) != len(checkpoints):
        raise ValueError("--labels must have the same length as checkpoints")

    plot_curves(checkpoints, labels, output_path, plot_val=not args.no_val, title=args.title)
    print(f"Saved SyncNet curve plot to {output_path}")


if __name__ == "__main__":
    main()
