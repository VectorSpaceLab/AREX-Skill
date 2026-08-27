#!/usr/bin/env python3
"""Merge multiple Isaac Lab HDF5 demonstration datasets into one file."""

from __future__ import annotations

import argparse
from pathlib import Path

import h5py


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge Isaac Lab-style HDF5 demonstration datasets.")
    parser.add_argument("--input_files", type=Path, nargs="+", required=True, help="Input HDF5 files to merge.")
    parser.add_argument("--output_file", type=Path, default=Path("merged_dataset.hdf5"), help="Merged output file.")
    return parser.parse_args()


def merge_datasets(input_files: list[Path], output_file: Path) -> None:
    for path in input_files:
        if not path.exists():
            raise FileNotFoundError(f"Dataset file does not exist: {path}")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(output_file, "w") as output:
        episode_idx = 0
        copy_attributes = True
        data_group = output.create_group("data")

        for filepath in input_files:
            with h5py.File(filepath, "r") as input_file:
                if "data" not in input_file:
                    raise KeyError(f"Missing 'data' group in {filepath}")
                for episode in input_file["data"]:
                    input_file.copy(f"data/{episode}", data_group, f"demo_{episode_idx}")
                    episode_idx += 1

                if copy_attributes:
                    for key, value in input_file["data"].attrs.items():
                        data_group.attrs[key] = value
                    copy_attributes = False


def main() -> int:
    args = parse_args()
    merge_datasets(args.input_files, args.output_file)
    print(f"Merged dataset saved to {args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
