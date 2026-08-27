#!/usr/bin/env python3
"""Run Photo2Cartoon PyTorch inference on a preprocessed face patch."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence, Tuple

import numpy as np

DEFAULT_PT = Path("models/photo2cartoon_weights.pt")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Photo2Cartoon PyTorch generator on a preprocessed face "
            "crop with an alpha mask."
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
        "--weights-pt",
        type=Path,
        help="Explicit path to photo2cartoon_weights.pt.",
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
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Execution device for the PyTorch model.",
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


def load_repo_model(repo_root: Path):
    repo_root = repo_root.expanduser().resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    try:
        from models import ResnetGenerator
    except Exception as exc:  # pragma: no cover - runtime dependency error
        raise RuntimeError(
            f"Could not import models.ResnetGenerator from {repo_root}: {exc}"
        ) from exc
    return ResnetGenerator


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


def choose_device(device_arg: str):
    try:
        import torch
    except Exception as exc:  # pragma: no cover - runtime dependency error
        raise RuntimeError(f"PyTorch is required for this recipe: {exc}") from exc

    if device_arg == "auto":
        return torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    if device_arg == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false")
    return torch.device("cuda:0" if device_arg == "cuda" else "cpu")


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
    weights_pt = resolve_path(args.weights_pt, repo_root, DEFAULT_PT)

    ResnetGenerator = load_repo_model(repo_root)
    device = choose_device(args.device)

    try:
        import torch
    except Exception as exc:  # pragma: no cover - runtime dependency error
        raise RuntimeError(f"PyTorch is required for this recipe: {exc}") from exc

    from PIL import Image

    face_rgba = load_image_rgba(args.face_rgba_path, args.face_rgb_path, args.mask_path)
    face_tensor, mask = prepare_tensor(face_rgba)

    net = ResnetGenerator(ngf=32, img_size=256, light=True).to(device)
    if not weights_pt.exists():
        raise RuntimeError(f"checkpoint not found: {weights_pt}")

    params = torch.load(weights_pt, map_location=device)
    if not isinstance(params, dict) or "genA2B" not in params:
        raise RuntimeError("checkpoint must be a dict containing the genA2B key")
    net.load_state_dict(params["genA2B"])
    net.eval()
    print("[Step1: load weights] success!")

    face = torch.from_numpy(face_tensor).to(device)
    print("[Step2: input contract] success!")
    with torch.no_grad():
        cartoon = net(face)[0][0]

    cartoon = np.transpose(cartoon.detach().cpu().numpy(), (1, 2, 0))
    cartoon = (cartoon + 1.0) * 127.5
    cartoon = (cartoon * mask + 255.0 * (1.0 - mask)).clip(0, 255).astype(np.uint8)

    args.save_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(cartoon, mode="RGB").save(args.save_path)
    validate_saved_image(args.save_path)
    print("[Step3: photo to cartoon] success!")
    print(f"Saved PyTorch cartoon portrait to {args.save_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
