#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch


def find_repo_root(anchor: Path) -> Path:
    candidates = [anchor, *anchor.parents]
    cwd = Path.cwd().resolve()
    candidates.extend([cwd, *cwd.parents])
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "run_longExp.py").is_file() and (candidate / "models").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not locate the repository root that contains run_longExp.py and models/."
    )


SEASONAL_KEYS = (
    "Linear_Seasonal.weight",
    "module.Linear_Seasonal.weight",
    "Linear_Seasonal.0.weight",
    "module.Linear_Seasonal.0.weight",
)
TREND_KEYS = (
    "Linear_Trend.weight",
    "module.Linear_Trend.weight",
    "Linear_Trend.0.weight",
    "module.Linear_Trend.0.weight",
)


def strip_module_prefix(state_dict: dict) -> dict:
    cleaned = {}
    for key, value in state_dict.items():
        if key.startswith("module."):
            cleaned[key[len("module."):]] = value
        else:
            cleaned[key] = value
    return cleaned


def unwrap_checkpoint(payload):
    if isinstance(payload, dict):
        for key in ("state_dict", "model_state_dict", "model", "net"):
            inner = payload.get(key)
            if isinstance(inner, dict):
                return inner
    return payload


def candidate_checkpoints(checkpoint_dir: Path, model_name: str | None) -> list[Path]:
    candidates: list[Path] = []
    for path in checkpoint_dir.rglob("checkpoint.pth"):
        if model_name and model_name not in str(path):
            continue
        candidates.append(path)
    if not candidates:
        for path in checkpoint_dir.rglob("*.pth"):
            if model_name and model_name not in str(path):
                continue
            candidates.append(path)
    return sorted(candidates, key=lambda item: item.stat().st_mtime, reverse=True)


def to_numpy(weight):
    if hasattr(weight, "detach"):
        return weight.detach().cpu().numpy()
    return np.asarray(weight)


def pick_weight(state_dict: dict, names: Iterable[str], label: str):
    cleaned = strip_module_prefix(state_dict)
    for key in names:
        if key in state_dict:
            return state_dict[key], key
        if key in cleaned:
            return cleaned[key], key
    available = ", ".join(sorted(state_dict.keys())[:40])
    raise KeyError(f"Could not find {label} weight in checkpoint. Available keys: {available}")


def save_heatmap(weight, output_path: Path, title: str) -> None:
    array = to_numpy(weight)
    if array.ndim != 2:
        raise ValueError(f"Expected a 2D weight matrix for {title}, got shape {array.shape}")

    fig, ax = plt.subplots()
    image = ax.imshow(array, cmap="plasma_r")
    ax.set_title(title)
    fig.colorbar(image, pad=0.03)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=500, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot DLinear seasonal and trend weights.")
    parser.add_argument("--checkpoint", type=Path, default=None, help="Exact checkpoint file to plot.")
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=Path("checkpoints"),
        help="Directory to search when --checkpoint is not given.",
    )
    parser.add_argument(
        "--model-name",
        default=None,
        help="Optional substring filter when searching a checkpoint directory.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("weights_plot"),
        help="Root directory for generated plots.",
    )
    args = parser.parse_args()
    repo_root = find_repo_root(Path(__file__).resolve())

    if args.checkpoint is not None:
        checkpoint = args.checkpoint.expanduser()
        if not checkpoint.is_absolute():
            checkpoint = (repo_root / checkpoint).resolve()
        else:
            checkpoint = checkpoint.resolve()
        if not checkpoint.exists():
            raise SystemExit(f"Checkpoint not found: {checkpoint}")
    else:
        search_root = args.checkpoint_dir.expanduser()
        if not search_root.is_absolute():
            search_root = (repo_root / search_root).resolve()
        else:
            search_root = search_root.resolve()
        if not search_root.exists():
            raise SystemExit(f"Checkpoint directory not found: {search_root}")
        matches = candidate_checkpoints(search_root, args.model_name)
        if not matches:
            raise SystemExit(
                f"No checkpoint files found under {search_root} with filter {args.model_name!r}"
            )
        checkpoint = matches[0]

    payload = torch.load(checkpoint, map_location=torch.device("cpu"))
    state_dict = unwrap_checkpoint(payload)
    if not isinstance(state_dict, dict):
        raise SystemExit(f"Unsupported checkpoint structure in {checkpoint}")

    seasonal, seasonal_key = pick_weight(state_dict, SEASONAL_KEYS, "seasonal")
    trend, trend_key = pick_weight(state_dict, TREND_KEYS, "trend")

    run_name = checkpoint.parent.name or checkpoint.stem
    output_root = args.output_root.expanduser()
    if not output_root.is_absolute():
        output_root = (repo_root / output_root).resolve()
    else:
        output_root = output_root.resolve()
    output_dir = output_root / run_name
    save_heatmap(seasonal, output_dir / "seasonal.pdf", f"seasonal ({seasonal_key})")
    save_heatmap(trend, output_dir / "trend.pdf", f"trend ({trend_key})")

    print(f"Saved seasonal plot to {output_dir / 'seasonal.pdf'}")
    print(f"Saved trend plot to {output_dir / 'trend.pdf'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
