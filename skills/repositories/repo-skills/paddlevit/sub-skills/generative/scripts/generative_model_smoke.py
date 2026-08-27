#!/usr/bin/env python3
"""Run a tiny deterministic Paddle GAN contract smoke.

The models in this script are deliberately self-contained synthetic stand-ins.
They check the public tensor boundaries used by PaddleViT TransGAN and
Styleformer without importing the source checkout, loading weights, reading
data, downloading anything, or training. A source-root build is required for
source compatibility; this smoke is only a cheap shape/finite-value check.
"""
from __future__ import annotations

import argparse
import json
from typing import Dict, Iterable, List


def _finite(paddle, *tensors) -> bool:
    return all(bool(paddle.all(paddle.isfinite(tensor)).item()) for tensor in tensors)


def _check_transgan(paddle, nn, functional, args) -> Dict[str, object]:
    class TinyTransGANGenerator(nn.Layer):
        def __init__(self) -> None:
            super().__init__()
            self.project = nn.Linear(256, 32 * 4 * 4)
            self.to_rgb = nn.Conv2D(32, 3, kernel_size=1)

        def forward(self, latent):
            x = self.project(latent).reshape([latent.shape[0], 32, 4, 4])
            x = functional.interpolate(x, size=[32, 32], mode="nearest")
            return self.to_rgb(x)

    class TinyTransGANDiscriminator(nn.Layer):
        def __init__(self) -> None:
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2D(3, 16, kernel_size=3, stride=2, padding=1),
                nn.LeakyReLU(0.2),
                nn.Conv2D(16, 32, kernel_size=3, stride=2, padding=1),
                nn.LeakyReLU(0.2),
            )
            self.head = nn.Linear(32, 1)

        def forward(self, image):
            x = self.features(image)
            x = functional.adaptive_avg_pool2d(x, output_size=1).reshape([image.shape[0], 32])
            return self.head(x)

    generator = TinyTransGANGenerator()
    discriminator = TinyTransGANDiscriminator()
    generator.eval()
    discriminator.eval()
    latent = paddle.arange(args.batch_size * 256, dtype="float32").reshape([args.batch_size, 256]) / 1000.0
    with paddle.no_grad():
        image = generator(latent)
        score = discriminator(image)
    expected_image = [args.batch_size, 3, 32, 32]
    expected_score = [args.batch_size, 1]
    if list(image.shape) != expected_image or list(score.shape) != expected_score:
        raise AssertionError(f"TransGAN contract mismatch: image={image.shape}, score={score.shape}")
    if not _finite(paddle, image, score):
        raise AssertionError("TransGAN synthetic output contains non-finite values")
    return {
        "model": "transgan",
        "latent": list(latent.shape),
        "generator": list(image.shape),
        "discriminator": list(score.shape),
        "finite": True,
    }


def _check_styleformer(paddle, nn, functional, args, image_size: int) -> Dict[str, object]:
    class TinyStyleformerGenerator(nn.Layer):
        def __init__(self) -> None:
            super().__init__()
            self.mapping = nn.Sequential(nn.Linear(512, 64), nn.LeakyReLU(0.2), nn.Linear(64, 64 * 4 * 4))
            self.to_rgb = nn.Conv2D(64, 3, kernel_size=1)

        def forward(self, latent):
            x = self.mapping(latent).reshape([latent.shape[0], 64, 4, 4])
            x = functional.interpolate(x, size=[image_size, image_size], mode="nearest")
            return self.to_rgb(x)

    class TinyStyleformerDiscriminator(nn.Layer):
        def __init__(self) -> None:
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2D(3, 16, kernel_size=1),
                nn.LeakyReLU(0.2),
                nn.Conv2D(16, 32, kernel_size=3, stride=2, padding=1),
                nn.LeakyReLU(0.2),
            )
            self.head = nn.Linear(32, 1)

        def forward(self, image):
            x = self.features(image)
            x = functional.adaptive_avg_pool2d(x, output_size=1).reshape([image.shape[0], 32])
            return self.head(x)

    generator = TinyStyleformerGenerator()
    discriminator = TinyStyleformerDiscriminator()
    generator.eval()
    discriminator.eval()
    latent = paddle.arange(args.batch_size * 512, dtype="float32").reshape([args.batch_size, 512]) / 1000.0
    with paddle.no_grad():
        image = generator(latent)
        score = discriminator(image)
    expected_image = [args.batch_size, 3, image_size, image_size]
    expected_score = [args.batch_size, 1]
    if list(image.shape) != expected_image or list(score.shape) != expected_score:
        raise AssertionError(f"Styleformer {image_size}px contract mismatch: image={image.shape}, score={score.shape}")
    if not _finite(paddle, image, score):
        raise AssertionError(f"Styleformer {image_size}px output contains non-finite values")
    return {
        "model": "styleformer",
        "image_size": image_size,
        "latent": list(latent.shape),
        "generator": list(image.shape),
        "discriminator": list(score.shape),
        "finite": True,
    }


def _sizes(raw: str) -> List[int]:
    values = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            value = int(item)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid image size {item!r}") from exc
        if value not in (32, 48, 64, 128):
            raise argparse.ArgumentTypeError("style sizes must be 32, 48, 64, or 128")
        values.append(value)
    if not values:
        raise argparse.ArgumentTypeError("provide at least one style image size")
    return values


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run deterministic synthetic TransGAN/Styleformer tensor checks; no source checkout, downloads, checkpoints, data, or training."
    )
    parser.add_argument("--model", choices=("transgan", "styleformer", "all"), default="all", help="contract to check (default: all)")
    parser.add_argument("--device", default="cpu", help="Paddle device such as cpu, gpu:0, or auto (default: cpu)")
    parser.add_argument("--batch-size", type=int, default=1, help="synthetic batch size (default: 1)")
    parser.add_argument("--style-sizes", type=_sizes, default=[32, 48, 64, 128], help="comma-separated Styleformer sizes (default: all shipped sizes)")
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be positive")
    try:
        import paddle
        import paddle.nn as nn
        import paddle.nn.functional as functional
    except ImportError as exc:
        print(f"SKIP: Paddle is not importable: {exc}")
        return 2

    device = args.device
    if device == "auto":
        device = "gpu:0" if paddle.is_compiled_with_cuda() else "cpu"
    try:
        paddle.set_device(device)
    except Exception as exc:
        print(f"ERROR: cannot select Paddle device {device!r}: {exc}")
        return 1

    # Fixed inputs and seed make parameter initialization and outputs repeatable.
    paddle.seed(2024)
    selected: Iterable[str] = ("transgan", "styleformer") if args.model == "all" else (args.model,)
    checks: List[Dict[str, object]] = []
    for model_name in selected:
        if model_name == "transgan":
            checks.append(_check_transgan(paddle, nn, functional, args))
        else:
            for image_size in args.style_sizes:
                checks.append(_check_styleformer(paddle, nn, functional, args, image_size))

    report = {
        "ok": True,
        "device": paddle.get_device(),
        "checks": checks,
        "note": "synthetic contract smoke only; not source-model, checkpoint, metric, or benchmark verification",
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"OK: deterministic synthetic GAN smoke on {report['device']}")
        for item in checks:
            print(f"  {item['model']} {item.get('image_size', 32)}px: generator={item['generator']} discriminator={item['discriminator']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
