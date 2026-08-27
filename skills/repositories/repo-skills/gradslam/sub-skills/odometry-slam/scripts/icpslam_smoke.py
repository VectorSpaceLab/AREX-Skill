#!/usr/bin/env python3
"""Run ICPSLAM on a deterministic tiny CPU RGB-D fixture.

The helper never downloads data or opens a GUI.  By default it runs all three
supported odometry choices and reports pose/map shapes for each one.
"""

import argparse
import json
import sys


def make_parser():
    parser = argparse.ArgumentParser(
        description="Smoke-test ICPSLAM with an in-memory CPU RGB-D fixture."
    )
    parser.add_argument(
        "--odom",
        choices=("gt", "icp", "gradicp", "all"),
        default="all",
        help="Odometry choice to run (default: all).",
    )
    parser.add_argument(
        "--numiters",
        type=int,
        default=3,
        help="ICP/GradICP iterations for the tiny check (default: 3).",
    )
    parser.add_argument(
        "--dsratio",
        type=int,
        default=2,
        help="Integer downsampling ratio for localization (default: 2).",
    )
    return parser


def make_fixture(torch):
    """Return a small, positive-depth, channels-last RGBDImages object."""
    from gradslam.structures.rgbdimages import RGBDImages

    batch, length, height, width = 1, 2, 8, 8
    rows = torch.arange(height, dtype=torch.float32).view(height, 1).expand(height, width)
    cols = torch.arange(width, dtype=torch.float32).view(1, width).expand(height, width)
    depth = 1.0 + 0.02 * cols + 0.03 * rows
    color = torch.stack(
        (cols / float(width - 1), rows / float(height - 1), torch.full_like(rows, 0.5)),
        dim=-1,
    )

    colors = color.view(1, 1, height, width, 3).repeat(batch, length, 1, 1, 1)
    depths = depth.view(1, 1, height, width, 1).repeat(batch, length, 1, 1, 1)
    intrinsics = torch.eye(4, dtype=torch.float32).view(1, 1, 4, 4).repeat(batch, 1, 1, 1)
    intrinsics[..., 0, 0] = 4.0
    intrinsics[..., 1, 1] = 4.0
    intrinsics[..., 0, 2] = (width - 1) / 2.0
    intrinsics[..., 1, 2] = (height - 1) / 2.0
    poses = torch.eye(4, dtype=torch.float32).view(1, 1, 4, 4).repeat(batch, length, 1, 1)
    return RGBDImages(colors, depths, intrinsics, poses, channels_first=False)


def run_one(torch, ICPSLAM, odom, numiters, dsratio):
    frames = make_fixture(torch)
    slam = ICPSLAM(
        odom=odom,
        dsratio=dsratio,
        numiters=numiters,
        device="cpu",
    )
    maps, poses = slam(frames)
    if not torch.isfinite(poses).all().item():
        raise RuntimeError("recovered poses contain non-finite values")
    if maps.points_padded is None or not torch.isfinite(maps.points_padded).all().item():
        raise RuntimeError("aggregated map contains no finite padded points")
    return {
        "odom": odom,
        "poses_shape": list(poses.shape),
        "map_shape": list(maps.points_padded.shape),
        "points_per_batch": [int(value) for value in maps.num_points_per_pointcloud.tolist()],
        "device": str(poses.device),
        "finite": True,
    }


def main(argv=None):
    args = make_parser().parse_args(argv)
    if args.numiters < 1 or args.dsratio < 1:
        print("--numiters and --dsratio must be positive integers", file=sys.stderr)
        return 2

    # Imports are deferred so --help remains usable before optional native
    # odometry extensions are loaded.
    import torch
    from gradslam.slam.icpslam import ICPSLAM

    choices = ("gt", "icp", "gradicp") if args.odom == "all" else (args.odom,)
    failures = 0
    for odom in choices:
        try:
            result = run_one(torch, ICPSLAM, odom, args.numiters, args.dsratio)
            print(json.dumps(result, sort_keys=True))
        except Exception as exc:  # report the selected backend/solver failure
            failures += 1
            print(
                "odom={0} ERROR {1}: {2}".format(odom, type(exc).__name__, exc),
                file=sys.stderr,
            )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
