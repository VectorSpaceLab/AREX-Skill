#!/usr/bin/env python3
"""Run a deterministic standalone classification output-contract smoke.

This defines a tiny independent Paddle classifier and never imports PaddleViT.
It performs no training, downloads, checkpoint loads, or file writes.
"""
from __future__ import annotations
import argparse
import json
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test a standalone Paddle classification output contract without source imports.")
    parser.add_argument("--device", default="cpu", help="Paddle device, e.g. cpu or gpu:0")
    parser.add_argument("--batch-size", type=int, default=1, help="Positive synthetic batch size")
    parser.add_argument("--channels", type=int, default=3, help="Positive input channels")
    parser.add_argument("--image-size", type=int, default=32, help="Positive square input size")
    parser.add_argument("--num-classes", type=int, default=1000, help="Positive logits width")
    parser.add_argument("--seed", type=int, default=0, help="Deterministic Paddle seed")
    parser.add_argument("--require-paddle", action="store_true", help="Fail if Paddle is unavailable instead of skipping")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON")
    return parser.parse_args()


def emit(result: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
    elif result["status"] == "ok":
        print(f"OK: device={result['device']} input={result['input_shape']} logits={result['output_shape']} checksum={result['checksum']:.6f}")
    elif result["status"] == "skipped":
        print(f"SKIPPED: {result['reason']}")
    else:
        print(f"FAILED: {result['reason']}", file=sys.stderr)


def main() -> int:
    args = parse_args()
    for name in ("batch_size", "channels", "image_size", "num_classes"):
        if getattr(args, name) <= 0:
            result = {"status": "failed", "reason": f"--{name.replace('_', '-')} must be positive"}
            emit(result, args.json)
            return 2
    try:
        import paddle
    except ModuleNotFoundError:
        result = {"status": "skipped", "reason": "Paddle is not installed; install a Paddle CPU/GPU wheel to execute the model smoke."}
        if args.require_paddle:
            result["status"] = "failed"
            result["reason"] = "Paddle is required but is not installed."
            emit(result, args.json)
            return 2
        emit(result, args.json)
        return 0
    try:
        paddle.set_device(args.device)
        paddle.seed(args.seed)

        class TinyClassifier(paddle.nn.Layer):
            def __init__(self, channels: int, classes: int) -> None:
                super().__init__()
                self.pool = paddle.nn.AdaptiveAvgPool2D(output_size=1)
                self.head = paddle.nn.Linear(channels, classes)

            def forward(self, inputs):  # type: ignore[no-untyped-def]
                return self.head(self.pool(inputs).flatten(1))

        model = TinyClassifier(args.channels, args.num_classes)
        model.eval()
        total = args.batch_size * args.channels * args.image_size * args.image_size
        inputs = paddle.arange(total, dtype="float32").reshape([args.batch_size, args.channels, args.image_size, args.image_size])
        inputs = inputs / float(max(1, total))
        with paddle.no_grad():
            first = model(inputs)
            second = model(inputs)
        expected = [args.batch_size, args.num_classes]
        if list(first.shape) != expected:
            raise RuntimeError(f"unexpected logits shape: got {list(first.shape)}, expected {expected}")
        if not bool(paddle.all(paddle.isfinite(first)).item()):
            raise RuntimeError("logits contain non-finite values")
        same = paddle.allclose(first, second)
        if hasattr(same, "item"):
            same = same.item()
        if not bool(same):
            raise RuntimeError("eval-mode output was not deterministic")
        emit({"status": "ok", "paddle_version": paddle.__version__, "device": paddle.get_device(), "input_shape": list(inputs.shape), "output_shape": list(first.shape), "checksum": float(paddle.sum(first).item())}, args.json)
        return 0
    except Exception as exc:
        emit({"status": "failed", "reason": f"{type(exc).__name__}: {exc}. Rerun with --device cpu to isolate CUDA/cuDNN issues."}, args.json)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
