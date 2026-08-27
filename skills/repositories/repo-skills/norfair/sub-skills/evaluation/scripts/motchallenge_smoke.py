#!/usr/bin/env python3
"""Tiny synthetic MOTChallenge smoke helper for Norfair evaluation.

The helper creates a no-download fixture with one sequence, one ground-truth
track, matching predictions, and a detection file. It exercises:

- InformationFile
- DetectionFileParser
- PredictionsTextFile
- Accumulators / eval_motChallenge when motmetrics is installed

It does not depend on source-tree paths or on real MOTChallenge datasets.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence

import numpy as np

from motchallenge_eval import (
    import_norfair_metrics,
    load_prediction_matrix,
    metrics_dependencies_missing,
    runtime_dependencies_missing,
)

SEQUENCE_NAME = "SYNTH-01"
FRAME_BOXES = [
    # frame, id, left, top, width, height
    (1, 1, 11.0, 11.0, 20.0, 20.0),
    (2, 1, 13.0, 11.0, 20.0, 20.0),
]


@dataclass
class TinyTrackedObject:
    id: int
    estimate: np.ndarray


def tracked_object_from_tlwh(obj_id: int, left: float, top: float, width: float, height: float) -> TinyTrackedObject:
    return TinyTrackedObject(
        id=obj_id,
        estimate=np.array(
            [[left, top], [left + width, top + height]],
            dtype=float,
        ),
    )


def create_fixture(fixture_root: Path) -> Path:
    """Create a tiny MOTChallenge train split and return its dataset root."""

    if fixture_root.exists():
        shutil.rmtree(fixture_root)

    dataset_root = fixture_root / "train"
    sequence_dir = dataset_root / SEQUENCE_NAME
    (sequence_dir / "gt").mkdir(parents=True, exist_ok=True)
    (sequence_dir / "det").mkdir(parents=True, exist_ok=True)
    (sequence_dir / "img1").mkdir(parents=True, exist_ok=True)

    (sequence_dir / "seqinfo.ini").write_text(
        "\n".join(
            [
                "[Sequence]",
                f"name={SEQUENCE_NAME}",
                "imDir=img1",
                "frameRate=30",
                "seqLength=2",
                "imWidth=64",
                "imHeight=64",
                "imExt=.jpg",
                "",
            ]
        ),
        encoding="utf-8",
    )

    gt_lines = []
    det_lines = []
    for frame, obj_id, left, top, width, height in FRAME_BOXES:
        # MOTChallenge ground truth: frame,id,left,top,width,height,conf,class,visibility
        gt_lines.append(f"{frame},{obj_id},{left},{top},{width},{height},1,1,1")
        # MOTChallenge detections: frame,id,left,top,width,height,conf,x,y,z
        det_lines.append(f"{frame},-1,{left},{top},{width},{height},0.99,-1,-1,-1")

    (sequence_dir / "gt" / "gt.txt").write_text("\n".join(gt_lines) + "\n", encoding="utf-8")
    (sequence_dir / "det" / "det.txt").write_text("\n".join(det_lines) + "\n", encoding="utf-8")
    return dataset_root


def parse_detection_counts(sequence_dir: Path) -> Sequence[int]:
    norfair_metrics = import_norfair_metrics()
    info = norfair_metrics.InformationFile(sequence_dir / "seqinfo.ini")
    parser = norfair_metrics.DetectionFileParser(sequence_dir, information_file=info)
    return [len(frame_detections) for frame_detections in parser]


def write_predictions_and_metrics(sequence_dir: Path, output_root: Path):
    """Write perfect predictions and compute metrics when dependencies allow."""

    norfair_metrics = import_norfair_metrics()
    info = norfair_metrics.InformationFile(sequence_dir / "seqinfo.ini")
    prediction_writer = norfair_metrics.PredictionsTextFile(
        input_path=sequence_dir,
        save_path=output_root,
        information_file=info,
    )

    missing = metrics_dependencies_missing()
    accumulator = None
    if not missing:
        accumulator = norfair_metrics.Accumulators()
        accumulator.create_accumulator(sequence_dir, information_file=info)

    for frame, obj_id, left, top, width, height in FRAME_BOXES:
        tracked = [tracked_object_from_tlwh(obj_id, left, top, width, height)]
        prediction_writer.update(predictions=tracked, frame_number=frame)
        if accumulator is not None:
            accumulator.update(predictions=tracked)

    if not prediction_writer.text_file.closed:
        prediction_writer.text_file.close()

    prediction_path = output_root / "predictions" / f"{SEQUENCE_NAME}.txt"

    if accumulator is None:
        return prediction_path, missing, None, None

    summary_dataframe = accumulator.compute_metrics()
    accumulator.save_metrics(save_path=output_root)
    return prediction_path, missing, accumulator.summary_text, summary_dataframe


def lookup_metric(summary_dataframe, metric_name: str) -> Optional[float]:
    if summary_dataframe is None:
        return None
    if "OVERALL" not in summary_dataframe.index:
        return None
    for column in summary_dataframe.columns:
        if str(column).lower() == metric_name.lower():
            return float(summary_dataframe.loc["OVERALL", column])
    return None


def run_smoke(output_root: Path, keep_fixture: bool, assert_perfect: bool) -> Dict[str, object]:
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    fixture_root = output_root / "_fixture"
    dataset_root = create_fixture(fixture_root)
    sequence_dir = dataset_root / SEQUENCE_NAME

    try:
        core_missing = runtime_dependencies_missing(include_metrics=False)
        if core_missing:
            return {
                "status": "blocked_required_dependency",
                "sequence": SEQUENCE_NAME,
                "dataset_root": str(dataset_root),
                "output_root": str(output_root),
                "prediction_path": None,
                "prediction_shape": None,
                "detection_counts_by_frame": None,
                "missing_dependencies": core_missing,
                "message": "Synthetic fixture was created, but Norfair is not importable. Install `norfair[metrics]` in the active Python environment.",
            }

        try:
            detection_counts = list(parse_detection_counts(sequence_dir))
            prediction_path, missing, summary_text, summary_dataframe = write_predictions_and_metrics(
                sequence_dir=sequence_dir,
                output_root=output_root,
            )
        except RuntimeError as exc:
            if "Norfair is not importable" in str(exc):
                return {
                    "status": "blocked_required_dependency",
                    "sequence": SEQUENCE_NAME,
                    "dataset_root": str(dataset_root),
                    "output_root": str(output_root),
                    "prediction_path": None,
                    "prediction_shape": None,
                    "detection_counts_by_frame": None,
                    "missing_dependencies": ["norfair"],
                    "message": str(exc),
                }
            raise
        prediction_matrix = load_prediction_matrix(prediction_path)

        result: Dict[str, object] = {
            "sequence": SEQUENCE_NAME,
            "dataset_root": str(dataset_root),
            "output_root": str(output_root),
            "prediction_path": str(prediction_path),
            "prediction_shape": list(prediction_matrix.shape),
            "detection_counts_by_frame": detection_counts,
        }

        if missing:
            result.update(
                {
                    "status": "blocked_required_dependency",
                    "missing_dependencies": missing,
                    "message": "Synthetic fixture and predictions were created, but MOT metrics require `pip install norfair[metrics]`.",
                }
            )
        else:
            metrics_path = output_root / "metrics.txt"
            overall_mota = lookup_metric(summary_dataframe, "mota")
            overall_idf1 = lookup_metric(summary_dataframe, "idf1")
            result.update(
                {
                    "status": "ok",
                    "metrics_path": str(metrics_path),
                    "overall_mota": overall_mota,
                    "overall_idf1": overall_idf1,
                    "summary_text": summary_text,
                }
            )
            if assert_perfect:
                if overall_mota is None or overall_mota < 0.999:
                    raise AssertionError(f"Expected near-perfect OVERALL MOTA, got {overall_mota}")
                if overall_idf1 is not None and overall_idf1 < 0.999:
                    raise AssertionError(f"Expected near-perfect OVERALL IDF1, got {overall_idf1}")

        return result
    finally:
        if not keep_fixture and fixture_root.exists():
            shutil.rmtree(fixture_root)


def print_plain(result: Dict[str, object]) -> None:
    print(f"status: {result['status']}")
    print(f"sequence: {result['sequence']}")
    print(f"prediction_path: {result['prediction_path']}")
    print(f"prediction_shape: {result['prediction_shape']}")
    print(f"detection_counts_by_frame: {result['detection_counts_by_frame']}")
    if result["status"] == "ok":
        print(f"metrics_path: {result['metrics_path']}")
        print(f"overall_mota: {result['overall_mota']}")
        print(f"overall_idf1: {result['overall_idf1']}")
        print("summary_text:")
        print(result["summary_text"])
    else:
        print(f"missing_dependencies: {result.get('missing_dependencies')}")
        print(f"message: {result.get('message')}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create and score a tiny synthetic MOTChallenge fixture for Norfair evaluation."
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("motchallenge_smoke_output"),
        help="Directory where predictions and metrics should be written.",
    )
    parser.add_argument(
        "--keep-fixture",
        action="store_true",
        help="Keep the generated _fixture/train/SYNTH-01 tree for inspection.",
    )
    parser.add_argument(
        "--assert-perfect",
        action="store_true",
        help="Assert that the synthetic perfect predictions produce near-perfect OVERALL MOTA/IDF1.",
    )
    parser.add_argument("--json", action="store_true", help="Print a JSON result.")
    parser.add_argument(
        "--fail-on-dependency-block",
        action="store_true",
        help="Return a non-zero exit code when Norfair or metrics dependencies are missing.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_smoke(
            output_root=args.output_root,
            keep_fixture=args.keep_fixture,
            assert_perfect=args.assert_perfect,
        )
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_plain(result)

    if result["status"] == "blocked_required_dependency" and args.fail_on_dependency_block:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())