#!/usr/bin/env python3
"""Validate tiny SMP loss/metric tensor mode combinations and print JSON."""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any, Optional

torch = None
smp = None


MODE_CHOICES = ("binary", "multiclass", "multilabel")
LOSS_CHOICES = (
    "dice",
    "jaccard",
    "tversky",
    "focal",
    "lovasz",
    "soft-bce",
    "soft-ce",
    "mcc",
)
METRIC_REDUCTIONS = (
    "micro",
    "macro",
    "weighted",
    "micro-imagewise",
    "macro-imagewise",
    "weighted-imagewise",
    "none",
)


def positive_int(raw_value: str) -> int:
    parsed = int(raw_value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def parse_class_weights(raw_value: Optional[str]) -> Optional[list[float]]:
    if raw_value is None or raw_value == "":
        return None
    try:
        return [float(part.strip()) for part in raw_value.split(",")]
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "class weights must be a comma-separated float list"
        ) from error


def parse_zero_division(raw_value: str) -> str | float:
    if raw_value == "warn":
        return raw_value
    try:
        return float(raw_value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("zero division must be a float or 'warn'") from error


def tensor_to_json(tensor: torch.Tensor) -> Any:
    detached = tensor.detach().cpu()
    if detached.numel() == 1:
        return float(detached.reshape(-1)[0])
    return detached.tolist()


def deterministic_logits(shape: tuple[int, ...]) -> torch.Tensor:
    total_elements = math.prod(shape)
    return torch.linspace(-2.0, 2.0, steps=total_elements, dtype=torch.float32).reshape(
        shape
    )


def build_tensors(
    mode: str,
    batch_size: int,
    requested_classes: int,
    height: int,
    width: int,
    from_logits: bool,
    ignore_index: Optional[int],
) -> dict[str, torch.Tensor | int]:
    if mode == "binary":
        effective_classes = 1
        logits = deterministic_logits((batch_size, 1, height, width))
        target = (
            torch.arange(batch_size * height * width).reshape(batch_size, 1, height, width)
            % 2
        ).long()
        if ignore_index is not None:
            target = target.clone()
            target[0, 0, 0, 0] = ignore_index
        loss_input = logits if from_logits else logits.sigmoid()
        return {
            "effective_classes": effective_classes,
            "logits": logits,
            "loss_input": loss_input,
            "target": target,
        }

    if requested_classes < 2:
        raise ValueError("multiclass and multilabel modes require --classes >= 2")

    if mode == "multiclass":
        effective_classes = requested_classes
        logits = deterministic_logits((batch_size, effective_classes, height, width))
        target = (
            torch.arange(batch_size * height * width).reshape(batch_size, height, width)
            % effective_classes
        ).long()
        if ignore_index is not None:
            target = target.clone()
            target[0, 0, 0] = ignore_index
        loss_input = logits if from_logits else logits.softmax(dim=1)
        return {
            "effective_classes": effective_classes,
            "logits": logits,
            "loss_input": loss_input,
            "target": target,
        }

    effective_classes = requested_classes
    logits = deterministic_logits((batch_size, effective_classes, height, width))
    target = (
        torch.arange(batch_size * effective_classes * height * width).reshape(
            batch_size, effective_classes, height, width
        )
        % 3
        == 0
    ).long()
    if ignore_index is not None:
        target = target.clone()
        target[0, 0, 0, 0] = ignore_index
    loss_input = logits if from_logits else logits.sigmoid()
    return {
        "effective_classes": effective_classes,
        "logits": logits,
        "loss_input": loss_input,
        "target": target,
    }


def make_loss(
    loss_name: str,
    mode: str,
    from_logits: bool,
    ignore_index: Optional[int],
    class_weights: Optional[list[float]],
    effective_classes: int,
) -> torch.nn.Module:
    if class_weights is not None and len(class_weights) != effective_classes:
        raise ValueError(
            f"class_weights length {len(class_weights)} does not match classes {effective_classes}"
        )

    if loss_name == "dice":
        return smp.losses.DiceLoss(
            mode=mode,
            from_logits=from_logits,
            ignore_index=ignore_index,
            class_weights=class_weights,
        )
    if loss_name == "jaccard":
        return smp.losses.JaccardLoss(
            mode=mode,
            from_logits=from_logits,
            ignore_index=ignore_index,
            class_weights=class_weights,
        )
    if loss_name == "tversky":
        return smp.losses.TverskyLoss(
            mode=mode,
            from_logits=from_logits,
            ignore_index=ignore_index,
            class_weights=class_weights,
        )
    if loss_name == "focal":
        if mode == "multilabel" and ignore_index is not None:
            raise ValueError(
                "FocalLoss with mode=multilabel and ignore_index is not a safe smoke-check combination; "
                "use DiceLoss, JaccardLoss, TverskyLoss, or SoftBCEWithLogitsLoss for ignored multilabel pixels, "
                "and mask ignored pixels before get_stats"
            )
        return smp.losses.FocalLoss(
            mode=mode,
            from_logits=from_logits,
            ignore_index=ignore_index,
            class_weights=class_weights,
        )
    if loss_name == "lovasz":
        if class_weights is not None:
            raise ValueError("LovaszLoss does not accept class_weights")
        return smp.losses.LovaszLoss(
            mode=mode,
            from_logits=from_logits,
            ignore_index=ignore_index,
        )
    if loss_name == "soft-bce":
        if mode == "multiclass":
            raise ValueError("SoftBCEWithLogitsLoss is for binary or multilabel targets")
        if class_weights is not None:
            raise ValueError("SoftBCEWithLogitsLoss uses weight/pos_weight, not class_weights")
        return smp.losses.SoftBCEWithLogitsLoss(ignore_index=ignore_index)
    if loss_name == "soft-ce":
        if mode != "multiclass":
            raise ValueError("SoftCrossEntropyLoss is for multiclass targets")
        if class_weights is not None:
            raise ValueError("SoftCrossEntropyLoss does not accept class_weights")
        return smp.losses.SoftCrossEntropyLoss(
            ignore_index=ignore_index,
            smooth_factor=0.0,
        )
    if loss_name == "mcc":
        if mode != "binary":
            raise ValueError("MCCLoss only supports binary targets")
        if ignore_index is not None:
            raise ValueError("MCCLoss does not support ignore_index")
        if class_weights is not None:
            raise ValueError("MCCLoss does not accept class_weights")
        return smp.losses.MCCLoss()
    raise ValueError(f"Unsupported loss: {loss_name}")


def loss_inputs_for_name(
    loss_name: str,
    mode: str,
    tensors: dict[str, torch.Tensor | int],
) -> tuple[torch.Tensor, torch.Tensor]:
    logits = tensors["logits"]
    loss_input = tensors["loss_input"]
    target = tensors["target"]
    assert isinstance(logits, torch.Tensor)
    assert isinstance(loss_input, torch.Tensor)
    assert isinstance(target, torch.Tensor)

    if loss_name == "soft-bce":
        return logits, target.float()
    if loss_name == "soft-ce":
        return logits, target.long()
    if loss_name == "mcc":
        return logits.sigmoid(), target.float()
    if mode == "multilabel":
        return loss_input, target.float()
    return loss_input, target.long()


def compute_metrics(
    mode: str,
    tensors: dict[str, torch.Tensor | int],
    metric_threshold: Optional[float],
    metric_reduction: str,
    zero_division: str | float,
    ignore_index: Optional[int],
) -> dict[str, Any]:
    logits = tensors["logits"]
    target = tensors["target"]
    effective_classes = tensors["effective_classes"]
    assert isinstance(logits, torch.Tensor)
    assert isinstance(target, torch.Tensor)
    assert isinstance(effective_classes, int)

    reduction = None if metric_reduction == "none" else metric_reduction

    if mode == "multiclass":
        metric_output = logits.argmax(dim=1).long()
        metric_target = target.long()
        stats_kwargs: dict[str, Any] = {
            "mode": mode,
            "num_classes": effective_classes,
        }
        if ignore_index is not None:
            stats_kwargs["ignore_index"] = ignore_index
    else:
        if ignore_index is not None:
            return {
                "computed": False,
                "reason": "smp.metrics.get_stats supports ignore_index only for multiclass mode",
            }
        probabilities = logits.sigmoid()
        metric_target = target.long()
        if metric_threshold is None:
            metric_output = (probabilities >= 0.5).long()
            stats_kwargs = {"mode": mode}
        else:
            metric_output = probabilities
            stats_kwargs = {"mode": mode, "threshold": metric_threshold}

    tp, fp, fn, tn = smp.metrics.get_stats(metric_output, metric_target, **stats_kwargs)
    score_kwargs = {"reduction": reduction, "zero_division": zero_division}
    return {
        "computed": True,
        "metric_output_shape": list(metric_output.shape),
        "metric_output_dtype": str(metric_output.dtype),
        "metric_target_shape": list(metric_target.shape),
        "stats_shape": list(tp.shape),
        "stats": {
            "tp": tensor_to_json(tp),
            "fp": tensor_to_json(fp),
            "fn": tensor_to_json(fn),
            "tn": tensor_to_json(tn),
        },
        "scores": {
            "iou": tensor_to_json(smp.metrics.iou_score(tp, fp, fn, tn, **score_kwargs)),
            "f1": tensor_to_json(smp.metrics.f1_score(tp, fp, fn, tn, **score_kwargs)),
            "accuracy": tensor_to_json(
                smp.metrics.accuracy(tp, fp, fn, tn, **score_kwargs)
            ),
            "precision": tensor_to_json(
                smp.metrics.precision(tp, fp, fn, tn, **score_kwargs)
            ),
            "recall": tensor_to_json(smp.metrics.recall(tp, fp, fn, tn, **score_kwargs)),
        },
    }


def validate(args: argparse.Namespace) -> dict[str, Any]:
    global torch, smp

    try:
        import torch as torch_module
        import segmentation_models_pytorch as smp_module
    except ImportError as error:
        raise RuntimeError(
            "validation requires torch and segmentation_models_pytorch to be installed"
        ) from error

    torch = torch_module
    smp = smp_module
    torch.manual_seed(0)
    class_weights = parse_class_weights(args.class_weights)
    zero_division = parse_zero_division(args.zero_division)
    tensors = build_tensors(
        mode=args.mode,
        batch_size=args.batch,
        requested_classes=args.classes,
        height=args.height,
        width=args.width,
        from_logits=args.from_logits,
        ignore_index=args.ignore_index,
    )
    effective_classes = tensors["effective_classes"]
    assert isinstance(effective_classes, int)

    loss = make_loss(
        loss_name=args.loss,
        mode=args.mode,
        from_logits=args.from_logits,
        ignore_index=args.ignore_index,
        class_weights=class_weights,
        effective_classes=effective_classes,
    )
    loss_input, target = loss_inputs_for_name(args.loss, args.mode, tensors)
    loss_value = loss(loss_input, target)
    metrics = compute_metrics(
        mode=args.mode,
        tensors=tensors,
        metric_threshold=args.metric_threshold,
        metric_reduction=args.metric_reduction,
        zero_division=zero_division,
        ignore_index=args.ignore_index,
    )

    return {
        "ok": True,
        "mode": args.mode,
        "loss": args.loss,
        "from_logits": args.from_logits,
        "batch": args.batch,
        "classes": effective_classes,
        "height": args.height,
        "width": args.width,
        "ignore_index": args.ignore_index,
        "class_weights": class_weights,
        "metric_threshold": args.metric_threshold,
        "metric_reduction": args.metric_reduction,
        "zero_division": zero_division,
        "loss_input_shape": list(loss_input.shape),
        "loss_input_dtype": str(loss_input.dtype),
        "target_shape": list(target.shape),
        "target_dtype": str(target.dtype),
        "loss_value": float(loss_value.detach().cpu()),
        "metrics": metrics,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate tiny segmentation_models_pytorch loss/metric mode and shape "
            "combinations without downloads or training."
        )
    )
    parser.add_argument("--mode", choices=MODE_CHOICES, required=True)
    parser.add_argument("--loss", choices=LOSS_CHOICES, default="dice")
    parser.add_argument("--batch", type=positive_int, default=2)
    parser.add_argument("--classes", type=positive_int, default=3)
    parser.add_argument("--height", type=positive_int, default=8)
    parser.add_argument("--width", type=positive_int, default=8)
    parser.add_argument(
        "--from-logits",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Treat generated loss inputs as logits for losses that support from_logits.",
    )
    parser.add_argument(
        "--metric-threshold",
        type=float,
        default=None,
        help="Threshold for binary/multilabel floating metric outputs; omit to use hard masks.",
    )
    parser.add_argument(
        "--metric-reduction",
        choices=METRIC_REDUCTIONS,
        default="micro",
    )
    parser.add_argument(
        "--zero-division",
        default="1.0",
        help="Metric zero_division value: a float such as 0.0/1.0, or 'warn'.",
    )
    parser.add_argument(
        "--ignore-index",
        type=int,
        default=None,
        help="Ignored target value for supported losses and multiclass metrics.",
    )
    parser.add_argument(
        "--class-weights",
        default=None,
        help="Comma-separated class weights for supported multiclass/multilabel losses.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = validate(args)
    except Exception as error:  # noqa: BLE001 - CLI should return structured diagnostics.
        result = {
            "ok": False,
            "error_type": error.__class__.__name__,
            "error": str(error),
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
