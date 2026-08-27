#!/usr/bin/env python3
"""Parse retargeting criteria without external motion data or playback."""
from __future__ import annotations

import argparse

import torch

from curobo.types import DeviceCfg, ToolPoseCriteria


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a retargeting criterion")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    device_cfg = DeviceCfg(device=torch.device(args.device), dtype=torch.float32)
    criteria = ToolPoseCriteria(
        terminal_pose_axes_weight_factor=[1.0] * 6,
        non_terminal_pose_axes_weight_factor=[1.0] * 6,
        device_cfg=device_cfg,
    )
    print(criteria)


if __name__ == "__main__":
    main()
