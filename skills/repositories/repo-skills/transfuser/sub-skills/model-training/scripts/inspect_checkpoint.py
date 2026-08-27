#!/usr/bin/env python3
"""Inspect a TransFuser checkpoint without loading pickle by default.

The default mode reports file/container metadata and optionally reads the JSON
training arguments file. It does not call torch.load, execute pickle globals,
allocate tensors, download anything, or alter the checkpoint. Use
``--unsafe-load`` only for a trusted checkpoint in a matching environment when
state-dict keys and tensor shapes are needed.

Examples:
  python inspect_checkpoint.py RUN/model_20.pth --args-file RUN/args.txt
  python inspect_checkpoint.py RUN/model_20.pth --unsafe-load --json report.json
"""

from __future__ import print_function

import argparse
import hashlib
import json
import os
import sys
import zipfile
from collections import Counter
from pathlib import Path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Inspect TransFuser .pth metadata safely. Pickle deserialization "
            "is disabled unless --unsafe-load is explicitly supplied."
        )
    )
    parser.add_argument("checkpoint", help="Path to model_*.pth or optimizer_*.pth")
    parser.add_argument("--args-file", help="Optional run args.txt JSON file")
    parser.add_argument("--unsafe-load", action="store_true",
                        help="Trusted-file-only torch.load(map_location=cpu) for key/shape inspection")
    parser.add_argument("--json", dest="json_path", help="Write the report to this explicit path")
    parser.add_argument("--max-keys", type=int, default=20,
                        help="Maximum example state-dict keys to print in unsafe mode")
    return parser.parse_args(argv)


def sha256(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def read_args_file(path):
    if not path:
        return None, None
    args_path = Path(path).expanduser()
    try:
        with args_path.open("r") as handle:
            value = json.load(handle)
    except Exception as exc:
        return None, "could not read args file %s: %s" % (args_path, exc)
    if not isinstance(value, dict):
        return None, "args file must contain a JSON object: %s" % args_path
    keys = ("backbone", "image_architecture", "lidar_architecture", "use_velocity",
            "n_layer", "use_target_point_image", "use_point_pillars", "setting",
            "batch_size", "start_epoch", "parallel_training")
    selected = {key: value[key] for key in keys if key in value}
    return {"path": str(args_path), "selected": selected, "all_keys": sorted(value)}, None


def zip_metadata(path):
    if not zipfile.is_zipfile(str(path)):
        return {"is_zip": False}
    try:
        with zipfile.ZipFile(str(path), "r") as archive:
            names = archive.namelist()
            return {
                "is_zip": True,
                "entries": len(names),
                "entry_examples": names[:20],
                "has_data_pickle": any(name.endswith("data.pkl") for name in names),
                "has_version": any(name.endswith("version") for name in names),
            }
    except Exception as exc:
        return {"is_zip": True, "error": str(exc)}


def tensor_shape(value):
    try:
        return list(value.shape)
    except Exception:
        return None


def extract_state_mapping(value):
    """Find a likely state mapping without assuming a particular save wrapper."""
    try:
        from collections.abc import Mapping
    except ImportError:  # pragma: no cover - Python 3.7 fallback
        from collections import Mapping
    if isinstance(value, Mapping):
        if value and all(isinstance(key, str) for key in value):
            tensor_values = sum(1 for item in value.values() if tensor_shape(item) is not None)
            if tensor_values:
                return value
        for nested_key in ("state_dict", "model", "model_state_dict"):
            if nested_key in value:
                found = extract_state_mapping(value[nested_key])
                if found is not None:
                    return found
    return None


def unsafe_state_metadata(path, max_keys):
    try:
        import torch
    except Exception as exc:
        return {"error": "torch is required for --unsafe-load: %s" % exc}
    try:
        loaded = torch.load(str(path), map_location="cpu")
    except Exception as exc:
        return {"error": "torch.load failed for trusted checkpoint: %s" % exc}
    mapping = extract_state_mapping(loaded)
    if mapping is None:
        return {
            "container_type": type(loaded).__name__,
            "state_dict_found": False,
            "warning": "loaded object is not a recognizable tensor state mapping",
        }
    keys = sorted(str(key) for key in mapping.keys())
    prefix_counts = Counter("module." if key.startswith("module.") else "plain" for key in keys)
    examples = []
    total_elements = 0
    for key in keys[:max(0, max_keys)]:
        value = mapping.get(key)
        shape = tensor_shape(value)
        item = {"key": key, "shape": shape}
        if shape is not None:
            count = 1
            for dimension in shape:
                count *= int(dimension)
            item["numel"] = count
            total_elements += count
        examples.append(item)
    return {
        "container_type": type(loaded).__name__,
        "state_dict_found": True,
        "key_count": len(keys),
        "prefix_counts": dict(prefix_counts),
        "example_keys": examples,
        "example_numel_sum": total_elements,
    }


def make_report(args):
    path = Path(args.checkpoint).expanduser()
    report = {
        "schema": "transfuser.checkpoint-inspection.v1",
        "checkpoint": str(path),
        "unsafe_load_requested": bool(args.unsafe_load),
    }
    if not path.exists():
        report["error"] = "checkpoint does not exist"
        return report
    if not path.is_file():
        report["error"] = "checkpoint is not a regular file"
        return report
    report["file"] = {
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "suffix": path.suffix,
    }
    report["container"] = zip_metadata(path)

    args_info, args_error = read_args_file(args.args_file)
    if args_error:
        report["args_error"] = args_error
    elif args_info:
        report["training_args"] = args_info

    if args.unsafe_load:
        print("WARNING: --unsafe-load enables pickle deserialization; use only with a trusted file")
        report["unsafe_state"] = unsafe_state_metadata(path, args.max_keys)
    else:
        report["safe_mode"] = {
            "torch_load_called": False,
            "message": "container metadata only; tensor keys/shapes were not deserialized",
        }
    return report


def main(argv=None):
    args = parse_args(argv)
    report = make_report(args)
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.json_path:
        output = Path(args.json_path).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
        print("WROTE: %s" % output)
    return 0 if "error" not in report else 1


if __name__ == "__main__":
    sys.exit(main())
