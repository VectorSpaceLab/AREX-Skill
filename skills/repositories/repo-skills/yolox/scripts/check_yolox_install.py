#!/usr/bin/env python3
"""Safe root-level YOLOX installation and backend smoke check.

This helper uses the installed `yolox` package. It does not need datasets,
checkpoints, downloads, source-repo assets, or persistent output files.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import Dict, Iterable, Tuple

BUILTIN_NAMES = ("yolox-s", "yolox-m", "yolox-l", "yolox-x", "yolox-tiny", "yolox-nano", "yolov3")
CORE_IMPORTS = ("yolox", "torch", "torchvision", "cv2", "yolox.exp", "yolox.utils")
SUPPORT_IMPORTS = ("pycocotools", "onnx", "onnxsim", "onnxruntime", "loguru", "tqdm", "thop", "tabulate", "psutil")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check YOLOX imports, experiment/model construction, and optional CUDA readiness.")
    parser.add_argument("--name", default="yolox-nano", choices=BUILTIN_NAMES, help="Built-in YOLOX experiment name to resolve when --exp-file is not supplied.")
    parser.add_argument("--exp-file", default=None, help="Custom experiment Python file containing class Exp. Takes precedence over --name.")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto", help="Device to probe for optional model placement and dummy forward.")
    parser.add_argument("--test-size", type=int, default=64, help="Square test size for model-info and optional dummy forward. Use a multiple of 32.")
    parser.add_argument("--dummy-forward", action="store_true", help="Run a no-grad dummy forward without loading weights. Keep --test-size small on CPU.")
    parser.add_argument("--require-support-imports", action="store_true", help="Fail when optional support imports such as ONNX or pycocotools are missing.")
    return parser.parse_args()


def check_imports(names: Iterable[str]) -> Tuple[Dict[str, str], Dict[str, str]]:
    ok: Dict[str, str] = {}
    failed: Dict[str, str] = {}
    for name in names:
        try:
            module = importlib.import_module(name)
            ok[name] = str(getattr(module, "__version__", "imported"))
        except Exception as exc:
            failed[name] = f"{type(exc).__name__}: {exc}"
    return ok, failed


def print_report(title: str, ok: Dict[str, str], failed: Dict[str, str]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    for name in sorted(ok):
        print(f"OK   {name}: {ok[name]}")
    for name in sorted(failed):
        print(f"FAIL {name}: {failed[name]}")


def resolve_device(requested: str, torch_module):
    cuda_available = bool(torch_module.cuda.is_available())
    if requested == "auto":
        requested = "cuda" if cuda_available else "cpu"
    if requested == "cuda" and not cuda_available:
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False. Use --device cpu for package checks or install a CUDA-capable PyTorch runtime.")
    return torch_module.device(requested)


def main() -> int:
    args = parse_args()
    if args.test_size <= 0:
        print("ERROR: --test-size must be positive.", file=sys.stderr)
        return 2
    if args.test_size % 32 != 0:
        print("WARNING: YOLOX stride-based models normally use test sizes divisible by 32.", file=sys.stderr)

    core_ok, core_failed = check_imports(CORE_IMPORTS)
    print_report("Core imports", core_ok, core_failed)
    if core_failed:
        print("ERROR: core imports failed; install YOLOX, PyTorch, torchvision, and OpenCV first.", file=sys.stderr)
        return 1

    support_ok, support_failed = check_imports(SUPPORT_IMPORTS)
    print_report("Support imports", support_ok, support_failed)
    if support_failed:
        print("WARNING: some support imports failed. Inference may still work, but dataset/eval/export paths may need extra packages.", file=sys.stderr)
        if args.require_support_imports:
            return 1

    import torch
    import yolox
    from yolox.exp import get_exp
    from yolox.utils import get_model_info, postprocess

    print(f"\nYOLOX version: {getattr(yolox, '__version__', 'unknown')}")
    print(f"Torch version: {torch.__version__}; CUDA runtime: {torch.version.cuda}")
    print(f"CUDA available: {torch.cuda.is_available()}; device count: {torch.cuda.device_count()}")

    try:
        device = resolve_device(args.device, torch)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Selected device: {device}")

    if device.type == "cuda":
        try:
            print(f"CUDA device 0: {torch.cuda.get_device_name(0)} capability {torch.cuda.get_device_capability(0)}")
            torch.empty((1,), device=device)
            torch.cuda.synchronize()
            print("CUDA tiny allocation: OK")
        except Exception as exc:
            print(f"ERROR: CUDA allocation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1

    try:
        exp = get_exp(args.exp_file, args.name)
    except Exception as exc:
        print(f"ERROR: could not resolve YOLOX Exp: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print("\nExperiment")
    print("----------")
    print(f"source: {args.exp_file if args.exp_file else args.name}")
    for field in ("exp_name", "num_classes", "depth", "width", "input_size", "test_size"):
        print(f"{field}: {getattr(exp, field, '<missing>')}")

    smoke_size = (args.test_size, args.test_size)
    try:
        exp.test_size = smoke_size
        model = exp.get_model()
        model.eval().to(device)
        print("Model construction: OK")
        try:
            print(f"Model info at {smoke_size}: {get_model_info(model, smoke_size)}")
        except Exception as exc:
            print(f"WARNING: get_model_info failed: {type(exc).__name__}: {exc}", file=sys.stderr)
    except Exception as exc:
        print(f"ERROR: model construction failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.dummy_forward:
        try:
            dummy = torch.zeros((1, 3, args.test_size, args.test_size), device=device)
            with torch.no_grad():
                raw = model(dummy)
            print(f"Dummy forward: OK ({tuple(raw.shape) if hasattr(raw, 'shape') else type(raw).__name__})")
            processed = postprocess(raw.detach().float().cpu(), getattr(exp, "num_classes", 80), conf_thre=0.99, nms_thre=0.45, class_agnostic=True)
            print("Postprocess call: OK", [None if x is None else tuple(x.shape) for x in processed])
        except Exception as exc:
            print(f"ERROR: dummy forward/postprocess failed: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
    else:
        print("Dummy forward: skipped")

    print("\nYOLOX install smoke completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
