#!/usr/bin/env python3
"""Safe MMSegmentation MMSegInferencer smoke script.

With no arguments, this script performs import and signature checks only. It
never lists aliases or downloads weights unless --allow-download is set and a
model alias is supplied intentionally.
"""

from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path


ALIASES_CAN_DOWNLOAD = (
    "A model alias without --weights can trigger automatic checkpoint download. "
    "Use a local config path plus --weights for deterministic offline runs, or "
    "pass --allow-download when network/cache use is intentional."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check MMSegInferencer imports/signature, or run one local inferencer "
            "call when --model and --image are supplied."
        )
    )
    parser.add_argument("--model", help="Local config path or explicit MMSegmentation model alias")
    parser.add_argument("--weights", help="Local checkpoint/weights path")
    parser.add_argument("--image", help="Image path for optional inference")
    parser.add_argument("--device", default="cpu", help="Inference device, e.g. cpu or cuda:0")
    parser.add_argument("--out-dir", default="", help="Optional output directory for vis/ and pred/")
    parser.add_argument("--dataset-name", default=None, help="Dataset alias for classes/palette")
    parser.add_argument("--classes", nargs="*", help="Optional class names; overrides dataset_name")
    parser.add_argument(
        "--palette",
        nargs="*",
        help="Optional RGB palette as R,G,B entries, e.g. 128,64,128 244,35,232",
    )
    parser.add_argument("--batch-size", type=int, default=1, help="Inferencer batch size")
    parser.add_argument("--opacity", type=float, default=0.5, help="Overlay opacity")
    parser.add_argument("--with-labels", action="store_true", help="Draw class labels on overlays")
    parser.add_argument("--return-datasamples", action="store_true", help="Return SegDataSample objects")
    parser.add_argument("--return-vis", action="store_true", help="Return visualization arrays in memory")
    parser.add_argument("--allow-download", action="store_true", help="Allow model alias auto-download behavior")
    return parser.parse_args()


def check_imports() -> None:
    try:
        from mmseg.apis import MMSegInferencer
    except ImportError as exc:
        raise RuntimeError(
            "MMSegmentation imports failed; activate an environment with "
            "mmsegmentation, mmengine, mmcv, torch, numpy, and OpenCV installed"
        ) from exc

    signature = inspect.signature(MMSegInferencer)
    for required in ("model", "weights", "device", "scope"):
        if required not in signature.parameters:
            raise RuntimeError(f"MMSegInferencer signature missing {required}: {signature}")
    print(f"OK MMSegInferencer{signature}")


def parse_palette(entries: list[str] | None) -> list[list[int]] | None:
    if not entries:
        return None
    palette: list[list[int]] = []
    for entry in entries:
        parts = entry.split(",")
        if len(parts) != 3:
            raise ValueError(f"Palette entry must be R,G,B: {entry}")
        color = [int(part) for part in parts]
        if any(value < 0 or value > 255 for value in color):
            raise ValueError(f"Palette values must be in [0, 255]: {entry}")
        palette.append(color)
    return palette


def existing_path(path_value: str | None, label: str) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    if not path.exists():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    return path


def looks_like_local_config(model_value: str | None) -> bool:
    if not model_value:
        return False
    path = Path(model_value)
    return path.exists() or model_value.endswith((".py", ".json", ".yaml", ".yml"))


def run_optional_inferencer(args: argparse.Namespace) -> None:
    if not args.model and not args.image:
        print("OK import/signature checks only; provide --model --image to run inferencer")
        return
    if not args.model or not args.image:
        raise SystemExit("Optional inferencer run requires both --model and --image")

    image_path = existing_path(args.image, "image")
    weights_path = existing_path(args.weights, "weights") if args.weights else None

    model_is_local_config = looks_like_local_config(args.model)
    if model_is_local_config:
        model_path = existing_path(args.model, "model config")
        model_arg = str(model_path)
    else:
        model_arg = args.model
        if not weights_path and not args.allow_download:
            raise SystemExit(ALIASES_CAN_DOWNLOAD)

    palette = parse_palette(args.palette)
    if args.classes and palette and len(args.classes) != len(palette):
        raise ValueError("--classes and --palette must have the same length")

    from mmseg.apis import MMSegInferencer

    inferencer = MMSegInferencer(
        model=model_arg,
        weights=str(weights_path) if weights_path else None,
        classes=args.classes,
        palette=palette,
        dataset_name=args.dataset_name,
        device=args.device,
    )
    result = inferencer(
        str(image_path),
        return_datasamples=args.return_datasamples,
        batch_size=args.batch_size,
        return_vis=args.return_vis,
        show=False,
        out_dir=args.out_dir,
        opacity=args.opacity,
        with_labels=args.with_labels,
    )
    print(f"OK inferencer result type: {type(result).__name__}")
    if args.out_dir:
        print(f"OK requested output directory: {args.out_dir}")


def main() -> int:
    args = parse_args()
    try:
        check_imports()
        run_optional_inferencer(args)
    except Exception as exc:  # noqa: BLE001 - CLI should print concise failure
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
