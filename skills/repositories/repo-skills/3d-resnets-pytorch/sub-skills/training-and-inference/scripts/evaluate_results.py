#!/usr/bin/env python3
"""Evaluate top-k recognition accuracy for 3D ResNets result JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

GroundTruth = List[Tuple[str, int]]
ClassLabelsMap = Dict[str, int]


def get_class_labels(data: dict) -> ClassLabelsMap:
    if "labels" not in data:
        raise KeyError("ground-truth JSON is missing the 'labels' key")
    class_labels_map: ClassLabelsMap = {}
    for index, class_label in enumerate(data["labels"]):
        class_labels_map[class_label] = index
    return class_labels_map


def load_ground_truth(ground_truth_path: Path, subset: str) -> Tuple[GroundTruth, ClassLabelsMap]:
    with ground_truth_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "database" not in data:
        raise KeyError("ground-truth JSON is missing the 'database' key")

    class_labels_map = get_class_labels(data)
    ground_truth: GroundTruth = []

    for video_id, video_info in data["database"].items():
        if video_info.get("subset") != subset:
            continue
        annotations = video_info.get("annotations", {})
        if "label" not in annotations:
            raise KeyError(f"ground-truth entry '{video_id}' is missing annotations.label")
        label = annotations["label"]
        if label not in class_labels_map:
            raise KeyError(f"label '{label}' from '{video_id}' is not listed in ground-truth labels")
        ground_truth.append((video_id, class_labels_map[label]))

    return ground_truth, class_labels_map


def _load_result_entries(result_entries: Sequence[dict], class_labels_map: ClassLabelsMap, video_id: str, top_k: int) -> List[int]:
    labels_and_scores: List[Tuple[int, float]] = []

    for entry in result_entries:
        if not isinstance(entry, dict):
            raise TypeError(f"result entry for '{video_id}' must be a dict")
        if "segment" in entry and "result" in entry:
            raise ValueError(
                "result JSON appears to come from --inference_no_average; "
                "evaluate_results.py expects per-video [{'label', 'score'}] entries"
            )
        if "label" not in entry or "score" not in entry:
            raise KeyError(f"result entry for '{video_id}' must contain 'label' and 'score'")
        label = entry["label"]
        if label not in class_labels_map:
            raise KeyError(f"result label '{label}' for video '{video_id}' is not in the ground-truth label map")
        labels_and_scores.append((class_labels_map[label], float(entry["score"])))

    if not labels_and_scores:
        raise ValueError(f"result JSON does not contain any class scores for '{video_id}'")

    labels_and_scores.sort(key=lambda item: item[1], reverse=True)
    return [label for label, _ in labels_and_scores[: min(top_k, len(labels_and_scores))]]


def load_result(result_path: Path, top_k: int, class_labels_map: ClassLabelsMap) -> Dict[str, List[int]]:
    with result_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "results" not in data:
        raise KeyError("result JSON is missing the 'results' key")

    result: Dict[str, List[int]] = {}
    for video_id, video_results in data["results"].items():
        if not isinstance(video_results, list):
            raise TypeError(f"result entry for '{video_id}' must be a list")
        result[video_id] = _load_result_entries(video_results, class_labels_map, video_id, top_k)
    return result


def remove_nonexistent_ground_truth(ground_truth: GroundTruth, result: Dict[str, List[int]]) -> GroundTruth:
    return [line for line in ground_truth if line[0] in result]


def evaluate(ground_truth_path: Path, result_path: Path, subset: str, top_k: int, ignore: bool) -> float:
    print("load ground truth")
    ground_truth, class_labels_map = load_ground_truth(ground_truth_path, subset)
    print(f"number of ground truth: {len(ground_truth)}")

    print("load result")
    result = load_result(result_path, top_k, class_labels_map)
    print(f"number of result: {len(result)}")

    n_ground_truth = len(ground_truth)
    filtered_ground_truth = remove_nonexistent_ground_truth(ground_truth, result)
    if ignore:
        n_ground_truth = len(filtered_ground_truth)

    if n_ground_truth == 0:
        raise ValueError("no ground-truth samples matched the selected subset and result set")

    print(f"calculate top-{top_k} accuracy")
    correct = [1 if line[1] in result[line[0]] else 0 for line in filtered_ground_truth]
    accuracy = sum(correct) / n_ground_truth

    print(f"top-{top_k} accuracy: {accuracy}")
    return accuracy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("ground_truth_path", type=Path)
    parser.add_argument("result_path", type=Path)
    parser.add_argument("-k", type=int, default=1, help="top-k labels to score")
    parser.add_argument("--subset", type=str, default="validation", help="subset name in the ground-truth JSON")
    parser.add_argument("--save", action="store_true", help="write top{k}.txt next to the result file")
    parser.add_argument(
        "--ignore",
        action="store_true",
        help="ignore nonexistent videos in result",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    accuracy = evaluate(args.ground_truth_path, args.result_path, args.subset, args.k, args.ignore)
    if args.save:
        with (args.result_path.parent / f"top{args.k}.txt").open("w", encoding="utf-8") as f:
            f.write(str(accuracy))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
