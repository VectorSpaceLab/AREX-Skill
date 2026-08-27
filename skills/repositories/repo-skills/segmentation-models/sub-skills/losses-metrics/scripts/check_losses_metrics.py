#!/usr/bin/env python3
"""Deterministic Segmentation Models loss/metric smoke checks.

The script uses tiny in-memory tensors only. It is intended for validating the
runtime framework, loss/metric object construction, class indexing, per-image
aggregation, and optional threshold semantics before debugging a larger Keras
training pipeline.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

import numpy as np


GT0 = np.array(
    [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ],
    dtype="float32",
)

GT1 = np.array(
    [
        [1, 1, 0],
        [1, 1, 0],
        [0, 0, 0],
    ],
    dtype="float32",
)

PR1 = np.array(
    [
        [0, 0, 0],
        [1, 1, 0],
        [0, 0, 0],
    ],
    dtype="float32",
)

PR2 = np.array(
    [
        [0, 0, 0],
        [1, 1, 0],
        [1, 1, 0],
    ],
    dtype="float32",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run tiny deterministic assertions for segmentation_models losses and metrics.",
    )
    parser.add_argument(
        "--framework",
        choices=("tf.keras", "keras"),
        default=os.environ.get("SM_FRAMEWORK", "tf.keras"),
        help="Segmentation Models framework to set before import. Default: env SM_FRAMEWORK or tf.keras.",
    )
    parser.add_argument(
        "--threshold-demo",
        action="store_true",
        help="Also show strict metric threshold behavior around 0.5.",
    )
    parser.add_argument(
        "--smooth",
        type=float,
        default=1e-12,
        help="Smooth value for deterministic overlap checks. Default: 1e-12.",
    )
    return parser


def import_runtime(framework: str) -> tuple[Any, Any]:
    os.environ["SM_FRAMEWORK"] = framework
    try:
        import segmentation_models as sm  # noqa: WPS433 - import must happen after env selection
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise RuntimeError(
            "Could not import segmentation_models after setting SM_FRAMEWORK={!r}. "
            "Install segmentation-models plus a compatible Keras/TensorFlow backend."
            .format(framework)
        ) from exc

    if sm.framework() == "tf.keras":
        from tensorflow import keras  # noqa: WPS433
    elif sm.framework() == "keras":
        import keras  # noqa: WPS433
    else:  # pragma: no cover - defensive path
        raise RuntimeError("Unexpected Segmentation Models framework: {!r}".format(sm.framework()))

    return sm, keras


def to_4d(mask_2d: np.ndarray) -> np.ndarray:
    return mask_2d[None, :, :, None].astype("float32")


def eval_scalar(value: Any, keras: Any) -> float:
    if hasattr(value, "numpy"):
        value = value.numpy()
    else:
        value = keras.backend.eval(value)
    return float(np.asarray(value))


def assert_close(name: str, actual: float, expected: float, atol: float = 1e-6) -> None:
    if not np.allclose(actual, expected, atol=atol, rtol=0):
        raise AssertionError(f"{name}: expected {expected:.12g}, got {actual:.12g}")
    print(f"[ok] {name}: {actual:.8f} (expected {expected:.8f})")


def run_binary_overlap_checks(sm: Any, keras: Any, smooth: float) -> None:
    gt = to_4d(GT1)
    pr = to_4d(PR1)

    iou = eval_scalar(sm.metrics.IOUScore(smooth=smooth)(gt, pr), keras)
    f1 = eval_scalar(sm.metrics.FScore(beta=1, smooth=smooth)(gt, pr), keras)
    f2 = eval_scalar(sm.metrics.FScore(beta=2, smooth=smooth)(gt, pr), keras)
    precision = eval_scalar(sm.metrics.Precision(smooth=smooth)(gt, pr), keras)
    recall = eval_scalar(sm.metrics.Recall(smooth=smooth)(gt, pr), keras)
    jaccard_loss = eval_scalar(sm.losses.JaccardLoss(smooth=smooth)(gt, pr), keras)
    dice_loss = eval_scalar(sm.losses.DiceLoss(smooth=smooth)(gt, pr), keras)

    assert_close("IoU for TP=2 FP=0 FN=2", iou, 0.5)
    assert_close("F1/Dice score for TP=2 FP=0 FN=2", f1, 2.0 / 3.0)
    assert_close("F2 score for TP=2 FP=0 FN=2", f2, 5.0 / 9.0)
    assert_close("Precision for TP=2 FP=0", precision, 1.0)
    assert_close("Recall for TP=2 FN=2", recall, 0.5)
    assert_close("JaccardLoss = 1 - IoU", jaccard_loss, 0.5)
    assert_close("DiceLoss = 1 - F1", dice_loss, 1.0 / 3.0)


def run_per_image_checks(sm: Any, keras: Any, smooth: float) -> None:
    gt = np.stack([GT0, GT1], axis=0)[..., None].astype("float32")
    pr = np.stack([PR1, PR2], axis=0)[..., None].astype("float32")

    per_image = eval_scalar(sm.metrics.IOUScore(per_image=True, smooth=smooth)(gt, pr), keras)
    per_batch = eval_scalar(sm.metrics.IOUScore(per_image=False, smooth=smooth)(gt, pr), keras)

    assert_close("per_image IoU mean of empty-vs-fp and 1/3 cases", per_image, 1.0 / 6.0)
    assert_close("per_batch IoU over concatenated batch", per_batch, 0.25)


def run_class_index_checks(sm: Any, keras: Any, smooth: float) -> None:
    # Shape: B=1, H=1, W=3, C=3. Channel 0 is background; channels 1 and 2 are foreground.
    gt = np.array([[[[1, 0, 0], [0, 1, 0], [0, 0, 1]]]], dtype="float32")
    pr = np.array([[[[0, 0, 0], [0, 1, 0], [0, 0, 1]]]], dtype="float32")

    all_channels = eval_scalar(sm.metrics.IOUScore(smooth=smooth)(gt, pr), keras)
    foreground_only = eval_scalar(sm.metrics.IOUScore(class_indexes=[1, 2], smooth=smooth)(gt, pr), keras)
    weighted_foreground = eval_scalar(
        sm.metrics.IOUScore(class_indexes=[1, 2], class_weights=np.array([1.0, 0.5], dtype="float32"), smooth=smooth)(gt, pr),
        keras,
    )

    assert_close("all-channel IoU includes failed background", all_channels, 2.0 / 3.0)
    assert_close("class_indexes=[1,2] ignores background", foreground_only, 1.0)
    assert_close("class_weights multiply selected class scores before mean", weighted_foreground, 0.75)


def run_threshold_demo(sm: Any, keras: Any, smooth: float) -> None:
    gt = to_4d(GT1)
    at_threshold = to_4d(GT1 * 0.5)
    above_threshold = to_4d(GT1 * 0.51)

    strict_zero = eval_scalar(sm.metrics.IOUScore(threshold=0.5, smooth=smooth)(gt, at_threshold), keras)
    strict_one = eval_scalar(sm.metrics.IOUScore(threshold=0.5, smooth=smooth)(gt, above_threshold), keras)

    assert_close("threshold uses strict > so 0.5 becomes background", strict_zero, 0.0)
    assert_close("values above 0.5 become foreground", strict_one, 1.0)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sm, keras = import_runtime(args.framework)

    print("Segmentation Models version:", getattr(sm, "__version__", "unknown"))
    print("Segmentation Models framework:", sm.framework())
    print("Keras image data format:", keras.backend.image_data_format())

    run_binary_overlap_checks(sm, keras, args.smooth)
    run_per_image_checks(sm, keras, args.smooth)
    run_class_index_checks(sm, keras, args.smooth)
    if args.threshold_demo:
        run_threshold_demo(sm, keras, args.smooth)

    print("All deterministic loss/metric checks passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - command-line diagnostic path
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
