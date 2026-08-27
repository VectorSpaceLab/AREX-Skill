#!/usr/bin/env python3
"""Run a tiny deterministic, display-free structures smoke check.

The helper creates an in-memory RGB-D batch, derives maps, converts one frame
to filtered and dense point clouds, and prints a JSON shape summary. It never
opens a GUI, starts a browser, downloads data, or requires CUDA.
"""

import argparse
import json
from typing import Dict, Optional

import torch

from gradslam import Pointclouds, RGBDImages
from gradslam.structures.utils import pointclouds_from_rgbdimages


def _shape(value: Optional[torch.Tensor]):
    return None if value is None else list(value.shape)


def _fixture(channels_first: bool) -> Dict[str, object]:
    batch, sequence, height, width = 1, 1, 2, 3
    # Keep values explicit and positive except for one invalid depth pixel.
    rgb_last = torch.tensor(
        [[[[0.0, 0.1, 0.2], [0.3, 0.4, 0.5], [0.6, 0.7, 0.8]],
          [[0.9, 0.8, 0.7], [0.6, 0.5, 0.4], [0.3, 0.2, 0.1]]]],
        dtype=torch.float32,
    ).unsqueeze(1)
    depth_last = torch.tensor(
        [[[[1.0], [0.0], [2.0]], [[1.5], [2.5], [3.0]]]],
        dtype=torch.float32,
    ).unsqueeze(1)
    intrinsics = torch.eye(4, dtype=torch.float32).view(1, 1, 4, 4)
    poses = torch.eye(4, dtype=torch.float32).view(1, 1, 4, 4)
    poses[..., 0, 3] = 0.25

    if channels_first:
        rgb = rgb_last.permute(0, 1, 4, 2, 3).contiguous()
        depth = depth_last.permute(0, 1, 4, 2, 3).contiguous()
    else:
        rgb, depth = rgb_last, depth_last

    rgbd = RGBDImages(
        rgb,
        depth,
        intrinsics,
        poses=poses,
        channels_first=channels_first,
        device="cpu",
    )
    frame = rgbd[:, 0]
    filtered = pointclouds_from_rgbdimages(frame, filter_missing_depths=True)
    dense = pointclouds_from_rgbdimages(frame, filter_missing_depths=False)
    assert isinstance(filtered, Pointclouds)
    assert isinstance(dense, Pointclouds)
    assert filtered.num_points_per_pointcloud.tolist() == [5]
    assert dense.points_padded.shape == (batch, height * width, 3)

    return {
        "channels_first": channels_first,
        "device": str(rgbd.rgb_image.device),
        "rgb": _shape(rgbd.rgb_image),
        "depth": _shape(rgbd.depth_image),
        "intrinsics": _shape(rgbd.intrinsics),
        "poses": _shape(rgbd.poses),
        "valid_depth_mask": _shape(rgbd.valid_depth_mask),
        "vertex_map": _shape(rgbd.vertex_map),
        "normal_map": _shape(rgbd.normal_map),
        "global_vertex_map": _shape(rgbd.global_vertex_map),
        "global_normal_map": _shape(rgbd.global_normal_map),
        "filtered_points": _shape(filtered.points_list[0]),
        "dense_points": _shape(dense.points_padded),
        "filtered_counts": filtered.num_points_per_pointcloud.tolist(),
        "dense_nonpad_mask": dense.nonpad_mask.tolist(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Construct a deterministic tiny RGB-D/Pointclouds fixture."
    )
    parser.add_argument(
        "--channels-first",
        action="store_true",
        help="Run the fixture in (B,L,C,H,W) image layout (default: channels-last).",
    )
    parser.add_argument(
        "--both-layouts",
        action="store_true",
        help="Run and report both channels-last and channels-first layouts.",
    )
    args = parser.parse_args()

    torch.manual_seed(0)
    layouts = [args.channels_first]
    if args.both_layouts:
        layouts = [False, True]
    report = [_fixture(channels_first) for channels_first in layouts]
    output = report if len(report) > 1 else report[0]
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
