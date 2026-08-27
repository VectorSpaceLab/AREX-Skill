#!/usr/bin/env python
"""Portable scvi-tools training smoke template.

Creates a tiny synthetic AnnData object, trains an SCVI model, and runs a basic
inference method. This script is intentionally CPU-safe by default and does not
read repository-local files.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a small scvi-tools SCVI train/inference smoke test."
    )
    parser.add_argument("--max-epochs", type=int, default=1, help="Maximum training epochs.")
    parser.add_argument("--batch-size", type=int, default=32, help="Training minibatch size.")
    parser.add_argument(
        "--accelerator",
        default="cpu",
        choices=["cpu", "gpu", "auto"],
        help="Lightning accelerator to request. Use cpu for portable smoke tests.",
    )
    parser.add_argument(
        "--devices",
        default="1",
        help="Lightning devices value. Integers are converted when possible; use auto or -1 as needed.",
    )
    parser.add_argument("--n-obs", type=int, default=128, help="Synthetic observations.")
    parser.add_argument("--n-genes", type=int, default=50, help="Synthetic genes.")
    parser.add_argument(
        "--early-stopping", action="store_true", help="Enable validation early stopping."
    )
    parser.add_argument(
        "--load-sparse-tensor",
        action="store_true",
        help="Request sparse tensor loading when the synthetic fixture is sparse.",
    )
    return parser.parse_args()


def parse_devices(value: str) -> int | str:
    if value in {"auto", "-1"}:
        return value if value == "auto" else -1
    try:
        return int(value)
    except ValueError:
        return value


def main() -> int:
    args = parse_args()

    try:
        import torch
        import scvi
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"Failed to import scvi-tools dependencies: {exc}", file=sys.stderr)
        return 2

    accelerator = args.accelerator
    if accelerator == "gpu" and not torch.cuda.is_available():
        print("Requested --accelerator gpu, but torch.cuda.is_available() is False.", file=sys.stderr)
        return 3

    adata = scvi.data.synthetic_iid(batch_size=args.n_obs, n_genes=args.n_genes)
    scvi.model.SCVI.setup_anndata(adata, batch_key="batch")
    model = scvi.model.SCVI(adata, n_latent=5)

    train_kwargs: dict[str, Any] = {
        "max_epochs": args.max_epochs,
        "accelerator": accelerator,
        "devices": parse_devices(args.devices),
        "batch_size": args.batch_size,
        "train_size": 0.9,
        "validation_size": 0.1,
        "early_stopping": args.early_stopping,
        "load_sparse_tensor": args.load_sparse_tensor,
        "enable_progress_bar": False,
        "check_val_every_n_epoch": 1 if args.early_stopping else None,
    }
    train_kwargs = {key: value for key, value in train_kwargs.items() if value is not None}

    model.train(**train_kwargs)
    latent = model.get_latent_representation(batch_size=args.batch_size)

    summary = {
        "ok": True,
        "scvi_version": scvi.__version__,
        "torch_version": torch.__version__,
        "accelerator": accelerator,
        "devices": train_kwargs["devices"],
        "latent_shape": list(latent.shape),
        "is_trained": bool(model.is_trained_),
        "history_keys": sorted(list(getattr(model, "history_", {}) or {})),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
