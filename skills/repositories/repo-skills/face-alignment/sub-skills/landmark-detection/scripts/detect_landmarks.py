#!/usr/bin/env python3
"""Run face landmark detection on one image or a directory.

Purpose: provide a small, reusable smoke/demo helper for the landmark-detection
workflow. The helper prints a JSON summary and does not plot.

Prerequisites: install `face-alignment` into the active environment. Optional
backends such as RetinaFace and SCRFD require their extra dependencies.

Examples:
    python scripts/detect_landmarks.py --input /path/to/image.jpg --device cpu
    python scripts/detect_landmarks.py --input /path/to/images --landmarks-type 3d
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import torch
import face_alignment


_LANDMARKS_TYPE_MAP = {
    "2d": face_alignment.LandmarksType.TWO_D,
    "2.5d": face_alignment.LandmarksType.TWO_HALF_D,
    "3d": face_alignment.LandmarksType.THREE_D,
}

_DTYPE_MAP = {
    "float32": torch.float32,
    "float16": torch.float16,
    "bfloat16": torch.bfloat16,
}


def _parse_face_detector_kwargs(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON for --face-detector-kwargs: {exc}") from exc
    if not isinstance(value, dict):
        raise argparse.ArgumentTypeError("--face-detector-kwargs must decode to a JSON object")
    return value


def _serialise_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        return value.tolist()
    if torch.is_tensor(value):
        return value.detach().cpu().numpy().tolist()
    if isinstance(value, (list, tuple)):
        return [_serialise_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _serialise_value(val) for key, val in value.items()}
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    return value


def _summarise_result(result: Any, return_bboxes: bool, return_landmark_score: bool) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    if return_bboxes or return_landmark_score:
        landmarks, scores, boxes = result
    else:
        landmarks, scores, boxes = result, None, None

    if landmarks is None:
        summary["face_count"] = 0
        summary["landmark_shapes"] = []
    else:
        summary["face_count"] = len(landmarks)
        summary["landmark_shapes"] = [list(np.asarray(face).shape) for face in landmarks]
        summary["landmarks"] = [_serialise_value(face) for face in landmarks]

    if scores is not None:
        summary["scores"] = _serialise_value(scores)
    if boxes is not None:
        summary["detected_faces"] = _serialise_value(boxes)

    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Image path or directory path to process.")
    parser.add_argument(
        "--landmarks-type",
        choices=sorted(_LANDMARKS_TYPE_MAP),
        default="2d",
        help="Landmark family to predict.",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "mps"),
        default="cpu",
        help="Execution device for the landmark model.",
    )
    parser.add_argument(
        "--dtype",
        choices=sorted(_DTYPE_MAP),
        default="float32",
        help="Torch dtype to use for the landmark model.",
    )
    parser.add_argument(
        "--face-detector",
        default="sfd",
        help="Detector backend name passed to FaceAlignment.",
    )
    parser.add_argument(
        "--face-detector-kwargs",
        default="{}",
        help='JSON object forwarded to FaceAlignment as face_detector_kwargs.',
    )
    parser.add_argument("--compile", dest="compile", action="store_true", help="Enable torch.compile.")
    parser.add_argument("--no-compile", dest="compile", action="store_false", help="Disable torch.compile.")
    parser.set_defaults(compile=False)
    parser.add_argument(
        "--flip-input",
        dest="flip_input",
        action="store_true",
        help="Apply test-time horizontal flip averaging.",
    )
    parser.add_argument(
        "--no-flip-input",
        dest="flip_input",
        action="store_false",
        help="Disable test-time horizontal flip averaging.",
    )
    parser.set_defaults(flip_input=True)
    parser.add_argument(
        "--max-batch-size",
        type=int,
        default=1,
        help="Chunk size used when multiple faces are processed in one image.",
    )
    parser.add_argument(
        "--extensions",
        nargs="*",
        default=[".jpg", ".png"],
        help="Directory scan extensions when the input path is a directory.",
    )
    parser.add_argument(
        "--recursive",
        dest="recursive",
        action="store_true",
        help="Recursively scan directories.",
    )
    parser.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="Scan only the top-level directory.",
    )
    parser.set_defaults(recursive=True)
    parser.add_argument(
        "--show-progress-bar",
        dest="show_progress_bar",
        action="store_true",
        help="Display a progress bar for directory scans.",
    )
    parser.add_argument(
        "--no-show-progress-bar",
        dest="show_progress_bar",
        action="store_false",
        help="Suppress the directory progress bar.",
    )
    parser.set_defaults(show_progress_bar=True)
    parser.add_argument("--return-bboxes", action="store_true", help="Return detector boxes in the summary.")
    parser.add_argument(
        "--return-landmark-score",
        action="store_true",
        help="Return landmark scores in the summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"input path does not exist: {input_path}")

    try:
        face_detector_kwargs = _parse_face_detector_kwargs(args.face_detector_kwargs)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    fa = face_alignment.FaceAlignment(
        _LANDMARKS_TYPE_MAP[args.landmarks_type],
        device=args.device,
        dtype=_DTYPE_MAP[args.dtype],
        flip_input=args.flip_input,
        face_detector=args.face_detector,
        face_detector_kwargs=face_detector_kwargs,
        compile=args.compile,
        max_batch_size=args.max_batch_size,
    )

    summary: dict[str, Any] = {
        "input": str(input_path),
        "mode": "directory" if input_path.is_dir() else "image",
        "landmarks_type": args.landmarks_type,
        "device": args.device,
        "dtype": args.dtype,
        "face_detector": args.face_detector,
        "compile": args.compile,
        "flip_input": args.flip_input,
        "max_batch_size": args.max_batch_size,
        "face_detector_kwargs": face_detector_kwargs,
        "return_bboxes": args.return_bboxes,
        "return_landmark_score": args.return_landmark_score,
    }

    try:
        if input_path.is_dir():
            result = fa.get_landmarks_from_directory(
                str(input_path),
                extensions=args.extensions,
                recursive=args.recursive,
                show_progress_bar=args.show_progress_bar,
                return_bboxes=args.return_bboxes,
                return_landmark_score=args.return_landmark_score,
            )
            files: list[dict[str, Any]] = []
            for image_path, item in result.items():
                file_summary: dict[str, Any] = {"path": image_path}
                file_summary.update(_summarise_result(item, args.return_bboxes, args.return_landmark_score))
                files.append(file_summary)
            summary["files"] = files
            summary["file_count"] = len(files)
        else:
            result = fa.get_landmarks_from_image(
                str(input_path),
                return_bboxes=args.return_bboxes,
                return_landmark_score=args.return_landmark_score,
            )
            summary.update(_summarise_result(result, args.return_bboxes, args.return_landmark_score))
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"face alignment run failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(_serialise_value(summary), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
