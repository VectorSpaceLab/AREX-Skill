"""Safe synthetic smoke test for SAHI standard and sliced prediction APIs.

The script defines a deterministic in-memory DetectionModel subclass and runs
SAHI prediction on a synthetic image. It never downloads model weights, trains,
contacts the network, requires credentials, or writes outputs by default.
"""

from __future__ import annotations

import argparse
import math
from typing import Any


def import_runtime() -> dict[str, Any]:
    """Import SAHI runtime pieces after argparse so --help works without SAHI."""
    try:
        import numpy as np
        from sahi.models.base import DetectionModel
        from sahi.predict import get_prediction, get_sliced_prediction
        from sahi.prediction import ObjectPrediction
    except ImportError as exc:
        raise SystemExit(
            "Missing runtime dependency for the smoke test. Install/import SAHI with its base dependencies; "
            "no detector framework or model weights are required."
        ) from exc
    return {
        "np": np,
        "DetectionModel": DetectionModel,
        "ObjectPrediction": ObjectPrediction,
        "get_prediction": get_prediction,
        "get_sliced_prediction": get_sliced_prediction,
    }


def build_deterministic_model_class(detection_model_base: type, object_prediction_cls: type) -> type:
    """Create the dummy DetectionModel subclass after importing SAHI."""

    class DeterministicDetectionModel(detection_model_base):  # type: ignore[misc, valid-type]
        """Minimal DetectionModel that returns one predictable box per input image."""

        required_packages: list[str] | None = []

        def __init__(self, confidence_threshold: float = 0.25) -> None:
            super().__init__(
                model_path=None,
                model=None,
                config_path=None,
                device="cpu",
                confidence_threshold=confidence_threshold,
                category_mapping={"0": "synthetic-object"},
                load_at_init=False,
                image_size=None,
            )
            self.model = "deterministic-smoke-model"
            self.inference_calls = 0

        def load_model(self) -> None:
            self.model = "deterministic-smoke-model"

        def set_model(self, model: Any, **_: Any) -> None:
            self.model = model

        def perform_inference(self, image: Any) -> None:
            self.inference_calls += 1
            height, width = image.shape[:2]
            box_size = max(8, min(height, width) // 4)
            x1 = max(0, (width - box_size) // 2)
            y1 = max(0, (height - box_size) // 2)
            x2 = min(width, x1 + box_size)
            y2 = min(height, y1 + box_size)
            score = 0.91
            self._original_predictions = []
            if score >= self.confidence_threshold:
                self._original_predictions.append(
                    {
                        "bbox": [float(x1), float(y1), float(x2), float(y2)],
                        "score": score,
                        "category_id": 0,
                        "category_name": "synthetic-object",
                        "full_shape": [height, width],
                    }
                )

        def _create_object_prediction_list_from_original_predictions(
            self,
            shift_amount_list: list[list[int | float]] | list[int | float] | None = [[0, 0]],
            full_shape_list: list[list[int | float]] | list[int | float] | None = None,
        ) -> None:
            shifts = _normalize_pairs(shift_amount_list, default=[0, 0])
            full_shapes = _normalize_pairs(full_shape_list, default=None)
            shift = shifts[0] if shifts else [0, 0]
            full_shape = full_shapes[0] if full_shapes else None

            object_predictions = []
            for raw in self._original_predictions or []:
                object_predictions.append(
                    object_prediction_cls(
                        bbox=raw["bbox"],
                        category_id=raw["category_id"],
                        category_name=raw["category_name"],
                        score=raw["score"],
                        shift_amount=list(shift),
                        full_shape=full_shape or raw["full_shape"],
                    )
                )
            self._object_prediction_list_per_image = [object_predictions]

    return DeterministicDetectionModel


def _normalize_pairs(
    value: list[list[int | float]] | list[int | float] | None,
    default: list[int | float] | None,
) -> list[list[int | float]]:
    if value is None:
        return [] if default is None else [list(default)]
    if len(value) == 0:  # type: ignore[arg-type]
        return []
    if len(value) == 2 and all(isinstance(item, (int, float)) for item in value):  # type: ignore[arg-type]
        return [list(value)]  # type: ignore[list-item]
    return [list(item) for item in value]  # type: ignore[union-attr]


def make_image(np_module: Any, size: int) -> Any:
    image = np_module.zeros((size, size, 3), dtype=np_module.uint8)
    image[:, :, 0] = np_module.arange(size, dtype=np_module.uint8)[None, :] % 255
    image[:, :, 1] = np_module.arange(size, dtype=np_module.uint8)[:, None] % 255
    image[:, :, 2] = 127
    return image


def assert_prediction_result(result: Any, image_size: int, label: str) -> None:
    assert result.object_prediction_list, f"{label}: expected at least one prediction"
    assert "prediction" in result.durations_in_seconds, f"{label}: missing prediction duration"
    for pred in result.object_prediction_list:
        x1, y1, x2, y2 = pred.bbox.to_xyxy()
        assert pred.category.name == "synthetic-object", f"{label}: unexpected category {pred.category.name!r}"
        assert 0 <= x1 < x2 <= image_size, f"{label}: bbox x coordinates out of range: {pred.bbox.to_xyxy()}"
        assert 0 <= y1 < y2 <= image_size, f"{label}: bbox y coordinates out of range: {pred.bbox.to_xyxy()}"
        assert pred.score.value > 0.5, f"{label}: expected confidence above smoke threshold"


def run_standard(image: Any, model: Any, get_prediction: Any) -> Any:
    before = model.inference_calls
    result = get_prediction(image=image, detection_model=model, verbose=0)
    assert_prediction_result(result, image.shape[0], "standard")
    assert model.inference_calls == before + 1, "standard: expected exactly one inference call"
    assert len(result.object_prediction_list) == 1, "standard: dummy model should return one prediction"
    return result


def run_sliced(
    image: Any,
    model: Any,
    get_sliced_prediction: Any,
    slice_size: int,
    overlap: float,
    batch_size: int,
    perform_standard_pred: bool,
) -> Any:
    progress_events: list[tuple[int, int]] = []
    before = model.inference_calls
    result = get_sliced_prediction(
        image=image,
        detection_model=model,
        slice_height=slice_size,
        slice_width=slice_size,
        overlap_height_ratio=overlap,
        overlap_width_ratio=overlap,
        perform_standard_pred=perform_standard_pred,
        postprocess_type="GREEDYNMM",
        postprocess_match_metric="IOS",
        postprocess_match_threshold=0.5,
        postprocess_class_agnostic=False,
        verbose=0,
        progress_bar=False,
        progress_callback=lambda current, total: progress_events.append((current, total)),
        batch_size=batch_size,
    )
    assert_prediction_result(result, image.shape[0], "sliced")
    assert "slice" in result.durations_in_seconds, "sliced: missing slice duration"
    assert "postprocess" in result.durations_in_seconds, "sliced: missing postprocess duration"
    assert progress_events, "sliced: expected progress callback events"
    final_current, final_total = progress_events[-1]
    assert final_total >= 1, "sliced: expected at least one slice"
    assert final_current == final_total, f"sliced: final progress {progress_events[-1]} did not reach total"
    expected_min_calls = final_total + (1 if perform_standard_pred and final_total > 1 else 0)
    assert model.inference_calls >= before + expected_min_calls, "sliced: fewer inference calls than expected"
    expected_events = math.ceil(final_total / batch_size)
    assert len(progress_events) == expected_events, "sliced: callback count should match slice batches"
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a safe SAHI prediction smoke with a deterministic dummy model.")
    parser.add_argument("--mode", choices=["standard", "sliced", "both"], default="both", help="Prediction path to exercise.")
    parser.add_argument("--image-size", type=int, default=256, help="Synthetic square image size in pixels.")
    parser.add_argument("--slice-size", type=int, default=128, help="Slice height and width for sliced mode.")
    parser.add_argument("--overlap", type=float, default=0.2, help="Height/width overlap ratio for sliced mode.")
    parser.add_argument("--batch-size", type=int, default=1, help="Slices processed per batch in sliced mode.")
    parser.add_argument(
        "--no-standard-pass",
        action="store_true",
        help="Disable the extra full-image pass inside get_sliced_prediction.",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.25,
        help="Dummy model confidence threshold; values above 0.91 should fail assertions by design.",
    )
    args = parser.parse_args()

    if args.image_size <= 0:
        parser.error("--image-size must be positive")
    if args.slice_size <= 0:
        parser.error("--slice-size must be positive")
    if not 0 <= args.overlap < 1:
        parser.error("--overlap must satisfy 0 <= overlap < 1")
    if args.batch_size < 1:
        parser.error("--batch-size must be >= 1")
    if not 0 <= args.confidence_threshold <= 1:
        parser.error("--confidence-threshold must be between 0 and 1")
    return args


def main() -> None:
    args = parse_args()
    runtime = import_runtime()
    deterministic_model_cls = build_deterministic_model_class(
        runtime["DetectionModel"], runtime["ObjectPrediction"]
    )
    image = make_image(runtime["np"], args.image_size)
    model = deterministic_model_cls(confidence_threshold=args.confidence_threshold)

    if args.mode in {"standard", "both"}:
        standard = run_standard(image, model, runtime["get_prediction"])
        print(f"standard ok: {len(standard.object_prediction_list)} prediction")

    if args.mode in {"sliced", "both"}:
        sliced = run_sliced(
            image=image,
            model=model,
            get_sliced_prediction=runtime["get_sliced_prediction"],
            slice_size=args.slice_size,
            overlap=args.overlap,
            batch_size=args.batch_size,
            perform_standard_pred=not args.no_standard_pass,
        )
        print(f"sliced ok: {len(sliced.object_prediction_list)} predictions")

    print("SAHI sliced prediction smoke succeeded")


if __name__ == "__main__":
    main()
