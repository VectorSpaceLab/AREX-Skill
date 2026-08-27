#!/usr/bin/env python3
"""Create a deterministic tiny fastMRI-like HDF5 file for loader checks."""

from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import numpy as np


def ismrmrd_header(encoded_y: int, encoded_x: int, recon_y: int, recon_x: int) -> str:
    center = encoded_y // 2
    maximum = encoded_y - 1
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ismrmrdHeader xmlns="http://www.ismrm.org/ISMRMRD">
  <encoding>
    <encodedSpace>
      <matrixSize>
        <x>{encoded_x}</x>
        <y>{encoded_y}</y>
        <z>1</z>
      </matrixSize>
    </encodedSpace>
    <reconSpace>
      <matrixSize>
        <x>{recon_x}</x>
        <y>{recon_y}</y>
        <z>1</z>
      </matrixSize>
    </reconSpace>
    <encodingLimits>
      <kspace_encoding_step_1>
        <minimum>0</minimum>
        <maximum>{maximum}</maximum>
        <center>{center}</center>
      </kspace_encoding_step_1>
    </encodingLimits>
  </encoding>
</ismrmrdHeader>
"""


def make_complex_normal(rng: np.random.Generator, shape: tuple[int, ...]) -> np.ndarray:
    real = rng.normal(size=shape).astype(np.float32)
    imag = rng.normal(size=shape).astype(np.float32)
    return (real + 1j * imag).astype(np.complex64)


def create_file(
    output: Path,
    challenge: str,
    split: str,
    slices: int,
    coils: int,
    height: int,
    width: int,
    seed: int,
) -> None:
    rng = np.random.default_rng(seed)
    output.parent.mkdir(parents=True, exist_ok=True)

    if challenge == "singlecoil":
        kspace_shape = (slices, height, width)
        target_key = "reconstruction_esc"
    elif challenge == "multicoil":
        kspace_shape = (slices, coils, height, width)
        target_key = "reconstruction_rss"
    else:
        raise ValueError("challenge must be 'singlecoil' or 'multicoil'")

    kspace = make_complex_normal(rng, kspace_shape)
    recon_height = min(height, 16)
    recon_width = min(width, 16)
    recon = np.abs(rng.normal(size=(slices, recon_height, recon_width))).astype(np.float32)
    mask = np.zeros(width, dtype=bool)
    mask[::4] = True
    low_freq_start = max(width // 2 - 2, 0)
    low_freq_stop = min(width // 2 + 2, width)
    mask[low_freq_start:low_freq_stop] = True

    with h5py.File(output, "w") as handle:
        handle.create_dataset("kspace", data=kspace)
        handle.create_dataset("ismrmrd_header", data=ismrmrd_header(height, width, recon_height, recon_width))
        handle.attrs["acquisition"] = "TINY_FASTMRI_SYNTHETIC"
        if split in {"train", "val"}:
            handle.create_dataset(target_key, data=recon)
            handle.attrs["max"] = float(recon.max())
        elif split in {"test", "challenge"}:
            handle.create_dataset("mask", data=mask)
            handle.attrs["acceleration"] = 4
        else:
            raise ValueError("split must be one of: train, val, test, challenge")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a deterministic tiny fastMRI-like HDF5 file."
    )
    parser.add_argument("output", type=Path, help="Output .h5 path.")
    parser.add_argument(
        "--challenge",
        choices=("singlecoil", "multicoil"),
        default="multicoil",
        help="Which fastMRI challenge layout to create.",
    )
    parser.add_argument(
        "--split",
        choices=("train", "val", "test", "challenge"),
        default="train",
        help="Controls whether a reconstruction target or mask is written.",
    )
    parser.add_argument("--slices", type=int, default=3)
    parser.add_argument("--coils", type=int, default=4)
    parser.add_argument("--height", type=int, default=32)
    parser.add_argument("--width", type=int, default=32)
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args()

    create_file(
        output=args.output,
        challenge=args.challenge,
        split=args.split,
        slices=args.slices,
        coils=args.coils,
        height=args.height,
        width=args.width,
        seed=args.seed,
    )
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
