#!/usr/bin/env python3
"""Tiny in-memory CAM smoke test.

No pretrained weights, no network, and no filesystem outputs unless the user
adds them externally. Example:

  python tiny_cam_smoke.py --method gradcam
  python tiny_cam_smoke.py --method finercam --batch-size 2 --cuda
"""

from __future__ import annotations

import argparse

import torch
import torch.nn as nn

from pytorch_grad_cam import (
    AblationCAM,
    EigenCAM,
    EigenGradCAM,
    FinerCAM,
    FullGrad,
    GradCAM,
    GradCAMElementWise,
    GradCAMPlusPlus,
    HiResCAM,
    KPCA_CAM,
    LayerCAM,
    ScoreCAM,
    SegEigenCAM,
    ShapleyCAM,
    XGradCAM,
)
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

METHODS = {
    "gradcam": GradCAM,
    "hirescam": HiResCAM,
    "scorecam": ScoreCAM,
    "gradcam++": GradCAMPlusPlus,
    "ablationcam": AblationCAM,
    "xgradcam": XGradCAM,
    "eigencam": EigenCAM,
    "eigengradcam": EigenGradCAM,
    "layercam": LayerCAM,
    "fullgrad": FullGrad,
    "gradcamelementwise": GradCAMElementWise,
    "kpcacam": KPCA_CAM,
    "shapleycam": ShapleyCAM,
    "finercam": FinerCAM,
    "segeigencam": SegEigenCAM,
}


class TinyCNN(nn.Module):
    def __init__(self, num_classes: int = 4):
        super().__init__()
        self.conv = nn.Conv2d(3, 8, kernel_size=3, padding=1)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(8, num_classes)

    def forward(self, x):
        x = torch.relu(self.conv(x))
        return self.fc(self.pool(x).flatten(1))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny in-memory Grad-CAM smoke test.")
    parser.add_argument("--method", choices=sorted(METHODS), default="gradcam")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--cuda", action="store_true", help="Move the tiny model and tensor to CUDA if available.")
    args = parser.parse_args()

    device = torch.device("cuda" if args.cuda and torch.cuda.is_available() else "cpu")
    model = TinyCNN().to(device).eval()
    input_tensor = torch.rand(args.batch_size, 3, 16, 16, device=device)
    target_layers = [model.conv]
    targets = [ClassifierOutputTarget(1) for _ in range(args.batch_size)]

    cam_cls = METHODS[args.method]
    if cam_cls is FinerCAM:
        cam = cam_cls(model=model, target_layers=target_layers)
        output = cam(input_tensor=input_tensor, targets=None)
    else:
        with cam_cls(model=model, target_layers=target_layers) as cam:
            output = cam(input_tensor=input_tensor, targets=targets)

    assert tuple(output.shape) == (args.batch_size, 16, 16), output.shape
    print(f"OK {args.method} {device} output_shape={tuple(output.shape)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
