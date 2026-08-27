#!/usr/bin/env python3
"""Safe JSON-printing helper for ImageAI image classification.

This script wraps ImageAI 3.x PyTorch classification inference for two modes:
- ImageNet classification with imageai.Classification.ImageClassification
- Custom classification with imageai.Classification.Custom.CustomImageClassification

It never downloads weights and never assumes assets live in the current working
folder. Supply explicit local paths for the model, image, and (custom mode) JSON
class mapping.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path
from typing import Any, Callable

VALID_MODES = {"imagenet", "custom"}
VALID_MODEL_TYPES = {"mobilenetv2", "resnet50", "inceptionv3", "densenet121"}
VALID_MODEL_SUFFIXES = {".pt", ".pth"}


class JsonArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that emits machine-readable errors."""

    def error(self, message: str) -> None:  # pragma: no cover - argparse hook
        payload = {"ok": False, "error": message, "usage": self.format_usage().strip()}
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)


def emit_error(message: str, *, code: int = 2, details: dict[str, Any] | None = None) -> None:
    payload: dict[str, Any] = {"ok": False, "error": message}
    if details:
        payload["details"] = details
    print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
    raise SystemExit(code)


def resolve_file(path_text: str, role: str) -> Path:
    try:
        path = Path(path_text).expanduser().resolve(strict=False)
    except Exception as exc:  # defensive: malformed path-like input
        emit_error(f"Invalid {role} path: {path_text!r}", details={"exception": str(exc)})
    if not path.is_file():
        emit_error(f"Missing {role} file: {path}")
    return path


def validate_model_file(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix == ".h5":
        emit_error(
            "TensorFlow/Keras .h5 models are not supported by ImageAI 3.x classification. "
            "Use a PyTorch .pt/.pth model, or use ImageAI 2.1.6 or earlier for legacy .h5 artifacts.",
            details={"model_path": str(path)},
        )
    if suffix not in VALID_MODEL_SUFFIXES:
        emit_error(
            "Invalid model file extension. ImageAI 3.x classification expects a .pt or .pth PyTorch model file.",
            details={"model_path": str(path), "suffix": suffix or "<none>"},
        )


def validate_json_file(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        emit_error(
            "Invalid custom class JSON mapping; file is not valid JSON.",
            details={"json_path": str(path), "line": exc.lineno, "column": exc.colno, "message": exc.msg},
        )
    except OSError as exc:
        emit_error("Unable to read custom class JSON mapping.", details={"json_path": str(path), "exception": str(exc)})

    if not isinstance(data, dict) or not data:
        emit_error(
            "Invalid custom class JSON mapping; expected a non-empty object mapping class indices to labels.",
            details={"json_path": str(path)},
        )
    return len(data)


def set_model_type(classifier: Any, model_type: str) -> None:
    setters: dict[str, str] = {
        "mobilenetv2": "setModelTypeAsMobileNetV2",
        "resnet50": "setModelTypeAsResNet50",
        "inceptionv3": "setModelTypeAsInceptionV3",
        "densenet121": "setModelTypeAsDenseNet121",
    }
    setter_name = setters.get(model_type)
    if setter_name is None:
        emit_error(
            "Invalid model type. Choose one of: mobilenetv2, resnet50, inceptionv3, densenet121.",
            details={"model_type": model_type},
        )
    getattr(classifier, setter_name)()


def import_classifier(mode: str) -> Callable[[], Any]:
    try:
        if mode == "imagenet":
            from imageai.Classification import ImageClassification

            return ImageClassification
        if mode == "custom":
            from imageai.Classification.Custom import CustomImageClassification

            return CustomImageClassification
    except ModuleNotFoundError as exc:
        missing = exc.name or "unknown"
        if missing == "imageai":
            message = "ImageAI is not installed in the active Python environment. Install imageai before running classification."
        elif missing in {"torch", "torchvision", "PIL", "numpy"}:
            message = f"ImageAI dependency {missing!r} is missing in the active Python environment."
        else:
            message = f"A required Python module is missing while importing ImageAI: {missing!r}."
        emit_error(message, details={"missing_module": missing}, code=3)
    except Exception as exc:
        emit_error(
            "Failed to import ImageAI classification APIs in the active Python environment.",
            details={"exception_type": type(exc).__name__, "exception": str(exc)},
            code=3,
        )

    emit_error("Invalid mode. Choose 'imagenet' or 'custom'.", details={"mode": mode})


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = JsonArgumentParser(
        description="Run ImageAI ImageNet or custom image classification and print JSON results.",
    )
    parser.add_argument("--mode", required=True, choices=sorted(VALID_MODES), help="Classification mode: imagenet or custom.")
    parser.add_argument(
        "--model-type",
        required=True,
        choices=sorted(VALID_MODEL_TYPES),
        help="Architecture matching the supplied weights.",
    )
    parser.add_argument("--model-path", required=True, help="Path to a local .pt or .pth model file.")
    parser.add_argument("--image", required=True, help="Path to a local image file readable by Pillow/ImageAI.")
    parser.add_argument("--result-count", type=int, default=5, help="Number of top labels to return. Default: 5.")
    parser.add_argument("--cpu", action="store_true", help="Force CPU inference by calling ImageAI useCPU().")
    parser.add_argument("--json-path", help="Path to custom class mapping JSON. Required when --mode custom.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if args.result_count < 1:
        emit_error("--result-count must be at least 1.", details={"result_count": args.result_count})
    if args.mode == "imagenet" and args.result_count > 1000:
        emit_error("--result-count for ImageNet mode cannot exceed 1000.", details={"result_count": args.result_count})

    model_path = resolve_file(args.model_path, "model")
    validate_model_file(model_path)
    image_path = resolve_file(args.image, "image")

    json_path: Path | None = None
    custom_class_count: int | None = None
    if args.mode == "custom":
        if not args.json_path:
            emit_error("--json-path is required when --mode custom.")
        json_path = resolve_file(args.json_path, "custom class JSON mapping")
        custom_class_count = validate_json_file(json_path)
        if args.result_count > custom_class_count:
            emit_error(
                "--result-count cannot exceed the number of classes in the custom JSON mapping.",
                details={"result_count": args.result_count, "class_count": custom_class_count},
            )
    elif args.json_path:
        emit_error("--json-path is only valid with --mode custom.")

    classifier_cls = import_classifier(args.mode)
    classifier = classifier_cls()
    set_model_type(classifier, args.model_type)

    imageai_stdout = io.StringIO()
    imageai_stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(imageai_stdout), contextlib.redirect_stderr(imageai_stderr):
            classifier.setModelPath(str(model_path))
            if json_path is not None:
                classifier.setJsonPath(str(json_path))
            if args.cpu:
                classifier.useCPU()
            classifier.loadModel()
            labels, probabilities = classifier.classifyImage(str(image_path), result_count=args.result_count)
    except Exception as exc:
        details: dict[str, Any] = {"exception_type": type(exc).__name__, "exception": str(exc)}
        captured_stdout = imageai_stdout.getvalue().strip()
        captured_stderr = imageai_stderr.getvalue().strip()
        if captured_stdout or captured_stderr:
            details["captured_output"] = {}
            if captured_stdout:
                details["captured_output"]["stdout"] = captured_stdout[-4000:]
            if captured_stderr:
                details["captured_output"]["stderr"] = captured_stderr[-4000:]
        emit_error(
            "ImageAI classification failed. Check model type, model weights, custom JSON mapping, image file, and environment.",
            details=details,
            code=4,
        )

    predictions = [
        {"label": label, "probability": probability}
        for label, probability in zip(labels, probabilities)
    ]
    payload: dict[str, Any] = {
        "ok": True,
        "mode": args.mode,
        "model_type": args.model_type,
        "model_path": str(model_path),
        "image": str(image_path),
        "result_count": args.result_count,
        "cpu": bool(args.cpu),
        "predictions": predictions,
        "labels": labels,
        "probabilities": probabilities,
    }
    if json_path is not None:
        payload["json_path"] = str(json_path)
        payload["custom_class_count"] = custom_class_count

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
