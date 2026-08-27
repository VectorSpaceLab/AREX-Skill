#!/usr/bin/env python3
"""Safe MMPreTrain image classification helper.

This helper is adapted for bundled skill use. By default it constructs the
model with ``pretrained=False`` to avoid network downloads. Pass ``--checkpoint``
for a local/URL checkpoint, or ``--use-default-checkpoint`` when downloads from
the model zoo are allowed.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run MMPreTrain image classification with explicit checkpoint "
            "selection. Defaults to no checkpoint download."
        )
    )
    parser.add_argument(
        "--image",
        action="append",
        required=True,
        help="Image path/URL. Repeat for multiple images.",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="MMPreTrain model name or a user-provided config file path.",
    )
    checkpoint_group = parser.add_mutually_exclusive_group()
    checkpoint_group.add_argument(
        "--checkpoint",
        help="Local checkpoint path or checkpoint URL. Enables meaningful predictions.",
    )
    checkpoint_group.add_argument(
        "--use-default-checkpoint",
        action="store_true",
        help="Allow MMPreTrain to load/download the model-zoo default checkpoint.",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Inference device such as 'cpu', 'cuda', or 'cuda:0'. Default: cpu.",
    )
    parser.add_argument(
        "--device-map",
        help="Optional model dispatch map, for example 'auto'. Overrides simple device movement when supported.",
    )
    parser.add_argument(
        "--offload-folder",
        help="Writable folder for disk offload when --device-map uses disk.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Batch size for inferencer calls. Default: 1.",
    )
    parser.add_argument(
        "--classes",
        help="Comma-separated class names to override checkpoint/config metadata.",
    )
    parser.add_argument(
        "--classes-file",
        help="Text file with one class name per line to override checkpoint/config metadata.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Open a GUI window for visualization. Avoid in headless sessions.",
    )
    parser.add_argument(
        "--show-dir",
        help="Directory where visualization PNG files will be saved.",
    )
    parser.add_argument(
        "--resize",
        type=int,
        help="Resize the short edge before visualization.",
    )
    parser.add_argument(
        "--rescale-factor",
        type=float,
        help="Rescale visualization image by this factor.",
    )
    parser.add_argument(
        "--no-draw-score",
        action="store_true",
        help="Do not draw prediction scores in visualization.",
    )
    parser.add_argument(
        "--topk",
        type=int,
        default=1,
        help="Add a compact top-k summary from pred_scores. Default: 1.",
    )
    parser.add_argument(
        "--include-pred-scores",
        action="store_true",
        help="Include the full pred_scores vector in JSON output.",
    )
    parser.add_argument(
        "--output",
        help="Write JSON output to this file instead of stdout.",
    )
    return parser


def parse_classes(args: argparse.Namespace) -> list[str] | None:
    if args.classes and args.classes_file:
        raise SystemExit("Use only one of --classes or --classes-file.")
    if args.classes:
        return [item.strip() for item in args.classes.split(",") if item.strip()]
    if args.classes_file:
        path = Path(args.classes_file)
        return [line.strip() for line in path.read_text().splitlines() if line.strip()]
    return None


def to_jsonable(value: Any) -> Any:
    try:
        import numpy as np
    except Exception:  # pragma: no cover - numpy is normally installed with MMPreTrain
        np = None  # type: ignore[assignment]
    try:
        import torch
    except Exception:  # pragma: no cover - torch is normally installed with MMPreTrain
        torch = None  # type: ignore[assignment]

    if np is not None and isinstance(value, np.ndarray):
        return value.tolist()
    if torch is not None and isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return float(value.detach().cpu().item())
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(key): to_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value


def add_topk(item: dict[str, Any], classes: list[str] | None, topk: int) -> None:
    if topk <= 0 or "pred_scores" not in item:
        return
    try:
        import numpy as np

        scores = np.asarray(item["pred_scores"])
        if scores.ndim != 1 or scores.size == 0:
            return
        k = min(topk, int(scores.size))
        labels = np.argsort(scores)[::-1][:k]
        summary = []
        for label in labels:
            entry: dict[str, Any] = {
                "pred_label": int(label),
                "pred_score": float(scores[label]),
            }
            if classes is not None and int(label) < len(classes):
                entry["pred_class"] = classes[int(label)]
            summary.append(entry)
        item["topk"] = summary
    except Exception as exc:  # keep helper useful even if score conversion fails
        item["topk_error"] = str(exc)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    if args.topk < 0:
        parser.error("--topk must be non-negative")

    classes = parse_classes(args)

    if args.checkpoint:
        pretrained: bool | str = args.checkpoint
    elif args.use_default_checkpoint:
        pretrained = True
    else:
        pretrained = False
        print(
            "[classify_image] No checkpoint selected; using pretrained=False "
            "to avoid downloads. Predictions are random/untrained.",
            file=sys.stderr,
        )

    try:
        from mmpretrain.apis import ImageClassificationInferencer
    except Exception as exc:
        print(f"Failed to import mmpretrain.apis: {exc}", file=sys.stderr)
        return 2

    model_kwargs: dict[str, Any] = {}
    if args.device_map:
        model_kwargs["device_map"] = args.device_map
    if args.offload_folder:
        model_kwargs["offload_folder"] = args.offload_folder

    try:
        inferencer = ImageClassificationInferencer(
            args.model,
            pretrained=pretrained,
            device=None if args.device_map else args.device,
            classes=classes,
            **model_kwargs,
        )
    except ValueError as exc:
        print(f"Failed to build model/inferencer: {exc}", file=sys.stderr)
        print("Hint: run list_models.py to find an exact model name.", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"Failed to build model/inferencer: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3

    inputs: str | list[str]
    inputs = args.image[0] if len(args.image) == 1 else args.image

    try:
        # MMPreTrain progress bars can write to stdout. Redirect them so stdout
        # remains valid JSON when --output is not used.
        with contextlib.redirect_stdout(sys.stderr):
            results = inferencer(
                inputs,
                batch_size=args.batch_size,
                show=args.show,
                show_dir=args.show_dir,
                resize=args.resize,
                rescale_factor=args.rescale_factor,
                draw_score=not args.no_draw_score,
            )
    except Exception as exc:
        print(f"Inference failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 4

    effective_classes = classes or getattr(inferencer, "classes", None)
    compact_results = []
    for result in results:
        item = dict(result)
        add_topk(item, effective_classes, args.topk)
        if not args.include_pred_scores:
            item.pop("pred_scores", None)
        compact_results.append(to_jsonable(item))

    payload = {
        "model": args.model,
        "checkpoint": args.checkpoint
        or ("model-zoo-default" if args.use_default_checkpoint else None),
        "device": args.device_map or args.device,
        "results": compact_results,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
