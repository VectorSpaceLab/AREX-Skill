#!/usr/bin/env python3
"""Safe command-line helper for ImageAI video and camera object detection.

The helper validates sources and output choices before loading model weights. It
never opens a camera unless --camera-index is explicitly supplied.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv", ".m4v", ".webm"}
MAX_STORED_ANALYSIS_EVENTS = 1000


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def nonnegative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected integer, got {value!r}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def probability(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected number, got {value!r}") from exc
    if parsed < 0 or parsed > 100:
        raise argparse.ArgumentTypeError("probability threshold must be between 0 and 100")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run ImageAI video/camera object detection with standard COCO or custom models.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--mode", choices=["coco", "custom"], default="coco", help="Detector family to use.")
    parser.add_argument(
        "--model-type",
        choices=["retinanet", "yolov3", "tiny-yolov3"],
        required=True,
        help="ImageAI model architecture. Custom mode supports only yolov3 and tiny-yolov3.",
    )
    parser.add_argument("--model-path", required=True, help="Path to ImageAI PyTorch .pt or .pth model weights.")
    parser.add_argument("--json-path", help="Path to custom detection JSON config; required for --mode custom.")

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input-video", help="Path to input video file. Does not open a camera.")
    source.add_argument("--camera-index", type=nonnegative_int, help="Open this explicit cv2.VideoCapture camera index.")

    parser.add_argument(
        "--output-video",
        help="Output video base path. ImageAI appends .mp4; if a video suffix is supplied, this helper strips it.",
    )
    parser.add_argument("--fps", type=positive_int, default=20, help="Output FPS and callback/timeout second boundary.")
    parser.add_argument(
        "--frame-detection-interval",
        type=positive_int,
        default=1,
        help="Run fresh detection on frame 1 and every Nth frame.",
    )
    parser.add_argument(
        "--minimum-percentage-probability",
        type=probability,
        help="Detection confidence threshold in percent. Defaults to 50 for COCO, 40 for custom.",
    )
    parser.add_argument("--timeout", type=positive_int, help="Stop after this many approximate video seconds.")
    parser.add_argument("--no-save", action="store_true", help="Do not save a detected video; use callbacks/summary for output.")
    parser.add_argument("--log-progress", action="store_true", help="Print ImageAI frame progress.")
    parser.add_argument("--hide-name", action="store_true", help="Hide object names on rendered frames.")
    parser.add_argument("--hide-probability", action="store_true", help="Hide probabilities on rendered frames.")
    parser.add_argument("--hide-box", action="store_true", help="Hide bounding boxes on rendered frames.")
    parser.add_argument(
        "--custom-objects",
        help="COCO-only comma-separated class filter, e.g. person,car,traffic_light. Spaces/hyphens are normalized to underscores.",
    )
    parser.add_argument("--cpu", action="store_true", help="Force ImageAI detector to use CPU before loadModel().")
    parser.add_argument(
        "--analysis-summary",
        action="store_true",
        help="Attach lightweight callbacks and print count summaries as JSON.",
    )
    return parser


def fail(parser: argparse.ArgumentParser, message: str) -> None:
    parser.error(message)


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    model_path = Path(args.model_path)
    if not model_path.is_file():
        fail(parser, f"--model-path does not exist or is not a file: {model_path}")
    if model_path.suffix.lower() == ".h5":
        fail(parser, "ImageAI 3.x video detection expects PyTorch .pt/.pth weights, not TensorFlow .h5 files")
    if model_path.suffix.lower() not in {".pt", ".pth"}:
        fail(parser, "--model-path must end with .pt or .pth for ImageAI 3.x")

    if args.mode == "custom":
        if args.model_type == "retinanet":
            fail(parser, "--mode custom supports --model-type yolov3 or tiny-yolov3, not retinanet")
        if not args.json_path:
            fail(parser, "--json-path is required when --mode custom")
        json_path = Path(args.json_path)
        if not json_path.is_file():
            fail(parser, f"--json-path does not exist or is not a file: {json_path}")
        if args.custom_objects:
            fail(parser, "--custom-objects is supported only with --mode coco / VideoObjectDetection")
    elif args.json_path:
        fail(parser, "--json-path is only used with --mode custom")

    if not args.no_save and not args.output_video:
        fail(parser, "--output-video is required unless --no-save is supplied")

    if args.camera_index is not None and args.timeout is None:
        print(
            "warning: camera detection without --timeout can run until interrupted",
            file=sys.stderr,
        )


def normalize_output_base(output_video: Optional[str]) -> Tuple[Optional[str], List[str]]:
    if not output_video:
        return None, []
    path = Path(output_video)
    warnings: List[str] = []
    if path.suffix.lower() in VIDEO_SUFFIXES:
        warnings.append(f"stripped output suffix {path.suffix!r}; ImageAI appends .mp4 itself")
        path = path.with_suffix("")
    parent = path.parent if str(path.parent) else Path(".")
    parent.mkdir(parents=True, exist_ok=True)
    return str(path), warnings


def validate_video_file(path_text: str) -> Dict[str, Any]:
    import cv2

    path = Path(path_text)
    if not path.is_file():
        raise FileNotFoundError(f"input video does not exist: {path}")
    cap = cv2.VideoCapture(str(path))
    try:
        if not cap.isOpened():
            raise RuntimeError(f"OpenCV could not open input video: {path}")
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        source_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        if width <= 0 or height <= 0:
            raise RuntimeError(f"OpenCV reported invalid video dimensions for {path}: {width}x{height}")
        return {
            "kind": "file",
            "path": str(path),
            "width": width,
            "height": height,
            "frame_count": frame_count,
            "source_fps": source_fps,
        }
    finally:
        cap.release()


def open_camera(index: int):
    import cv2

    camera = cv2.VideoCapture(index)
    if not camera.isOpened():
        camera.release()
        raise RuntimeError(f"cv2.VideoCapture({index}) could not be opened")
    return camera


def set_model_type(detector: Any, model_type: str) -> None:
    if model_type == "retinanet":
        detector.setModelTypeAsRetinaNet()
    elif model_type == "yolov3":
        detector.setModelTypeAsYOLOv3()
    elif model_type == "tiny-yolov3":
        detector.setModelTypeAsTinyYOLOv3()
    else:  # argparse should prevent this
        raise ValueError(f"unsupported model type: {model_type}")


def parse_custom_objects(value: Optional[str]) -> List[str]:
    if not value:
        return []
    labels = []
    for raw in value.split(","):
        label = raw.strip().replace(" ", "_").replace("-", "_")
        if label:
            labels.append(label)
    return labels


def build_coco_custom_objects(detector: Any, labels: Iterable[str]) -> Optional[Dict[str, bool]]:
    labels = list(labels)
    if not labels:
        return None
    available = detector.CustomObjects()
    missing = [label for label in labels if label not in available]
    if missing:
        supported = ", ".join(sorted(available))
        raise ValueError(
            "unsupported COCO custom object label(s): "
            + ", ".join(missing)
            + ". Supported labels for the loaded model are: "
            + supported
        )
    selected = {label: False for label in available}
    for label in labels:
        selected[label] = True
    return selected


class AnalysisSummary:
    def __init__(self) -> None:
        self.data: Dict[str, Any] = {
            "frames": {"called": 0, "samples": [], "truncated": False},
            "seconds": {"called": 0, "samples": [], "truncated": False},
            "minutes": {"called": 0, "samples": [], "truncated": False},
            "complete": None,
        }

    def _append_sample(self, section: str, sample: Dict[str, Any]) -> None:
        bucket = self.data[section]
        bucket["called"] += 1
        if len(bucket["samples"]) < MAX_STORED_ANALYSIS_EVENTS:
            bucket["samples"].append(sample)
        else:
            bucket["truncated"] = True

    @staticmethod
    def _count_dict(counts: Dict[str, Any]) -> Dict[str, int]:
        return {str(key): int(value) for key, value in dict(counts).items()}

    def per_frame(self, frame_number: int, output_array: List[Dict[str, Any]], output_count: Dict[str, Any]) -> None:
        self._append_sample(
            "frames",
            {
                "frame": int(frame_number),
                "detections": len(output_array),
                "counts": self._count_dict(output_count),
            },
        )

    def per_second(
        self,
        second_number: int,
        output_arrays: List[List[Dict[str, Any]]],
        count_arrays: List[Dict[str, Any]],
        average_output_count: Dict[str, Any],
    ) -> None:
        self._append_sample(
            "seconds",
            {
                "second": int(second_number),
                "frames_in_window": len(output_arrays),
                "non_empty_frames": sum(1 for detections in output_arrays if detections),
                "average_output_count": self._count_dict(average_output_count),
                "last_frame_count": self._count_dict(count_arrays[-1]) if count_arrays else {},
            },
        )

    def per_minute(
        self,
        minute_number: int,
        output_arrays: List[List[Dict[str, Any]]],
        count_arrays: List[Dict[str, Any]],
        average_output_count: Dict[str, Any],
    ) -> None:
        self._append_sample(
            "minutes",
            {
                "minute": int(minute_number),
                "frames_in_window": len(output_arrays),
                "non_empty_frames": sum(1 for detections in output_arrays if detections),
                "average_output_count": self._count_dict(average_output_count),
                "last_frame_count": self._count_dict(count_arrays[-1]) if count_arrays else {},
            },
        )

    def complete(
        self,
        output_arrays: List[List[Dict[str, Any]]],
        count_arrays: List[Dict[str, Any]],
        average_output_count: Dict[str, Any],
    ) -> None:
        self.data["complete"] = {
            "frames": len(output_arrays),
            "count_arrays": len(count_arrays),
            "non_empty_frames": sum(1 for detections in output_arrays if detections),
            "average_output_count": self._count_dict(average_output_count),
        }


def make_detector(args: argparse.Namespace) -> Any:
    if args.mode == "coco":
        from imageai.Detection import VideoObjectDetection

        detector = VideoObjectDetection()
    else:
        from imageai.Detection.Custom import CustomVideoObjectDetection

        detector = CustomVideoObjectDetection()

    set_model_type(detector, args.model_type)
    detector.setModelPath(str(Path(args.model_path)))
    if args.mode == "custom":
        detector.setJsonPath(str(Path(args.json_path)))
    if args.cpu:
        detector.useCPU()
    detector.loadModel()
    return detector


def run(args: argparse.Namespace) -> Dict[str, Any]:
    output_base, warnings = normalize_output_base(args.output_video)
    save_detected_video = not args.no_save

    source_summary: Dict[str, Any]
    camera = None
    if args.input_video:
        source_summary = validate_video_file(args.input_video)
        input_file_path = args.input_video
        camera_input = None
    else:
        camera = open_camera(args.camera_index)
        source_summary = {"kind": "camera", "camera_index": args.camera_index}
        input_file_path = ""
        camera_input = camera

    temp_output_dir: Optional[tempfile.TemporaryDirectory[str]] = None
    if not save_detected_video:
        # ImageAI constructs a VideoWriter even when save_detected_video=False.
        # Use a temporary base path so a no-save run never creates './.mp4'.
        temp_output_dir = tempfile.TemporaryDirectory(prefix="imageai-video-nosave-")
        output_base_for_api = str(Path(temp_output_dir.name) / "discard")
    else:
        output_base_for_api = output_base

    threshold = args.minimum_percentage_probability
    if threshold is None:
        threshold = 40 if args.mode == "custom" else 50

    analysis: Optional[AnalysisSummary] = AnalysisSummary() if args.analysis_summary else None
    detector = make_detector(args)
    custom_objects = None
    if args.mode == "coco":
        custom_objects = build_coco_custom_objects(detector, parse_custom_objects(args.custom_objects))

    detection_kwargs: Dict[str, Any] = {
        "input_file_path": input_file_path,
        "camera_input": camera_input,
        "output_file_path": output_base_for_api or "",
        "frames_per_second": args.fps,
        "frame_detection_interval": args.frame_detection_interval,
        "minimum_percentage_probability": threshold,
        "log_progress": args.log_progress,
        "display_percentage_probability": not args.hide_probability,
        "display_object_name": not args.hide_name,
        "display_box": not args.hide_box,
        "save_detected_video": save_detected_video,
        "detection_timeout": args.timeout,
    }
    if analysis is not None:
        detection_kwargs.update(
            {
                "per_frame_function": analysis.per_frame,
                "per_second_function": analysis.per_second,
                "per_minute_function": analysis.per_minute,
                "video_complete_function": analysis.complete,
                "return_detected_frame": False,
            }
        )
    if args.mode == "coco":
        detection_kwargs["custom_objects"] = custom_objects

    try:
        returned_path = detector.detectObjectsFromVideo(**detection_kwargs)
    finally:
        if camera is not None:
            camera.release()
        if temp_output_dir is not None:
            temp_output_dir.cleanup()

    result: Dict[str, Any] = {
        "mode": args.mode,
        "model_type": args.model_type,
        "source": source_summary,
        "save_detected_video": save_detected_video,
        "output_base": output_base,
        "returned_path": returned_path,
        "frames_per_second": args.fps,
        "frame_detection_interval": args.frame_detection_interval,
        "minimum_percentage_probability": threshold,
        "detection_timeout": args.timeout,
        "display_percentage_probability": not args.hide_probability,
        "display_object_name": not args.hide_name,
        "display_box": not args.hide_box,
        "used_cpu_flag": bool(args.cpu),
        "custom_objects": parse_custom_objects(args.custom_objects) if args.mode == "coco" else None,
        "warnings": warnings,
    }
    if analysis is not None:
        result["analysis"] = analysis.data
    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)
    try:
        result = run(args)
    except Exception as exc:  # keep CLI failures concise and machine-readable enough for agents
        print(json.dumps({"ok": False, "error": str(exc), "error_type": type(exc).__name__}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
