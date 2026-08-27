#!/usr/bin/env python3
"""Run bundled U-2-Net saliency or human-segmentation inference.

Pretrained weights are not bundled. Use --allow-random-weights-for-smoke only
for plumbing checks; random-weight masks are not meaningful predictions.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp")


def load_runtime() -> Any:
    runtime_path = Path(__file__).resolve().parents[3] / "scripts" / "u2net_runtime.py"
    spec = importlib.util.spec_from_file_location("u2net_skill_runtime", runtime_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load bundled runtime from {runtime_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def emit_error(message: str, exit_code: int = 2, **extra: Any) -> None:
    payload = {"ok": False, "error": message}
    payload.update(extra)
    print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
    raise SystemExit(exit_code)


def warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run U-2-Net image-folder inference and save PNG masks.")
    parser.add_argument("--task", choices=("saliency", "human"), default="saliency")
    parser.add_argument("--model", choices=("u2net", "u2netp"), default="u2net", help="Saliency architecture; human mode always uses U2NET.")
    parser.add_argument("--weights", type=Path, default=None, help="Path to a compatible .pth state_dict. Required unless smoke mode is enabled.")
    parser.add_argument("--input-dir", type=Path, required=True, help="Directory containing input images.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for output PNG masks.")
    parser.add_argument("--resize", type=int, default=320, help="Square preprocessing size. Default: 320.")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--max-images", type=int, default=None, help="Optional positive limit after sorting inputs.")
    parser.add_argument("--allow-random-weights-for-smoke", action="store_true", help="Allow randomly initialized weights for plumbing-only checks.")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.resize <= 0:
        emit_error("--resize must be positive", resize=args.resize)
    if args.max_images is not None and args.max_images <= 0:
        emit_error("--max-images must be positive", max_images=args.max_images)


def collect_images(input_dir: Path, max_images: Optional[int]) -> Tuple[List[Path], List[str]]:
    directory = input_dir.expanduser().resolve()
    if not directory.is_dir():
        emit_error("--input-dir must be an existing directory", input_dir=str(directory))
    images: List[Path] = []
    skipped: List[str] = []
    for child in sorted(directory.iterdir(), key=lambda p: p.name):
        if not child.is_file():
            continue
        if child.suffix.lower() in SUPPORTED_EXTENSIONS:
            images.append(child)
        else:
            skipped.append(child.name)
    if max_images is not None:
        images = images[:max_images]
    if not images:
        emit_error("no supported input images found", input_dir=str(directory), supported_extensions=list(SUPPORTED_EXTENSIONS), skipped_files=skipped[:50])
    return images, skipped


def validate_weights(weights: Optional[Path], random_ok: bool) -> Tuple[Optional[Path], bool]:
    if weights is None:
        if not random_ok:
            emit_error("--weights is required unless --allow-random-weights-for-smoke is set")
        return None, True
    resolved = weights.expanduser().resolve()
    if not resolved.is_file():
        emit_error("weights file does not exist", weights=str(resolved))
    return resolved, False


def normalize(torch: Any, pred: Any, image_name: str) -> Tuple[Any, Optional[Dict[str, Any]]]:
    pred_min, pred_max = torch.min(pred), torch.max(pred)
    denom = pred_max - pred_min
    denom_value = float(denom.detach().cpu())
    if not math.isfinite(denom_value) or denom_value <= 1e-12:
        return torch.zeros_like(pred), {"image": image_name, "warning": "degenerate prediction denominator; wrote zero diagnostic mask"}
    out = (pred - pred_min) / denom
    if not bool(torch.isfinite(out).all().detach().cpu()):
        return torch.zeros_like(pred), {"image": image_name, "warning": "non-finite normalized prediction; wrote zero diagnostic mask"}
    return out, None


def save_mask(rt: Any, Image: Any, image_path: Path, pred: Any, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    arr = pred.squeeze().detach().cpu().numpy() * 255.0
    mask = Image.fromarray(arr.astype("uint8")).convert("RGB")
    original = Image.open(image_path).convert("RGB")
    mask = mask.resize(original.size, resample=Image.BILINEAR)
    out = output_dir / f"{image_path.stem}.png"
    mask.save(out)
    return out


def main() -> None:
    args = parse_args()
    validate_args(args)
    images, skipped = collect_images(args.input_dir, args.max_images)
    weights, random_weights = validate_weights(args.weights, args.allow_random_weights_for_smoke)
    try:
        rt = load_runtime()
    except Exception as exc:
        emit_error("failed to load bundled U-2-Net runtime", original_error=str(exc))
    torch, Image = rt.torch, rt.Image
    device = rt.select_torch_device(torch, args.device)
    actual_model = "u2net" if args.task == "human" else args.model
    net = rt.build_u2net_model(actual_model)
    if random_weights:
        warn("running with random weights for smoke testing only; masks are not meaningful")
    else:
        try:
            rt.load_state_dict_file(net, weights, torch)
        except Exception as exc:
            expected = "u2net_human_seg.pth-compatible U2NET(3,1)" if args.task == "human" else f"{actual_model}.pth-compatible state_dict"
            emit_error("failed to load checkpoint state_dict", weights=str(weights), expected=expected, original_error=str(exc))
    net.to(device).eval()
    output_dir = args.output_dir.expanduser().resolve()
    outputs: List[str] = []
    warnings: List[Dict[str, Any]] = []
    for image_path in images:
        image = rt.load_rgb(image_path)
        inputs = rt.preprocess_rgb(image, args.resize).to(device)
        with torch.no_grad():
            predictions = net(inputs)
        if not isinstance(predictions, (tuple, list)) or not predictions:
            emit_error("model forward returned no sequence outputs")
        pred = predictions[0][:, 0, :, :]
        pred, warning = normalize(torch, pred, image_path.name)
        if warning:
            warnings.append(warning)
        outputs.append(str(save_mask(rt, Image, image_path, pred, output_dir)))
    print(json.dumps({
        "ok": True,
        "task": args.task,
        "model": actual_model,
        "device": str(device),
        "resize": args.resize,
        "random_weights": random_weights,
        "processed_count": len(outputs),
        "output_dir": str(output_dir),
        "outputs": outputs,
        "skipped_files": skipped,
        "warnings": warnings,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
