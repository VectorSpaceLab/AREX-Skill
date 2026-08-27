#!/usr/bin/env python3
"""Validate a local .npz file for d3rlpy-style MDPDataset construction.

Required arrays: observations, actions, rewards, terminals.
Optional arrays: episode_terminals, timeouts.
The script reads only the supplied .npz file, prints a summary, and exits
non-zero on schema errors.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np


REQUIRED = ("observations", "actions", "rewards", "terminals")
OPTIONAL = ("episode_terminals", "timeouts")
FLAG_ARRAYS = ("terminals", "episode_terminals", "timeouts")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate local .npz arrays before MDPDataset conversion. No training or writes are performed.",
    )
    parser.add_argument("npz_path", help="local .npz file containing offline RL arrays")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON summary")
    return parser


def is_numeric_or_bool(array: np.ndarray) -> bool:
    return np.issubdtype(array.dtype, np.number) or np.issubdtype(array.dtype, np.bool_)


def flag_values_are_binary(array: np.ndarray) -> bool:
    flat = np.asarray(array).reshape(-1)
    if flat.size == 0:
        return False
    if np.issubdtype(flat.dtype, np.bool_):
        return True
    if not np.issubdtype(flat.dtype, np.number):
        return False
    finite = flat[np.isfinite(flat)]
    if finite.size != flat.size:
        return False
    unique = np.unique(finite)
    return bool(np.all(np.isin(unique, [0, 1, 0.0, 1.0])))


def array_summary(array: np.ndarray) -> Dict[str, object]:
    info: Dict[str, object] = {
        "shape": list(array.shape),
        "dtype": str(array.dtype),
    }
    if array.size and is_numeric_or_bool(array):
        numeric = np.asarray(array, dtype=np.float64).reshape(-1)
        finite_mask = np.isfinite(numeric)
        info["finite"] = bool(finite_mask.all())
        if finite_mask.any():
            finite = numeric[finite_mask]
            info["min"] = float(np.min(finite))
            info["max"] = float(np.max(finite))
            info["mean"] = float(np.mean(finite))
    else:
        info["finite"] = None
    return info


def validate(path: Path) -> Tuple[Dict[str, object], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if "://" in str(path):
        errors.append("path must be a local filesystem path, not a URL")
        return {}, errors, warnings
    if path.suffix != ".npz":
        errors.append("file extension must be .npz")
        return {}, errors, warnings
    if not path.exists():
        errors.append("file does not exist")
        return {}, errors, warnings
    if not path.is_file():
        errors.append("path is not a regular file")
        return {}, errors, warnings

    try:
        loaded = np.load(path, allow_pickle=False)
    except Exception as exc:  # pragma: no cover - defensive for malformed npz files
        errors.append(f"failed to load npz with allow_pickle=False: {exc}")
        return {}, errors, warnings

    with loaded as data:
        keys = list(data.files)
        arrays: Dict[str, np.ndarray] = {}
        for key in keys:
            try:
                arrays[key] = np.asarray(data[key])
            except Exception as exc:
                errors.append(f"failed to read array {key!r}: {exc}")

    missing = [name for name in REQUIRED if name not in arrays]
    if missing:
        errors.append("missing required arrays: " + ", ".join(missing))

    summary: Dict[str, object] = {
        "path": str(path),
        "keys": sorted(arrays),
        "required": list(REQUIRED),
        "optional_present": [name for name in OPTIONAL if name in arrays],
        "arrays": {name: array_summary(array) for name, array in sorted(arrays.items())},
    }

    if errors:
        return summary, errors, warnings

    first_lengths: Dict[str, int] = {}
    for name in REQUIRED + OPTIONAL:
        if name not in arrays:
            continue
        array = arrays[name]
        if array.ndim == 0:
            errors.append(f"{name} must have at least one dimension")
            continue
        first_lengths[name] = int(array.shape[0])
        if array.shape[0] == 0:
            errors.append(f"{name} has zero transitions")
        if not is_numeric_or_bool(array):
            errors.append(f"{name} must be numeric or boolean, got dtype {array.dtype}")
        elif array.size and not np.isfinite(np.asarray(array, dtype=np.float64)).all():
            errors.append(f"{name} contains NaN or infinite values")

    if "observations" in arrays and arrays["observations"].ndim < 2:
        warnings.append("observations is one-dimensional; vector observations are usually shaped (N, obs_dim)")

    if "actions" in arrays:
        if arrays["actions"].ndim == 1:
            warnings.append("actions is one-dimensional; this is valid for discrete actions but unusual for continuous control")
        elif arrays["actions"].ndim < 1:
            errors.append("actions must have at least one dimension")

    for name in ("rewards", "terminals", "episode_terminals", "timeouts"):
        if name in arrays and arrays[name].ndim > 2:
            warnings.append(f"{name} has ndim {arrays[name].ndim}; scalar transition arrays are usually (N,) or (N, 1)")
        if name in arrays and arrays[name].ndim == 2 and arrays[name].shape[1] != 1:
            warnings.append(f"{name} has second dimension {arrays[name].shape[1]}; expected scalar shape (N,) or (N, 1)")

    if first_lengths:
        expected = first_lengths.get("observations")
        for name, length in first_lengths.items():
            if expected is not None and length != expected:
                errors.append(f"first dimension mismatch: observations has {expected}, {name} has {length}")
        summary["transition_count"] = expected

    for name in FLAG_ARRAYS:
        if name in arrays and not flag_values_are_binary(arrays[name]):
            warnings.append(f"{name} is not strictly binary/boolean after finite-value check")

    if "episode_terminals" not in arrays and "timeouts" in arrays:
        warnings.append("timeouts is present but episode_terminals is absent; use terminals OR timeouts for episode boundaries when appropriate")
    if "episode_terminals" in arrays and "timeouts" in arrays:
        warnings.append("both episode_terminals and timeouts are present; document which one controls episode splitting")

    return summary, errors, warnings


def main() -> int:
    args = build_parser().parse_args()
    path = Path(args.npz_path).expanduser()
    summary, errors, warnings = validate(path)

    if args.strict and warnings:
        errors = errors + ["strict warning: " + warning for warning in warnings]

    if args.json:
        print(json.dumps({"ok": not errors, "summary": summary, "warnings": warnings, "errors": errors}, indent=2))
    else:
        print("MDPDataset .npz validation summary")
        print("ok:", "yes" if not errors else "no")
        if summary:
            print("keys:", ", ".join(summary.get("keys", [])))
            if "transition_count" in summary:
                print("transition_count:", summary["transition_count"])
            for name, info in summary.get("arrays", {}).items():
                print(f"- {name}: shape={info['shape']} dtype={info['dtype']} finite={info.get('finite')}")
        for warning in warnings:
            print("warning:", warning, file=sys.stderr)
        for error in errors:
            print("error:", error, file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
