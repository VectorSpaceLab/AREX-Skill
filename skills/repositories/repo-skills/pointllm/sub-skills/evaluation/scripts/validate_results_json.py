#!/usr/bin/env python3
"""Validate PointLLM evaluation JSON without importing PointLLM or calling APIs."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

CATEGORIES = [
    "airplane", "bathtub", "bed", "bench", "bookshelf", "bottle", "bowl",
    "car", "chair", "cone", "cup", "curtain", "desk", "door", "dresser",
    "flower pot", "glass box", "guitar", "keyboard", "lamp", "laptop",
    "mantel", "monitor", "night stand", "person", "piano", "plant", "radio",
    "range hood", "sink", "sofa", "stairs", "stool", "table", "tent",
    "toilet", "tv stand", "vase", "wardrobe", "xbox",
]
TRADITIONAL = [
    "bleu-1", "bleu-2", "bleu-3", "bleu-4", "rouge-1", "rouge-2",
    "rouge-l", "meteor", "sbert_similarity", "simcse_similarity",
]


def fail(errors: list[str], path: str, message: str) -> None:
    errors.append(f"{path}: {message}")


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def percentage_string(value: Any) -> bool:
    if not isinstance(value, str) or not value.endswith("%"):
        return False
    try:
        number = float(value[:-1])
    except ValueError:
        return False
    return 0 <= number <= 100


def integer(value: Any, minimum: int | None = None) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and (minimum is None or value >= minimum)


def required(obj: dict[str, Any], keys: list[str], path: str, errors: list[str]) -> None:
    for key in keys:
        if key not in obj:
            fail(errors, path, f"missing required field {key!r}")


def validate_generation(data: Any, kind: str, errors: list[str]) -> None:
    if not isinstance(data, dict):
        fail(errors, "$", "top level must be an object")
        return
    required(data, ["prompt", "results"], "$", errors)
    if not isinstance(data.get("prompt"), str):
        fail(errors, "$.prompt", "must be a string")
    rows = data.get("results")
    if not isinstance(rows, list):
        fail(errors, "$.results", "must be an array")
        return
    seen: set[str] = set()
    for index, row in enumerate(rows):
        path = f"$.results[{index}]"
        if not isinstance(row, dict):
            fail(errors, path, "must be an object")
            continue
        required(row, ["object_id", "ground_truth", "model_output"], path, errors)
        object_id = row.get("object_id")
        key = json.dumps(object_id, sort_keys=True)
        if key in seen:
            fail(errors, path + ".object_id", "duplicate object_id")
        seen.add(key)
        if not isinstance(row.get("model_output"), str):
            fail(errors, path + ".model_output", "must be a string")
        if kind == "modelnet":
            if not integer(row.get("object_id"), 0):
                fail(errors, path + ".object_id", "ModelNet object_id must be a nonnegative integer")
            if not integer(row.get("ground_truth"), 0) or row.get("ground_truth") >= 40:
                fail(errors, path + ".ground_truth", "must be an integer in 0..39")
            if not isinstance(row.get("label_name"), str):
                fail(errors, path + ".label_name", "required string for ModelNet40")
        elif kind == "objaverse":
            if not isinstance(object_id, str):
                fail(errors, path + ".object_id", "Objaverse object_id must be a string")
            if not isinstance(row.get("ground_truth"), str):
                fail(errors, path + ".ground_truth", "Objaverse ground_truth must be a string")


def validate_common_eval(data: Any, errors: list[str], row_keys: list[str]) -> list[Any]:
    if not isinstance(data, dict):
        fail(errors, "$", "top level must be an object")
        return []
    required(data, ["inference_prompt", "results", "prompt_tokens", "completion_tokens", "GPT_cost"], "$", errors)
    if not isinstance(data.get("inference_prompt"), str):
        fail(errors, "$.inference_prompt", "must be a string")
    for key in ("prompt_tokens", "completion_tokens"):
        if not integer(data.get(key), 0):
            fail(errors, "$." + key, "must be a nonnegative integer")
    if not is_number(data.get("GPT_cost")) or data.get("GPT_cost") < 0:
        fail(errors, "$.GPT_cost", "must be a nonnegative number")
    rows = data.get("results")
    if not isinstance(rows, list):
        fail(errors, "$.results", "must be an array")
        return []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        path = f"$.results[{index}]"
        if not isinstance(row, dict):
            fail(errors, path, "must be an object")
            continue
        required(row, row_keys, path, errors)
        key = json.dumps(row.get("object_id"), sort_keys=True)
        if key in seen:
            fail(errors, path + ".object_id", "duplicate object_id")
        seen.add(key)
        if not isinstance(row.get("object_id"), (str, int)) or isinstance(row.get("object_id"), bool):
            fail(errors, path + ".object_id", "must be a string or integer")
        if not isinstance(row.get("model_output"), str):
            fail(errors, path + ".model_output", "must be a string")
    return rows


def validate_open(data: Any, errors: list[str]) -> None:
    rows = validate_common_eval(data, errors, ["object_id", "ground_truth", "model_output", "gpt_cls_result", "gpt_reason"])
    required(data if isinstance(data, dict) else {}, ["accuracy", "total_predictions", "correct_predictions", "invalid_responses"], "$", errors)
    if isinstance(data, dict) and not percentage_string(data.get("accuracy")):
        fail(errors, "$.accuracy", "must be a percentage string such as '82.50%'")
    for key in ("total_predictions", "correct_predictions", "invalid_responses"):
        if isinstance(data, dict) and not integer(data.get(key), 0):
            fail(errors, "$." + key, "must be a nonnegative integer")
    for index, row in enumerate(rows):
        if isinstance(row, dict):
            if row.get("gpt_cls_result") not in ("T", "F", "INVALID"):
                fail(errors, f"$.results[{index}].gpt_cls_result", "must be T, F, or INVALID")
            if not isinstance(row.get("ground_truth"), str):
                fail(errors, f"$.results[{index}].ground_truth", "must be a string")
            if not isinstance(row.get("gpt_reason"), str):
                fail(errors, f"$.results[{index}].gpt_reason", "must be a string")


def validate_modelnet_eval(data: Any, errors: list[str]) -> None:
    rows = validate_common_eval(data, errors, ["object_id", "ground_truth", "model_output", "gpt_cls_result", "ground_truth_label", "gpt_cls_label", "gpt_reason", "prompt_tokens", "completion_tokens"])
    required(data if isinstance(data, dict) else {}, ["accuracy", "clean_accuracy", "total_predictions", "correct_predictions", "invalid_correct_predictions", "invalid_responses"], "$", errors)
    if isinstance(data, dict):
        for key in ("accuracy", "clean_accuracy"):
            if not percentage_string(data.get(key)):
                fail(errors, "$." + key, "must be a percentage string")
        for key in ("total_predictions", "correct_predictions", "invalid_correct_predictions", "invalid_responses"):
            if not integer(data.get(key), 0):
                fail(errors, "$." + key, "must be a nonnegative integer")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        path = f"$.results[{index}]"
        if not integer(row.get("ground_truth"), 0) or row.get("ground_truth") >= 40:
            fail(errors, path + ".ground_truth", "must be an integer in 0..39")
        if not integer(row.get("gpt_cls_result"), 0) or row.get("gpt_cls_result") >= 40:
            fail(errors, path + ".gpt_cls_result", "must be an integer in 0..39, including random invalid assignments")
        if not isinstance(row.get("ground_truth_label"), str) or row.get("ground_truth_label") not in CATEGORIES:
            fail(errors, path + ".ground_truth_label", "must be one of the 40 ModelNet category names")
        if not isinstance(row.get("gpt_cls_label"), str) or not isinstance(row.get("gpt_reason"), str):
            fail(errors, path, "classification label and reason must be strings")
        for key in ("prompt_tokens", "completion_tokens"):
            if not integer(row.get(key), 0):
                fail(errors, path + "." + key, "must be a nonnegative integer")


def validate_caption(data: Any, errors: list[str]) -> None:
    rows = validate_common_eval(data, errors, ["object_id", "ground_truth", "model_output", "gpt_score", "gpt_reason"])
    required(data if isinstance(data, dict) else {}, ["average_score", "total_score", "total_predictions", "invalid_responses"], "$", errors)
    if isinstance(data, dict):
        try:
            average = float(data["average_score"])
            if not isinstance(data.get("average_score"), str) or not 0 <= average <= 100:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            fail(errors, "$.average_score", "must be a formatted numeric string in 0..100")
        try:
            total = float(data["total_score"])
            count = int(data.get("total_predictions", 0))
            if not isinstance(data.get("total_score"), str) or not 0 <= total <= 100 * max(0, count):
                raise ValueError
        except (KeyError, TypeError, ValueError):
            fail(errors, "$.total_score", "must be a formatted numeric string in 0..100 per prediction")
        for key in ("total_predictions", "invalid_responses"):
            if not integer(data.get(key), 0):
                fail(errors, "$." + key, "must be a nonnegative integer")
    for index, row in enumerate(rows):
        if isinstance(row, dict):
            score = row.get("gpt_score")
            if not integer(score) or score < -1 or score > 100:
                fail(errors, f"$.results[{index}].gpt_score", "must be -1 or an integer in 0..100")
            if not isinstance(row.get("ground_truth"), str) or not isinstance(row.get("gpt_reason"), str):
                fail(errors, f"$.results[{index}]", "ground_truth and gpt_reason must be strings")


def validate_traditional(data: Any, errors: list[str]) -> None:
    if not isinstance(data, dict):
        fail(errors, "$", "top level must be an object")
        return
    required(data, ["inference_prompt", "overall_scores", "results"], "$", errors)
    if not isinstance(data.get("inference_prompt"), str):
        fail(errors, "$.inference_prompt", "must be a string")
    overall = data.get("overall_scores")
    if not isinstance(overall, dict):
        fail(errors, "$.overall_scores", "must be an object")
    else:
        for key in TRADITIONAL:
            if key not in overall or not isinstance(overall[key], str):
                fail(errors, "$.overall_scores." + key, "must be a formatted numeric string")
    rows = data.get("results")
    if not isinstance(rows, list):
        fail(errors, "$.results", "must be an array")
        return
    seen: set[str] = set()
    for index, row in enumerate(rows):
        path = f"$.results[{index}]"
        if not isinstance(row, dict):
            fail(errors, path, "must be an object")
            continue
        required(row, ["object_id", "ground_truth", "model_output", "scores"], path, errors)
        key = json.dumps(row.get("object_id"), sort_keys=True)
        if key in seen:
            fail(errors, path + ".object_id", "duplicate object_id")
        seen.add(key)
        if not isinstance(row.get("model_output"), str):
            fail(errors, path + ".model_output", "must be a string")
        scores = row.get("scores")
        if not isinstance(scores, dict):
            fail(errors, path + ".scores", "must be an object")
        else:
            for key in TRADITIONAL:
                if key not in scores or not is_number(scores[key]):
                    fail(errors, path + ".scores." + key, "must be numeric")


def detect(data: Any) -> str:
    if isinstance(data, dict) and "overall_scores" in data:
        return "traditional"
    if isinstance(data, dict) and "average_score" in data:
        return "object-captioning"
    if isinstance(data, dict) and "clean_accuracy" in data:
        return "modelnet-close-set-classification"
    if isinstance(data, dict) and "accuracy" in data:
        return "open-free-form-classification"
    return "generation"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PointLLM result/evaluation JSON locally.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--kind", choices=["auto", "generation", "objaverse", "modelnet", "open-free-form-classification", "modelnet-close-set-classification", "object-captioning", "traditional"], default="auto")
    args = parser.parse_args()
    errors: list[str] = []
    try:
        data = json.loads(args.path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.path}", file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read valid JSON from {args.path}: {exc}", file=sys.stderr)
        return 1
    kind = detect(data) if args.kind == "auto" else args.kind
    if kind in ("generation", "objaverse", "modelnet"):
        validate_generation(data, kind, errors)
    elif kind == "open-free-form-classification":
        validate_open(data, errors)
    elif kind == "modelnet-close-set-classification":
        validate_modelnet_eval(data, errors)
    elif kind == "object-captioning":
        validate_caption(data, errors)
    elif kind == "traditional":
        validate_traditional(data, errors)
    if errors:
        print(f"INVALID ({kind}): {len(errors)} error(s)")
        for error in errors:
            print("- " + error)
        return 1
    print(f"VALID ({kind}): {len(data.get('results', []))} result row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
