#!/usr/bin/env python3
"""Convert a legacy NanoDet `.pth` checkpoint into Lightning format."""

from __future__ import annotations

import argparse

import torch

from nanodet.util import convert_old_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a legacy NanoDet .pth checkpoint into Lightning format.",
    )
    parser.add_argument("--file_path", required=True, help="Path to the old .pth checkpoint.")
    parser.add_argument("--out_path", required=True, help="Path to write the converted .ckpt file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    old_check_point = torch.load(args.file_path, map_location=lambda storage, loc: storage)
    new_check_point = convert_old_model(old_check_point)
    torch.save(new_check_point, args.out_path)
    print("Checkpoint saved to:", args.out_path)


if __name__ == "__main__":
    main()
