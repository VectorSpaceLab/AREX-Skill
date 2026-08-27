#!/usr/bin/env python3
"""Create fastMRI zero-filled reconstruction files for submission-style workflows."""

import argparse
import xml.etree.ElementTree as etree
from pathlib import Path
from typing import Iterable, Tuple

import h5py
import fastmri
from fastmri.data import transforms
from fastmri.data.mri_data import et_query


def _crop_size_from_header(header: bytes) -> Tuple[int, int]:
    root = etree.fromstring(header)
    path = ["encoding", "encodedSpace", "matrixSize"]
    return int(et_query(root, path + ["x"])), int(et_query(root, path + ["y"]))


def iter_h5_files(data_path: Path) -> Iterable[Path]:
    if not data_path.exists():
        raise FileNotFoundError(f"data path does not exist: {data_path}")
    if data_path.is_file():
        if data_path.suffix != ".h5":
            raise ValueError(f"expected an .h5 file or directory, got: {data_path}")
        yield data_path
        return
    yield from sorted(data_path.glob("*.h5"))


def reconstruct_file(path: Path, challenge: str):
    with h5py.File(path, "r") as hf:
        if "kspace" not in hf:
            raise KeyError(f"{path.name} is missing dataset 'kspace'")
        if "ismrmrd_header" not in hf:
            raise KeyError(f"{path.name} is missing dataset 'ismrmrd_header'")

        crop_size = _crop_size_from_header(hf["ismrmrd_header"][()])
        image = fastmri.ifft2c(transforms.to_tensor(hf["kspace"][()]))

    if image.shape[-2] < crop_size[1]:
        crop_size = (image.shape[-2], image.shape[-2])

    image = transforms.complex_center_crop(image, crop_size)
    image = fastmri.complex_abs(image)

    if challenge == "multicoil":
        image = fastmri.rss(image, dim=1)

    return image.numpy()


def save_zero_filled(data_path: Path, output_path: Path, challenge: str) -> int:
    reconstructions = {}
    for h5_path in iter_h5_files(data_path):
        reconstructions[h5_path.name] = reconstruct_file(h5_path, challenge)

    if not reconstructions:
        raise ValueError(f"no .h5 files found in {data_path}")

    fastmri.save_reconstructions(reconstructions, output_path)
    return len(reconstructions)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create zero-filled fastMRI reconstruction .h5 files with dataset key 'reconstruction'."
    )
    parser.add_argument("--data-path", type=Path, required=True, help="Input .h5 file or directory of fastMRI k-space files.")
    parser.add_argument("--output-path", type=Path, required=True, help="Directory for output reconstruction .h5 files.")
    parser.add_argument("--challenge", choices=["singlecoil", "multicoil"], required=True, help="fastMRI challenge type.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    count = save_zero_filled(args.data_path, args.output_path, args.challenge)
    print(f"wrote {count} reconstruction file(s) to {args.output_path}")


if __name__ == "__main__":
    main()
