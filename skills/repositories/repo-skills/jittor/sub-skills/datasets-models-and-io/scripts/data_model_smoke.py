#!/usr/bin/env python3
"""No-download Jittor data/transform/model-zoo smoke test.

This script uses only synthetic images, TensorDataset, Jittor transforms, and
resnet18(pretrained=False). It does not download datasets or pretrained weights.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Sequence


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a no-download Jittor TensorDataset, transform, and resnet18 shape smoke."
    )
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size for the TensorDataset smoke.")
    parser.add_argument("--num-samples", type=int, default=2, help="Number of synthetic samples to generate.")
    parser.add_argument("--image-size", type=int, default=32, help="Square CHW image size; use at least 32 for ResNet.")
    parser.add_argument("--num-classes", type=int, default=1000, help="Classifier output classes for resnet18.")
    parser.add_argument("--seed", type=int, default=0, help="NumPy random seed for synthetic images.")
    parser.add_argument(
        "--skip-model",
        action="store_true",
        help="Only check transform and TensorDataset batching; default also runs resnet18(pretrained=False).",
    )
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    if args.batch_size < 1:
        raise ValueError("--batch-size must be positive")
    if args.num_samples < args.batch_size:
        raise ValueError("--num-samples must be at least --batch-size")
    if args.image_size < 32:
        raise ValueError("--image-size must be at least 32 for this ResNet smoke")
    if args.num_classes < 1:
        raise ValueError("--num-classes must be positive")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    validate_args(args)

    # Force CPU-safe import behavior on hosts where CUDA is visible but not usable.
    os.environ.setdefault("nvcc_path", "")

    import numpy as np
    from PIL import Image
    import jittor as jt
    from jittor.dataset import TensorDataset
    import jittor.transform as T
    import jittor.models as models

    rng = np.random.default_rng(args.seed)
    transform = T.Compose([
        T.Resize((args.image_size, args.image_size)),
        T.ToTensor(),
        T.ImageNormalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])

    transformed = []
    for _ in range(args.num_samples):
        # HWC uint8 synthetic image, intentionally larger than target to exercise Resize.
        hwc = rng.integers(
            0,
            256,
            size=(args.image_size + 4, args.image_size + 2, 3),
            dtype=np.uint8,
        )
        pil_img = Image.fromarray(hwc, "RGB")
        transformed_img = transform(pil_img)
        chw = transformed_img.numpy() if hasattr(transformed_img, "numpy") else np.asarray(transformed_img, dtype=np.float32)
        chw = np.asarray(chw, dtype=np.float32)
        expected_chw = (3, args.image_size, args.image_size)
        if tuple(chw.shape) != expected_chw:
            raise AssertionError(f"transform returned shape {chw.shape}, expected {expected_chw}")
        transformed.append(chw)

    images_np = np.stack(transformed, axis=0).astype("float32")
    labels_np = (np.arange(args.num_samples, dtype=np.int32) % max(1, args.num_classes)).astype("int32")

    dataset = TensorDataset(jt.array(images_np), jt.array(labels_np)).set_attrs(
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
    )
    batch_images, batch_labels = next(iter(dataset))

    expected_batch_shape = [args.batch_size, 3, args.image_size, args.image_size]
    if list(batch_images.shape) != expected_batch_shape:
        raise AssertionError(f"batch image shape {batch_images.shape}, expected {expected_batch_shape}")
    if list(batch_labels.shape) != [args.batch_size]:
        raise AssertionError(f"batch label shape {batch_labels.shape}, expected [{args.batch_size}]")

    summary = {
        "downloaded": False,
        "tensor_dataset_batch_shape": list(batch_images.shape),
        "label_shape": list(batch_labels.shape),
        "transform": "Resize -> ToTensor -> ImageNormalize",
    }

    if not args.skip_model:
        model = models.resnet18(pretrained=False, num_classes=args.num_classes)
        model.eval()
        with jt.no_grad():
            logits = model(batch_images)
            logits.sync()
        expected_logits = [args.batch_size, args.num_classes]
        if list(logits.shape) != expected_logits:
            raise AssertionError(f"resnet18 logits shape {logits.shape}, expected {expected_logits}")
        summary.update({
            "model": "resnet18(pretrained=False)",
            "logits_shape": list(logits.shape),
        })

    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
