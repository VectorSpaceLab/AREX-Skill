#!/usr/bin/env python3
"""Evaluate a Donut checkpoint on a dataset or validate JSONL rows.

Examples:
    python scripts/evaluate_dataset.py --dataset_name_or_path naver-clova-ix/cord-v2 --pretrained_model_name_or_path ./result/train_cord/smoke
    python scripts/evaluate_dataset.py --dataset_name_or_path /path/to/dataset --validate_only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import fmean
from typing import Any, Dict, Iterator, List


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate a Donut checkpoint or validate a local dataset layout.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dataset_name_or_path", required=True, help="Hugging Face dataset name or local dataset root.")
    parser.add_argument("--pretrained_model_name_or_path", help="Checkpoint directory or hub id used for evaluation.")
    parser.add_argument("--split", default="test", help="Dataset split to evaluate.")
    parser.add_argument("--task_name", help="Override the task name used for prompts and scoring.")
    parser.add_argument("--save_path", help="Optional JSON output path for predictions and scores.")
    parser.add_argument("--max_samples", type=int, default=None, help="Optional smoke-test limit for the number of samples.")
    parser.add_argument("--validate_only", action="store_true", help="Validate the dataset schema and exit without loading a model.")
    return parser


def infer_task_name(dataset_name_or_path: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    return Path(str(dataset_name_or_path).rstrip("/")).name


def load_ground_truth(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("ground_truth must decode to a JSON object")
        return parsed
    raise TypeError(f"ground_truth must be a JSON string or dict, got {type(raw).__name__}")


def iter_local_samples(dataset_root: Path, split: str) -> Iterator[Dict[str, Any]]:
    from PIL import Image

    root = dataset_root
    split_root = root if (root / "metadata.jsonl").is_file() else root / split
    metadata_path = split_root / "metadata.jsonl"
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Missing metadata.jsonl at {metadata_path}")

    with metadata_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"{metadata_path}:{line_no}: each row must be a JSON object")
            if "file_name" not in record:
                raise KeyError(f"{metadata_path}:{line_no}: missing file_name")
            if "ground_truth" not in record:
                raise KeyError(f"{metadata_path}:{line_no}: missing ground_truth")

            file_name = record["file_name"]
            if not isinstance(file_name, str) or not file_name:
                raise TypeError(f"{metadata_path}:{line_no}: file_name must be a non-empty string")

            image_path = Path(file_name)
            candidates = [image_path] if image_path.is_absolute() else [split_root / image_path, root / image_path]
            for candidate in candidates:
                if candidate.is_file():
                    image_path = candidate
                    break
            else:
                raise FileNotFoundError(f"{metadata_path}:{line_no}: image file not found for {file_name}")

            ground_truth = load_ground_truth(record["ground_truth"])
            with Image.open(image_path) as image:
                yield {
                    "image": image.convert("RGB"),
                    "ground_truth": ground_truth,
                    "file_name": file_name,
                    "_source": str(image_path),
                }


def iter_hf_samples(dataset_name_or_path: str, split: str) -> Iterator[Dict[str, Any]]:
    from datasets import load_dataset

    dataset = load_dataset(dataset_name_or_path, split=split)
    for sample in dataset:
        ground_truth = load_ground_truth(sample["ground_truth"])
        yield {
            "image": sample["image"],
            "ground_truth": ground_truth,
            "file_name": sample.get("file_name"),
            "_source": dataset_name_or_path,
        }


def validate_sample(sample: Dict[str, Any], task_name: str, index: int) -> None:
    ground_truth = sample["ground_truth"]
    if not isinstance(ground_truth, dict):
        raise TypeError(f"sample {index}: ground_truth must decode to a dict")

    if "gt_parses" in ground_truth:
        if task_name != "docvqa":
            raise ValueError(f"sample {index}: gt_parses indicates DocVQA-style data, but task_name={task_name!r}")
        gt_parses = ground_truth["gt_parses"]
        if not isinstance(gt_parses, list) or not gt_parses:
            raise TypeError(f"sample {index}: gt_parses must be a non-empty list")
        for qa_index, qa in enumerate(gt_parses):
            if not isinstance(qa, dict):
                raise TypeError(f"sample {index}: gt_parses[{qa_index}] must be a dict")
            if "question" not in qa or "answer" not in qa:
                raise KeyError(f"sample {index}: gt_parses[{qa_index}] must contain question and answer")
    elif "gt_parse" in ground_truth:
        if task_name == "docvqa":
            raise ValueError(f"sample {index}: docvqa expects gt_parses, not gt_parse")
        gt_parse = ground_truth["gt_parse"]
        if not isinstance(gt_parse, dict):
            raise TypeError(f"sample {index}: gt_parse must be a dict")
        if task_name == "rvlcdip" and "class" not in gt_parse:
            raise KeyError(f"sample {index}: rvlcdip ground truth must contain class")
    else:
        raise KeyError(f"sample {index}: ground_truth must contain gt_parse or gt_parses")


def build_prompt(task_name: str, ground_truth: Dict[str, Any]) -> str:
    if task_name == "docvqa":
        question = ground_truth["gt_parses"][0]["question"]
        return f"<s_{task_name}><s_question>{str(question).lower()}</s_question><s_answer>"
    return f"<s_{task_name}>"


def score_sample(task_name: str, prediction: Dict[str, Any], ground_truth: Dict[str, Any], evaluator: Any) -> float:
    if task_name == "rvlcdip":
        return float(prediction["class"] == ground_truth["gt_parse"]["class"])
    if task_name == "docvqa":
        answers = {qa["answer"] for qa in ground_truth["gt_parses"]}
        return float(prediction["answer"] in answers)
    return float(evaluator.cal_acc(prediction, ground_truth["gt_parse"]))


def evaluate(args: argparse.Namespace) -> int:
    task_name = infer_task_name(args.dataset_name_or_path, args.task_name)

    dataset_path = Path(args.dataset_name_or_path).expanduser()
    if dataset_path.exists():
        sample_iter = iter_local_samples(dataset_path, args.split)
    elif args.dataset_name_or_path.startswith((".", "/", "~")):
        raise FileNotFoundError(f"Local dataset path does not exist: {args.dataset_name_or_path}")
    else:
        sample_iter = iter_hf_samples(args.dataset_name_or_path, args.split)

    validated = 0
    if args.validate_only:
        for index, sample in enumerate(sample_iter):
            validate_sample(sample, task_name, index)
            validated += 1
            if args.max_samples is not None and validated >= args.max_samples:
                break
        print(f"Validated {validated} samples for task {task_name!r} on split {args.split!r}.")
        return 0

    if not args.pretrained_model_name_or_path:
        print("error: --pretrained_model_name_or_path is required unless --validate_only is set", file=sys.stderr)
        return 2

    import torch
    from donut import DonutModel, JSONParseEvaluator

    model = DonutModel.from_pretrained(args.pretrained_model_name_or_path)
    if torch.cuda.is_available():
        model.half()
        model.to("cuda")
    model.eval()
    evaluator = JSONParseEvaluator()

    predictions: List[Dict[str, Any]] = []
    ground_truths: List[Any] = []
    scores: List[float] = []

    with torch.no_grad():
        for index, sample in enumerate(sample_iter):
            validate_sample(sample, task_name, index)
            prompt = build_prompt(task_name, sample["ground_truth"])
            output = model.inference(image=sample["image"], prompt=prompt)["predictions"][0]
            score = score_sample(task_name, output, sample["ground_truth"], evaluator)

            predictions.append(output)
            ground_truths.append(sample["ground_truth"]["gt_parses"] if "gt_parses" in sample["ground_truth"] else sample["ground_truth"]["gt_parse"])
            scores.append(score)

            if args.max_samples is not None and len(scores) >= args.max_samples:
                break

    if not scores:
        print("error: no samples were available for evaluation", file=sys.stderr)
        return 1

    ted_accuracy = fmean(scores)
    f1_accuracy = evaluator.cal_f1(predictions, ground_truths)
    print(
        f"Total number of samples: {len(scores)}, Tree Edit Distance (TED) based accuracy score: {ted_accuracy}, F1 accuracy score: {f1_accuracy}"
    )

    if args.save_path:
        save_path = Path(args.save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with save_path.open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "ted_accuracies": scores,
                    "ted_accuracy": ted_accuracy,
                    "f1_accuracy": f1_accuracy,
                    "predictions": predictions,
                    "ground_truths": ground_truths,
                },
                handle,
            )
        print(f"Saved scores to {save_path}")
    return 0


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return evaluate(args)
    except (FileNotFoundError, ImportError, KeyError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
