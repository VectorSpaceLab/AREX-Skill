#!/usr/bin/env python3
"""Run a one-frame synthetic AB3DMOT tracker smoke without dataset files.

The script imports AB3DMOT from the active Python environment, constructs a tiny
in-memory KITTI-style detection, calls AB3DMOT.track once, and reports the output
shape. It is intended for dependency/API sanity checks, not benchmark validation.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback as traceback_module
import warnings
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Optional, Sequence, Tuple


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synthetic one-frame smoke for AB3DMOT.track with no dataset files.")
    parser.add_argument("--repo-root", type=str, default=None, help="AB3DMOT checkout root; required unless the current directory contains AB3DMOT_libs")
    parser.add_argument("--toolbox-root", type=str, default=None, help="Xinshuo_PyToolbox root; required unless Xinshuo modules are already importable")
    parser.add_argument("--dataset", default="KITTI", choices=("KITTI", "nuScenes"), help="Synthetic config dataset")
    parser.add_argument("--det-name", default=None, help="Detector name; defaults to pointrcnn for KITTI and megvii for nuScenes")
    parser.add_argument("--category", default=None, help="Category; defaults to Car")
    parser.add_argument("--id-init", type=int, default=1, help="Initial track ID")
    parser.add_argument("--affi-pro", action="store_true", default=True, help="Use processed affinity output")
    parser.add_argument("--raw-affinity", dest="affi_pro", action="store_false", help="Return raw detection-by-track affinity")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--traceback", action="store_true", help="Print a Python traceback on failure")
    return parser.parse_args(argv)


def prepare_runtime(repo_root_arg: Optional[str], toolbox_root_arg: Optional[str]) -> None:
    """Put the two external source trees on sys.path before any runtime import."""
    repo_root = Path(repo_root_arg).expanduser().resolve() if repo_root_arg else Path.cwd().resolve()
    if not (repo_root / "AB3DMOT_libs").is_dir():
        raise RuntimeError(
            "missing AB3DMOT checkout: {!s} has no AB3DMOT_libs; pass --repo-root /path/to/AB3DMOT".format(repo_root)
        )
    toolbox_root = Path(toolbox_root_arg).expanduser().resolve() if toolbox_root_arg else None
    if toolbox_root is not None and not toolbox_root.is_dir():
        raise RuntimeError(
            "missing Xinshuo toolbox: {!s} does not exist; pass --toolbox-root /path/to/Xinshuo_PyToolbox".format(toolbox_root)
        )
    for path in (toolbox_root, repo_root):
        if path is not None and str(path) not in sys.path:
            sys.path.insert(0, str(path))


def import_runtime() -> Tuple[Any, Any]:
    try:
        import numpy as np  # type: ignore
        from AB3DMOT_libs.model import AB3DMOT  # type: ignore
    except ModuleNotFoundError as exc:
        missing = exc.name or str(exc)
        if missing == "AB3DMOT_libs" or missing.startswith("AB3DMOT_libs."):
            raise RuntimeError(
                "missing AB3DMOT checkout on sys.path (could not import {!r}); pass --repo-root /path/to/AB3DMOT".format(missing)
            ) from exc
        if missing.startswith("xinshuo"):
            raise RuntimeError(
                "missing Xinshuo toolbox module {!r}; clone Xinshuo_PyToolbox and pass --toolbox-root /path/to/Xinshuo_PyToolbox (or set PYTHONPATH)".format(missing)
            ) from exc
        raise RuntimeError(
            "missing Python dependency {!r}; install the AB3DMOT numeric/runtime requirements".format(missing)
        ) from exc
    except Exception as exc:
        raise RuntimeError("failed while importing AB3DMOT runtime modules: {}".format(exc)) from exc
    return np, AB3DMOT


def default_detector(dataset: str) -> str:
    return "pointrcnn" if dataset == "KITTI" else "megvii"


def image_hw(dataset: str) -> Dict[str, Tuple[int, int]]:
    if dataset == "KITTI":
        return {"image": (375, 1242), "lidar": (720, 1920)}
    return {"image": (900, 1600), "lidar": (720, 1920)}


class NullLog:
    """File-like sink for AB3DMOT print_log calls during smoke checks."""

    def write(self, _message: str) -> None:
        return None

    def flush(self) -> None:
        return None


def build_detection(np: Any) -> Dict[str, Any]:
    # dets order is raw [h, w, l, x, y, z, theta].
    dets = np.array([[1.56, 1.60, 3.80, 2.0, 1.5, 20.0, -1.57]], dtype=float)
    # info order is [alpha, type_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2, score].
    info = np.array([[-1.57, 2.0, 700.0, 170.0, 900.0, 320.0, 0.95]], dtype=float)
    return {"dets": dets, "info": info}


def run_smoke(args: argparse.Namespace) -> Dict[str, Any]:
    det_name = args.det_name or default_detector(args.dataset)
    category = args.category or "Car"
    cfg = SimpleNamespace(
        dataset=args.dataset,
        det_name=det_name,
        ego_com=False,
        vis=False,
        affi_pro=args.affi_pro,
        num_hypo=1,
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("default")
        np, AB3DMOT = import_runtime()
        tracker = AB3DMOT(
            cfg,
            category,
            calib=None,
            oxts=None,
            img_dir=None,
            vis_dir=None,
            hw=image_hw(args.dataset),
            log=NullLog(),
            ID_init=args.id_init,
        )
        results, affinity = tracker.track(build_detection(np), frame=0, seq_name="synthetic")

    if not isinstance(results, list) or len(results) != 1:
        raise RuntimeError("expected results to be a one-element list for num_hypo=1, got {!r}".format(type(results)))

    result_array = results[0]
    result_shape = tuple(int(x) for x in getattr(result_array, "shape", ()))
    affinity_shape = tuple(int(x) for x in getattr(affinity, "shape", ()))

    if result_shape != (1, 15):
        raise RuntimeError("expected one 15-column output row, got shape {}".format(result_shape))
    if args.affi_pro and affinity_shape != (0, 1):
        raise RuntimeError("expected processed first-frame affinity shape (0, 1), got {}".format(affinity_shape))
    if not args.affi_pro and affinity_shape != (1, 0):
        raise RuntimeError("expected raw first-frame affinity shape (1, 0), got {}".format(affinity_shape))

    first_row = result_array[0].tolist()
    return {
        "status": "ok",
        "dataset": args.dataset,
        "det_name": det_name,
        "category": category,
        "result_shape": list(result_shape),
        "affinity_shape": list(affinity_shape),
        "track_id": int(first_row[7]),
        "score": float(first_row[14]),
        "row_contract": "[h,w,l,x,y,z,theta,track_id,alpha,type_id,bbox_x1,bbox_y1,bbox_x2,bbox_y2,score]",
        "warnings_seen": sorted({str(item.message) for item in caught}),
    }


def print_text(report: Dict[str, Any]) -> None:
    print("AB3DMOT synthetic tracking smoke: {}".format(report["status"]))
    print("Dataset/detector/category: {}/{}/{}".format(report["dataset"], report["det_name"], report["category"]))
    print("Result shape: {}".format(tuple(report["result_shape"])))
    print("Affinity shape: {}".format(tuple(report["affinity_shape"])))
    print("Track ID: {}".format(report["track_id"]))
    print("Score: {:.3f}".format(report["score"]))
    print("Row contract: {}".format(report["row_contract"]))
    if report["warnings_seen"]:
        print("Warnings observed:")
        for warning in report["warnings_seen"]:
            print("  - {}".format(warning))


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        prepare_runtime(args.repo_root, args.toolbox_root)
        report = run_smoke(args)
    except Exception as exc:
        failure = {
            "status": "failed",
            "error": str(exc),
            "hint": "Use --repo-root /path/to/AB3DMOT and, when Xinshuo is external, --toolbox-root /path/to/Xinshuo_PyToolbox; no ambient PYTHONPATH is required.",
        }
        if args.json:
            print(json.dumps(failure, indent=2, sort_keys=True))
        else:
            print("AB3DMOT synthetic tracking smoke: failed", file=sys.stderr)
            print("error: {}".format(exc), file=sys.stderr)
            print(failure["hint"], file=sys.stderr)
        if args.traceback:
            traceback_module.print_exc()
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
