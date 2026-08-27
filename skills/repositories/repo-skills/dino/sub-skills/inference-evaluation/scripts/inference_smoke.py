#!/usr/bin/env python3
"""Run one DINO image inference without the original notebook.

The project root is supplied at runtime so this helper is portable across DINO
checkouts. It intentionally performs one deterministic image transform and one
forward pass; it never downloads weights/data or evaluates a dataset. Checkpoint
files are pickle-like inputs and must be trusted before loading.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple


MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run one DINO checkpoint on one RGB image and emit normalized "
            "and transformed-pixel detections. No dataset loop or downloads."
        )
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        required=True,
        help="DINO project root containing main.py, models/, datasets/, and util/.",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Config path, absolute or relative to --project-root.",
    )
    parser.add_argument(
        "--checkpoint",
        required=True,
        help="Checkpoint path, absolute or relative to --project-root.",
    )
    parser.add_argument(
        "--image",
        required=True,
        help="One input image path (opened and converted to RGB).",
    )
    parser.add_argument(
        "--device",
        default="cuda",
        help="Torch device, for example cuda, cuda:0, or cpu (default: cuda).",
    )
    parser.add_argument(
        "--checkpoint-key",
        choices=("model", "ema_model", "state_dict"),
        default="model",
        help="State-dict key inside the checkpoint (default: model).",
    )
    parser.add_argument(
        "--resize",
        type=int,
        default=800,
        help="Short-side resize target before normalization (default: 800).",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=1333,
        help="Maximum long-side size after aspect-preserving resize.",
    )
    parser.add_argument(
        "--score-threshold",
        type=float,
        default=0.30,
        help="PostProcess score filter in [0, 1] (default: 0.30).",
    )
    parser.add_argument(
        "--max-detections",
        type=int,
        default=None,
        help="Optional cap after thresholding; does not change model top-k.",
    )
    parser.add_argument(
        "--label-map",
        type=Path,
        default=None,
        help="Optional JSON ID-to-name map, relative to --project-root if needed.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional path for the machine-readable prediction record.",
    )
    parser.add_argument(
        "--visualize",
        type=Path,
        default=None,
        help="Optional PNG/JPEG path for a Pillow visualization.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing existing --output-json/--visualize files.",
    )
    return parser


def resolve_file(root: Path, value: str | Path, label: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist or is not a file: {path}")
    return path


def validate_args(args: argparse.Namespace) -> Tuple[Path, Path, Path, Path]:
    root = args.project_root.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"--project-root is not a directory: {root}")
    required = (root / "main.py", root / "models", root / "datasets", root / "util")
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise ValueError(
            "--project-root is not a recognizable DINO root; missing: "
            + ", ".join(missing)
        )
    if args.resize <= 0 or args.max_size <= 0:
        raise ValueError("--resize and --max-size must be positive integers")
    if not 0.0 <= args.score_threshold <= 1.0 or not math.isfinite(args.score_threshold):
        raise ValueError("--score-threshold must be a finite number in [0, 1]")
    if args.max_detections is not None and args.max_detections <= 0:
        raise ValueError("--max-detections must be positive when supplied")

    config = resolve_file(root, args.config, "config")
    checkpoint = resolve_file(root, args.checkpoint, "checkpoint")
    image = resolve_file(root, args.image, "image")
    output_paths = []
    for value in (args.output_json, args.visualize):
        if value is None:
            continue
        path = value.expanduser()
        output_paths.append((root / path if not path.is_absolute() else path).resolve())
    if len(output_paths) != len(set(output_paths)):
        raise ValueError("--output-json and --visualize must use different paths")
    if image in output_paths:
        raise ValueError("an output path must not replace the input image")
    if not args.overwrite:
        existing = [str(path) for path in output_paths if path.exists()]
        if existing:
            raise FileExistsError(
                "output already exists; pass --overwrite: " + ", ".join(existing)
            )
    if args.output_json is not None:
        path = args.output_json.expanduser()
        args.output_json = (root / path if not path.is_absolute() else path).resolve()
    if args.visualize is not None:
        path = args.visualize.expanduser()
        args.visualize = (root / path if not path.is_absolute() else path).resolve()
    return root, config, checkpoint, image


def resize_keep_aspect(image: Any, short_side: int, max_size: int) -> Any:
    """Match datasets.transforms.resize for one deterministic scale."""
    width, height = image.size
    size = float(short_side)
    min_original = float(min(width, height))
    max_original = float(max(width, height))
    if max_original / min_original * size > max_size:
        size = int(round(max_size * min_original / max_original))
    size = int(size)
    if width < height:
        out_width = size
        out_height = int(size * height / width)
    else:
        out_height = size
        out_width = int(size * width / height)
    if width == height:
        out_width = out_height = size
    if (out_width, out_height) == image.size:
        return image
    # Resampling is looked up lazily so --help works without Pillow installed.
    from PIL import Image

    return image.resize((out_width, out_height), Image.Resampling.BILINEAR)


def image_to_tensor(image: Any, torch: Any) -> Any:
    import numpy as np

    array = np.asarray(image, dtype=np.uint8).copy()
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError(f"expected an RGB image array, got shape {array.shape}")
    tensor = torch.from_numpy(array).permute(2, 0, 1).float().div(255.0)
    mean = torch.tensor(MEAN, dtype=tensor.dtype).view(3, 1, 1)
    std = torch.tensor(STD, dtype=tensor.dtype).view(3, 1, 1)
    return (tensor - mean) / std


def load_label_map(path: Optional[Path]) -> Dict[str, str]:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, Mapping):
        raise ValueError(f"label map must be a JSON object: {path}")
    return {str(key): str(name) for key, name in value.items()}


def load_checkpoint_state(
    checkpoint_path: Path, checkpoint_key: str, torch: Any, clean_state_dict: Any
) -> Mapping[str, Any]:
    try:
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    except TypeError:  # compatibility with older torch releases
        checkpoint = torch.load(checkpoint_path, map_location="cpu")
    if not isinstance(checkpoint, Mapping):
        raise ValueError(f"checkpoint is not a mapping: {checkpoint_path}")
    if checkpoint_key not in checkpoint:
        available = ", ".join(str(key) for key in checkpoint.keys())
        raise KeyError(
            f"checkpoint has no '{checkpoint_key}' state; available keys: {available}"
        )
    state = checkpoint[checkpoint_key]
    if not isinstance(state, Mapping):
        raise ValueError(f"checkpoint['{checkpoint_key}'] is not a state dict")
    return clean_state_dict(state)


def build_model(root: Path, config_path: Path, checkpoint_path: Path, key: str, device: Any) -> Tuple[Any, Any, Any]:
    # Project imports are deliberately delayed until after path/file checks.
    sys.path.insert(0, str(root))
    from main import build_model_main
    from util import utils
    from util.slconfig import SLConfig

    args = SLConfig.fromfile(str(config_path))
    args.device = str(device)
    # The config files are model configs, not full CLI namespaces.
    if not hasattr(args, "dataset_file"):
        args.dataset_file = "coco"
    model, _criterion, postprocessors = build_model_main(args)
    state = load_checkpoint_state(checkpoint_path, key, __import__("torch"), utils.clean_state_dict)
    try:
        model.load_state_dict(state, strict=True)
    except RuntimeError as exc:
        raise RuntimeError(
            "checkpoint/config mismatch during strict load; pair the scale, "
            "backbone, class count, and checkpoint family before retrying: " + str(exc)
        ) from exc
    model.to(device)
    model.eval()
    return model, postprocessors, args


def display_path(path: Path, root: Path) -> str:
    """Return a portable identity without exposing an absolute local path."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def make_visualization(image: Any, detections: Sequence[Mapping[str, Any]], output: Path) -> None:
    from PIL import ImageDraw

    canvas = image.copy().convert("RGB")
    draw = ImageDraw.Draw(canvas)
    width, height = canvas.size
    line_width = max(1, round(max(width, height) / 400))
    for item in detections:
        x1, y1, x2, y2 = item["box_xyxy_normalized"]
        box = (
            clamp(x1, 0.0, 1.0) * width,
            clamp(y1, 0.0, 1.0) * height,
            clamp(x2, 0.0, 1.0) * width,
            clamp(y2, 0.0, 1.0) * height,
        )
        color = (255, 64, 32)
        draw.rectangle(box, outline=color, width=line_width)
        name = item.get("label_name")
        label = f"{name or item['label']} {item['score']:.3f}"
        text_y = max(0, int(box[1]) - 12)
        draw.text((int(box[0]), text_y), label, fill=color)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def run(args: argparse.Namespace) -> Dict[str, Any]:
    root, config_path, checkpoint_path, image_path = validate_args(args)
    label_map_path = None
    if args.label_map is not None:
        label_map_path = resolve_file(root, args.label_map, "label map")
    elif (root / "util" / "coco_id2name.json").is_file():
        label_map_path = root / "util" / "coco_id2name.json"
    label_map = load_label_map(label_map_path)

    import torch
    from PIL import Image

    try:
        device = torch.device(args.device)
    except (RuntimeError, TypeError) as exc:
        raise ValueError(f"invalid --device {args.device!r}: {exc}") from exc
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(
            f"requested {device} but CUDA is unavailable; use --device cpu for a smoke test "
            "or route CUDA setup to data-model-setup"
        )

    with Image.open(image_path) as opened:
        original = opened.convert("RGB")
    original_width, original_height = original.size
    transformed = resize_keep_aspect(original, args.resize, args.max_size)
    transformed_width, transformed_height = transformed.size
    image_tensor = image_to_tensor(transformed, torch).to(device)

    model, postprocessors, _config = build_model(
        root, config_path, checkpoint_path, args.checkpoint_key, device
    )
    with torch.inference_mode():
        raw_outputs = model([image_tensor])
        # [1, 1] intentionally preserves normalized xyxy for notebook-style use.
        target_sizes = torch.ones((1, 2), dtype=torch.float32, device=device)
        processed = postprocessors["bbox"](raw_outputs, target_sizes)[0]

    scores = processed["scores"].detach().cpu()
    labels = processed["labels"].detach().cpu()
    normalized_xyxy = processed["boxes"].detach().cpu()
    from_boxes = normalized_xyxy
    # Importing util.box_ops after the project path is installed keeps --help light.
    from util import box_ops

    normalized_cxcywh = box_ops.box_xyxy_to_cxcywh(from_boxes)
    keep = scores >= args.score_threshold
    indices = keep.nonzero(as_tuple=False).flatten().tolist()
    if args.max_detections is not None:
        indices = indices[: args.max_detections]

    detections = []
    for index in indices:
        label = int(labels[index].item())
        box_cxcywh = [float(value) for value in normalized_cxcywh[index].tolist()]
        box_xyxy = [float(value) for value in normalized_xyxy[index].tolist()]
        detections.append(
            {
                "score": float(scores[index].item()),
                "label": label,
                "label_name": label_map.get(str(label)),
                "box_cxcywh_normalized": box_cxcywh,
                "box_xyxy_normalized": box_xyxy,
                "box_xyxy_transformed": [
                    box_xyxy[0] * transformed_width,
                    box_xyxy[1] * transformed_height,
                    box_xyxy[2] * transformed_width,
                    box_xyxy[3] * transformed_height,
                ],
            }
        )

    result: Dict[str, Any] = {
        # Keep output artifacts portable and avoid leaking private absolute
        # checkout/environment prefixes. External inputs are identified by name.
        "image": display_path(image_path, root),
        "config": display_path(config_path, root),
        "checkpoint": display_path(checkpoint_path, root),
        "checkpoint_key": args.checkpoint_key,
        "device": str(device),
        "input": {
            "color": "RGB",
            "original_size_hw": [original_height, original_width],
            "transformed_size_hw": [transformed_height, transformed_width],
            "resize_short_side": args.resize,
            "resize_max_size": args.max_size,
            "normalization_mean": list(MEAN),
            "normalization_std": list(STD),
        },
        "postprocess": {
            "target_size_hw": [1.0, 1.0],
            "coordinate_note": "normalized xyxy converted to normalized cxcywh",
            "score_threshold": args.score_threshold,
            "max_detections_after_threshold": args.max_detections,
            "num_returned": len(detections),
        },
        "detections": detections,
    }
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        with args.output_json.open("w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
            handle.write("\n")
    if args.visualize is not None:
        make_visualization(transformed, detections, args.visualize)
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run(args)
    except (
        FileExistsError,
        FileNotFoundError,
        ImportError,
        KeyError,
        RuntimeError,
        ValueError,
        OSError,
    ) as exc:
        print(f"inference_smoke.py: error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
