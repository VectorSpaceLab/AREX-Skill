#!/usr/bin/env python3
"""Build a bundled ScaledYOLOv4 YAML model and run a synthetic forward pass.

By default this helper imports from the skill-owned ``runtime/`` mirror. Use
``--runtime-root`` only when intentionally checking another ScaledYOLOv4 source
root. The check does not download weights, read a training dataset, or write
repository files.

Model construction is wrapped in ``torch.no_grad()`` because this checkout's
bias initialization uses an in-place update that newer PyTorch versions reject
while gradients are enabled.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def default_runtime_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "runtime"
        if (candidate / "models" / "yolo.py").is_file() and (candidate / "models" / "yolov4-p5.yaml").is_file():
            return candidate
    raise RuntimeError("could not locate bundled runtime/ mirror containing models/yolo.py")


def _device_name(requested: str, torch_module) -> object:
    if requested == "auto":
        return torch_module.device("cuda:0" if torch_module.cuda.is_available() else "cpu")
    if requested == "cuda":
        return torch_module.device("cuda:0")
    return torch_module.device(requested)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=None,
        help="optional ScaledYOLOv4 source root; defaults to this skill's bundled runtime/ mirror",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="deprecated alias for --runtime-root, kept for compatibility with older checks",
    )
    parser.add_argument(
        "--cfg",
        nargs="+",
        default=["models/yolov4-p5.yaml"],
        help="one or more model YAML paths, relative to the runtime root",
    )
    parser.add_argument("--img-size", type=int, default=64, help="synthetic square input size")
    parser.add_argument(
        "--device",
        default="auto",
        help="auto, cpu, cuda, or an explicit torch device such as cuda:0",
    )
    args = parser.parse_args()

    runtime_root = (args.runtime_root or args.repo_root or default_runtime_root()).expanduser().resolve()
    if not (runtime_root / "models" / "yolo.py").is_file():
        parser.error(f"runtime root does not contain models/yolo.py: {runtime_root}")
    if args.img_size <= 0:
        parser.error("--img-size must be positive")

    sys.dont_write_bytecode = True
    sys.path.insert(0, str(runtime_root))
    try:
        import torch
        from models.yolo import Model
    except Exception as exc:  # pragma: no cover - diagnostic error path
        print(f"Unable to import the model stack from bundled runtime: {exc}", file=sys.stderr)
        return 2

    try:
        device = _device_name(args.device, torch)
    except Exception as exc:
        print(f"Invalid device {args.device!r}: {exc}", file=sys.stderr)
        return 2
    if device.type == "cuda" and not torch.cuda.is_available():
        print("CUDA was requested but torch.cuda.is_available() is false", file=sys.stderr)
        return 2

    print(f"runtime_root={runtime_root}")
    print(f"torch={torch.__version__} cuda_available={torch.cuda.is_available()} device={device}")
    failures = 0
    for cfg in args.cfg:
        cfg_path = Path(cfg).expanduser()
        if not cfg_path.is_absolute():
            cfg_path = runtime_root / cfg_path
        if not cfg_path.is_file():
            print(f"FAIL {cfg}: file not found", file=sys.stderr)
            failures += 1
            continue

        try:
            with torch.no_grad():
                model = Model(str(cfg_path)).to(device).eval()
                inputs = torch.zeros((1, 3, args.img_size, args.img_size), device=device)
                outputs = model(inputs)
            primary = outputs[0] if isinstance(outputs, tuple) else outputs
            shape = tuple(primary.shape) if hasattr(primary, "shape") else type(primary).__name__
            strides = getattr(model, "stride", None)
            stride_values = strides.detach().cpu().tolist() if strides is not None else None
            cfg_display = cfg_path.relative_to(runtime_root) if cfg_path.is_relative_to(runtime_root) else cfg_path
            print(f"OK   {cfg_display} output_shape={shape} strides={stride_values}")
        except Exception as exc:  # pragma: no cover - diagnostic error path
            print(f"FAIL {cfg}: {type(exc).__name__}: {exc}", file=sys.stderr)
            failures += 1

    print(f"Model checks: {len(args.cfg) - failures}/{len(args.cfg)} passed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
