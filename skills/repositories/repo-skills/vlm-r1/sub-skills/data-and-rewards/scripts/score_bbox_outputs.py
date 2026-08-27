#!/usr/bin/env python3
"""Score tiny bbox fixtures with IoU or OD-style matching.

The script accepts either file paths or inline strings. It understands the
same answer wrappers used by the reward helpers:
- optional <answer>...</answer>
- optional fenced JSON blocks
- JSON arrays of box objects with bbox_2d and label
- single bbox lists like [x1, y1, x2, y2]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def read_input(raw: str) -> str:
    path = Path(raw)
    looks_like_inline = raw.lstrip().startswith(("{", "[", "<")) or "\n" in raw
    if path.exists() and not looks_like_inline:
        return path.read_text(encoding="utf-8")
    return raw


def extract_payload(text: str) -> str:
    answer_matches = re.findall(r"<answer>(.*?)</answer>", text, re.DOTALL)
    if answer_matches:
        text = answer_matches[-1].strip()

    json_matches = re.findall(r"```json(.*?)```", text, re.DOTALL)
    if json_matches:
        return json_matches[-1].strip()

    fenced_matches = re.findall(r"```(.*?)```", text, re.DOTALL)
    if fenced_matches:
        return fenced_matches[-1].strip()

    return text.strip()


def parse_jsonish(text: str) -> Any:
    payload = extract_payload(text)
    if not payload:
        return None
    if payload.lower() in {"none", "null"}:
        return None
    return json.loads(payload)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def normalize_box(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        coords = item.get("bbox_2d", item.get("bbox"))
        if not isinstance(coords, (list, tuple)) or len(coords) != 4:
            raise ValueError("box object must contain bbox_2d or bbox with four coordinates")
        return {
            "bbox_2d": [coords[0], coords[1], coords[2], coords[3]],
            "label": str(item.get("label", "")),
        }

    if isinstance(item, (list, tuple)) and len(item) == 4 and all(is_number(x) for x in item):
        return {"bbox_2d": [item[0], item[1], item[2], item[3]], "label": ""}

    raise ValueError("expected a single bbox list or a box object")


def has_single_box_shape(value: Any) -> bool:
    if isinstance(value, dict):
        return "bbox_2d" in value or "bbox" in value
    if isinstance(value, (list, tuple)) and len(value) == 4 and all(is_number(x) for x in value):
        return True
    return False


def to_box_list(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []

    if isinstance(value, dict):
        for key in ("boxes", "pred_boxes", "gt_boxes", "annotations"):
            if key in value:
                nested = value[key]
                return to_box_list(nested)
        return [normalize_box(value)]

    if isinstance(value, (list, tuple)):
        if len(value) == 4 and all(is_number(x) for x in value):
            return [normalize_box(value)]
        return [normalize_box(item) for item in value]

    raise ValueError(f"unsupported bbox payload type: {type(value).__name__}")


def iou(box1: list[Any], box2: list[Any]) -> float:
    inter_x1 = max(box1[0], box2[0])
    inter_y1 = max(box1[1], box2[1])
    inter_x2 = min(box1[2] - 1, box2[2] - 1)
    inter_y2 = min(box1[3] - 1, box2[3] - 1)
    if inter_x1 < inter_x2 and inter_y1 < inter_y2:
        inter = (inter_x2 - inter_x1 + 1) * (inter_y2 - inter_y1 + 1)
    else:
        inter = 0
    union = (box1[2] - box1[0]) * (box1[3] - box1[1]) + (box2[2] - box2[0]) * (box2[3] - box2[1]) - inter
    return float(inter) / union if union else 0.0


def normalize_label(value: Any) -> str:
    return str(value).strip().lower() if value is not None else ""


def duplicates(boxes: list[dict[str, Any]]) -> int:
    counter = Counter(
        (
            tuple(box.get("bbox_2d", [])),
            normalize_label(box.get("label")),
        )
        for box in boxes
        if isinstance(box.get("bbox_2d"), list)
    )
    return sum(count - 1 for count in counter.values() if count > 1)


def greedy_od_score(
    pred_boxes: list[dict[str, Any]],
    gt_boxes: list[dict[str, Any]],
    threshold: float,
    alpha: float,
    beta: float,
    gamma: float,
) -> dict[str, Any]:
    if not gt_boxes and not pred_boxes:
        return {
            "score": 1.0,
            "position_score": 1.0,
            "label_score": 1.0,
            "completeness_score": 1.0,
            "matches": [],
            "unmatched_preds": [],
            "unmatched_gts": [],
        }

    if not gt_boxes:
        return {
            "score": 0.0,
            "position_score": 0.0,
            "label_score": 0.0,
            "completeness_score": 0.0,
            "matches": [],
            "unmatched_preds": list(range(len(pred_boxes))),
            "unmatched_gts": [],
        }

    if not pred_boxes:
        return {
            "score": 0.0,
            "position_score": 0.0,
            "label_score": 0.0,
            "completeness_score": 0.0,
            "matches": [],
            "unmatched_preds": [],
            "unmatched_gts": list(range(len(gt_boxes))),
        }

    iou_matrix: list[list[float]] = []
    for pred_box in pred_boxes:
        row: list[float] = []
        for gt_box in gt_boxes:
            try:
                row.append(iou(pred_box["bbox_2d"], gt_box["bbox_2d"]))
            except Exception:
                row.append(0.0)
        iou_matrix.append(row)

    unmatched_preds = list(range(len(pred_boxes)))
    unmatched_gts = list(range(len(gt_boxes)))
    matches: list[dict[str, Any]] = []

    while unmatched_preds and unmatched_gts:
        best_pred = -1
        best_gt = -1
        best_iou = -1.0

        for pred_idx in unmatched_preds:
            for gt_idx in unmatched_gts:
                current_iou = iou_matrix[pred_idx][gt_idx]
                if current_iou > best_iou:
                    best_iou = current_iou
                    best_pred = pred_idx
                    best_gt = gt_idx

        if best_iou < threshold:
            break

        pred_label = normalize_label(pred_boxes[best_pred].get("label"))
        gt_label = normalize_label(gt_boxes[best_gt].get("label"))
        label_correct = pred_label == gt_label
        matches.append(
            {
                "pred_index": best_pred,
                "gt_index": best_gt,
                "iou": best_iou if label_correct else 0.0,
                "label_correct": label_correct,
            }
        )
        unmatched_preds.remove(best_pred)
        unmatched_gts.remove(best_gt)

    position_score = sum(match["iou"] for match in matches) / len(gt_boxes) if matches else 0.0
    label_score = sum(1.0 for match in matches if match["label_correct"]) / len(gt_boxes) if matches else 0.0
    miss_rate = len(unmatched_gts) / len(gt_boxes)
    false_alarm_rate = len(unmatched_preds) / len(pred_boxes) if pred_boxes else 0.0
    completeness_score = 1.0 - (miss_rate + false_alarm_rate) / 2.0
    denominator = alpha + beta + gamma
    final_score = (
        alpha * position_score + beta * label_score + gamma * completeness_score
    ) / denominator if denominator else 0.0

    return {
        "score": final_score,
        "position_score": position_score,
        "label_score": label_score,
        "completeness_score": completeness_score,
        "matches": matches,
        "unmatched_preds": unmatched_preds,
        "unmatched_gts": unmatched_gts,
    }


def score_pair(
    prediction: Any,
    solution: Any,
    mode: str,
    threshold: float,
    alpha: float,
    beta: float,
    gamma: float,
) -> dict[str, Any]:
    if mode == "auto":
        if (prediction is None and solution is None) or (prediction == [] and solution == []):
            mode = "od"
        elif has_single_box_shape(prediction) and has_single_box_shape(solution):
            mode = "iou"
        else:
            mode = "od"

    if mode == "iou":
        if prediction is None and solution is None:
            return {"mode": "iou", "score": 1.0, "iou": 1.0}
        if prediction is None or solution is None:
            return {"mode": "iou", "score": 0.0, "iou": 0.0}
        if not has_single_box_shape(prediction) or not has_single_box_shape(solution):
            raise ValueError("iou mode expects one bbox on each side")
        pred_box = normalize_box(prediction)["bbox_2d"]
        gt_box = normalize_box(solution)["bbox_2d"]
        iou_score = iou(pred_box, gt_box)
        return {"mode": "iou", "score": iou_score, "iou": iou_score, "pred_box": pred_box, "gt_box": gt_box}

    pred_boxes = to_box_list(prediction)
    gt_boxes = to_box_list(solution)
    result = greedy_od_score(pred_boxes, gt_boxes, threshold, alpha, beta, gamma)
    result["mode"] = "od"
    result["prediction_count"] = len(pred_boxes)
    result["ground_truth_count"] = len(gt_boxes)
    result["duplicate_prediction_entries"] = duplicates(pred_boxes)
    result["duplicate_ground_truth_entries"] = duplicates(gt_boxes)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score tiny bbox fixtures with IoU or OD-style matching.",
    )
    parser.add_argument("--prediction", required=True, help="Prediction text or file path.")
    parser.add_argument("--solution", required=True, help="Ground-truth text or file path.")
    parser.add_argument(
        "--mode",
        default="auto",
        choices=("auto", "iou", "od"),
        help="Choose single-box IoU, OD-style matching, or auto-detection.",
    )
    parser.add_argument("--threshold", type=float, default=0.5, help="IoU threshold for OD-style matching.")
    parser.add_argument("--alpha", type=float, default=0.7, help="Position weight for OD-style matching.")
    parser.add_argument("--beta", type=float, default=0.0, help="Label weight for OD-style matching.")
    parser.add_argument("--gamma", type=float, default=0.3, help="Completeness weight for OD-style matching.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    raw_prediction = read_input(args.prediction)
    raw_solution = read_input(args.solution)

    try:
        prediction = parse_jsonish(raw_prediction)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"invalid prediction JSON: {exc.msg}"}, indent=2, ensure_ascii=False))
        return 1

    try:
        solution = parse_jsonish(raw_solution)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"invalid solution JSON: {exc.msg}"}, indent=2, ensure_ascii=False))
        return 1

    try:
        result = score_pair(prediction, solution, args.mode, args.threshold, args.alpha, args.beta, args.gamma)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, indent=2, ensure_ascii=False))
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
