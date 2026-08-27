#!/usr/bin/env python3
"""Print or verify the MASt3R-SLAM checkpoint manifest.

Safe by default: it only prints the expected filenames and public download URLs.
It can optionally verify that a checkpoint directory already contains the three
required assets.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

MANIFEST = [
    (
        "MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth",
        "https://download.europe.naverlabs.com/ComputerVision/MASt3R/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth",
    ),
    (
        "MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric_retrieval_trainingfree.pth",
        "https://download.europe.naverlabs.com/ComputerVision/MASt3R/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric_retrieval_trainingfree.pth",
    ),
    (
        "MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric_retrieval_codebook.pkl",
        "https://download.europe.naverlabs.com/ComputerVision/MASt3R/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric_retrieval_codebook.pkl",
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-dir", type=pathlib.Path, help="Existing checkpoint directory to verify.")
    parser.add_argument("--print-download-commands", action="store_true", help="Print wget commands for the public assets.")
    args = parser.parse_args()

    for filename, url in MANIFEST:
        print(f"{filename}\t{url}")
        if args.print_download_commands:
            print(f"wget {url} -P <checkpoint-dir>")

    if args.checkpoint_dir:
        missing = []
        for filename, _ in MANIFEST:
            path = args.checkpoint_dir / filename
            if path.exists():
                print(f"ok: {path}")
            else:
                missing.append(str(path))
        if missing:
            print("missing checkpoints:", file=sys.stderr)
            for item in missing:
                print(f"- {item}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
