#!/usr/bin/env python3
"""Validate EdgeConnect evaluation inputs before computing pixel metrics or FID.

The helper has two subcommands:
- `pixel`: check that ground-truth and prediction directories line up by basename.
- `fid`: check image directories or cached `mu`/`sigma` statistics files.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def list_images(directory):
    return [path for path in sorted(directory.iterdir()) if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES]


def load_npz_stats(path):
    try:
        with np.load(str(path), allow_pickle=False) as data:
            keys = sorted(data.files)
            has_mu = "mu" in data.files
            has_sigma = "sigma" in data.files
            return {
                "type": "npz",
                "path": str(path),
                "keys": keys,
                "has_mu": has_mu,
                "has_sigma": has_sigma,
                "ok": has_mu and has_sigma,
            }
    except Exception as exc:
        return {"type": "npz", "path": str(path), "ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def pixel_report(data_path, output_path):
    gt_dir = Path(data_path).expanduser().resolve()
    pred_dir = Path(output_path).expanduser().resolve()

    report = {
        "mode": "pixel",
        "ground_truth_dir": str(gt_dir),
        "prediction_dir": str(pred_dir),
        "ground_truth_count": 0,
        "prediction_count": 0,
        "missing_predictions": [],
        "extra_predictions": [],
        "warnings": [],
        "ok": False,
    }

    if not gt_dir.exists() or not gt_dir.is_dir():
        report["error"] = "ground-truth directory does not exist or is not a directory"
        return report
    if not pred_dir.exists() or not pred_dir.is_dir():
        report["error"] = "prediction directory does not exist or is not a directory"
        return report

    gt_files = list_images(gt_dir)
    pred_files = list_images(pred_dir)
    report["ground_truth_count"] = len(gt_files)
    report["prediction_count"] = len(pred_files)

    pred_map = {}
    duplicates = []
    for path in pred_files:
        if path.name in pred_map:
            duplicates.append(path.name)
        pred_map[path.name] = path
    if duplicates:
        report["error"] = "duplicate prediction basenames: %s" % ", ".join(sorted(set(duplicates)))
        return report

    missing = []
    extras = set(pred_map)
    for gt_path in gt_files:
        if gt_path.name not in pred_map:
            missing.append(gt_path.name)
        else:
            extras.discard(gt_path.name)

    report["missing_predictions"] = missing
    report["extra_predictions"] = sorted(extras)
    if missing:
        report["error"] = "missing prediction(s) for: %s" % ", ".join(missing)
        return report
    if not gt_files:
        report["error"] = "ground-truth directory has no top-level image files"
        return report
    if not pred_files:
        report["error"] = "prediction directory has no top-level image files"
        return report
    if extras:
        report["warnings"].append("ignored %d extra prediction image(s): %s" % (len(extras), ", ".join(sorted(extras))))

    report["ok"] = True
    return report


def fid_report(path_a, path_b):
    first = Path(path_a).expanduser().resolve()
    second = Path(path_b).expanduser().resolve()

    report = {
        "mode": "fid",
        "paths": [str(first), str(second)],
        "items": [],
        "warnings": [],
        "ok": False,
    }

    for path in [first, second]:
        item = {"path": str(path)}
        if path.is_dir():
            images = list_images(path)
            item.update({"type": "directory", "count": len(images)})
            if not path.exists() or not path.is_dir():
                item["error"] = "path does not exist or is not a directory"
            elif not images:
                item["error"] = "directory has no top-level image files"
        elif path.is_file() and path.suffix.lower() == ".npz":
            item.update(load_npz_stats(path))
            if not item.get("ok"):
                item.setdefault("error", "npz statistics file is not a valid FID archive")
        else:
            item["error"] = "expected a directory of images or a .npz statistics file"
        report["items"].append(item)

    errors = [item.get("error") for item in report["items"] if item.get("error")]
    if errors:
        report["error"] = "; ".join(errors)
        return report

    counts = [item.get("count") for item in report["items"] if item.get("type") == "directory"]
    if counts and min(counts) < 2:
        report["warnings"].append("FID is possible with one image, but very small sample counts make the score unstable")

    report["ok"] = True
    return report


def build_parser():
    parser = argparse.ArgumentParser(description="Validate EdgeConnect evaluation inputs before scoring.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    pixel = subparsers.add_parser("pixel", help="check paired ground-truth and prediction directories")
    pixel.add_argument("--data-path", required=True, help="ground-truth image directory")
    pixel.add_argument("--output-path", required=True, help="prediction image directory")
    pixel.add_argument("--json", action="store_true", help="print the report as JSON")

    fid = subparsers.add_parser("fid", help="check two FID inputs: directories or cached npz stats")
    fid.add_argument("--paths", nargs=2, required=True, metavar=("REAL", "FAKE"), help="two image directories or .npz statistics files")
    fid.add_argument("--json", action="store_true", help="print the report as JSON")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.mode == "pixel":
        report = pixel_report(args.data_path, args.output_path)
    else:
        report = fid_report(args.paths[0], args.paths[1])

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        if report["mode"] == "pixel":
            print("Pixel input check")
            print("ground_truth_dir: %s" % report["ground_truth_dir"])
            print("prediction_dir: %s" % report["prediction_dir"])
            print("ground_truth_count: %d" % report["ground_truth_count"])
            print("prediction_count: %d" % report["prediction_count"])
            if report["warnings"]:
                for warning in report["warnings"]:
                    print("warning: %s" % warning)
        else:
            print("FID input check")
            for item in report["items"]:
                print("path: %s" % item["path"])
                if item.get("type") == "directory":
                    print("  type: directory")
                    print("  count: %d" % item.get("count", 0))
                else:
                    print("  type: npz")
                    print("  keys: %s" % ", ".join(item.get("keys", [])))
                    print("  has_mu: %s" % item.get("has_mu"))
                    print("  has_sigma: %s" % item.get("has_sigma"))
                if item.get("error"):
                    print("  error: %s" % item["error"])
            if report["warnings"]:
                for warning in report["warnings"]:
                    print("warning: %s" % warning)

        if report.get("error"):
            print("error: %s" % report["error"], file=sys.stderr)
            return 1
        print("status: ok")

    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
