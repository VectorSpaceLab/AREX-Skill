#!/usr/bin/env python3
"""Run bundled U-2-Net portrait inference with explicit paths.

Supports APDrawingGAN-style cropped portrait images and own-image face-crop mode.
Pretrained portrait weights are not bundled. Use --allow-random-weights-for-smoke
only for plumbing checks.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp")
DEFAULT_CASCADE = Path(__file__).resolve().parent / "haarcascade_frontalface_default.xml"


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
    p = argparse.ArgumentParser(description="Run U-2-Net portrait map inference and save PNG outputs.")
    p.add_argument("--weights", type=Path, default=None, help="u2net_portrait.pth-compatible weights; required unless smoke mode is enabled.")
    p.add_argument("--input-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--mode", choices=("portrait-set", "own-images"), default="portrait-set")
    p.add_argument("--cascade", type=Path, default=DEFAULT_CASCADE, help="Haar cascade XML for own-images mode. Defaults to bundled cascade.")
    p.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    p.add_argument("--max-images", type=int, default=None)
    p.add_argument("--allow-random-weights-for-smoke", action="store_true")
    return p.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.max_images is not None and args.max_images <= 0:
        error("--max-images must be positive", max_images=args.max_images)


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


def validate_weights(weights: Optional[Path], random_ok: bool) -> Tuple[Optional[Path], bool]:
    if weights is None:
        if not random_ok:
            error("--weights is required unless --allow-random-weights-for-smoke is set")
        return None, True
    resolved = weights.expanduser().resolve()
    if not resolved.is_file():
        error("weights file does not exist", weights=str(resolved), expected="u2net_portrait.pth-compatible U2NET(3,1) state_dict")
    return resolved, False


def normalize(torch: Any, pred: Any, image_name: str) -> Tuple[Any, Optional[Dict[str, Any]]]:
    pred_min, pred_max = torch.min(pred), torch.max(pred)
    denom = pred_max - pred_min
    denom_value = float(denom.detach().cpu())
    if not math.isfinite(denom_value) or denom_value <= 1e-12:
        return torch.zeros_like(pred), {"image": image_name, "warning": "degenerate prediction denominator; wrote zero diagnostic portrait"}
    out = (pred - pred_min) / denom
    if not bool(torch.isfinite(out).all().detach().cpu()):
        return torch.zeros_like(pred), {"image": image_name, "warning": "non-finite normalized prediction; wrote zero diagnostic portrait"}
    return out, None


def load_cascade(cv2: Any, path: Path) -> Any:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        error("cascade XML does not exist", cascade=str(resolved))
    cascade = cv2.CascadeClassifier(str(resolved))
    if cascade.empty():
        error("OpenCV could not load cascade XML", cascade=str(resolved))
    return cascade


def largest_face(cascade: Any, cv2: Any, image: Any) -> Optional[Tuple[int, int, int, int]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, 1.1, 4)
    if len(faces) == 0:
        return None
    return max((tuple(map(int, f)) for f in faces), key=lambda f: f[2] * f[3])


def crop_face(np: Any, cv2: Any, img: Any, face: Optional[Tuple[int, int, int, int]]) -> Any:
    if face is None:
        return cv2.resize(img, (512, 512), interpolation=cv2.INTER_AREA)
    x, y, w, h = face
    height, width = img.shape[:2]
    lpad, rpad, tpad, bpad = int(w * 0.4), int(w * 0.4), int(h * 0.6), int(h * 0.2)
    left, right = max(0, x - lpad), min(width, x + w + rpad)
    top, bottom = max(0, y - tpad), min(height, y + h + bpad)
    l, r, t, b = max(0, lpad - x), max(0, x + w + rpad - width), max(0, tpad - y), max(0, y + h + bpad - height)
    face_img = img[top:bottom, left:right]
    if face_img.ndim == 2:
        face_img = np.repeat(face_img[:, :, np.newaxis], 3, axis=2)
    face_img = np.pad(face_img, ((t, b), (l, r), (0, 0)), mode="constant", constant_values=255)
    hf, wf = face_img.shape[:2]
    if hf - 2 > wf:
        pad = int((hf - wf) / 2)
        face_img = np.pad(face_img, ((0, 0), (pad, pad), (0, 0)), mode="constant", constant_values=255)
    elif wf - 2 > hf:
        pad = int((wf - hf) / 2)
        face_img = np.pad(face_img, ((pad, pad), (0, 0), (0, 0)), mode="constant", constant_values=255)
    return cv2.resize(face_img, (512, 512), interpolation=cv2.INTER_AREA)


def save_uint8(Image: Any, output_dir: Path, stem: str, arr: Any) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"{stem}.png"
    Image.fromarray((arr * 255.0).astype("uint8")).save(out)
    return out


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
    cv2 = None
    if args.mode == "own-images":
        try:
            cv2 = importlib.import_module("cv2")
        except Exception as exc:
            error("Failed to import cv2; install OpenCV for own-image face detection", original_error=str(exc))
    device = rt.select_torch_device(torch, args.device)
    net = rt.U2NET(3, 1)
    if random_weights:
        warn("running with random weights for smoke testing only; outputs are not meaningful portraits")
    else:
        try:
            rt.load_state_dict_file(net, weights, torch)
        except Exception as exc:
            error("failed to load checkpoint state_dict", weights=str(weights), original_error=str(exc))
    net.to(device).eval()
    output_dir = args.output_dir.expanduser().resolve()
    outputs: List[str] = []
    warnings: List[Dict[str, Any]] = []
    if args.mode == "own-images":
        cascade = load_cascade(cv2, args.cascade)
    for image_path in images:
        if args.mode == "own-images":
            bgr = cv2.imread(str(image_path))
            if bgr is None:
                warnings.append({"image": image_path.name, "warning": "OpenCV could not read image; skipped"})
                continue
            face = largest_face(cascade, cv2, bgr)
            if face is None:
                warnings.append({"image": image_path.name, "warning": "no face detected; used whole-image fallback"})
            tensor = rt.preprocess_bgr_portrait(crop_face(np, cv2, bgr, face)).to(device)
        else:
            tensor = rt.preprocess_rgb(rt.load_rgb(image_path), 512).to(device)
        with torch.no_grad():
            pred = 1.0 - net(tensor)[0][:, 0, :, :]
        pred, warning = normalize(torch, pred, image_path.name)
        if warning:
            warnings.append(warning)
        outputs.append(str(save_uint8(Image, output_dir, image_path.stem, pred.squeeze().detach().cpu().numpy())))
    print(json.dumps({"ok": True, "mode": args.mode, "device": str(device), "random_weights": random_weights, "processed_count": len(outputs), "outputs": outputs, "skipped_files": skipped, "warnings": warnings}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
