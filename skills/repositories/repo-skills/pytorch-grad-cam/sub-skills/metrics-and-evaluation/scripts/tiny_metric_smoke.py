#!/usr/bin/env python3
"""Tiny metric smoke for ROAD / confidence-change style helpers."""

from __future__ import annotations

import torch
import torch.nn as nn

from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.metrics.cam_mult_image import CamMultImageConfidenceChange
from pytorch_grad_cam.metrics.road import ROADCombined
from pytorch_grad_cam.refine_cam import RefineCAM
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget


class TinyCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(3, 8, kernel_size=3, padding=1)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(8, 4)

    def forward(self, x):
        x = torch.relu(self.conv(x))
        return self.fc(self.pool(x).flatten(1))


def main() -> int:
    model = TinyCNN().eval()
    x = torch.rand(2, 3, 16, 16)
    targets = [ClassifierOutputTarget(1), ClassifierOutputTarget(2)]

    with GradCAM(model=model, target_layers=[model.conv]) as cam:
        grayscale_cam = cam(input_tensor=x, targets=targets)

    metric = CamMultImageConfidenceChange()
    scores = metric(x, grayscale_cam, targets, model)
    assert scores.shape[0] == 2

    refine = RefineCAM(model=model, target_layers=[model.conv], base_method=GradCAM)
    refined = refine(input_tensor=x, targets=targets)
    assert refined.shape == (2, 16, 16)

    road = ROADCombined(percentiles=[20, 50])
    road_scores = road(x, grayscale_cam, targets, model)
    assert road_scores.shape[0] == 2

    print("OK metric smoke", scores.shape, refined.shape, road_scores.shape)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
