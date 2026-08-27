#!/usr/bin/env python3
"""Offline scorer for saved VLM-R1 REC/OVD bbox predictions.

The script intentionally avoids model imports, checkpoint loading, image reads, and
repo-specific dependencies. It accepts JSON, JSONL, or native-style JSON objects
with a top-level ``results`` list.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

BBox = List[float]
BoxObj = Dict[str, Any]
MISSING = object()

ANSWER_RE = re.compile(r"<answer>(.*?)</answer>", re.IGNORECASE | re.DOTALL)
FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
BRACKET_BBOX_RE = re.compile(
    r"\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*"
    r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]"
)

DIRECT_PRED_KEYS = (
    "extracted_answer",
    "prediction",
    "pred_bbox",
    "bbox",
    "answer_bbox",
    "model_answer",
)
TEXT_PRED_KEYS = ("model_output", "output", "completion", "response", "answer", "text")
GT_KEYS = ("ground_truth", "solution", "gt_bbox", "target_bbox", "bbox")
ID_KEYS = ("id", "image", "question")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _to_bbox(seq: Sequence[Any]) -> Optional[BBox]:
    if len(seq) != 4 or not all(_is_number(v) for v in seq):
        return None
    return [float(v) for v in seq]


def read_text(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def load_records(path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    text = read_text(path)
    if not text.strip():
        return [], {"source_format": "empty"}

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        records: List[Dict[str, Any]] = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    records.append(row)
                else:
                    records.append({"value": row})
            except json.JSONDecodeError as exc:
                records.append(
                    {
                        "__parse_error__": f"line {line_no}: {exc.msg}",
                        "__raw__": line[:500],
                    }
                )
        return records, {"source_format": "jsonl"}

    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return [r if isinstance(r, dict) else {"value": r} for r in payload["results"]], {
            "source_format": "json.results",
            "container_keys": sorted(payload.keys()),
        }
    if isinstance(payload, list):
        return [r if isinstance(r, dict) else {"value": r} for r in payload], {"source_format": "json.list"}
    if isinstance(payload, dict):
        return [payload], {"source_format": "json.object"}
    return [{"value": payload}], {"source_format": "json.scalar"}


def deep_get(row: Dict[str, Any], dotted_key: str) -> Any:
    current: Any = row
    for part in dotted_key.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return MISSING
    return current


def pick_key(row: Dict[str, Any], requested: Optional[str], candidates: Iterable[str]) -> Tuple[Any, Optional[str]]:
    if requested:
        value = deep_get(row, requested)
        return value, requested if value is not MISSING else requested
    for key in candidates:
        value = deep_get(row, key)
        if value is not MISSING:
            return value, key
    return MISSING, None


def row_identifier(row: Dict[str, Any]) -> Any:
    for key in ID_KEYS:
        value = row.get(key)
        if value is not None:
            return value
    return None


def json_loads_relaxed(text: str) -> Tuple[Any, List[str]]:
    stripped = text.strip()
    try:
        return json.loads(stripped), []
    except json.JSONDecodeError as first_exc:
        repaired = re.sub(r",\s*([}\]])", r"\1", stripped)
        if repaired != stripped:
            try:
                return json.loads(repaired), ["repaired_trailing_commas"]
            except json.JSONDecodeError:
                pass
        return MISSING, [f"malformed_json: {first_exc.msg}"]


def candidate_texts(text: str) -> List[Tuple[str, str]]:
    candidates: List[Tuple[str, str]] = []
    answer_matches = ANSWER_RE.findall(text)
    if answer_matches:
        candidates.append(("answer", answer_matches[-1].strip()))
    fence_matches = FENCE_RE.findall(text)
    if fence_matches:
        candidates.append(("fenced_json", fence_matches[-1].strip()))
    candidates.append(("full_text", text.strip()))
    # Preserve order while removing exact duplicates.
    seen = set()
    unique: List[Tuple[str, str]] = []
    for label, value in candidates:
        if value not in seen:
            unique.append((label, value))
            seen.add(value)
    return unique


def normalize_box_object(value: Any) -> Tuple[Optional[BoxObj], List[str]]:
    warnings: List[str] = []
    if isinstance(value, dict):
        bbox_value = MISSING
        for key in ("bbox_2d", "bbox", "box"):
            if key in value:
                bbox_value = value[key]
                break
        if bbox_value is MISSING and all(k in value for k in ("x1", "y1", "x2", "y2")):
            bbox_value = [value["x1"], value["y1"], value["x2"], value["y2"]]
        bbox = _to_bbox(bbox_value) if isinstance(bbox_value, Sequence) and not isinstance(bbox_value, (str, bytes)) else None
        if bbox is None:
            return None, ["object_missing_valid_bbox"]
        obj: BoxObj = {"bbox_2d": bbox}
        if value.get("label") is not None:
            obj["label"] = str(value["label"])
        if value.get("score") is not None and _is_number(value["score"]):
            obj["score"] = float(value["score"])
        return obj, warnings

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        bbox = _to_bbox(value)
        if bbox is not None:
            return {"bbox_2d": bbox}, warnings
    return None, ["not_a_bbox_object"]


def boxes_from_json_value(value: Any) -> Tuple[List[BoxObj], List[str]]:
    warnings: List[str] = []
    if isinstance(value, list):
        direct_bbox = _to_bbox(value)
        if direct_bbox is not None:
            return [{"bbox_2d": direct_bbox}], warnings
        boxes: List[BoxObj] = []
        for idx, item in enumerate(value):
            box, item_warnings = normalize_box_object(item)
            if box is None:
                warnings.extend(f"item_{idx}_{w}" for w in item_warnings)
            else:
                boxes.append(box)
        return boxes, warnings

    box, box_warnings = normalize_box_object(value)
    if box is not None:
        return [box], warnings
    return [], box_warnings


def parse_box_list(value: Any) -> Tuple[List[BoxObj], List[str]]:
    warnings: List[str] = []
    if value is MISSING or value is None:
        return [], ["missing_value"]

    if isinstance(value, str):
        malformed_notes: List[str] = []
        for label, candidate in candidate_texts(value):
            parsed, json_warnings = json_loads_relaxed(candidate)
            if parsed is not MISSING:
                boxes, box_warnings = boxes_from_json_value(parsed)
                if boxes:
                    return boxes, json_warnings + box_warnings
                malformed_notes.extend(f"{label}_{w}" for w in box_warnings)
            elif label == "fenced_json":
                malformed_notes.extend(f"malformed_fenced_json_{w}" for w in json_warnings)

        bracket = BRACKET_BBOX_RE.search(value)
        if bracket:
            return [
                {
                    "bbox_2d": [
                        float(bracket.group(1)),
                        float(bracket.group(2)),
                        float(bracket.group(3)),
                        float(bracket.group(4)),
                    ]
                }
            ], malformed_notes
        return [], malformed_notes or ["no_bbox_found_in_text"]

    boxes, box_warnings = boxes_from_json_value(value)
    return boxes, box_warnings


def parse_single_bbox(value: Any) -> Tuple[Optional[BBox], List[str]]:
    boxes, warnings = parse_box_list(value)
    if boxes:
        return boxes[0]["bbox_2d"], warnings
    return None, warnings


def parse_size(value: Any, order: str) -> Optional[Tuple[float, float]]:
    if isinstance(value, dict):
        if "height" in value and "width" in value and _is_number(value["height"]) and _is_number(value["width"]):
            return float(value["height"]), float(value["width"])
        if "h" in value and "w" in value and _is_number(value["h"]) and _is_number(value["w"]):
            return float(value["h"]), float(value["w"])
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) >= 2:
        if _is_number(value[0]) and _is_number(value[1]):
            first, second = float(value[0]), float(value[1])
            return (first, second) if order == "height-width" else (second, first)
    return None


def get_size_pair(row: Dict[str, Any], key: Optional[str], role: str, order: str) -> Optional[Tuple[float, float]]:
    if key:
        value = deep_get(row, key)
        return None if value is MISSING else parse_size(value, order)

    value = row.get(f"{role}_size")
    parsed = parse_size(value, order) if value is not None else None
    if parsed is not None:
        return parsed

    h_key = f"{role}_height"
    w_key = f"{role}_width"
    if _is_number(row.get(h_key)) and _is_number(row.get(w_key)):
        return float(row[h_key]), float(row[w_key])
    return None


def resize_bbox(bbox: BBox, input_size: Tuple[float, float], image_size: Tuple[float, float]) -> BBox:
    input_height, input_width = input_size
    image_height, image_width = image_size
    if input_height <= 0 or input_width <= 0:
        return bbox[:]
    return [
        bbox[0] / input_width * image_width,
        bbox[1] / input_height * image_height,
        bbox[2] / input_width * image_width,
        bbox[3] / input_height * image_height,
    ]


def bbox_iou(box1: BBox, box2: BBox) -> float:
    inter_x1 = max(box1[0], box2[0])
    inter_y1 = max(box1[1], box2[1])
    inter_x2 = min(box1[2] - 1, box2[2] - 1)
    inter_y2 = min(box1[3] - 1, box2[3] - 1)
    if inter_x1 < inter_x2 and inter_y1 < inter_y2:
        inter = (inter_x2 - inter_x1 + 1) * (inter_y2 - inter_y1 + 1)
    else:
        inter = 0.0
    area1 = max(0.0, (box1[2] - box1[0]) * (box1[3] - box1[1]))
    area2 = max(0.0, (box2[2] - box2[0]) * (box2[3] - box2[1]))
    union = area1 + area2 - inter
    return float(inter) / union if union > 0 else 0.0


def warning_is_parse_error(warning: str) -> bool:
    return any(
        token in warning
        for token in (
            "malformed",
            "missing_value",
            "no_bbox",
            "not_a_bbox",
            "object_missing_valid_bbox",
            "parse_error",
        )
    )


def score_rec_row(row: Dict[str, Any], index: int, args: argparse.Namespace) -> Dict[str, Any]:
    if "__parse_error__" in row:
        return {
            "index": index,
            "id": row_identifier(row),
            "scored": False,
            "correct": False,
            "parse_error": True,
            "warnings": [row["__parse_error__"]],
        }

    pred_candidates = DIRECT_PRED_KEYS + TEXT_PRED_KEYS
    pred_value, pred_key = pick_key(row, args.prediction_key, pred_candidates)
    gt_value, gt_key = pick_key(row, args.ground_truth_key, GT_KEYS)

    pred_bbox, pred_warnings = parse_single_bbox(pred_value)
    gt_bbox, gt_warnings = parse_single_bbox(gt_value)
    warnings = [f"prediction_{w}" for w in pred_warnings] + [f"ground_truth_{w}" for w in gt_warnings]

    resized = False
    resize_wanted = False
    if pred_bbox is not None and args.resize_mode != "off":
        if args.resize_mode == "on":
            resize_wanted = True
        elif pred_key in TEXT_PRED_KEYS or isinstance(pred_value, str):
            resize_wanted = True

    if pred_bbox is not None and resize_wanted:
        input_size = get_size_pair(row, args.input_size_key, "input", args.size_order)
        image_size = get_size_pair(row, args.image_size_key, "image", args.size_order)
        if input_size and image_size:
            pred_bbox = resize_bbox(pred_bbox, input_size, image_size)
            resized = True
        else:
            warnings.append("resize_requested_but_size_metadata_missing")

    missing_gt = gt_value is MISSING or gt_bbox is None
    scored = not missing_gt
    if pred_bbox is None:
        pred_bbox_for_iou = [0.0, 0.0, 0.0, 0.0]
    else:
        pred_bbox_for_iou = pred_bbox
    iou_value = bbox_iou(pred_bbox_for_iou, gt_bbox) if gt_bbox is not None else None
    correct = bool(iou_value is not None and iou_value > args.iou_threshold)

    return {
        "index": index,
        "id": row_identifier(row),
        "prediction_key": pred_key,
        "ground_truth_key": gt_key,
        "pred_bbox": pred_bbox,
        "gt_bbox": gt_bbox,
        "iou": iou_value,
        "correct": correct,
        "scored": scored,
        "resized": resized,
        "parse_error": any(warning_is_parse_error(w) for w in warnings),
        "missing_ground_truth": missing_gt,
        "warnings": warnings,
    }


def label_matches(pred: BoxObj, gt: BoxObj, require_label: bool) -> bool:
    if not require_label:
        return True
    return str(pred.get("label", "")).lower() == str(gt.get("label", "")).lower()


def greedy_matches(
    pred_boxes: List[BoxObj],
    gt_boxes: List[BoxObj],
    threshold: float,
    require_label: bool,
) -> List[Dict[str, Any]]:
    unmatched_pred = set(range(len(pred_boxes)))
    unmatched_gt = set(range(len(gt_boxes)))
    matches: List[Dict[str, Any]] = []

    while unmatched_pred and unmatched_gt:
        best: Optional[Tuple[float, int, int]] = None
        for pred_idx in unmatched_pred:
            for gt_idx in unmatched_gt:
                pred = pred_boxes[pred_idx]
                gt = gt_boxes[gt_idx]
                iou_value = bbox_iou(pred["bbox_2d"], gt["bbox_2d"])
                if not label_matches(pred, gt, require_label):
                    effective_iou = 0.0
                else:
                    effective_iou = iou_value
                if best is None or effective_iou > best[0]:
                    best = (effective_iou, pred_idx, gt_idx)
        if best is None or best[0] <= threshold:
            break
        iou_value, pred_idx, gt_idx = best
        matches.append(
            {
                "pred_idx": pred_idx,
                "gt_idx": gt_idx,
                "iou": iou_value,
                "pred_label": pred_boxes[pred_idx].get("label"),
                "gt_label": gt_boxes[gt_idx].get("label"),
            }
        )
        unmatched_pred.remove(pred_idx)
        unmatched_gt.remove(gt_idx)
    return matches


def score_ovd_row(row: Dict[str, Any], index: int, args: argparse.Namespace) -> Dict[str, Any]:
    if "__parse_error__" in row:
        return {
            "index": index,
            "id": row_identifier(row),
            "scored": False,
            "correct": False,
            "parse_error": True,
            "warnings": [row["__parse_error__"]],
        }

    pred_value, pred_key = pick_key(row, args.prediction_key, DIRECT_PRED_KEYS + TEXT_PRED_KEYS)
    gt_value, gt_key = pick_key(row, args.ground_truth_key, GT_KEYS + ("normalized_solution",))

    pred_boxes, pred_warnings = parse_box_list(pred_value)
    gt_boxes, gt_warnings = parse_box_list(gt_value)
    warnings = [f"prediction_{w}" for w in pred_warnings] + [f"ground_truth_{w}" for w in gt_warnings]

    missing_gt = gt_value is MISSING
    scored = not missing_gt
    matches = greedy_matches(pred_boxes, gt_boxes, args.iou_threshold, args.require_label) if scored else []
    precision = len(matches) / len(pred_boxes) if pred_boxes else (1.0 if not gt_boxes and scored else 0.0)
    recall = len(matches) / len(gt_boxes) if gt_boxes else (1.0 if not pred_boxes and scored else 0.0)
    mean_iou = sum(m["iou"] for m in matches) / len(gt_boxes) if gt_boxes else (1.0 if not pred_boxes and scored else 0.0)
    strict_ok = len(matches) == len(pred_boxes) if args.strict_extra_boxes else True
    correct = bool(scored and len(matches) == len(gt_boxes) and strict_ok)

    return {
        "index": index,
        "id": row_identifier(row),
        "prediction_key": pred_key,
        "ground_truth_key": gt_key,
        "pred_boxes": pred_boxes,
        "gt_boxes": gt_boxes,
        "matches": matches,
        "precision": precision,
        "recall": recall,
        "mean_iou": mean_iou,
        "correct": correct,
        "scored": scored,
        "parse_error": any(warning_is_parse_error(w) for w in warnings),
        "missing_ground_truth": missing_gt,
        "warnings": warnings,
    }


def summarize(results: List[Dict[str, Any]], task: str) -> Dict[str, Any]:
    scored = [r for r in results if r.get("scored")]
    correct = [r for r in scored if r.get("correct")]
    if task == "rec":
        ious = [r["iou"] for r in scored if isinstance(r.get("iou"), (int, float))]
    else:
        ious = [r["mean_iou"] for r in scored if isinstance(r.get("mean_iou"), (int, float))]
    accuracy = len(correct) / len(scored) if scored else 0.0
    return {
        "rows": len(results),
        "scored": len(scored),
        "correct": len(correct),
        "accuracy": accuracy,
        "accuracy_percent": accuracy * 100.0,
        "mean_iou": sum(ious) / len(ious) if ious else 0.0,
        "parse_errors": sum(1 for r in results if r.get("parse_error")),
        "missing_ground_truth": sum(1 for r in results if r.get("missing_ground_truth")),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score saved VLM-R1 REC/OVD bbox predictions without loading a model.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--task", required=True, choices=("rec", "ovd"), help="Scoring task type.")
    parser.add_argument("--input", required=True, help="Input JSON/JSONL path, or '-' for stdin.")
    parser.add_argument("--output", default="-", help="Output JSON path, or '-' for stdout.")
    parser.add_argument("--prediction-key", help="Dotted key for prediction text/bbox. Auto-detects common keys if omitted.")
    parser.add_argument("--ground-truth-key", help="Dotted key for ground-truth bbox/objects. Auto-detects common keys if omitted.")
    parser.add_argument("--iou-threshold", type=float, default=0.5, help="Correctness threshold; rows require IoU strictly greater than this value.")
    parser.add_argument(
        "--resize-mode",
        choices=("auto", "on", "off"),
        default="auto",
        help="REC only: auto resizes text predictions with size metadata; on resizes every parsed prediction; off disables resize.",
    )
    parser.add_argument("--input-size-key", help="Dotted key for input size metadata, usually [height, width].")
    parser.add_argument("--image-size-key", help="Dotted key for original image size metadata, usually [height, width].")
    parser.add_argument(
        "--size-order",
        choices=("height-width", "width-height"),
        default="height-width",
        help="Interpret two-element size arrays in this order.",
    )
    parser.add_argument("--require-label", action="store_true", help="OVD only: require matching labels before a bbox can match.")
    parser.add_argument("--strict-extra-boxes", action="store_true", help="OVD only: mark rows incorrect when unmatched predictions remain.")
    parser.add_argument("--summary-only", action="store_true", help="Omit per-row results from the output JSON.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    records, source_meta = load_records(args.input)
    scorer = score_rec_row if args.task == "rec" else score_ovd_row
    results = [scorer(row, index, args) for index, row in enumerate(records)]
    payload: Dict[str, Any] = {
        "schema_version": "vlm-r1-bbox-score-v1",
        "task": args.task,
        "iou_threshold": args.iou_threshold,
        "source": source_meta,
        "summary": summarize(results, args.task),
    }
    if not args.summary_only:
        payload["results"] = results

    output_text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.output == "-":
        sys.stdout.write(output_text)
    else:
        Path(args.output).write_text(output_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
