#!/usr/bin/env python3
"""Safe API smoke test for a user-provided Object-Detection-Metrics checkout.

The legacy repository is source-style rather than pip-installable. This helper
accepts either --repo-root PATH, where PATH/lib contains BoundingBox.py, or
--lib-dir PATH pointing directly at a copied lib directory. It imports the
source classes, builds tiny in-memory detections/ground truths, computes VOC AP,
and prints AP/TP/FP expectations. It performs no network access, GUI display,
image writes, or destructive filesystem actions.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path
from typing import Any, Iterable


EXPECTED_BY_CASE = {
    "perfect": {"ap": 1.0, "tp": 1, "fp": 0, "positives": 1},
    "duplicate": {"ap": 1.0, "tp": 1, "fp": 1, "positives": 1},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import Object-Detection-Metrics source-style API classes from a "
            "user-provided checkout/copy and run a tiny in-memory AP smoke test."
        )
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--repo-root",
        type=Path,
        help="Path to a checkout/copy whose lib/ directory contains BoundingBox.py.",
    )
    source.add_argument(
        "--lib-dir",
        type=Path,
        help="Path directly to the copied lib directory containing BoundingBox.py.",
    )
    parser.add_argument(
        "--ap-method",
        choices=("every-point", "eleven-point"),
        default="every-point",
        help="AP interpolation enum to route into Evaluator.GetPascalVOCMetrics.",
    )
    parser.add_argument(
        "--case",
        choices=("perfect", "duplicate"),
        default="perfect",
        help="Synthetic in-memory case: perfect has 1 TP/0 FP; duplicate has 1 TP/1 FP.",
    )
    parser.add_argument(
        "--iou-threshold",
        type=float,
        default=0.5,
        help="IoU threshold for the synthetic smoke test (default: 0.5).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only the final PASS/FAIL line and errors.",
    )
    return parser.parse_args()


def candidate_lib_dir(args: argparse.Namespace) -> Path | None:
    if args.lib_dir is not None:
        return args.lib_dir.expanduser().resolve()
    if args.repo_root is not None:
        return (args.repo_root.expanduser().resolve() / "lib")
    return None


def print_no_source_guidance() -> None:
    print("No --repo-root or --lib-dir was supplied; source modules were not imported.")
    print("Provide a checkout/copy with one of:")
    print("  python scripts/api_metric_smoke.py --repo-root PATH")
    print("  python scripts/api_metric_smoke.py --lib-dir PATH_TO_LIB")
    print("Running a formula-only duplicate-detection sanity check instead.")
    ap, tp, fp = formula_only_duplicate_case()
    print(f"FORMULA_ONLY duplicate case: AP={ap:.6f} total_TP={tp} total_FP={fp}")
    print("This confirms the expected duplicate-detection interpretation, not the source API import.")


def formula_only_duplicate_case() -> tuple[float, int, int]:
    """Duplicate-detection sanity check mirroring the AP interpretation.

    One GT, one highest-confidence true positive, and one lower-confidence
    duplicate false positive yields recall [1, 1], precision [1, 0.5]. The VOC
    every-point precision envelope integrates to AP 1.0 while FP remains 1.
    """
    recall = [1.0, 1.0]
    precision = [1.0, 0.5]
    mrec = [0.0] + recall + [1.0]
    mpre = [0.0] + precision + [0.0]
    for idx in range(len(mpre) - 1, 0, -1):
        mpre[idx - 1] = max(mpre[idx - 1], mpre[idx])
    ap = 0.0
    for idx in range(len(mrec) - 1):
        if mrec[idx + 1] != mrec[idx]:
            ap += (mrec[idx + 1] - mrec[idx]) * mpre[idx + 1]
    return ap, 1, 1


def import_source_api(lib_dir: Path) -> dict[str, Any]:
    if not lib_dir.exists() or not lib_dir.is_dir():
        raise FileNotFoundError(f"lib directory does not exist: {lib_dir}")
    required = ["BoundingBox.py", "BoundingBoxes.py", "Evaluator.py", "utils.py"]
    missing = [name for name in required if not (lib_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"missing expected source files in lib directory: {', '.join(missing)}")

    os.environ.setdefault("MPLBACKEND", "Agg")
    sys.path.insert(0, str(lib_dir))
    try:
        from BoundingBox import BoundingBox  # type: ignore
        from BoundingBoxes import BoundingBoxes  # type: ignore
        from Evaluator import Evaluator  # type: ignore
        from utils import BBFormat, BBType, CoordinatesType, MethodAveragePrecision  # type: ignore
    except ImportError as exc:  # includes missing cv2 from utils.py
        explain_import_error(exc)
        raise

    return {
        "BoundingBox": BoundingBox,
        "BoundingBoxes": BoundingBoxes,
        "Evaluator": Evaluator,
        "BBFormat": BBFormat,
        "BBType": BBType,
        "CoordinatesType": CoordinatesType,
        "MethodAveragePrecision": MethodAveragePrecision,
    }


def explain_import_error(exc: ImportError) -> None:
    message = str(exc)
    print(f"IMPORT_ERROR: {message}", file=sys.stderr)
    if "cv2" in message:
        print(
            "Hint: utils.py imports cv2 at import time. Install opencv-python-headless "
            "for non-GUI environments or opencv-python where GUI support is required.",
            file=sys.stderr,
        )
    else:
        print(
            "Hint: this repository is source-style. Pass --repo-root PATH containing lib/ "
            "or --lib-dir PATH pointing directly at the lib directory; the lib directory "
            "itself must be on sys.path.",
            file=sys.stderr,
        )


def enum_for_method(api: dict[str, Any], method_name: str) -> Any:
    enum_cls = api["MethodAveragePrecision"]
    if method_name == "every-point":
        method = enum_cls.EveryPointInterpolation
    elif method_name == "eleven-point":
        method = enum_cls.ElevenPointInterpolation
    else:  # argparse prevents this
        raise ValueError(f"unsupported AP method: {method_name}")
    if method not in (enum_cls.EveryPointInterpolation, enum_cls.ElevenPointInterpolation):
        raise AssertionError("AP method enum routing failed")
    return method


def build_boxes(api: dict[str, Any], case_name: str) -> Any:
    BoundingBox = api["BoundingBox"]
    BoundingBoxes = api["BoundingBoxes"]
    BBFormat = api["BBFormat"]
    BBType = api["BBType"]
    CoordinatesType = api["CoordinatesType"]

    boxes = BoundingBoxes()
    boxes.addBoundingBox(
        BoundingBox(
            "img-1",
            "person",
            10,
            10,
            50,
            50,
            CoordinatesType.Absolute,
            bbType=BBType.GroundTruth,
            format=BBFormat.XYX2Y2,
        )
    )
    boxes.addBoundingBox(
        BoundingBox(
            "img-1",
            "person",
            10,
            10,
            50,
            50,
            CoordinatesType.Absolute,
            bbType=BBType.Detected,
            classConfidence=0.99,
            format=BBFormat.XYX2Y2,
        )
    )
    if case_name == "duplicate":
        boxes.addBoundingBox(
            BoundingBox(
                "img-1",
                "person",
                10,
                10,
                50,
                50,
                CoordinatesType.Absolute,
                bbType=BBType.Detected,
                classConfidence=0.50,
                format=BBFormat.XYX2Y2,
            )
        )
    return boxes


def to_plain_list(value: Any) -> list[float]:
    if hasattr(value, "tolist"):
        value = value.tolist()
    return [float(v) for v in value]


def run_source_smoke(api: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    Evaluator = api["Evaluator"]
    method = enum_for_method(api, args.ap_method)
    boxes = build_boxes(api, args.case)
    results = Evaluator().GetPascalVOCMetrics(
        boxes,
        IOUThreshold=args.iou_threshold,
        method=method,
    )
    if len(results) != 1:
        raise AssertionError(f"expected one class result, received {len(results)}")
    result = results[0]
    expected = EXPECTED_BY_CASE[args.case]
    ap = float(result["AP"])
    tp = int(result["total TP"])
    fp = int(result["total FP"])
    positives = int(result["total positives"])
    if result["class"] != "person":
        raise AssertionError(f"expected class 'person', received {result['class']!r}")
    if not math.isclose(ap, expected["ap"], rel_tol=1e-12, abs_tol=1e-12):
        raise AssertionError(f"expected AP {expected['ap']}, received {ap}")
    if (tp, fp, positives) != (expected["tp"], expected["fp"], expected["positives"]):
        raise AssertionError(
            f"expected TP/FP/positives {(expected['tp'], expected['fp'], expected['positives'])}, "
            f"received {(tp, fp, positives)}"
        )
    return {
        "class": result["class"],
        "ap": ap,
        "tp": tp,
        "fp": fp,
        "positives": positives,
        "precision": to_plain_list(result["precision"]),
        "recall": to_plain_list(result["recall"]),
        "method_enum": str(method),
    }


def explain_runtime_error(exc: BaseException) -> None:
    message = str(exc)
    print(f"ERROR: {message}", file=sys.stderr)
    if isinstance(exc, OSError) and "imgSize" in message:
        print(
            "Hint: typeCoordinates=CoordinatesType.Relative requires imgSize=(width, height).",
            file=sys.stderr,
        )
    if isinstance(exc, OSError) and "classConfidence" in message:
        print(
            "Hint: bbType=BBType.Detected requires classConfidence=<float confidence>.",
            file=sys.stderr,
        )
    if "relative coordinates" in message and "XYWH" in message:
        print(
            "Hint: relative coordinates use normalized center x/y and width/height with BBFormat.XYWH.",
            file=sys.stderr,
        )
    if "cv2" in message:
        print(
            "Hint: install opencv-python-headless for non-GUI import/drawing support.",
            file=sys.stderr,
        )


def main() -> int:
    args = parse_args()
    lib_dir = candidate_lib_dir(args)
    if lib_dir is None:
        print_no_source_guidance()
        return 0

    try:
        api = import_source_api(lib_dir)
        summary = run_source_smoke(api, args)
    except (ImportError, FileNotFoundError, OSError, AssertionError, ValueError) as exc:
        if not isinstance(exc, ImportError):
            explain_runtime_error(exc)
        return 1

    if not args.quiet:
        print(f"Imported source API from: {lib_dir}")
        print(f"AP method routed to enum: {summary['method_enum']}")
        print(f"Synthetic case: {args.case}")
        print(f"Precision: {summary['precision']}")
        print(f"Recall: {summary['recall']}")
        print(
            "Expected and observed: "
            f"class={summary['class']} AP={summary['ap']:.6f} "
            f"total_positives={summary['positives']} total_TP={summary['tp']} total_FP={summary['fp']}"
        )
    print("PASS api_metric_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
