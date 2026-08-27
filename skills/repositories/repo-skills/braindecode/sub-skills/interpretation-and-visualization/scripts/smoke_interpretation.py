#!/usr/bin/env python3
"""Run local frequency-gradient and optional Captum attribution checks."""
from __future__ import annotations
import argparse
import torch
from torch import nn
from braindecode.visualization.frequency import amplitude_gradients

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--captum", action="store_true", help="also run saliency when Captum is installed")
    args = p.parse_args()
    x = torch.randn(2, 2, 32)
    frequency_model = nn.Conv1d(2, 2, kernel_size=5).eval()
    grads = amplitude_gradients(frequency_model, x)
    assert grads.shape[0] == 2
    print(f"amplitude_gradients_shape={tuple(grads.shape)}")
    if args.captum:
        try:
            from braindecode.visualization import saliency
            attribution_model = nn.Sequential(nn.Flatten(), nn.Linear(2 * 32, 2)).eval()
            target = torch.zeros(x.shape[0], dtype=torch.long)
            attrs = saliency(attribution_model, x, target)
            assert attrs.shape == x.shape
            print(f"saliency_shape={tuple(attrs.shape)}")
        except ImportError as exc:
            raise SystemExit(f"Captum requested but unavailable: {exc}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
