#!/usr/bin/env python3
"""Validate Pascal VOC-style mAP file formats with an isolated tiny fixture.

This helper does not import TensorFlow, does not depend on the source checkout's
mAP directory, and only uses the Python standard library.

It exercises three cases:
- perfect: one ground-truth box, one matching prediction, expected mAP = 1.0
- class-mismatch: same box geometry, wrong predicted class, expected mAP = 0.0
- missing-predicted: a ground-truth file without a predicted counterpart, expected failure
"""

from __future__ import annotations

import argparse
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

IOU_THRESHOLD = 0.5


class FixtureError(RuntimeError):
    """Raised when a synthetic fixture violates the expected contract."""


@dataclass
class GTBox:
    class_name: str
    left: float
    top: float
    right: float
    bottom: float
    difficult: bool = False
    used: bool = False


@dataclass
class PredBox:
    class_name: str
    score: float
    left: float
    top: float
    right: float
    bottom: float


@dataclass
class CaseResult:
    name: str
    map_score: Optional[float]
    ap_by_class: Dict[str, float]
    expected: Optional[float] = None
    expected_failure: bool = False
    failure_message: Optional[str] = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Pascal VOC-style mAP file formats with a tiny isolated fixture.",
    )
    parser.add_argument(
        "--case",
        choices=("all", "perfect", "class-mismatch", "missing-predicted"),
        default="all",
        help="Which synthetic case to run.",
    )
    return parser.parse_args()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_fixture(root: Path, case: str) -> None:
    gt_dir = root / "ground-truth"
    pred_dir = root / "predicted"
    gt_dir.mkdir(parents=True, exist_ok=True)
    pred_dir.mkdir(parents=True, exist_ok=True)

    if case == "perfect":
        write_text(gt_dir / "000001.txt", "cat 10 10 20 20\n")
        write_text(pred_dir / "000001.txt", "cat 0.9900 10 10 20 20\n")
    elif case == "class-mismatch":
        write_text(gt_dir / "000001.txt", "cat 10 10 20 20\n")
        write_text(pred_dir / "000001.txt", "dog 0.9900 10 10 20 20\n")
    elif case == "missing-predicted":
        write_text(gt_dir / "000001.txt", "cat 10 10 20 20\n")
        write_text(pred_dir / "000002.txt", "cat 0.9900 10 10 20 20\n")
    else:
        raise FixtureError(f"unknown fixture case: {case}")


def parse_gt_line(line: str, path: Path) -> GTBox:
    parts = line.split()
    if len(parts) not in (5, 6):
        raise FixtureError(
            f"ground-truth file {path.name} has wrong format: expected 5 fields or 6 with difficult, got {len(parts)}"
        )
    class_name, left, top, right, bottom = parts[:5]
    difficult = len(parts) == 6
    if difficult and parts[5] != "difficult":
        raise FixtureError(f"ground-truth file {path.name} has unsupported trailing token: {parts[5]}")
    try:
        return GTBox(
            class_name=class_name,
            left=float(left),
            top=float(top),
            right=float(right),
            bottom=float(bottom),
            difficult=difficult,
        )
    except ValueError as exc:
        raise FixtureError(f"ground-truth file {path.name} has non-numeric coordinates: {line}") from exc


def parse_pred_line(line: str, path: Path) -> PredBox:
    parts = line.split()
    if len(parts) != 6:
        raise FixtureError(
            f"predicted file {path.name} has wrong format: expected 6 fields, got {len(parts)}"
        )
    class_name, score, left, top, right, bottom = parts
    try:
        return PredBox(
            class_name=class_name,
            score=float(score),
            left=float(left),
            top=float(top),
            right=float(right),
            bottom=float(bottom),
        )
    except ValueError as exc:
        raise FixtureError(f"predicted file {path.name} has non-numeric score or coordinates: {line}") from exc


def read_gt_files(gt_dir: Path) -> Dict[str, List[GTBox]]:
    files = sorted(gt_dir.glob("*.txt"))
    if not files:
        raise FixtureError("no ground-truth files found")
    parsed: Dict[str, List[GTBox]] = {}
    for path in files:
        boxes: List[GTBox] = []
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            boxes.append(parse_gt_line(line, path))
        parsed[path.stem] = boxes
    return parsed


def read_pred_files(pred_dir: Path) -> Dict[str, List[PredBox]]:
    files = sorted(pred_dir.glob("*.txt"))
    if not files:
        raise FixtureError("no predicted files found")
    parsed: Dict[str, List[PredBox]] = {}
    for path in files:
        boxes: List[PredBox] = []
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            boxes.append(parse_pred_line(line, path))
        parsed[path.stem] = boxes
    return parsed


def pair_stems(gt: Dict[str, List[GTBox]], pred: Dict[str, List[PredBox]]) -> List[str]:
    gt_stems = set(gt)
    pred_stems = set(pred)
    missing_pred = sorted(gt_stems - pred_stems)
    missing_gt = sorted(pred_stems - gt_stems)
    if missing_pred:
        raise FixtureError(f"missing predicted counterpart for: {', '.join(missing_pred)}")
    if missing_gt:
        raise FixtureError(f"missing ground-truth counterpart for: {', '.join(missing_gt)}")
    return sorted(gt_stems)


def iou(box_a: Sequence[float], box_b: Sequence[float]) -> float:
    left = max(box_a[0], box_b[0])
    top = max(box_a[1], box_b[1])
    right = min(box_a[2], box_b[2])
    bottom = min(box_a[3], box_b[3])
    inter_w = right - left + 1.0
    inter_h = bottom - top + 1.0
    if inter_w <= 0.0 or inter_h <= 0.0:
        return 0.0
    inter = inter_w * inter_h
    area_a = (box_a[2] - box_a[0] + 1.0) * (box_a[3] - box_a[1] + 1.0)
    area_b = (box_b[2] - box_b[0] + 1.0) * (box_b[3] - box_b[1] + 1.0)
    return inter / (area_a + area_b - inter)


def voc_ap(rec: List[float], prec: List[float]) -> float:
    rec = [0.0] + rec + [1.0]
    prec = [0.0] + prec + [0.0]
    for idx in range(len(prec) - 2, -1, -1):
        prec[idx] = max(prec[idx], prec[idx + 1])
    ap = 0.0
    for idx in range(1, len(rec)):
        if rec[idx] != rec[idx - 1]:
            ap += (rec[idx] - rec[idx - 1]) * prec[idx]
    return ap


def evaluate_fixture(root: Path) -> CaseResult:
    gt_dir = root / "ground-truth"
    pred_dir = root / "predicted"
    gt = read_gt_files(gt_dir)
    pred = read_pred_files(pred_dir)
    stems = pair_stems(gt, pred)

    gt_classes = sorted({box.class_name for boxes in gt.values() for box in boxes if not box.difficult})
    if not gt_classes:
        raise FixtureError("no evaluable ground-truth classes found")

    ap_by_class: Dict[str, float] = {}
    for class_name in gt_classes:
        class_gt: Dict[str, List[GTBox]] = {
            stem: [box for box in gt[stem] if box.class_name == class_name]
            for stem in stems
        }
        predictions: List[Tuple[str, PredBox]] = []
        for stem in stems:
            for box in pred[stem]:
                if box.class_name == class_name:
                    predictions.append((stem, box))
        predictions.sort(key=lambda item: item[1].score, reverse=True)

        total_gt = sum(len(boxes) for boxes in class_gt.values())
        tp: List[int] = []
        fp: List[int] = []
        for stem, pred_box in predictions:
            candidate_gt = class_gt[stem]
            best_iou = -1.0
            best_box: Optional[GTBox] = None
            for gt_box in candidate_gt:
                if gt_box.difficult or gt_box.used:
                    continue
                current_iou = iou(
                    (pred_box.left, pred_box.top, pred_box.right, pred_box.bottom),
                    (gt_box.left, gt_box.top, gt_box.right, gt_box.bottom),
                )
                if current_iou > best_iou:
                    best_iou = current_iou
                    best_box = gt_box
            if best_box is not None and best_iou >= IOU_THRESHOLD:
                best_box.used = True
                tp.append(1)
                fp.append(0)
            else:
                tp.append(0)
                fp.append(1)

        cumsum_tp = 0
        cumsum_fp = 0
        rec: List[float] = []
        prec: List[float] = []
        for tp_val, fp_val in zip(tp, fp):
            cumsum_tp += tp_val
            cumsum_fp += fp_val
            rec.append(cumsum_tp / total_gt if total_gt else 0.0)
            denom = cumsum_tp + cumsum_fp
            prec.append(cumsum_tp / denom if denom else 0.0)

        ap_by_class[class_name] = voc_ap(rec, prec)

    map_score = sum(ap_by_class.values()) / len(ap_by_class)
    return CaseResult(name="", map_score=map_score, ap_by_class=ap_by_class)


def run_case(case: str) -> CaseResult:
    with tempfile.TemporaryDirectory(prefix=f"map_fixture_{case}_") as tmpdir:
        root = Path(tmpdir)
        build_fixture(root, case)
        if case == "missing-predicted":
            try:
                evaluate_fixture(root)
            except FixtureError as exc:
                return CaseResult(
                    name=case,
                    map_score=None,
                    ap_by_class={},
                    expected_failure=True,
                    failure_message=str(exc),
                )
            raise FixtureError("missing-predicted case unexpectedly passed")

        result = evaluate_fixture(root)
        result.name = case
        result.expected = 1.0 if case == "perfect" else 0.0
        if not math.isclose(result.map_score or 0.0, result.expected, abs_tol=1e-6):
            raise FixtureError(
                f"{case} case expected mAP {result.expected:.4f} but got {result.map_score:.4f}"
            )
        return result


def print_case_result(result: CaseResult) -> None:
    if result.expected_failure:
        print(f"{result.name}: expected failure ({result.failure_message})")
        return
    ap_list = ", ".join(f"{cls}={score:.4f}" for cls, score in sorted(result.ap_by_class.items()))
    print(f"{result.name}: mAP={result.map_score:.4f} [{ap_list}]")


def main() -> int:
    args = parse_args()
    cases = [args.case] if args.case != "all" else ["perfect", "class-mismatch", "missing-predicted"]
    for case in cases:
        result = run_case(case)
        print_case_result(result)
    print("map_fixture_check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
