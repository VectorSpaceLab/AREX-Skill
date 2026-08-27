#!/usr/bin/env python3
"""Safe CLI helper for ImageAI still-image object detection.

The helper deliberately does not download model weights and does not assume a
repository checkout or current working directory. Supply explicit paths to model
assets and images. Relative paths, if used, resolve according to the shell that
invokes this script.
"""

from __future__ import annotations

import argparse
import json
import sys
from difflib import get_close_matches
from pathlib import Path
from typing import Any, Iterable


COCO80_KEYS = (
    "person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
    "traffic_light", "fire_hydrant", "stop_sign", "parking_meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports_ball",
    "kite", "baseball_bat", "baseball_glove", "skateboard", "surfboard", "tennis_racket",
    "bottle", "wine_glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot_dog", "pizza", "donut", "cake", "chair",
    "sofa", "pottedplant", "bed", "diningtable", "toilet", "tvmonitor", "laptop", "mouse",
    "remote", "keyboard", "cell_phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy_bear", "hair_drier", "toothbrush",
)

COCO91_KEYS = (
    "unlabeled", "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic_light", "fire_hydrant", "street_sign", "stop_sign", "parking_meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe",
    "hat", "backpack", "umbrella", "shoe", "eye_glasses", "handbag", "tie", "suitcase",
    "frisbee", "skis", "snowboard", "sports_ball", "kite", "baseball_bat", "baseball_glove",
    "skateboard", "surfboard", "tennis_racket", "bottle", "plate", "wine_glass", "cup", "fork",
    "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli", "carrot",
    "hot_dog", "pizza", "donut", "cake", "chair", "couch", "potted_plant", "bed", "mirror",
    "dining_table", "window", "desk", "toilet", "door", "tv", "laptop", "mouse", "remote",
    "keyboard", "cell_phone", "microwave", "oven", "toaster", "sink", "refrigerator", "blender",
    "book", "clock", "vase", "scissors", "teddy_bear", "hair_drier", "toothbrush", "hair_brush",
)


class UserFacingError(RuntimeError):
    """Runtime error with a concise message intended for CLI users."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run ImageAI still-image object detection with explicit local model assets.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--mode", choices=("coco", "custom"), required=True, help="Use COCO pretrained detection or a custom ImageAI YOLO detector.")
    parser.add_argument("--model-type", choices=("retinanet", "yolov3", "tiny-yolov3"), required=True, help="Detection model architecture. RetinaNet is COCO-only.")
    parser.add_argument("--model-path", required=True, help="Path to a local .pt or .pth ImageAI model weight file.")
    parser.add_argument("--json-path", help="Path to custom detection config JSON; required in custom mode.")
    parser.add_argument("--input-image", required=True, help="Path to an input .jpg, .jpeg, or .png image.")
    parser.add_argument("--output-image", help="Path for annotated output image. Required for --output-type file; optional convenience save for --output-type array.")
    parser.add_argument("--output-type", choices=("file", "array"), default="file", help="ImageAI output mode.")
    parser.add_argument("--extract", action="store_true", help="Extract detected object crops as paths in file mode or arrays in array mode.")
    parser.add_argument("--minimum-percentage-probability", type=float, help="Final confidence threshold in 0-100 units; defaults to 50 for COCO and 40 for custom detection.")
    parser.add_argument("--hide-name", action="store_true", help="Hide object names on the rendered output image.")
    parser.add_argument("--hide-probability", action="store_true", help="Hide probability text on the rendered output image.")
    parser.add_argument("--hide-box", action="store_true", help="Hide bounding boxes on the rendered output image.")
    parser.add_argument("--custom-objects", help="Comma-separated object filter. COCO names use CustomObjects keywords; custom names use JSON labels with spaces replaced by underscores.")
    parser.add_argument("--nms-treshold", type=float, help="Custom YOLO non-maximum suppression threshold; note ImageAI source spelling 'treshold'.")
    parser.add_argument("--objectness-treshold", type=float, help="Custom YOLO objectness threshold; note ImageAI source spelling 'treshold'.")
    parser.add_argument("--cpu", action="store_true", help="Force CPU inference before loading the model.")
    parser.add_argument("--print-json", action="store_true", help="Print a machine-readable JSON summary instead of human-readable lines.")
    return parser


def normalize_path(path_text: str) -> Path:
    return Path(path_text).expanduser().resolve()


def validate_existing_file(parser: argparse.ArgumentParser, label: str, path_text: str) -> Path:
    path = normalize_path(path_text)
    if not path.is_file():
        parser.error(f"{label} does not exist or is not a file: {path}")
    return path


def validate_model_path(parser: argparse.ArgumentParser, path_text: str) -> Path:
    path = validate_existing_file(parser, "--model-path", path_text)
    if path.suffix == ".h5":
        parser.error("--model-path points to a TensorFlow-era .h5 model. ImageAI 3.x object detection expects PyTorch .pt or .pth weights.")
    if path.suffix not in {".pt", ".pth"}:
        parser.error(f"--model-path must end with .pt or .pth, got: {path.name}")
    return path


def validate_image_path(parser: argparse.ArgumentParser, path_text: str) -> Path:
    path = validate_existing_file(parser, "--input-image", path_text)
    if path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        parser.error(f"--input-image must be a .jpg, .jpeg, or .png file, got: {path.name}")
    return path


def validate_output_path(parser: argparse.ArgumentParser, output_text: str | None, input_path: Path, required: bool) -> Path | None:
    if required and not output_text:
        parser.error("--output-image is required when --output-type file is selected so the annotated image has an explicit destination.")
    if not output_text:
        return None
    output_path = normalize_path(output_text)
    if output_path == input_path:
        parser.error("--output-image must not be the same file as --input-image; refusing to overwrite the input image.")
    if output_path.parent and not output_path.parent.is_dir():
        parser.error(f"Parent directory for --output-image does not exist: {output_path.parent}")
    return output_path


def current_extraction_dir(output_image: Path) -> Path:
    # Match the current ImageAI source: '.'.join(output_image_path.split('.')[:-1]) + '-extracted'.
    return Path(".".join(str(output_image).split(".")[:-1]) + "-extracted")


def validate_probability(parser: argparse.ArgumentParser, name: str, value: float | None, default: float) -> float:
    if value is None:
        return default
    if not 0 <= value <= 100:
        parser.error(f"{name} must be between 0 and 100, got {value}")
    return value


def validate_unit_interval(parser: argparse.ArgumentParser, name: str, value: float | None, default: float) -> float:
    if value is None:
        return default
    if not 0 <= value <= 1:
        parser.error(f"{name} must be between 0 and 1, got {value}")
    return value


def parse_object_list(text: str | None, *, lower: bool) -> list[str]:
    if not text:
        return []
    objects = []
    for raw in text.split(","):
        item = raw.strip().replace(" ", "_")
        if lower:
            item = item.lower()
        if item:
            objects.append(item)
    return objects


def unsupported_message(items: Iterable[str], valid_keys: Iterable[str]) -> str:
    valid = sorted(set(valid_keys))
    chunks = []
    for item in items:
        matches = get_close_matches(item, valid, n=3, cutoff=0.55)
        if matches:
            chunks.append(f"{item!r} (did you mean: {', '.join(matches)})")
        else:
            chunks.append(repr(item))
    return "Unsupported object names: " + ", ".join(chunks)


def load_custom_detection_config(parser: argparse.ArgumentParser, json_text: str | None) -> tuple[Path, list[str], list[Any]]:
    if not json_text:
        parser.error("--json-path is required in custom mode.")
    json_path = validate_existing_file(parser, "--json-path", json_text)
    try:
        with json_path.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
    except json.JSONDecodeError as exc:
        parser.error(f"--json-path is not valid JSON: {exc}")
    if not isinstance(config, dict):
        parser.error("--json-path must contain a JSON object with 'labels' and 'anchors'.")
    labels = config.get("labels")
    anchors = config.get("anchors")
    if not isinstance(labels, list) or not all(isinstance(label, str) for label in labels) or not labels:
        parser.error("--json-path must contain a non-empty string array at key 'labels'.")
    if not isinstance(anchors, list) or not anchors:
        parser.error("--json-path must contain a non-empty array at key 'anchors'.")
    return json_path, labels, anchors


def build_custom_filter_for_config(parser: argparse.ArgumentParser, requested: list[str], labels: list[str]) -> dict[str, bool] | None:
    if not requested:
        return None
    exact_key_by_lower: dict[str, str] = {}
    valid_exact = []
    for label in labels:
        key = label.replace(" ", "_")
        valid_exact.append(key)
        exact_key_by_lower.setdefault(key.lower(), key)
    selected: dict[str, bool] = {}
    unsupported = []
    for item in requested:
        exact = exact_key_by_lower.get(item.lower())
        if exact is None:
            unsupported.append(item)
        else:
            selected[exact] = True
    if unsupported:
        parser.error(unsupported_message(unsupported, valid_exact))
    return selected


def build_coco_filter(parser: argparse.ArgumentParser, requested: list[str], model_type: str, detector: Any) -> dict[str, bool] | None:
    if not requested:
        return None
    valid = COCO91_KEYS if model_type == "retinanet" else COCO80_KEYS
    unsupported = [item for item in requested if item not in valid]
    if unsupported:
        parser.error(unsupported_message(unsupported, valid))
    kwargs = {item: True for item in requested}
    return detector.CustomObjects(**kwargs)


def set_model_type(detector: Any, model_type: str) -> None:
    if model_type == "retinanet":
        detector.setModelTypeAsRetinaNet()
    elif model_type == "yolov3":
        detector.setModelTypeAsYOLOv3()
    elif model_type == "tiny-yolov3":
        detector.setModelTypeAsTinyYOLOv3()
    else:  # argparse should prevent this.
        raise UserFacingError(f"Unsupported model type: {model_type}")


def summarize_array(value: Any) -> dict[str, Any]:
    shape = getattr(value, "shape", None)
    dtype = getattr(value, "dtype", None)
    return {
        "type": type(value).__name__,
        "shape": list(shape) if shape is not None else None,
        "dtype": str(dtype) if dtype is not None else None,
    }


def split_result(result: Any, output_type: str, extract: bool) -> tuple[list[dict[str, Any]], Any | None, list[Any]]:
    image_array = None
    extracted: list[Any] = []
    if output_type == "array":
        if extract:
            if not isinstance(result, tuple) or len(result) != 3:
                raise UserFacingError(f"Unexpected array/extraction return shape from ImageAI: {type(result).__name__}")
            image_array, detections, extracted = result
        else:
            if not isinstance(result, tuple) or len(result) != 2:
                raise UserFacingError(f"Unexpected array return shape from ImageAI: {type(result).__name__}")
            image_array, detections = result
    else:
        if extract:
            if not isinstance(result, tuple) or len(result) != 2:
                raise UserFacingError(f"Unexpected file/extraction return shape from ImageAI: {type(result).__name__}")
            detections, extracted = result
        else:
            detections = result
    if not isinstance(detections, list):
        raise UserFacingError(f"Unexpected detections type from ImageAI: {type(detections).__name__}; expected list of dictionaries.")
    return detections, image_array, list(extracted or [])


def run_detection(args: argparse.Namespace, parser: argparse.ArgumentParser) -> dict[str, Any]:
    if args.mode == "custom" and args.model_type == "retinanet":
        parser.error("retinanet is only supported in --mode coco; custom detection supports yolov3 and tiny-yolov3.")
    if args.mode == "coco" and args.json_path:
        parser.error("--json-path is only used in --mode custom.")
    if args.mode == "coco" and (args.nms_treshold is not None or args.objectness_treshold is not None):
        parser.error("--nms-treshold and --objectness-treshold apply only in --mode custom.")

    model_path = validate_model_path(parser, args.model_path)
    input_path = validate_image_path(parser, args.input_image)
    output_path = validate_output_path(parser, args.output_image, input_path, required=(args.output_type == "file"))

    if args.extract and args.output_type == "file":
        if output_path is None:
            parser.error("--output-image is required when --output-type file is used with --extract.")
        extraction_dir = current_extraction_dir(output_path)
        if extraction_dir.exists():
            parser.error(f"Extraction directory already exists and ImageAI will not reuse it: {extraction_dir}")
    else:
        extraction_dir = None

    minimum_probability = validate_probability(
        parser,
        "--minimum-percentage-probability",
        args.minimum_percentage_probability,
        default=40.0 if args.mode == "custom" else 50.0,
    )
    nms_treshold = validate_unit_interval(parser, "--nms-treshold", args.nms_treshold, default=0.4)
    objectness_treshold = validate_unit_interval(parser, "--objectness-treshold", args.objectness_treshold, default=0.4)

    custom_json_path = None
    custom_labels: list[str] | None = None
    custom_filter = None
    if args.mode == "custom":
        custom_json_path, custom_labels, _anchors = load_custom_detection_config(parser, args.json_path)
        requested = parse_object_list(args.custom_objects, lower=False)
        custom_filter = build_custom_filter_for_config(parser, requested, custom_labels)
    else:
        requested = parse_object_list(args.custom_objects, lower=True)
        valid_coco_keys = COCO91_KEYS if args.model_type == "retinanet" else COCO80_KEYS
        unsupported = [item for item in requested if item not in valid_coco_keys]
        if unsupported:
            parser.error(unsupported_message(unsupported, valid_coco_keys))

    try:
        if args.mode == "coco":
            from imageai.Detection import ObjectDetection
            detector = ObjectDetection()
        else:
            from imageai.Detection.Custom import CustomObjectDetection
            detector = CustomObjectDetection()
    except Exception as exc:  # pragma: no cover - environment-specific
        raise UserFacingError(f"Failed to import ImageAI detection APIs. Install ImageAI and its PyTorch/OpenCV dependencies first. Import error: {exc}") from exc

    set_model_type(detector, args.model_type)
    detector.setModelPath(str(model_path))
    if custom_json_path is not None:
        detector.setJsonPath(str(custom_json_path))
    if args.cpu:
        detector.useCPU()
    detector.loadModel()

    if args.mode == "coco":
        custom_filter = build_coco_filter(parser, requested, args.model_type, detector)

    call_kwargs: dict[str, Any] = {
        "input_image": str(input_path),
        "output_image_path": str(output_path) if args.output_type == "file" and output_path is not None else None,
        "output_type": args.output_type,
        "extract_detected_objects": bool(args.extract),
        "minimum_percentage_probability": minimum_probability,
        "display_percentage_probability": not args.hide_probability,
        "display_object_name": not args.hide_name,
        "display_box": not args.hide_box,
        "custom_objects": custom_filter,
    }
    if args.mode == "custom":
        call_kwargs["nms_treshold"] = nms_treshold
        call_kwargs["objectness_treshold"] = objectness_treshold

    result = detector.detectObjectsFromImage(**call_kwargs)
    detections, image_array, extracted = split_result(result, args.output_type, bool(args.extract))

    wrote_array_output = False
    if args.output_type == "array" and output_path is not None:
        try:
            import cv2
        except Exception as exc:  # pragma: no cover - environment-specific
            raise UserFacingError(f"Array output was produced but cv2 could not be imported to write --output-image: {exc}") from exc
        if not cv2.imwrite(str(output_path), image_array):
            raise UserFacingError(f"cv2.imwrite failed for --output-image: {output_path}")
        wrote_array_output = True

    if args.output_type == "file" and output_path is not None and not output_path.is_file():
        raise UserFacingError(f"ImageAI completed but did not write the expected output image: {output_path}")

    if args.extract and args.output_type == "file":
        extracted_summary: Any = [str(Path(item)) for item in extracted]
    elif args.extract:
        extracted_summary = [summarize_array(item) for item in extracted]
    else:
        extracted_summary = []

    summary = {
        "mode": args.mode,
        "model_type": args.model_type,
        "model_path": str(model_path),
        "json_path": str(custom_json_path) if custom_json_path is not None else None,
        "input_image": str(input_path),
        "output_type": args.output_type,
        "output_image": str(output_path) if output_path is not None else None,
        "output_image_written": bool(output_path and output_path.is_file()),
        "array_output_saved_by_helper": wrote_array_output,
        "extract": bool(args.extract),
        "extraction_dir": str(extraction_dir) if extraction_dir is not None else None,
        "minimum_percentage_probability": minimum_probability,
        "nms_treshold": nms_treshold if args.mode == "custom" else None,
        "objectness_treshold": objectness_treshold if args.mode == "custom" else None,
        "custom_objects": requested,
        "detections_count": len(detections),
        "detections": detections,
        "image_array": summarize_array(image_array) if image_array is not None else None,
        "extracted_count": len(extracted),
        "extracted": extracted_summary,
    }
    if custom_labels is not None:
        summary["custom_config_labels"] = custom_labels
    return summary


def print_human(summary: dict[str, Any]) -> None:
    print(f"Mode: {summary['mode']}  Model: {summary['model_type']}  Detections: {summary['detections_count']}")
    if summary.get("output_image"):
        status = "written" if summary.get("output_image_written") else "not written"
        print(f"Output image: {summary['output_image']} ({status})")
    if summary.get("extraction_dir"):
        print(f"Extraction directory: {summary['extraction_dir']}")
    if not summary["detections"]:
        print("No detections returned.")
    for item in summary["detections"]:
        print(f"{item.get('name')} : {item.get('percentage_probability')} : {item.get('box_points')}")
    if summary.get("extract"):
        print(f"Extracted objects: {summary['extracted_count']}")
        for item in summary.get("extracted", []):
            print(f"  {item}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    summary = run_detection(args, parser)
    if args.print_json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human(summary)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UserFacingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
