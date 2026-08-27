#!/usr/bin/env python3
"""Tiny tensorboardX embedding projector smoke check.

This script exercises metadata TSVs, metadata headers, projector label-image
sprites, global_step, and tag-based directory layout. It uses only local
filesystem output and temporary directories by default.
"""

from __future__ import annotations

import argparse
import contextlib
import pathlib
import tempfile


def _import_deps():
    try:
        from tensorboardX import SummaryWriter
    except Exception as exc:  # pragma: no cover - environment guard
        print(f"SKIP: tensorboardX SummaryWriter is required for this smoke ({exc})")
        return None, None, None
    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover - environment guard
        print(f"SKIP: NumPy is required for the projector smoke ({exc})")
        return None, None, None
    try:
        import torch
    except Exception as exc:  # pragma: no cover - environment guard
        print(f"SKIP: PyTorch is required for the projector smoke ({exc})")
        return None, None, None
    return SummaryWriter, np, torch


def _run(logdir: pathlib.Path) -> None:
    SummaryWriter, np, torch = _import_deps()
    if SummaryWriter is None or np is None or torch is None:
        return

    features = np.array(
        [
            [0.0, 0.1, 0.2],
            [1.0, 1.1, 1.2],
            [2.0, 2.1, 2.2],
            [3.0, 3.1, 3.2],
        ],
        dtype=np.float32,
    )
    metadata = [("zero", "train"), ("one", "train"), ("two", "valid"), ("three", "valid")]
    label_img = torch.zeros(4, 3, 4, 4)
    for idx in range(label_img.shape[0]):
        label_img[idx] += idx / 10.0

    with SummaryWriter(str(logdir)) as writer:
        writer.add_embedding(
            features,
            metadata=metadata,
            metadata_header=["name", "split"],
            label_img=label_img,
            global_step=7,
            tag="demo",
        )

    projector = logdir / "projector_config.pbtxt"
    tensor_path = logdir / "00007" / "demo" / "tensors.tsv"
    metadata_path = logdir / "00007" / "demo" / "metadata.tsv"
    sprite_path = logdir / "00007" / "demo" / "sprite.png"
    for path in (projector, tensor_path, metadata_path, sprite_path):
        if not path.exists():
            raise RuntimeError(f"Expected projector output missing: {path}")
    print("OK: add_embedding wrote projector files with metadata and label images")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a tiny tensorboardX projector smoke check.")
    parser.add_argument("--logdir", type=pathlib.Path, help="Optional output log directory to keep after the run.")
    args = parser.parse_args(argv)

    if args.logdir is not None:
        args.logdir.mkdir(parents=True, exist_ok=True)
        _run(args.logdir)
    else:
        with tempfile.TemporaryDirectory(prefix="tbx-projector-") as tmp:
            _run(pathlib.Path(tmp))
    return 0


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        raise SystemExit(main())
    raise SystemExit(130)
