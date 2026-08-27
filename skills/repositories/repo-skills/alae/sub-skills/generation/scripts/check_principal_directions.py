#!/usr/bin/env python3
"""Safe checker for ALAE principal direction files.

This script verifies expected direction_*.npy filenames and can optionally inspect
array shapes with NumPy. It does not import ALAE modules, load checkpoints, use
CUDA, start a GUI, train, or download anything.
"""

from __future__ import print_function

import argparse
import json
import sys
from pathlib import Path

DEFAULT_DIRECTIONS = [0, 1, 2, 3, 4, 10, 11, 17, 19]
DIRECTION_LABELS = {
    0: "gender",
    1: "smile/smiling",
    2: "attractive",
    3: "wavy-hair",
    4: "young",
    10: "big-lips",
    11: "big-nose",
    17: "chubby",
    19: "glasses/eyeglasses",
}


def parse_indices(text):
    if text.strip().lower() in ("default", "committed"):
        return list(DEFAULT_DIRECTIONS)
    result = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            result.append(int(part))
        except ValueError:
            raise argparse.ArgumentTypeError("indices must be comma-separated integers")
    if not result:
        raise argparse.ArgumentTypeError("at least one direction index is required")
    return result


def resolve_under_repo(repo_root, value):
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def add_result(results, level, check, message, path=None, detail=None):
    item = {"level": level, "check": check, "message": message}
    if path is not None:
        item["path"] = str(path)
    if detail is not None:
        item["detail"] = detail
    results.append(item)


def load_numpy(results):
    try:
        import numpy as np  # noqa: F401
        return np
    except Exception as exc:  # pragma: no cover - depends on user environment
        add_result(results, "ERROR", "numpy", "NumPy is required for --inspect-shapes but could not be imported", detail=str(exc))
        return None


def inspect_shape(np, path, expected_dim):
    array = np.load(str(path), allow_pickle=False)
    shape = tuple(int(v) for v in array.shape)
    detail = {"shape": shape, "dtype": str(array.dtype)}
    if expected_dim > 0:
        detail["expected_dim"] = expected_dim
        if len(shape) != 1 or shape[0] != expected_dim:
            return "WARN", detail
    return "OK", detail


def print_results(results, as_json):
    if as_json:
        print(json.dumps(results, indent=2, sort_keys=True))
        return
    width = max([len(item["level"]) for item in results] + [5])
    for item in results:
        path_suffix = ""
        if "path" in item:
            path_suffix = " | " + item["path"]
        detail_suffix = ""
        if "detail" in item:
            detail_suffix = " | " + json.dumps(item["detail"], sort_keys=True)
        print("{level:<{width}} {check}: {message}{path_suffix}{detail_suffix}".format(width=width, path_suffix=path_suffix, detail_suffix=detail_suffix, **item))


def build_parser():
    parser = argparse.ArgumentParser(
        description="Safely check ALAE principal_directions/direction_*.npy files and optional NumPy shapes."
    )
    parser.add_argument("--repo-root", default=".", help="ALAE checkout root to inspect (default: current directory).")
    parser.add_argument("--directions-dir", default="principal_directions", help="Directory containing direction_*.npy files, relative to repo root unless absolute.")
    parser.add_argument("--indices", type=parse_indices, default=list(DEFAULT_DIRECTIONS), help="Comma-separated direction indices to check, or 'default' (default: committed FFHQ set).")
    parser.add_argument("--inspect-shapes", action="store_true", help="Import NumPy and inspect array shape/dtype for each present .npy file.")
    parser.add_argument("--expected-dim", type=int, default=512, help="Expected one-dimensional vector length when inspecting shapes; use 0 to disable shape warnings (default: 512).")
    parser.add_argument("--check-intermediates", action="store_true", help="Also report whether wspace_att_<idx>.npy intermediate files exist.")
    parser.add_argument("--warn-extra", action="store_true", help="Warn if direction_*.npy files exist for indices outside --indices.")
    parser.add_argument("--soft", action="store_true", help="Always exit 0 after reporting findings.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve()
    results = []

    if not repo_root.is_dir():
        add_result(results, "ERROR", "repo-root", "Repository root is not an existing directory", repo_root)
        print_results(results, args.json)
        return 0 if args.soft else 1

    directions_dir = resolve_under_repo(repo_root, args.directions_dir)
    if not directions_dir.is_dir():
        add_result(results, "ERROR", "directions", "Principal-directions directory is missing", directions_dir)
        print_results(results, args.json)
        return 0 if args.soft else 1

    np = load_numpy(results) if args.inspect_shapes else None
    expected_indices = list(args.indices)
    for index in expected_indices:
        label = DIRECTION_LABELS.get(index, "attribute-%d" % index)
        path = directions_dir / ("direction_%d.npy" % index)
        if not path.is_file():
            add_result(results, "ERROR", "direction", "Missing expected direction file", path, {"index": index, "label": label})
            continue
        add_result(results, "OK", "direction", "Direction file exists", path, {"index": index, "label": label})
        if args.inspect_shapes and np is not None:
            try:
                level, detail = inspect_shape(np, path, args.expected_dim)
                if level == "OK":
                    add_result(results, "OK", "shape", "Direction vector shape is compatible", path, detail)
                else:
                    add_result(results, "WARN", "shape", "Direction vector shape differs from expected FFHQ latent size", path, detail)
            except Exception as exc:  # pragma: no cover - depends on user files
                add_result(results, "ERROR", "shape", "Could not load direction array with NumPy", path, str(exc))

        if args.check_intermediates:
            intermediate = directions_dir / ("wspace_att_%d.npy" % index)
            if intermediate.is_file():
                add_result(results, "OK", "intermediate", "Regeneration intermediate exists", intermediate, {"index": index})
            else:
                add_result(results, "WARN", "intermediate", "Regeneration intermediate is absent; this is normal when only using committed directions", intermediate, {"index": index})

    if args.warn_extra:
        expected_set = set(expected_indices)
        extras = []
        for path in directions_dir.glob("direction_*.npy"):
            stem = path.stem.replace("direction_", "", 1)
            try:
                index = int(stem)
            except ValueError:
                continue
            if index not in expected_set:
                extras.append(index)
        if extras:
            add_result(results, "WARN", "extra", "Additional direction files are present", directions_dir, {"extra_indices": sorted(extras)})
        else:
            add_result(results, "OK", "extra", "No additional direction files outside expected set", directions_dir)

    print_results(results, args.json)
    if args.soft:
        return 0
    has_error = any(item["level"] == "ERROR" for item in results)
    has_warning = any(item["level"] == "WARN" for item in results)
    if has_error or (args.strict and has_warning):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
