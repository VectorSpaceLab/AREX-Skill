#!/usr/bin/env python3
"""Launch a VITS training run with a safe port and an explicit checkout root.

Prereqs:
- CUDA-capable PyTorch.
- The monotonic-alignment extension must already be built.
- Use `--run` only when you really want to start the long training job.

Example:
  python scripts/launch_training.py --repo-root /path/to/vits --config configs/ljs_base.json --model-name ljs_base --run
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch a VITS training run.")
    parser.add_argument("--repo-root", required=True, help="Path to the VITS checkout.")
    parser.add_argument("--config", required=True, help="Config JSON relative to the repo root or an absolute path.")
    parser.add_argument("--model-name", required=True, help="Name for the run directory under logs/.")
    parser.add_argument(
        "--mode",
        choices=("auto", "single", "multi"),
        default="auto",
        help="Choose the single- or multi-speaker launcher.",
    )
    parser.add_argument(
        "--master-port",
        type=int,
        default=29500,
        help="Valid TCP port for torch.distributed initialization.",
    )
    parser.add_argument(
        "--run",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Actually spawn the training job. The default is a dry run.",
    )
    parser.add_argument(
        "--dry-run",
        dest="run",
        action="store_false",
        help="Alias for the dry-run default.",
    )
    return parser.parse_args()


def resolve_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    sys.path.insert(0, str(repo_root))

    config_path = resolve_path(repo_root, args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    n_speakers = int(config.get("data", {}).get("n_speakers", 0) or 0)
    if args.mode == "single":
        chosen = "single"
    elif args.mode == "multi":
        chosen = "multi"
    else:
        chosen = "multi" if n_speakers > 1 else "single"

    model_dir = repo_root / "logs" / args.model_name
    print(f"repo_root={repo_root}")
    print(f"config={config_path}")
    print(f"model_dir={model_dir}")
    print(f"launcher={chosen}")
    print(f"master_port={args.master_port}")
    if not args.run:
        print("dry_run=ok")
        return 0

    import torch
    import utils
    import train as single_train
    import train_ms as multi_train

    if not torch.cuda.is_available():
        raise RuntimeError("VITS training requires CUDA")

    hps = utils.HParams(**config)
    hps.model_dir = str(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config_path, model_dir / "config.json")

    runner = multi_train.run if chosen == "multi" else single_train.run

    n_gpus = torch.cuda.device_count()
    if n_gpus <= 0:
        raise RuntimeError("No CUDA devices visible for training")

    os.environ["MASTER_ADDR"] = "localhost"
    os.environ["MASTER_PORT"] = str(args.master_port)

    print(f"n_gpus={n_gpus}")
    torch.multiprocessing.spawn(runner, nprocs=n_gpus, args=(n_gpus, hps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
