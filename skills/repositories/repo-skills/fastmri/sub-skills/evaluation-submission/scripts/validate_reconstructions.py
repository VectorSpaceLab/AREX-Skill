#!/usr/bin/env python3
"""Validate fastMRI prediction HDF5 files before metrics or submission packaging."""

import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import h5py

TARGET_KEYS = {
    "multicoil": "reconstruction_rss",
    "singlecoil": "reconstruction_esc",
}


def _read_attr(hf: h5py.File, name: str):
    value = hf.attrs.get(name)
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


def _prediction_files(path: Path) -> List[Path]:
    if not path.exists():
        raise FileNotFoundError(f"predictions path does not exist: {path}")
    if path.is_file():
        if path.suffix != ".h5":
            raise ValueError(f"prediction file must end with .h5: {path}")
        return [path]
    return sorted(path.glob("*.h5"))


def _target_files(path: Optional[Path]) -> Dict[str, Path]:
    if path is None:
        return {}
    if not path.exists():
        raise FileNotFoundError(f"target path does not exist: {path}")
    if path.is_file():
        if path.suffix != ".h5":
            raise ValueError(f"target file must end with .h5: {path}")
        return {path.name: path}
    return {file.name: file for file in sorted(path.glob("*.h5"))}


def validate_prediction_file(path: Path) -> Tuple[bool, str]:
    try:
        with h5py.File(path, "r") as hf:
            if "reconstruction" not in hf:
                return False, "missing dataset 'reconstruction'"
            shape = hf["reconstruction"].shape
            if len(shape) < 3:
                return False, f"reconstruction should be at least 3D, got shape {shape}"
    except OSError as exc:
        return False, f"could not read HDF5: {exc}"
    return True, "ok"


def target_in_filter(path: Path, acquisition: Optional[str], acceleration: Optional[int]) -> bool:
    with h5py.File(path, "r") as hf:
        if acquisition is not None and _read_attr(hf, "acquisition") != acquisition:
            return False
        if acceleration is not None and _read_attr(hf, "acceleration") != acceleration:
            return False
    return True


def validate_targets(
    pred_files: List[Path],
    target_map: Dict[str, Path],
    challenge: Optional[str],
    acquisition: Optional[str],
    acceleration: Optional[int],
) -> Tuple[List[str], int]:
    errors: List[str] = []
    included = 0
    target_key = TARGET_KEYS.get(challenge) if challenge else None

    pred_names = {path.name for path in pred_files}
    for pred_name in sorted(pred_names - set(target_map)):
        errors.append(f"prediction has no matching target: {pred_name}")
    for target_name in sorted(set(target_map) - pred_names):
        errors.append(f"target has no matching prediction: {target_name}")

    for name in sorted(pred_names & set(target_map)):
        target_path = target_map[name]
        try:
            with h5py.File(target_path, "r") as hf:
                if target_key is not None and target_key not in hf:
                    errors.append(f"{name}: target missing key '{target_key}' for challenge '{challenge}'")
                    continue
            if target_in_filter(target_path, acquisition, acceleration):
                included += 1
        except OSError as exc:
            errors.append(f"{name}: could not read target HDF5: {exc}")

    return errors, included


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check fastMRI prediction files for required datasets, filenames, target keys, and filters."
    )
    parser.add_argument("--predictions-path", type=Path, required=True, help="Prediction .h5 file or directory.")
    parser.add_argument("--target-path", type=Path, default=None, help="Optional target .h5 file or directory for filename/key/filter checks.")
    parser.add_argument("--challenge", choices=sorted(TARGET_KEYS), default=None, help="Challenge used to choose target key when targets are supplied.")
    parser.add_argument("--acceleration", type=int, default=None, help="Optional acceleration filter to preview evaluation coverage.")
    parser.add_argument("--acquisition", default=None, help="Optional acquisition filter to preview evaluation coverage.")
    parser.add_argument("--require-v2", action="store_true", help="Require prediction filenames to end with _v2.h5.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    pred_files = _prediction_files(args.predictions_path)
    if not pred_files:
        raise SystemExit(f"no prediction .h5 files found in {args.predictions_path}")

    errors: List[str] = []
    for path in pred_files:
        ok, message = validate_prediction_file(path)
        if not ok:
            errors.append(f"{path.name}: {message}")
        if args.require_v2 and not path.name.endswith("_v2.h5"):
            errors.append(f"{path.name}: filename does not end with _v2.h5")

    included = None
    if args.target_path is not None:
        if args.challenge is None:
            errors.append("--challenge is required when --target-path is supplied")
        target_errors, included = validate_targets(
            pred_files,
            _target_files(args.target_path),
            args.challenge,
            args.acquisition,
            args.acceleration,
        )
        errors.extend(target_errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)

    message = f"validated {len(pred_files)} prediction file(s)"
    if included is not None:
        message += f"; {included} matched target file(s) included after filters"
        if included == 0:
            message += " (check acquisition/acceleration filters before evaluating)"
    print(message)


if __name__ == "__main__":
    main()
