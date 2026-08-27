#!/usr/bin/env python3
"""Strip leading DataParallel prefixes from a checkpoint state dict."""

from __future__ import annotations

import argparse
from collections import OrderedDict
from pathlib import Path
from typing import Mapping

import torch


def strip_module_prefix(state_dict: Mapping[str, object]) -> OrderedDict[str, object]:
    stripped = OrderedDict()
    for key, value in state_dict.items():
        new_key = key[7:] if key.startswith("module.") else key
        stripped[new_key] = value
    return stripped


def load_checkpoint(file_path: Path):
    return torch.load(file_path, map_location="cpu")


def save_checkpoint(obj, file_path: Path) -> None:
    torch.save(obj, file_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", type=Path, help="checkpoint file to rewrite")
    parser.add_argument("--dst_file_path", default=None, type=Path, help="destination path; defaults to the source file")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    dst_file_path = args.dst_file_path or args.file_path

    checkpoint = load_checkpoint(args.file_path)

    if isinstance(checkpoint, dict) and "state_dict" in checkpoint and isinstance(checkpoint["state_dict"], Mapping):
        checkpoint["state_dict"] = strip_module_prefix(checkpoint["state_dict"])
        save_checkpoint(checkpoint, dst_file_path)
    elif isinstance(checkpoint, Mapping):
        save_checkpoint(strip_module_prefix(checkpoint), dst_file_path)
    else:
        raise TypeError("checkpoint must be a mapping or a dict containing 'state_dict'")

    print(f"saved stripped checkpoint to {dst_file_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
