#!/usr/bin/env python3
"""Smoke-test bundled U-2-Net architecture entry points and print shapes as JSON."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Iterable


def load_runtime() -> Any:
    runtime_path = Path(__file__).resolve().parents[3] / "scripts" / "u2net_runtime.py"
    spec = importlib.util.spec_from_file_location("u2net_skill_runtime", runtime_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load bundled runtime from {runtime_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fail(message: str, exit_code: int = 2, **extra: Any) -> None:
    payload = {"ok": False, "error": message}
    payload.update(extra)
    print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
    raise SystemExit(exit_code)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny bundled U-2-Net forward pass and report output tensor shapes.")
    parser.add_argument("--model", choices=("u2net", "u2netp", "refactor-full", "refactor-lite"), default="u2netp")
    parser.add_argument("--height", type=int, default=64, help="Input tensor height. Default: 64.")
    parser.add_argument("--width", type=int, default=64, help="Input tensor width. Default: 64.")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    return parser.parse_args()


def as_sequence(outputs: Any) -> Iterable[Any]:
    if not isinstance(outputs, (tuple, list)):
        fail("model forward returned a non-sequence", returned_type=type(outputs).__name__)
    return outputs


def main() -> None:
    args = parse_args()
    if args.height <= 0 or args.width <= 0:
        fail("--height and --width must be positive", height=args.height, width=args.width)
    try:
        rt = load_runtime()
        torch = rt.torch
    except Exception as exc:  # pragma: no cover
        fail("failed to load bundled U-2-Net runtime", original_error=str(exc))
    try:
        device = rt.select_torch_device(torch, args.device)
        if args.model in ("refactor-full", "refactor-lite"):
            refactor_path = Path(__file__).resolve().parents[3] / "scripts" / "u2net_refactor_runtime.py"
            spec = importlib.util.spec_from_file_location("u2net_skill_refactor_runtime", refactor_path)
            if spec is None or spec.loader is None:
                fail("could not load bundled refactor runtime", refactor_runtime=str(refactor_path))
            refactor = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(refactor)
            model = (refactor.U2NET_full() if args.model == "refactor-full" else refactor.U2NET_lite()).to(device).eval()
        else:
            model = rt.build_u2net_model(args.model).to(device).eval()
        x = torch.zeros((1, 3, args.height, args.width), dtype=torch.float32, device=device)
        with torch.no_grad():
            outputs = list(as_sequence(model(x)))
    except Exception as exc:  # pragma: no cover
        fail("forward pass failed", model=args.model, device=args.device, original_error=str(exc))
    shapes = [list(t.shape) for t in outputs]
    result = {
        "ok": True,
        "model": args.model,
        "device": str(device),
        "input_shape": [1, 3, args.height, args.width],
        "output_count": len(outputs),
        "output_shapes": shapes,
        "fused_output_shape": shapes[0] if shapes else None,
    }
    expected = [1, 1, args.height, args.width]
    warnings = []
    if len(outputs) != 7:
        warnings.append(f"expected 7 outputs, got {len(outputs)}")
    if any(shape != expected for shape in shapes):
        warnings.append(f"expected all output shapes to be {expected}")
    if warnings:
        result["warnings"] = warnings
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
