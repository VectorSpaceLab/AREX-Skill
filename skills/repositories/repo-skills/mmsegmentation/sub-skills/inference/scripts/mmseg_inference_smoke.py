#!/usr/bin/env python3
"""Safe MMSegmentation lower-level inference smoke script.

With no arguments, this script performs import and signature checks only. When
--config, --checkpoint, and --image are provided, it runs one local inference and
optionally saves an overlay and raw predicted label mask.
"""

from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check MMSegmentation inference APIs, or run one local "
            "config/checkpoint/image inference when all inputs are supplied."
        )
    )
    parser.add_argument("--config", help="MMSegmentation config file for optional inference")
    parser.add_argument("--checkpoint", help="Local checkpoint file for optional inference")
    parser.add_argument("--image", help="Image path for optional inference")
    parser.add_argument("--device", default="cpu", help="Inference device, e.g. cpu or cuda:0")
    parser.add_argument("--out-file", help="Optional rendered overlay output path")
    parser.add_argument("--pred-file", help="Optional raw predicted label-mask PNG output path")
    parser.add_argument(
        "--opacity",
        type=float,
        default=0.5,
        help="Opacity for rendered overlay; must be in (0, 1]",
    )
    parser.add_argument(
        "--with-labels",
        action="store_true",
        help="Draw class labels on the rendered overlay",
    )
    parser.add_argument("--title", default="result", help="Visualization title/name")
    parser.add_argument(
        "--allow-random-weights",
        action="store_true",
        help="Allow --checkpoint to be omitted for pipeline-only smoke runs",
    )
    return parser.parse_args()


def check_imports() -> None:
    try:
        from mmseg.apis import inference_model, init_model, show_result_pyplot
    except ImportError as exc:
        raise RuntimeError(
            "MMSegmentation imports failed; activate an environment with "
            "mmsegmentation, mmengine, mmcv, torch, numpy, and OpenCV installed"
        ) from exc

    expected = {
        "init_model": "config",
        "inference_model": "model",
        "show_result_pyplot": "result",
    }
    objects = {
        "init_model": init_model,
        "inference_model": inference_model,
        "show_result_pyplot": show_result_pyplot,
    }
    for name, required_parameter in expected.items():
        signature = inspect.signature(objects[name])
        if required_parameter not in signature.parameters:
            raise RuntimeError(f"{name} signature missing {required_parameter}: {signature}")
        print(f"OK {name}{signature}")


def require_existing(path_value: str | None, label: str) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    if not path.exists():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    return path


def run_optional_inference(args: argparse.Namespace) -> None:
    supplied = [args.config, args.checkpoint, args.image]
    if not any(supplied):
        print("OK import/signature checks only; provide --config --checkpoint --image to run inference")
        return
    if not args.config or not args.image:
        raise SystemExit("Optional inference requires at least --config and --image")
    if not args.checkpoint and not args.allow_random_weights:
        raise SystemExit("Refusing random-weight inference; pass --checkpoint or --allow-random-weights")

    config_path = require_existing(args.config, "config")
    checkpoint_path = require_existing(args.checkpoint, "checkpoint") if args.checkpoint else None
    image_path = require_existing(args.image, "image")

    from mmengine.model import revert_sync_batchnorm
    from mmseg.apis import inference_model, init_model, show_result_pyplot

    model = init_model(str(config_path), str(checkpoint_path) if checkpoint_path else None, device=args.device)
    if args.device == "cpu":
        model = revert_sync_batchnorm(model)

    result = inference_model(model, str(image_path))
    print(f"OK inference result type: {type(result).__name__}")

    if args.out_file:
        out_file = Path(args.out_file)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        show_result_pyplot(
            model,
            str(image_path),
            result,
            title=args.title,
            opacity=args.opacity,
            with_labels=args.with_labels,
            draw_gt=False,
            draw_pred=True,
            show=False,
            out_file=str(out_file),
        )
        print(f"OK wrote overlay: {out_file}")

    if args.pred_file:
        pred_file = Path(args.pred_file)
        pred_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            import numpy as np
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError("Saving --pred-file requires numpy and Pillow") from exc
        if not hasattr(result, "pred_sem_seg"):
            raise RuntimeError("Result has no pred_sem_seg field to save as a semantic mask")
        mask = result.pred_sem_seg.data[0].detach().cpu().numpy().astype(np.uint8)
        Image.fromarray(mask).save(pred_file)
        print(f"OK wrote predicted mask: {pred_file}")


def main() -> int:
    args = parse_args()
    try:
        check_imports()
        run_optional_inference(args)
    except Exception as exc:  # noqa: BLE001 - CLI should print concise failure
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
