#!/usr/bin/env python3
"""Check a target checkout environment for the SR3/DDPM iterative-refinement repo.

The script performs safe preflight checks only: dependency imports, optional
source-package imports from a supplied checkout, comment-bearing config parsing,
and optional CUDA allocation. It never trains, samples, downloads data, logs to
W&B, or loads checkpoints.

Examples:
    python scripts/check_environment.py --repo-root /path/to/checkout --config /path/to/checkout/config/sr_sr3_16_128.json
    python scripts/check_environment.py --repo-root /path/to/checkout --config /path/to/checkout/config/sr_sr3_64_512.json --cuda
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any


def strip_json_comments(text: str) -> str:
    return "\n".join(line.split("//")[0] for line in text.splitlines())


def load_config(path: Path) -> dict[str, Any]:
    try:
        return json.loads(strip_json_comments(path.read_text()))
    except Exception as exc:  # noqa: BLE001 - present concise CLI diagnostics
        raise RuntimeError(f"could not parse config {path}: {exc}") from exc


def check_import(module: str) -> tuple[bool, str]:
    try:
        imported = importlib.import_module(module)
        version = getattr(imported, "__version__", None)
        return True, f"{module} imported" + (f" ({version})" if version else "")
    except Exception as exc:  # noqa: BLE001
        return False, f"{module} import failed: {type(exc).__name__}: {exc}"


def nested(mapping: dict[str, Any], *keys: str) -> Any:
    cur: Any = mapping
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def summarize_config(config: dict[str, Any]) -> list[str]:
    datasets = config.get("datasets", {}) or {}
    lines = [
        f"config.name={config.get('name')}",
        f"config.phase={config.get('phase')}",
        f"gpu_ids={config.get('gpu_ids')}",
        f"model={nested(config, 'model', 'which_model_G')}",
        f"conditional={nested(config, 'model', 'diffusion', 'conditional')}",
        f"image_size={nested(config, 'model', 'diffusion', 'image_size')}",
        f"in_channel={nested(config, 'model', 'unet', 'in_channel')}",
        f"out_channel={nested(config, 'model', 'unet', 'out_channel')}",
        f"resume_state={nested(config, 'path', 'resume_state')}",
    ]
    for phase, ds in sorted(datasets.items()):
        lines.append(
            f"dataset.{phase}: root={ds.get('dataroot')} datatype={ds.get('datatype')} "
            f"mode={ds.get('mode')} L={ds.get('l_resolution')} R={ds.get('r_resolution')} data_len={ds.get('data_len')}"
        )
    return lines


def cuda_check() -> tuple[bool, str]:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return False, f"torch import failed before CUDA check: {exc}"
    if not torch.cuda.is_available():
        return False, "torch.cuda.is_available() is false"
    try:
        tensor = torch.ones(1, device="cuda")
        value = float(tensor.item())
        name = torch.cuda.get_device_name(0)
        return True, f"CUDA allocation ok on {name}; test value={value}"
    except Exception as exc:  # noqa: BLE001
        return False, f"CUDA allocation failed: {type(exc).__name__}: {exc}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run safe environment/config checks for a target SR3/DDPM repo checkout.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", type=Path, help="Target checkout root; added to sys.path for core/data/model import checks.")
    parser.add_argument("--config", type=Path, help="Comment-bearing config file to parse and summarize.")
    parser.add_argument("--cuda", action="store_true", help="Also allocate a tiny CUDA tensor.")
    parser.add_argument("--optional-wandb", action="store_true", help="Check optional wandb import too.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    failures = 0

    if args.repo_root:
        if not args.repo_root.is_dir():
            print(f"ERROR: repo root is not a directory: {args.repo_root}")
            failures += 1
        else:
            sys.path.insert(0, str(args.repo_root.resolve()))
            print(f"OK: using repo root for import checks: {args.repo_root}")

    required_modules = ["torch", "torchvision", "numpy", "PIL", "lmdb", "tensorboardX", "cv2", "tqdm"]
    if args.repo_root:
        required_modules.extend(["core.logger", "core.metrics", "data", "model", "model.networks"])
    if args.optional_wandb:
        required_modules.append("wandb")

    print("# Import checks")
    for module in required_modules:
        ok, message = check_import(module)
        print(("OK: " if ok else "ERROR: ") + message)
        if not ok and module != "wandb":
            failures += 1

    if args.config:
        print("# Config parse")
        try:
            config = load_config(args.config)
        except RuntimeError as exc:
            print(f"ERROR: {exc}")
            failures += 1
        else:
            for line in summarize_config(config):
                print("OK: " + line)

    if args.cuda:
        print("# CUDA check")
        ok, message = cuda_check()
        print(("OK: " if ok else "ERROR: ") + message)
        if not ok:
            failures += 1

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
