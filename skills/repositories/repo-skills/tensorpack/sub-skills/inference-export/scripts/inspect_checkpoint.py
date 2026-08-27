#!/usr/bin/env python3
"""Inspect checkpoint or .npz weights safely.

The script lists variable names and shapes, and can optionally re-save the
loaded parameters to a normalized .npz file.

Examples:
    python scripts/inspect_checkpoint.py model.npz
    python scripts/inspect_checkpoint.py model-1000 --dump-npz copy.npz
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from typing import Dict, Mapping, Any

import numpy as np


def _eprint(*parts):
    print(*parts, file=sys.stderr)


def _normalize_name(name: str) -> str:
    return name[:-2] if isinstance(name, str) and name.endswith(":0") else name


def _load_numpy_params(path: str) -> Dict[str, np.ndarray]:
    if path.endswith(".npz"):
        with np.load(path, allow_pickle=False) as data:
            return {_normalize_name(k): data[k] for k in data.files}
    if path.endswith(".npy"):
        obj = np.load(path, allow_pickle=True)
        if hasattr(obj, "item"):
            try:
                obj = obj.item()
            except ValueError as exc:
                raise ValueError(f"{path} does not contain a dict-like object") from exc
        if not isinstance(obj, dict):
            raise ValueError(f"{path} does not contain a dict-like object")
        return {_normalize_name(k): v for k, v in obj.items()}
    raise ValueError(f"Unsupported numpy weight file: {path}")


def _import_tensorflow():
    try:
        import tensorflow as tf  # type: ignore
    except Exception as exc:  # pragma: no cover - runtime dependency path
        raise RuntimeError(
            "TensorFlow is required to inspect checkpoint files. "
            "Use a .npz file or install TensorFlow to inspect a checkpoint."
        ) from exc
    return tf


def _resolve_checkpoint_path(path: str, tf):
    path = os.path.expanduser(path)
    if os.path.isdir(path):
        state_file = os.path.join(path, "checkpoint")
        if os.path.exists(state_file):
            latest = tf.compat.v1.train.latest_checkpoint(path)
            if latest:
                return latest
        candidates = sorted(glob.glob(os.path.join(path, "*.index")))
        if candidates:
            return candidates[-1][:-6]
        raise FileNotFoundError(f"No checkpoint found in directory: {path}")

    if os.path.basename(path) == "checkpoint":
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing checkpoint state file: {path}")
        latest = tf.compat.v1.train.latest_checkpoint(os.path.dirname(path))
        if latest:
            return latest
        raise FileNotFoundError(f"No latest checkpoint recorded in: {os.path.dirname(path)}")

    if path.endswith(".index"):
        path = path[:-6]
    if ".data-" in path:
        path = path.split(".data-")[0]

    if not (os.path.exists(path) or os.path.exists(path + ".index")):
        raise FileNotFoundError(f"Checkpoint prefix not found: {path}")
    return path


def _load_checkpoint_params(path: str) -> Dict[str, np.ndarray]:
    tf = _import_tensorflow()
    ckpt_path = _resolve_checkpoint_path(path, tf)
    reader = tf.compat.v1.train.NewCheckpointReader(ckpt_path)
    keys = sorted(reader.get_variable_to_shape_map().keys())
    return {k: reader.get_tensor(k) for k in keys}


def load_params(path: str) -> Dict[str, np.ndarray]:
    if path.endswith((".npz", ".npy")):
        return _load_numpy_params(path)
    return _load_checkpoint_params(path)


def _print_listing(params: Mapping[str, Any]):
    for name in sorted(params.keys()):
        value = params[name]
        shape = tuple(np.shape(value))
        dtype = getattr(value, "dtype", None)
        if dtype is not None:
            print(f"{name}\tshape={shape}\tdtype={dtype}")
        else:
            print(f"{name}\tshape={shape}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="List variables in a checkpoint or .npz file and optionally dump them to .npz."
    )
    parser.add_argument(
        "path",
        help="Checkpoint prefix / checkpoint state file / .npz / .npy to inspect",
    )
    parser.add_argument(
        "--dump-npz",
        metavar="PATH",
        help="Write the loaded variables to a .npz file",
    )
    args = parser.parse_args(argv)

    try:
        params = load_params(args.path)
    except Exception as exc:
        _eprint(f"error: {exc}")
        return 2

    _print_listing(params)

    if args.dump_npz:
        if not args.dump_npz.endswith(".npz"):
            _eprint("error: --dump-npz must end with .npz")
            return 2
        try:
            np.savez_compressed(args.dump_npz, **params)
        except Exception as exc:
            _eprint(f"error: unable to write {args.dump_npz}: {exc}")
            return 2
        print(f"wrote {args.dump_npz}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
