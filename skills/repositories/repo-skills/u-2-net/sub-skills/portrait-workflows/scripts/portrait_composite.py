#!/usr/bin/env python3
"""Create bundled U-2-Net portrait/original composites with explicit controls."""
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


def error(message: str, exit_code: int = 2, **extra: Any) -> None:
    payload = {"ok": False, "error": message}
    payload.update(extra)
    print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
    raise SystemExit(exit_code)


def warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run U-2-Net portrait inference and blend the portrait map with a Gaussian-blurred original image.")
    p.add_argument("--weights", type=Path, default=None, help="u2net_portrait.pth-compatible weights; required unless smoke mode is enabled.")
    p.add_argument("--input-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--sigma", type=float, required=True, help="Gaussian blur sigma; must be >= 0.")
    p.add_argument("--alpha", type=float, required=True, help="Blend weight for blurred original; must be in [0,1].")
    p.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    p.add_argument("--max-images", type=int, default=None)
    p.add_argument("--allow-random-weights-for-smoke", action="store_true")
    return p.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.max_images is not None and args.max_images <= 0:
        error("--max-images must be positive", max_images=args.max_images)
    if not math.isfinite(args.sigma) or args.sigma < 0:
        error("--sigma must be a finite number >= 0", sigma=args.sigma)
    if not math.isfinite(args.alpha) or not (0 <= args.alpha <= 1):
        error("--alpha must be a finite number in [0, 1]", alpha=args.alpha)


def validate_weights(weights: Optional[Path], random_ok: bool) -> Tuple[Optional[Path], bool]:
    if weights is None:
        if not random_ok:
            error("--weights is required unless --allow-random-weights-for-smoke is set")
        return None, True
    resolved = weights.expanduser().resolve()
    if not resolved.is_file():
        error("weights file does not exist", weights=str(resolved))
    return resolved, False


def collect_images(input_dir: Path, max_images: Optional[int]) -> Tuple[List[Path], List[str]]:
    directory = input_dir.expanduser().resolve()
    if not directory.is_dir():
        error("--input-dir must be an existing directory", input_dir=str(directory))
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
        error("no supported input images found", input_dir=str(directory), skipped_files=skipped[:50])
    return images, skipped


def normalize(torch: Any, pred: Any, image_name: str) -> Tuple[Any, Optional[Dict[str, Any]]]:
    pred_min, pred_max = torch.min(pred), torch.max(pred)
    denom = pred_max - pred_min
    denom_value = float(denom.detach().cpu())
    if not math.isfinite(denom_value) or denom_value <= 1e-12:
        return torch.zeros_like(pred), {"image": image_name, "warning": "degenerate prediction denominator; used zero portrait map"}
    out = (pred - pred_min) / denom
    if not bool(torch.isfinite(out).all().detach().cpu()):
        return torch.zeros_like(pred), {"image": image_name, "warning": "non-finite normalized prediction; used zero portrait map"}
    return out, None


def name_number(value: float) -> str:
    return f"{value:g}".replace("-", "m").replace(".", "p")


def main() -> None:
    args = parse_args()
    validate_args(args)
    images, skipped = collect_images(args.input_dir, args.max_images)
    weights, random_weights = validate_weights(args.weights, args.allow_random_weights_for_smoke)
    try:
        rt = load_runtime()
    except Exception as exc:
        error("failed to load bundled U-2-Net runtime", original_error=str(exc))
    torch, np, Image = rt.torch, rt.np, rt.Image
    from skimage import filters, transform
    device = rt.select_torch_device(torch, args.device)
    net = rt.U2NET(3, 1)
    if random_weights:
        warn("running with random weights for smoke testing only; composites are not meaningful portraits")
    else:
        try:
            rt.load_state_dict_file(net, weights, torch)
        except Exception as exc:
            error("failed to load checkpoint state_dict", weights=str(weights), original_error=str(exc))
    net.to(device).eval()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    warnings: List[Dict[str, Any]] = []
    outputs: List[str] = []
    for image_path in images:
        original = np.asarray(Image.open(image_path).convert("RGB"), dtype="float32")
        tensor = rt.preprocess_rgb(original, 512).to(device)
        with torch.no_grad():
            pred = 1.0 - net(tensor)[0][:, 0, :, :]
        pred, warning = normalize(torch, pred, image_path.name)
        if warning:
            warnings.append(warning)
        portrait = pred.squeeze().detach().cpu().numpy()
        portrait_resized = transform.resize(portrait, original.shape[:2], order=2, preserve_range=True)
        portrait_gray = (portrait_resized / (np.amax(portrait_resized) + 1e-8) * 255.0)[:, :, np.newaxis]
        blurred = filters.gaussian(original, sigma=args.sigma, preserve_range=True, channel_axis=-1)
        composite = np.clip(blurred * args.alpha + portrait_gray * (1.0 - args.alpha), 0, 255).astype("uint8")
        out = output_dir / f"{image_path.stem}_sigma_{name_number(args.sigma)}_alpha_{name_number(args.alpha)}_composite.png"
        Image.fromarray(composite).save(out)
        outputs.append(str(out))
    print(json.dumps({"ok": True, "device": str(device), "sigma": args.sigma, "alpha": args.alpha, "random_weights": random_weights, "processed_count": len(outputs), "outputs": outputs, "skipped_files": skipped, "warnings": warnings}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
