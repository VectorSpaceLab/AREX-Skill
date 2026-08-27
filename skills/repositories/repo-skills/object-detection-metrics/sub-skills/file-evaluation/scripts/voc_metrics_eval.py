#!/usr/bin/env python3
"""Self-contained PASCAL VOC AP/mAP evaluator for text-folder detections.

This helper evaluates ground-truth and detection ``.txt`` folders using the
legacy Object-Detection-Metrics PASCAL VOC semantics without importing the
source checkout, opening plots, prompting, deleting directories, using the
network, or touching credentials. It writes only the explicitly requested
output files and otherwise prints a text summary to stdout.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Box:
    """One ground-truth or detection box in absolute XYX2Y2 coordinates."""

    image_id: str
    class_id: str
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: Optional[float] = None

    @property
    def coords(self) -> Tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2, self.y2)


class EvaluationError(ValueError):
    """Raised for invalid user input that should exit with a clear message."""


def parse_img_size(value: Optional[str]) -> Optional[Tuple[int, int]]:
    if value is None:
        return None
    cleaned = value.strip().replace("(", "").replace(")", "")
    pieces = [p.strip() for p in cleaned.split(",")]
    if len(pieces) != 2 or not pieces[0] or not pieces[1]:
        raise EvaluationError("--img-size must use WIDTH,HEIGHT, for example 600,400")
    try:
        width = int(pieces[0])
        height = int(pieces[1])
    except ValueError as exc:
        raise EvaluationError("--img-size values must be integers, for example 600,400") from exc
    if width <= 0 or height <= 0:
        raise EvaluationError("--img-size WIDTH and HEIGHT must be positive integers")
    return (width, height)


def as_float(token: str, *, path: Path, line_no: int, field: str) -> float:
    try:
        value = float(token)
    except ValueError as exc:
        raise EvaluationError(f"{path}:{line_no}: {field} must be numeric, got {token!r}") from exc
    if not math.isfinite(value):
        raise EvaluationError(f"{path}:{line_no}: {field} must be finite, got {token!r}")
    return value


def convert_relative_to_absolute(
    size: Tuple[int, int], values: Tuple[float, float, float, float]
) -> Tuple[float, float, float, float]:
    """Convert YOLO-style relative center-x, center-y, width, height to XYX2Y2.

    Mirrors ``utils.convertToAbsoluteValues`` from the source project:
    x1/y1 are rounded from the relative center and extent, x2/y2 add rounded
    width/height, and the resulting box is clipped to the image bounds.
    """

    width, height = size
    cx, cy, box_w, box_h = values
    x1 = round(((2 * float(cx) - float(box_w)) * width / 2))
    y1 = round(((2 * float(cy) - float(box_h)) * height / 2))
    x2 = x1 + round(float(box_w) * width)
    y2 = y1 + round(float(box_h) * height)
    if x1 < 0:
        x1 = 0
    if y1 < 0:
        y1 = 0
    if x2 >= width:
        x2 = width - 1
    if y2 >= height:
        y2 = height - 1
    return (float(x1), float(y1), float(x2), float(y2))


def to_absolute_box(
    raw: Tuple[float, float, float, float],
    *,
    fmt: str,
    coords: str,
    img_size: Optional[Tuple[int, int]],
    path: Path,
    line_no: int,
) -> Tuple[float, float, float, float]:
    if coords == "rel":
        if img_size is None:
            raise EvaluationError("--img-size is required when --gt-coords or --det-coords is rel")
        if fmt != "xywh":
            raise EvaluationError(
                f"{path}:{line_no}: relative coordinates use YOLO-style center-x center-y "
                "width height; use --*-format xywh, not xyrb"
            )
        if raw[2] < 0 or raw[3] < 0:
            raise EvaluationError(f"{path}:{line_no}: relative width and height must be non-negative")
        return convert_relative_to_absolute(img_size, raw)

    left, top, third, fourth = raw
    if fmt == "xywh":
        if third < 0 or fourth < 0:
            raise EvaluationError(f"{path}:{line_no}: width and height must be non-negative")
        x1, y1, x2, y2 = left, top, left + third, top + fourth
    else:  # fmt == "xyrb"
        x1, y1, x2, y2 = left, top, third, fourth

    if x2 < x1 or y2 < y1:
        raise EvaluationError(
            f"{path}:{line_no}: invalid box has right/bottom before left/top: "
            f"({x1}, {y1}, {x2}, {y2})"
        )
    return (x1, y1, x2, y2)


def parse_folder(
    folder: Path,
    *,
    is_ground_truth: bool,
    fmt: str,
    coords: str,
    img_size: Optional[Tuple[int, int]],
    warnings: List[str],
) -> Tuple[List[Box], List[str]]:
    role = "ground-truth" if is_ground_truth else "detection"
    if not folder.exists():
        raise EvaluationError(f"{role} folder does not exist: {folder}")
    if not folder.is_dir():
        raise EvaluationError(f"{role} path is not a folder: {folder}")

    boxes: List[Box] = []
    stems: List[str] = []
    files = sorted(folder.glob("*.txt"))
    if not files:
        warnings.append(f"No .txt files found in {role} folder {folder}")

    expected_fields = 5 if is_ground_truth else 6
    schema = (
        "class left top width height or class left top right bottom"
        if is_ground_truth
        else "class confidence left top width height or class confidence left top right bottom"
    )

    for path in files:
        image_id = path.stem
        stems.append(image_id)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise EvaluationError(f"{path}: cannot read as UTF-8 text") from exc
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split()
            if len(parts) != expected_fields:
                raise EvaluationError(
                    f"{path}:{line_no}: expected {expected_fields} whitespace-separated fields "
                    f"({schema}); got {len(parts)}. Class labels cannot contain spaces."
                )
            class_id = parts[0]
            if not class_id:
                raise EvaluationError(f"{path}:{line_no}: class label cannot be empty")
            if is_ground_truth:
                offset = 1
                confidence: Optional[float] = None
            else:
                confidence = as_float(parts[1], path=path, line_no=line_no, field="confidence")
                offset = 2
            raw_values = tuple(
                as_float(parts[offset + idx], path=path, line_no=line_no, field=f"coordinate {idx + 1}")
                for idx in range(4)
            )
            x1, y1, x2, y2 = to_absolute_box(
                raw_values, fmt=fmt, coords=coords, img_size=img_size, path=path, line_no=line_no
            )
            boxes.append(Box(image_id, class_id, x1, y1, x2, y2, confidence))
    return boxes, stems


def boxes_intersect(box_a: Sequence[float], box_b: Sequence[float]) -> bool:
    if box_a[0] > box_b[2]:
        return False
    if box_b[0] > box_a[2]:
        return False
    if box_a[3] < box_b[1]:
        return False
    if box_a[1] > box_b[3]:
        return False
    return True


def area(box: Sequence[float]) -> float:
    return (box[2] - box[0] + 1) * (box[3] - box[1] + 1)


def iou(box_a: Sequence[float], box_b: Sequence[float]) -> float:
    if not boxes_intersect(box_a, box_b):
        return 0.0
    x_a = max(box_a[0], box_b[0])
    y_a = max(box_a[1], box_b[1])
    x_b = min(box_a[2], box_b[2])
    y_b = min(box_a[3], box_b[3])
    intersection = (x_b - x_a + 1) * (y_b - y_a + 1)
    union = area(box_a) + area(box_b) - intersection
    return intersection / union if union > 0 else 0.0


def calculate_average_precision(recall: List[float], precision: List[float]) -> Tuple[float, List[float], List[float]]:
    """Every-point interpolation used by the default PASCAL VOC implementation."""

    mrec = [0.0] + list(recall) + [1.0]
    mpre = [0.0] + list(precision) + [0.0]
    for idx in range(len(mpre) - 1, 0, -1):
        mpre[idx - 1] = max(mpre[idx - 1], mpre[idx])
    changed = [idx + 1 for idx in range(len(mrec) - 1) if mrec[idx + 1] != mrec[idx]]
    ap = 0.0
    for idx in changed:
        ap += (mrec[idx] - mrec[idx - 1]) * mpre[idx]
    return ap, mpre[:-1], mrec[:-1]


def evaluate(
    ground_truths: List[Box],
    detections: List[Box],
    *,
    threshold: float,
    warnings: List[str],
) -> Dict[str, object]:
    classes = sorted({box.class_id for box in ground_truths} | {box.class_id for box in detections})
    if not classes:
        raise EvaluationError("no valid classes: no ground-truth or detection boxes were parsed")

    results: List[Dict[str, object]] = []
    ignored_classes: List[str] = []
    ap_sum = 0.0
    valid_count = 0

    for class_id in classes:
        class_gts = [box for box in ground_truths if box.class_id == class_id]
        class_dets = [box for box in detections if box.class_id == class_id]
        npos = len(class_gts)
        if npos == 0:
            ignored_classes.append(class_id)
            warnings.append(
                f"Class {class_id!r} has detections but no ground-truth positives; excluded from AP/mAP"
            )
            continue

        gts_by_image: Dict[str, List[Box]] = {}
        for gt in class_gts:
            gts_by_image.setdefault(gt.image_id, []).append(gt)
        matched_by_image: Dict[str, List[bool]] = {
            image_id: [False] * len(items) for image_id, items in gts_by_image.items()
        }

        sorted_dets = sorted(class_dets, key=lambda box: box.confidence if box.confidence is not None else 0.0, reverse=True)
        tp_flags: List[int] = []
        fp_flags: List[int] = []

        for det in sorted_dets:
            candidates = gts_by_image.get(det.image_id, [])
            best_iou = -1.0
            best_index = -1
            for idx, gt in enumerate(candidates):
                overlap = iou(det.coords, gt.coords)
                if overlap > best_iou:
                    best_iou = overlap
                    best_index = idx
            if best_iou >= threshold and best_index >= 0:
                if not matched_by_image[det.image_id][best_index]:
                    tp_flags.append(1)
                    fp_flags.append(0)
                    matched_by_image[det.image_id][best_index] = True
                else:
                    tp_flags.append(0)
                    fp_flags.append(1)
            else:
                tp_flags.append(0)
                fp_flags.append(1)

        precision: List[float] = []
        recall: List[float] = []
        acc_tp = 0
        acc_fp = 0
        for tp, fp in zip(tp_flags, fp_flags):
            acc_tp += tp
            acc_fp += fp
            precision.append(acc_tp / (acc_tp + acc_fp) if (acc_tp + acc_fp) else 0.0)
            recall.append(acc_tp / npos)

        ap, interpolated_precision, interpolated_recall = calculate_average_precision(recall, precision)
        total_tp = sum(tp_flags)
        total_fp = sum(fp_flags)
        results.append(
            {
                "class": class_id,
                "AP": ap,
                "AP_percent": ap * 100.0,
                "precision": precision,
                "recall": recall,
                "interpolated_precision": interpolated_precision,
                "interpolated_recall": interpolated_recall,
                "total positives": npos,
                "total TP": total_tp,
                "total FP": total_fp,
            }
        )
        ap_sum += ap
        valid_count += 1

    if valid_count == 0:
        raise EvaluationError("no valid classes: ground-truth positives are required for AP/mAP")

    map_value = ap_sum / valid_count
    return {
        "metric": "PASCAL VOC every-point AP",
        "threshold": threshold,
        "classes": results,
        "ignored_classes": ignored_classes,
        "valid_classes": valid_count,
        "mAP": map_value,
        "mAP_percent": map_value * 100.0,
        "warnings": warnings,
    }


def summarize_stem_warnings(gt_stems: Iterable[str], det_stems: Iterable[str], warnings: List[str]) -> None:
    gt_set = set(gt_stems)
    det_set = set(det_stems)
    gt_only = sorted(gt_set - det_set)
    det_only = sorted(det_set - gt_set)
    if gt_only:
        preview = ", ".join(gt_only[:5])
        suffix = "" if len(gt_only) <= 5 else f" ... (+{len(gt_only) - 5} more)"
        warnings.append(
            f"{len(gt_only)} ground-truth file stem(s) have no matching detection file: {preview}{suffix}"
        )
    if det_only:
        preview = ", ".join(det_only[:5])
        suffix = "" if len(det_only) <= 5 else f" ... (+{len(det_only) - 5} more)"
        warnings.append(
            f"{len(det_only)} detection file stem(s) have no matching ground-truth file: {preview}{suffix}. "
            "Their boxes count as false positives when their class has ground-truth positives elsewhere."
        )


def format_percent(value: float) -> str:
    return f"{value * 100.0:.2f}%"


def text_summary(result: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append("Object Detection Metrics")
    lines.append("Self-contained PASCAL VOC every-point AP/mAP helper")
    lines.append("")
    lines.append(f"IoU threshold: {result['threshold']:.6g}")
    warnings = result.get("warnings", [])
    if warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in warnings:  # type: ignore[assignment]
            lines.append(f"- {warning}")
    lines.append("")
    lines.append("Average Precision (AP), Precision and Recall per class:")
    for class_result in result["classes"]:  # type: ignore[index]
        precision = [f"{p:.2f}" for p in class_result["precision"]]  # type: ignore[index]
        recall = [f"{r:.2f}" for r in class_result["recall"]]  # type: ignore[index]
        lines.append("")
        lines.append(f"Class: {class_result['class']}")
        lines.append(f"AP: {format_percent(class_result['AP'])}")
        lines.append(f"Precision: {precision}")
        lines.append(f"Recall: {recall}")
        lines.append(f"Total positives: {class_result['total positives']}")
        lines.append(f"Total TP: {class_result['total TP']}")
        lines.append(f"Total FP: {class_result['total FP']}")
    lines.append("")
    lines.append(f"mAP: {format_percent(result['mAP'])}")
    return "\n".join(lines) + "\n"


def write_text_file(path_value: str, content: str) -> None:
    path = Path(path_value)
    if path.exists() and path.is_dir():
        raise EvaluationError(f"output path is a directory, expected a file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate PASCAL VOC AP/mAP from ground-truth and detection text folders. "
            "Ground-truth lines are class plus four coordinates; detection lines are class, "
            "confidence, plus four coordinates. The helper is noninteractive and does not plot."
        )
    )
    parser.add_argument("--gt-folder", required=True, help="Folder containing ground-truth .txt files")
    parser.add_argument("--det-folder", required=True, help="Folder containing detection .txt files")
    parser.add_argument("--threshold", type=float, default=0.5, help="IoU threshold for TP/FP matching (default: 0.5)")
    parser.add_argument("--gt-format", choices=("xywh", "xyrb"), default="xywh", help="Ground-truth coordinate format (default: xywh)")
    parser.add_argument("--det-format", choices=("xywh", "xyrb"), default="xywh", help="Detection coordinate format (default: xywh)")
    parser.add_argument("--gt-coords", choices=("abs", "rel"), default="abs", help="Ground-truth coordinate reference (default: abs)")
    parser.add_argument("--det-coords", choices=("abs", "rel"), default="abs", help="Detection coordinate reference (default: abs)")
    parser.add_argument("--img-size", help="Required for relative coordinates, in WIDTH,HEIGHT form")
    parser.add_argument("--output-json", help="Optional JSON output file")
    parser.add_argument("--output-text", help="Optional text summary output file")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = parse_args(argv)
        if not math.isfinite(args.threshold) or args.threshold < 0.0 or args.threshold > 1.0:
            raise EvaluationError("--threshold must be a finite value between 0 and 1")
        img_size = parse_img_size(args.img_size)
        if (args.gt_coords == "rel" or args.det_coords == "rel") and img_size is None:
            raise EvaluationError("--img-size is required when --gt-coords or --det-coords is rel")

        warnings: List[str] = []
        gt_boxes, gt_stems = parse_folder(
            Path(args.gt_folder),
            is_ground_truth=True,
            fmt=args.gt_format,
            coords=args.gt_coords,
            img_size=img_size,
            warnings=warnings,
        )
        det_boxes, det_stems = parse_folder(
            Path(args.det_folder),
            is_ground_truth=False,
            fmt=args.det_format,
            coords=args.det_coords,
            img_size=img_size,
            warnings=warnings,
        )
        summarize_stem_warnings(gt_stems, det_stems, warnings)
        result = evaluate(gt_boxes, det_boxes, threshold=args.threshold, warnings=warnings)
        text = text_summary(result)

        if args.output_text:
            write_text_file(args.output_text, text)
        json_indent = 2 if args.pretty else None
        if args.output_json:
            write_text_file(args.output_json, json.dumps(result, indent=json_indent, sort_keys=True) + "\n")
        if not args.output_text and not args.output_json:
            print(text, end="")
        else:
            print(
                f"Evaluated {len(result['classes'])} class(es); mAP={format_percent(result['mAP'])}",
                file=sys.stdout,
            )
        return 0
    except EvaluationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
