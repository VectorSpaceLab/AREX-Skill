#!/usr/bin/env python3
"""Smoke-check ECCV2022-RIFE source imports, torch backend, and Model.inference.

This helper is safe by default: it does not download checkpoints, load external
weights, read datasets, write outputs, or run repository benchmarks/training.
It verifies that a checkout plus Python environment can import the core model
API and run one tiny random-tensor inference with randomly initialized weights.
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Sequence


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-check ECCV2022-RIFE source imports and Model.inference without checkpoints or datasets.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        help="ECCV2022-RIFE checkout root. Defaults to the current directory or a parent containing model/RIFE.py.",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Backend to smoke-check. 'cpu' hides CUDA before importing torch/model.RIFE.",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=32,
        help="Square random image size for the inference smoke. Use a positive multiple of 32.",
    )
    parser.add_argument(
        "--arbitrary",
        action="store_true",
        help="Instantiate Model(arbitrary=True) to exercise the RIFE_m IFNet_m path.",
    )
    parser.add_argument(
        "--no-inference",
        action="store_true",
        help="Only import modules and print signatures; skip random tensor inference.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON summary instead of human-readable lines.")
    return parser.parse_args(argv)


def find_repo_root(user_root: Optional[str]) -> Path:
    candidates = []
    if user_root:
        candidates.append(Path(user_root).expanduser())
    else:
        cwd = Path.cwd()
        candidates.extend([cwd, *cwd.parents])
    for candidate in candidates:
        root = candidate.resolve()
        if (root / "model" / "RIFE.py").is_file() and (root / "inference_img.py").is_file():
            return root
    searched = ", ".join(str(path) for path in candidates[:5])
    raise SystemExit(f"ERROR: could not find ECCV2022-RIFE checkout root containing model/RIFE.py and inference_img.py; searched {searched}")


def validate_args(args: argparse.Namespace) -> None:
    if args.size <= 0:
        raise SystemExit("ERROR: --size must be positive")
    if args.size % 32 != 0:
        raise SystemExit("ERROR: --size should be a multiple of 32 for this direct Model.inference smoke; source CLIs pad real inputs")


def print_result(result: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    for key, value in result.items():
        print(f"{key}: {value}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    validate_args(args)

    # model.RIFE chooses its module-level device at import time. Hide CUDA before
    # importing torch/model.RIFE when a CPU fallback smoke is requested.
    if args.device == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    repo_root = find_repo_root(args.repo_root)
    sys.path.insert(0, str(repo_root))

    import torch  # imported after optional CUDA hiding
    from model.RIFE import Model
    from dataset import VimeoDataset

    cuda_available = bool(torch.cuda.is_available())
    if args.device == "cuda" and not cuda_available:
        raise SystemExit("ERROR: --device cuda requested but torch.cuda.is_available() is false")
    selected_device = "cuda" if args.device in ("auto", "cuda") and cuda_available else "cpu"

    result: Dict[str, Any] = {
        "status": "import-ok",
        "repo_root": str(repo_root),
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cuda_available": cuda_available,
        "cuda_device_count": torch.cuda.device_count() if cuda_available else 0,
        "selected_device": selected_device,
        "model_init_signature": str(inspect.signature(Model)),
        "model_inference_signature": str(inspect.signature(Model.inference)),
        "model_update_signature": str(inspect.signature(Model.update)),
        "vimeo_dataset_signature": str(inspect.signature(VimeoDataset)),
        "arbitrary": bool(args.arbitrary),
        "weights_loaded": False,
    }

    if cuda_available:
        result["cuda_device_0"] = torch.cuda.get_device_name(0)
        result["cuda_capability_0"] = ".".join(str(x) for x in torch.cuda.get_device_capability(0))

    if args.no_inference:
        print_result(result, args.json)
        return 0

    torch.set_grad_enabled(False)
    model = Model(arbitrary=args.arbitrary)
    model.eval()
    device = torch.device(selected_device)
    img0 = torch.rand(1, 3, args.size, args.size, device=device)
    img1 = torch.rand(1, 3, args.size, args.size, device=device)
    with torch.no_grad():
        output = model.inference(img0, img1, timestep=0.25 if args.arbitrary else 0.5)
    if tuple(output.shape) != (1, 3, args.size, args.size):
        raise SystemExit(f"ERROR: unexpected output shape {tuple(output.shape)}")
    result.update(
        {
            "status": "ok",
            "smoke_shape": list(output.shape),
            "smoke_output_device": str(output.device),
            "smoke_note": "randomly initialized weights; validates API/backend only, not interpolation quality",
        }
    )
    print_result(result, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
