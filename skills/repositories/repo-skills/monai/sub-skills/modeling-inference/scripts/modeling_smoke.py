#!/usr/bin/env python3
"""Tiny CPU smoke check for MONAI modeling and inference primitives."""

from __future__ import annotations

import argparse
import json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny CPU-only MONAI modeling smoke check: UNet forward, "
            "DiceCE loss, DiceMetric, and sliding_window_inference."
        )
    )
    parser.add_argument("--spatial-size", type=int, default=16, help="Cubic input size for the synthetic 3D volume.")
    parser.add_argument("--roi-size", type=int, default=8, help="Cubic sliding-window ROI size.")
    parser.add_argument("--classes", type=int, default=2, help="Number of segmentation classes/output channels.")
    parser.add_argument("--seed", type=int, default=7, help="Torch random seed for deterministic synthetic tensors.")
    return parser


def run_smoke(spatial_size: int, roi_size: int, classes: int, seed: int) -> dict[str, object]:
    if spatial_size < 8:
        raise ValueError("--spatial-size must be at least 8 for the tiny UNet.")
    if roi_size < 4 or roi_size > spatial_size:
        raise ValueError("--roi-size must be between 4 and --spatial-size.")
    if classes < 2:
        raise ValueError("--classes must be at least 2 for this multi-class smoke check.")

    try:
        import torch
        from monai.inferers import sliding_window_inference
        from monai.losses import DiceCELoss
        from monai.metrics import DiceMetric
        from monai.networks import one_hot
        from monai.networks.nets import UNet
    except ImportError as error:
        raise RuntimeError(
            "This smoke check requires an environment with MONAI and PyTorch installed. "
            "Install the MONAI package and its core dependencies, then rerun the script."
        ) from error

    torch.manual_seed(seed)
    device = torch.device("cpu")

    model = UNet(
        spatial_dims=3,
        in_channels=1,
        out_channels=classes,
        channels=(4, 8),
        strides=(2,),
        num_res_units=1,
    ).to(device)
    model.eval()

    image = torch.randn(1, 1, spatial_size, spatial_size, spatial_size, device=device)
    label = torch.randint(0, classes, (1, 1, spatial_size, spatial_size, spatial_size), device=device)

    with torch.no_grad():
        logits = model(image)
        sw_logits = sliding_window_inference(
            inputs=image,
            roi_size=(roi_size, roi_size, roi_size),
            sw_batch_size=2,
            predictor=model,
            overlap=0.25,
            mode="gaussian",
        )

    loss_fn = DiceCELoss(to_onehot_y=True, softmax=True)
    loss_value = float(loss_fn(logits, label).detach().cpu())

    pred_indices = torch.argmax(sw_logits, dim=1, keepdim=True)
    pred_one_hot = one_hot(pred_indices, num_classes=classes)
    label_one_hot = one_hot(label, num_classes=classes)

    metric = DiceMetric(include_background=False, reduction="mean")
    metric(y_pred=pred_one_hot, y=label_one_hot)
    dice_value = float(metric.aggregate().detach().cpu())
    metric.reset()

    return {
        "ok": True,
        "device": str(device),
        "image_shape": list(image.shape),
        "logits_shape": list(logits.shape),
        "sliding_window_shape": list(sw_logits.shape),
        "loss": round(loss_value, 6),
        "foreground_dice": round(dice_value, 6),
    }


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    result = run_smoke(
        spatial_size=args.spatial_size,
        roi_size=args.roi_size,
        classes=args.classes,
        seed=args.seed,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
