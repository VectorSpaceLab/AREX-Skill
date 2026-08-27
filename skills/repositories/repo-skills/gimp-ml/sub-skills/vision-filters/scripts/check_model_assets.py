#!/usr/bin/env python3
"""Check expected GIMP-ML vision-filter assets without downloading or loading them."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

ASSETS = {
    # The plugin names best_fpn.h5, while the inspected Predictor helper also
    # loads the sibling serialized generator as mymodel.pth.
    "deblur": ("deblur/best_fpn.h5", "deblur/mymodel.pth"),
    "dehaze": ("deepdehaze/dehazer.pth",),
    "denoise": ("deepdenoise/net.pth", "deepdenoise/est_net.pth"),
    "enlighten": ("enlightening/200_net_G_A.pth",),
    "depth": ("MiDaS/model.pt",),
    "segmentation": ("deeplabv3/deeplabv3+model.pt",),
    "face-parsing": ("faceparse/79999_iter.pth",),
    "super-resolution": ("super_resolution/model_srresnet.pth",),
    "interpolation": (
        "interpolateframes/contextnet.pkl",
        "interpolateframes/flownet.pkl",
        "interpolateframes/unet.pkl",
    ),
}


def selected_assets(operation: str) -> Iterable[tuple[str, str]]:
    groups = ASSETS if operation == "all" else {operation: ASSETS[operation]}
    for name, paths in groups.items():
        for relative in paths:
            yield name, relative


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Report present and missing GIMP-ML vision-filter checkpoint files "
            "under an explicit weights root. This command never downloads, "
            "opens, or modifies checkpoint files."
        )
    )
    parser.add_argument(
        "weights_root",
        type=Path,
        help="directory corresponding to the plugin's generic weights/ root",
    )
    parser.add_argument(
        "--operation",
        choices=["all", *ASSETS.keys()],
        default="all",
        help="check one operation's assets (default: all)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.weights_root.expanduser()
    print(f"weights root: {root}")
    present = 0
    missing = 0
    for operation, relative in selected_assets(args.operation):
        candidate = root / relative
        # Relative names are constants above; resolve only for a clear directory
        # check and do not follow a user-supplied path beyond this asset root.
        if candidate.is_file():
            print(f"PRESENT  {operation:15} {relative}")
            present += 1
        else:
            print(f"MISSING  {operation:15} {relative}")
            missing += 1
    print(f"summary: {present} present, {missing} missing")
    if missing:
        print("No files were downloaded or loaded; provide the missing assets before inference.")
        return 1
    print("All requested asset paths exist; file contents and model compatibility were not checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
