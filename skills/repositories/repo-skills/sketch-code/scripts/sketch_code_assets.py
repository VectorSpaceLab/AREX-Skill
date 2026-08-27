#!/usr/bin/env python3
"""Safe SketchCode asset manifest and path checker.

This helper does not download anything. It records the public asset URLs used by
SketchCode's historical setup scripts and checks whether a user-supplied runtime
root already contains the expected dataset/model files.
"""

import argparse
from pathlib import Path
from typing import Optional

ASSETS = [
    {
        "id": "dataset-zip",
        "url": "http://sketch-code.s3.amazonaws.com/data/all_data.zip",
        "default_path": "data/all_data.zip",
        "purpose": "Synthetic paired PNG/GUI dataset archive used for training examples.",
    },
    {
        "id": "model-json",
        "url": "http://sketch-code.s3.amazonaws.com/model_json_weights/model_json.json",
        "default_path": "bin/model_json.json",
        "purpose": "Pretrained Keras model architecture JSON required for conversion/fine-tuning.",
    },
    {
        "id": "weights",
        "url": "http://sketch-code.s3.amazonaws.com/model_json_weights/weights.h5",
        "default_path": "bin/weights.h5",
        "purpose": "Pretrained Keras HDF5 weights required for conversion/fine-tuning.",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print/check SketchCode external asset locations without downloading.")
    parser.add_argument("--root", help="Optional SketchCode runtime root to check for default data/ and bin/ asset paths.")
    parser.add_argument("--print-download-commands", action="store_true", help="Print wget/unzip commands for a human-approved download; never executes them.")
    return parser


def _status(root: Optional[Path], rel_path: str) -> str:
    if root is None:
        return "not checked"
    path = root / rel_path
    if path.exists():
        kind = "directory" if path.is_dir() else "file"
        return f"present ({kind})"
    return "missing"


def _print_manifest(root: Optional[Path]) -> None:
    print("SketchCode external asset manifest")
    for asset in ASSETS:
        print(f"\n[{asset['id']}]")
        print(f"purpose: {asset['purpose']}")
        print(f"url: {asset['url']}")
        print(f"default_path: {asset['default_path']}")
        print(f"status: {_status(root, asset['default_path'])}")


def _print_commands() -> None:
    print("\nHuman-approved download commands (review storage/network policy first):")
    print("mkdir -p data bin")
    print("wget http://sketch-code.s3.amazonaws.com/data/all_data.zip -O data/all_data.zip")
    print("unzip data/all_data.zip -d data/all_data")
    print("wget http://sketch-code.s3.amazonaws.com/model_json_weights/model_json.json -O bin/model_json.json")
    print("wget http://sketch-code.s3.amazonaws.com/model_json_weights/weights.h5 -O bin/weights.h5")


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.root).expanduser().resolve() if args.root else None
    if root is not None and not root.is_dir():
        raise SystemExit(f"--root is not a directory: {root}")
    _print_manifest(root)
    if args.print_download_commands:
        _print_commands()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
