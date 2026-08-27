#!/usr/bin/env python3
"""Tiny synthetic Mapper configuration smoke; no downloads or viewer."""
from __future__ import annotations

import argparse

import torch

from curobo.perception import Mapper, MapperCfg


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a bounded cuRobo mapper smoke check")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this smoke check")
    center = torch.zeros(3, device=args.device, dtype=torch.float32)
    cfg = MapperCfg(
        extent_meters_xyz=(0.4, 0.4, 0.4),
        voxel_size=0.04,
        esdf_voxel_size=0.08,
        grid_center=center,
        num_cameras=1,
        image_height=4,
        image_width=4,
        device=args.device,
    )
    mapper = Mapper(cfg)
    print({"stats": mapper.get_stats(), "memory_mb": mapper.memory_usage_mb()})
    mapper.reset()


if __name__ == "__main__":
    main()
