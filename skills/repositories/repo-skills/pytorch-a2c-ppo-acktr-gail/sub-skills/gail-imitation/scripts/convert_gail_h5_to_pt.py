#!/usr/bin/env python3
"""Convert this repo's GAIL expert HDF5 files to the PyTorch .pt format.

The expected HDF5 datasets are:
  - obs_B_T_Do: observations/states, shape [B, T, Do]
  - a_B_T_Da: actions, shape [B, T, Da]
  - r_B_T: rewards, shape [B, T]
  - len_B: valid trajectory lengths, shape [B]

The output is a torch-saved dict with keys: states, actions, rewards, lengths.
This script performs local validation only; it never downloads data.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import torch

REQUIRED_DATASETS = ("obs_B_T_Do", "a_B_T_Da", "r_B_T", "len_B")


class ConversionError(Exception):
    """Raised for user-correctable conversion problems."""


def _load_h5py():
    try:
        import h5py  # type: ignore
    except ModuleNotFoundError as exc:
        raise ConversionError(
            "Missing dependency 'h5py'. Install it in the active environment "
            "before converting GAIL expert HDF5 files."
        ) from exc
    return h5py


def _default_pt_path(h5_file: Path) -> Path:
    return h5_file.with_suffix(".pt")


def _available_keys(h5_file) -> str:
    keys = []
    h5_file.visit(lambda name: keys.append(name))
    return ", ".join(keys) if keys else "<none>"


def _require_datasets(h5_file) -> None:
    missing = [name for name in REQUIRED_DATASETS if name not in h5_file]
    if missing:
        raise ConversionError(
            "Missing required HDF5 dataset(s): {}. Available keys: {}".format(
                ", ".join(missing), _available_keys(h5_file)
            )
        )


def _shape_tuple(dataset) -> Tuple[int, ...]:
    return tuple(int(dim) for dim in dataset.shape)


def _validate_shapes(h5_file) -> Dict[str, Tuple[int, ...]]:
    shapes = {name: _shape_tuple(h5_file[name]) for name in REQUIRED_DATASETS}

    if len(shapes["obs_B_T_Do"]) != 3:
        raise ConversionError(
            f"obs_B_T_Do must have shape [B, T, Do], got {shapes['obs_B_T_Do']}"
        )
    if len(shapes["a_B_T_Da"]) != 3:
        raise ConversionError(
            f"a_B_T_Da must have shape [B, T, Da], got {shapes['a_B_T_Da']}"
        )
    if len(shapes["r_B_T"]) != 2:
        raise ConversionError(
            f"r_B_T must have shape [B, T], got {shapes['r_B_T']}"
        )
    if len(shapes["len_B"]) != 1:
        raise ConversionError(f"len_B must have shape [B], got {shapes['len_B']}")

    b_obs, t_obs, _ = shapes["obs_B_T_Do"]
    b_act, t_act, _ = shapes["a_B_T_Da"]
    b_rew, t_rew = shapes["r_B_T"]
    (b_len,) = shapes["len_B"]

    if not (b_obs == b_act == b_rew == b_len):
        raise ConversionError(
            "Trajectory count B mismatch: obs_B_T_Do={}, a_B_T_Da={}, "
            "r_B_T={}, len_B={}".format(b_obs, b_act, b_rew, b_len)
        )
    if not (t_obs == t_act == t_rew):
        raise ConversionError(
            "Timestep count T mismatch: obs_B_T_Do={}, a_B_T_Da={}, r_B_T={}".format(
                t_obs, t_act, t_rew
            )
        )
    if b_obs <= 0 or t_obs <= 0:
        raise ConversionError(
            f"Expected at least one trajectory and one timestep, got B={b_obs}, T={t_obs}"
        )

    lengths = np.asarray(h5_file["len_B"][:])
    if not np.issubdtype(lengths.dtype, np.number):
        raise ConversionError(f"len_B must be numeric, got dtype {lengths.dtype}")
    if np.any(lengths < 0):
        raise ConversionError("len_B contains negative trajectory lengths")
    if np.any(lengths > t_obs):
        raise ConversionError(
            f"len_B contains values greater than T={t_obs}; max length is {lengths.max()}"
        )
    if np.any(lengths == 0):
        print(
            "warning: len_B contains zero-length trajectories; ExpertDataset may be empty "
            "after subsampling",
            file=sys.stderr,
        )

    return shapes


def convert(h5_file: Path, pt_file: Path) -> Dict[str, torch.Tensor]:
    if not h5_file.exists():
        raise ConversionError(f"Input HDF5 file does not exist: {h5_file}")
    if not h5_file.is_file():
        raise ConversionError(f"Input HDF5 path is not a file: {h5_file}")

    h5py = _load_h5py()
    try:
        with h5py.File(h5_file, "r") as handle:
            _require_datasets(handle)
            _validate_shapes(handle)
            states = torch.from_numpy(np.asarray(handle["obs_B_T_Do"][:])).float()
            actions = torch.from_numpy(np.asarray(handle["a_B_T_Da"][:])).float()
            rewards = torch.from_numpy(np.asarray(handle["r_B_T"][:])).float()
            lengths = torch.from_numpy(np.asarray(handle["len_B"][:])).long()
    except OSError as exc:
        raise ConversionError(f"Could not open HDF5 file {h5_file}: {exc}") from exc

    data = {
        "states": states,
        "actions": actions,
        "rewards": rewards,
        "lengths": lengths,
    }

    pt_file.parent.mkdir(parents=True, exist_ok=True)
    torch.save(data, pt_file)
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert GAIL expert HDF5 trajectories to this repo's .pt format."
    )
    parser.add_argument(
        "--h5-file",
        required=True,
        type=Path,
        help="Input HDF5 file with obs_B_T_Do, a_B_T_Da, r_B_T, and len_B datasets.",
    )
    parser.add_argument(
        "--pt-file",
        default=None,
        type=Path,
        help="Output .pt file. Defaults to the input path with a .pt suffix.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    h5_file = args.h5_file
    pt_file = args.pt_file if args.pt_file is not None else _default_pt_path(h5_file)

    try:
        data = convert(h5_file, pt_file)
    except ConversionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        "wrote {pt_file} with states {states}, actions {actions}, rewards {rewards}, "
        "lengths {lengths}".format(
            pt_file=pt_file,
            states=tuple(data["states"].shape),
            actions=tuple(data["actions"].shape),
            rewards=tuple(data["rewards"].shape),
            lengths=tuple(data["lengths"].shape),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
