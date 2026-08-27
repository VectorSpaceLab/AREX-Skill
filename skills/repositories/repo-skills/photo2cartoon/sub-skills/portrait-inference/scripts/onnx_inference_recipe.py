#!/usr/bin/env python3
"""Run Photo2Cartoon ONNX inference on a preprocessed face patch."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence, Tuple

import numpy as np

DEFAULT_ONNX = Path("models/photo2cartoon_weights.onnx")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Photo2Cartoon ONNX graph on a preprocessed face crop with "
            "an alpha mask."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository checkout root used to import models and resolve defaults.",
    )
    parser.add_argument(
        "--weights-onnx",
        type=Path,
        help="Explicit path to photo2cartoon_weights.onnx.",
    )
    parser.add_argument(
        "--face-rgba-path",
        type=Path,
        help="Path to a preprocessed RGBA face patch.",
    )
    parser.add_argument(
        "--face-rgb-path",
        type=Path,
        help="Path to a preprocessed RGB face patch if the mask is separate.",
    )
    parser.add_argument(
        "--mask-path",
        type=Path,
        help="Path to the alpha mask when the face patch is RGB only.",
    )
    parser.add_argument(
        "--save-path",
        type=Path,
        required=True,
        help="Path for the generated cartoon image.",
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        default=["CPUExecutionProvider"],
        help="onnxruntime providers to request, in order.",
    )
    parser.add_argument(
        "--input-name",
        default="input",
        help="Expected ONNX input tensor name.",
    )
    parser.add_argument(
        "--output-name",
        default="output",
        help="Expected ONNX output tensor name.",
    )
    return parser


def resolve_path(explicit: Optional[Path], repo_root: Path, default_rel: Path) -> Path:
    if explicit is not None:
        return explicit.expanduser()
    return (repo_root / default_rel).expanduser()


def load_image_rgba(face_rgba_path: Optional[Path], face_rgb_path: Optional[Path], mask_path: Optional[Path]):
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - runtime dependency error
        raise RuntimeError(f"Pillow is required to read and write images: {exc}") from exc

    if face_rgba_path is None and face_rgb_path is None:
        raise ValueError("provide --face-rgba-path or --face-rgb-path")

    if face_rgba_path is not None:
        with Image.open(face_rgba_path) as image:
            rgba = image.convert("RGBA")
            return rgba

    if mask_path is None:
        raise ValueError("--face-rgb-path requires --mask-path")

    with Image.open(face_rgb_path) as image:
        rgb = image.convert("RGB")
    with Image.open(mask_path) as image:
        mask = image.convert("L")
    if rgb.size != mask.size:
        mask = mask.resize(rgb.size, Image.BOX)

    rgba = Image.merge("RGBA", (*rgb.split(), mask))
    return rgba


def prepare_tensor(image_rgba) -> Tuple[np.ndarray, np.ndarray]:
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - runtime dependency error
        raise RuntimeError(f"Pillow is required to resize the face patch: {exc}") from exc

    resized = image_rgba.resize((256, 256), Image.BOX)
    array = np.asarray(resized, dtype=np.uint8)
    if array.ndim != 3 or array.shape[2] != 4:
        raise ValueError("face input must resolve to an RGBA image")

    face = array[:, :, :3].astype(np.float32)
    mask = array[:, :, 3:4].astype(np.float32) / 255.0
    face = (face * mask + (1.0 - mask) * 255.0) / 127.5 - 1.0
    face = np.transpose(face[np.newaxis, :, :, :], (0, 3, 1, 2)).astype(np.float32)
    return face, mask


def validate_saved_image(path: Path) -> None:
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - runtime dependency error
        raise RuntimeError(f"Pillow is required to validate the output file: {exc}") from exc

    if not path.exists():
        raise RuntimeError(f"output file not found: {path}")
    if path.stat().st_size == 0:
        raise RuntimeError(f"output file is empty: {path}")
    with Image.open(path) as image:
        image.load()
        if image.mode != "RGB":
            raise RuntimeError(f"output image must decode as RGB, got {image.mode!r}")
        if image.size[0] <= 0 or image.size[1] <= 0:
            raise RuntimeError(f"output image has invalid size: {image.size}")


def run(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.expanduser()
    weights_onnx = resolve_path(args.weights_onnx, repo_root, DEFAULT_ONNX)

    try:
        import onnxruntime as ort
    except Exception as exc:  # pragma: no cover - runtime dependency error
        raise RuntimeError(f"onnxruntime is required for this recipe: {exc}") from exc

    try:
        available = set(ort.get_available_providers())
    except Exception:
        available = set()
    missing = [provider for provider in args.providers if provider not in available]
    if missing:
        raise RuntimeError(
            f"requested ONNX providers are unavailable: {missing}; available={sorted(available)}"
        )

    if not weights_onnx.exists():
        raise RuntimeError(f"graph not found: {weights_onnx}")

    session = ort.InferenceSession(str(weights_onnx), providers=args.providers)
    inputs = session.get_inputs()
    outputs = session.get_outputs()
    if not inputs or not outputs:
        raise RuntimeError("ONNX session has no inputs or outputs")
    actual_input_name = inputs[0].name
    actual_output_name = outputs[0].name
    if actual_input_name != args.input_name:
        raise RuntimeError(
            f"expected input name {args.input_name!r}, found {actual_input_name!r}; "
            "inspect session.get_inputs()"
        )
    if actual_output_name != args.output_name:
        raise RuntimeError(
            f"expected output name {args.output_name!r}, found {actual_output_name!r}; "
            "inspect session.get_outputs()"
        )
    print("[Step1: load weights] success!")

    face_rgba = load_image_rgba(args.face_rgba_path, args.face_rgb_path, args.mask_path)
    face_tensor, mask = prepare_tensor(face_rgba)
    print("[Step2: input contract] success!")

    cartoon = session.run([args.output_name], {args.input_name: face_tensor})[0]
    cartoon = np.transpose(cartoon[0], (1, 2, 0))
    cartoon = (cartoon + 1.0) * 127.5
    cartoon = (cartoon * mask + 255.0 * (1.0 - mask)).clip(0, 255).astype(np.uint8)

    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - runtime dependency error
        raise RuntimeError(f"Pillow is required to save the output file: {exc}") from exc

    args.save_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(cartoon, mode="RGB").save(args.save_path)
    validate_saved_image(args.save_path)
    print("[Step3: photo to cartoon] success!")
    print(f"Saved ONNX cartoon portrait to {args.save_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
