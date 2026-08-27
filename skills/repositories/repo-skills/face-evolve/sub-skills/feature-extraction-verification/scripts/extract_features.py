#!/usr/bin/env python3
"""Safe face.evoLVe PyTorch feature-extraction wrapper.

The preprocessing and TTA logic are distilled from the repository's
extract_feature_v1.py and extract_feature_v2.py helpers. The script imports
only backbone constructors from an explicit --repo-root; it does not import the
original util extraction files.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

CANONICAL_BACKBONES = [
    "IR_50",
    "IR_101",
    "IR_152",
    "IR_SE_50",
    "IR_SE_101",
    "IR_SE_152",
    "ResNet_50",
    "ResNet_101",
    "ResNet_152",
]

BACKBONE_ALIASES = {
    "IR50": "IR_50",
    "IR_50": "IR_50",
    "IR101": "IR_101",
    "IR_101": "IR_101",
    "IR152": "IR_152",
    "IR_152": "IR_152",
    "IRSE50": "IR_SE_50",
    "IR_SE50": "IR_SE_50",
    "IR_SE_50": "IR_SE_50",
    "IRSE101": "IR_SE_101",
    "IR_SE101": "IR_SE_101",
    "IR_SE_101": "IR_SE_101",
    "IRSE152": "IR_SE_152",
    "IR_SE152": "IR_SE_152",
    "IR_SE_152": "IR_SE_152",
    "RESNET50": "ResNet_50",
    "RESNET_50": "ResNet_50",
    "RESNET101": "ResNet_101",
    "RESNET_101": "ResNet_101",
    "RESNET152": "ResNet_152",
    "RESNET_152": "ResNet_152",
}

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract face.evoLVe embeddings from a trained PyTorch backbone "
            "checkpoint using distilled v1/v2 preprocessing."
        )
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Path to a face.evoLVe source checkout used only for importing backbone constructors.",
    )
    parser.add_argument(
        "--backbone",
        required=True,
        help="Backbone name, e.g. IR_50, IR_SE_50, ResNet_50.",
    )
    parser.add_argument("--checkpoint", required=True, help="PyTorch backbone checkpoint file.")
    image_group = parser.add_mutually_exclusive_group(required=True)
    image_group.add_argument("--image-root", help="ImageFolder root for batch extraction.")
    image_group.add_argument("--image-file", help="Single image file for one-row extraction.")
    parser.add_argument("--output-npy", required=True, help="Output .npy path for embeddings.")
    parser.add_argument("--batch-size", type=int, default=512, help="Inference batch size.")
    parser.add_argument(
        "--device",
        default="auto",
        help="Inference device: auto, cpu, cuda, cuda:0, etc. Default: auto.",
    )
    parser.add_argument(
        "--preprocess",
        choices=["auto", "v1", "v2"],
        default="auto",
        help="v1=ImageFolder/torchvision semantics, v2=OpenCV semantics. Default: auto.",
    )
    parser.add_argument(
        "--input-size",
        nargs=2,
        type=int,
        default=[112, 112],
        metavar=("H", "W"),
        help="Backbone crop size. face.evoLVe model-zoo checkpoints usually use 112 112.",
    )
    parser.add_argument(
        "--no-tta",
        action="store_false",
        dest="tta",
        help="Disable horizontal-flip test-time augmentation.",
    )
    parser.set_defaults(tta=True)
    return parser.parse_args()


def normalize_backbone_name(name: str) -> str:
    token = name.strip().replace("-", "_").replace(" ", "_").upper()
    if token in BACKBONE_ALIASES:
        return BACKBONE_ALIASES[token]
    valid = ", ".join(CANONICAL_BACKBONES)
    raise SystemExit(f"Unsupported backbone '{name}'. Supported: {valid}")


def validate_input_size(values: Sequence[int]) -> Tuple[int, int]:
    if len(values) != 2:
        raise SystemExit("--input-size must contain two integers: H W")
    height, width = int(values[0]), int(values[1])
    if height <= 0 or width <= 0:
        raise SystemExit("--input-size values must be positive")
    if height != width:
        raise SystemExit("face.evoLVe extraction paths assume square input, e.g. 112 112")
    if height not in (112, 224):
        print(
            "Warning: source backbones assert input size 112 or 224; nonstandard sizes may fail.",
            file=sys.stderr,
        )
    return height, width


def resolve_device(device_arg: str):
    import torch

    if device_arg == "auto":
        device_arg = "cuda:0" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_arg)
    if device.type == "cuda":
        if not torch.cuda.is_available():
            raise SystemExit("CUDA was requested but torch.cuda.is_available() is False")
        if device.index is not None and device.index >= torch.cuda.device_count():
            raise SystemExit(
                f"CUDA device index {device.index} is not available; "
                f"visible count is {torch.cuda.device_count()}"
            )
    return device


def load_backbone(repo_root: Path, backbone_name: str, input_size: Tuple[int, int]):
    repo_root = repo_root.expanduser().resolve()
    if not repo_root.exists():
        raise SystemExit(f"--repo-root does not exist: {repo_root}")
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    try:
        irse = importlib.import_module("backbone.model_irse")
        resnet = importlib.import_module("backbone.model_resnet")
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise SystemExit(
            "Could not import face.evoLVe backbone modules from --repo-root. "
            "Confirm that the path contains backbone/model_irse.py and backbone/model_resnet.py. "
            f"Original error: {exc}"
        ) from exc

    factories = {
        "IR_50": irse.IR_50,
        "IR_101": irse.IR_101,
        "IR_152": irse.IR_152,
        "IR_SE_50": irse.IR_SE_50,
        "IR_SE_101": irse.IR_SE_101,
        "IR_SE_152": irse.IR_SE_152,
        "ResNet_50": resnet.ResNet_50,
        "ResNet_101": resnet.ResNet_101,
        "ResNet_152": resnet.ResNet_152,
    }
    return factories[backbone_name]([input_size[0], input_size[1]])


def select_state_dict(checkpoint_obj):
    import torch

    if hasattr(checkpoint_obj, "state_dict"):
        return checkpoint_obj.state_dict()

    if not isinstance(checkpoint_obj, dict):
        raise SystemExit("Checkpoint is not a state dict or a dict containing a state dict")

    for key in (
        "state_dict",
        "model_state_dict",
        "backbone_state_dict",
        "backbone",
        "model",
        "net",
        "module",
        "weights",
    ):
        value = checkpoint_obj.get(key)
        if isinstance(value, dict):
            return value

    if checkpoint_obj and all(isinstance(value, torch.Tensor) for value in checkpoint_obj.values()):
        return checkpoint_obj

    visible = ", ".join(map(str, list(checkpoint_obj.keys())[:12]))
    raise SystemExit(
        "Could not find backbone weights in checkpoint. "
        f"Top-level keys include: {visible}"
    )


def strip_common_prefixes(state_dict) -> OrderedDict:
    cleaned = OrderedDict()
    prefixes = ("module.", "backbone.", "model.", "net.")
    for key, value in state_dict.items():
        if not isinstance(key, str):
            continue
        new_key = key
        changed = True
        while changed:
            changed = False
            for prefix in prefixes:
                if new_key.startswith(prefix):
                    new_key = new_key[len(prefix) :]
                    changed = True
        cleaned[new_key] = value
    return cleaned


def load_checkpoint(model, checkpoint_path: Path, device, backbone_name: str):
    import torch

    checkpoint_path = checkpoint_path.expanduser().resolve()
    if not checkpoint_path.exists():
        raise SystemExit(f"--checkpoint does not exist: {checkpoint_path}")

    checkpoint_obj = torch.load(str(checkpoint_path), map_location=device)
    state_dict = strip_common_prefixes(select_state_dict(checkpoint_obj))
    try:
        model.load_state_dict(state_dict, strict=True)
    except RuntimeError as exc:
        model_keys = set(model.state_dict().keys())
        ckpt_keys = set(state_dict.keys())
        missing = sorted(model_keys - ckpt_keys)[:8]
        unexpected = sorted(ckpt_keys - model_keys)[:8]
        message = [
            f"Failed to load checkpoint into {backbone_name}.",
            "Likely causes: wrong backbone, wrong input size, head-only checkpoint, or unhandled key prefix.",
        ]
        if missing:
            message.append("Example missing model keys: " + ", ".join(missing))
        if unexpected:
            message.append("Example unexpected checkpoint keys: " + ", ".join(unexpected))
        message.append("Original load_state_dict error follows:")
        message.append(str(exc))
        raise SystemExit("\n".join(message)) from exc

    model.to(device)
    model.eval()
    return model


def l2_norm(tensor, axis: int = 1):
    import torch

    norm = torch.norm(tensor, 2, axis, keepdim=True).clamp_min(1e-12)
    return tensor / norm


def de_preprocess(tensor):
    return tensor * 0.5 + 0.5


def hflip_batch_v1(batch):
    import torch
    import torchvision.transforms as transforms
    import torchvision.transforms.functional as TF

    normalize = transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
    to_pil = transforms.ToPILImage()
    to_tensor = transforms.ToTensor()
    flipped = torch.empty_like(batch)
    for idx, image_tensor in enumerate(batch):
        pil = to_pil(de_preprocess(image_tensor.cpu()))
        flipped[idx] = normalize(to_tensor(TF.hflip(pil)))
    return flipped


def build_v1_transform(input_size: Tuple[int, int]):
    import torchvision.transforms as transforms

    resize = [int(128 * input_size[0] / 112), int(128 * input_size[1] / 112)]
    return transforms.Compose(
        [
            transforms.Resize(resize),
            transforms.CenterCrop([input_size[0], input_size[1]]),
            transforms.ToTensor(),
            transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5]),
        ]
    )


def forward_batch(model, batch, device, tta: bool, flip_batch=None):
    import torch

    with torch.no_grad():
        emb = model(batch.to(device)).detach().cpu()
        if tta:
            if flip_batch is None:
                flip_batch = hflip_batch_v1(batch)
            emb = emb + model(flip_batch.to(device)).detach().cpu()
    return l2_norm(emb).numpy().astype("float32")


def extract_imagefolder_v1(image_root: Path, model, device, batch_size: int, input_size: Tuple[int, int], tta: bool):
    import numpy as np
    import torch
    import torchvision.datasets as datasets

    image_root = image_root.expanduser().resolve()
    if not image_root.exists():
        raise SystemExit(f"--image-root does not exist: {image_root}")
    transform = build_v1_transform(input_size)
    dataset = datasets.ImageFolder(str(image_root), transform)
    if len(dataset) == 0:
        raise SystemExit(f"No images found under ImageFolder root: {image_root}")

    loader = torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        pin_memory=(device.type == "cuda"),
        num_workers=0,
    )
    features = [forward_batch(model, batch, device, tta) for batch, _labels in loader]
    return np.concatenate(features, axis=0)


def chunked(items: Sequence[Path], batch_size: int) -> Iterable[Sequence[Path]]:
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def collect_images(image_root: Path) -> List[Path]:
    image_root = image_root.expanduser().resolve()
    if not image_root.exists():
        raise SystemExit(f"--image-root does not exist: {image_root}")
    paths = sorted(
        path for path in image_root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )
    if not paths:
        raise SystemExit(f"No supported image files found under: {image_root}")
    return paths


def extract_paths_v1(paths: Sequence[Path], model, device, batch_size: int, input_size: Tuple[int, int], tta: bool):
    import numpy as np
    import torch
    from PIL import Image

    transform = build_v1_transform(input_size)
    features = []
    for batch_paths in chunked(list(paths), batch_size):
        tensors = []
        for path in batch_paths:
            with Image.open(path) as image:
                tensors.append(transform(image.convert("RGB")))
        batch = torch.stack(tensors, dim=0)
        features.append(forward_batch(model, batch, device, tta))
    return np.concatenate(features, axis=0)


def preprocess_v2_pair(path: Path, input_size: Tuple[int, int]):
    import cv2
    import numpy as np
    import torch

    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise SystemExit(f"OpenCV could not read image: {path}")

    resize_h = int(128 * input_size[0] / 112)
    resize_w = int(128 * input_size[1] / 112)
    resized = cv2.resize(image, (resize_w, resize_h))
    y0 = int((resize_h - input_size[0]) / 2)
    x0 = int((resize_w - input_size[1]) / 2)
    crop = resized[y0 : y0 + input_size[0], x0 : x0 + input_size[1]]
    crop = crop[..., ::-1].copy()  # BGR -> RGB
    flipped = cv2.flip(crop, 1)

    def to_tensor(rgb_image):
        array = rgb_image.transpose(2, 0, 1).astype(np.float32)
        array = (array - 127.5) / 128.0
        return torch.from_numpy(array)

    return to_tensor(crop), to_tensor(flipped)


def extract_paths_v2(paths: Sequence[Path], model, device, batch_size: int, input_size: Tuple[int, int], tta: bool):
    import numpy as np
    import torch

    features = []
    for batch_paths in chunked(list(paths), batch_size):
        originals = []
        flipped = []
        for path in batch_paths:
            original_tensor, flipped_tensor = preprocess_v2_pair(path, input_size)
            originals.append(original_tensor)
            flipped.append(flipped_tensor)
        batch = torch.stack(originals, dim=0)
        flip_batch = torch.stack(flipped, dim=0) if tta else None
        features.append(forward_batch(model, batch, device, tta, flip_batch=flip_batch))
    return np.concatenate(features, axis=0)


def resolve_preprocess(preprocess: str, using_image_root: bool) -> str:
    if preprocess != "auto":
        return preprocess
    return "v1" if using_image_root else "v2"


def main() -> int:
    args = parse_args()

    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be positive")

    import numpy as np

    input_size = validate_input_size(args.input_size)
    backbone_name = normalize_backbone_name(args.backbone)
    device = resolve_device(args.device)
    repo_root = Path(args.repo_root)

    model = load_backbone(repo_root, backbone_name, input_size)
    model = load_checkpoint(model, Path(args.checkpoint), device, backbone_name)

    preprocess = resolve_preprocess(args.preprocess, using_image_root=bool(args.image_root))

    if args.image_root:
        image_root = Path(args.image_root)
        if preprocess == "v1":
            features = extract_imagefolder_v1(image_root, model, device, args.batch_size, input_size, args.tta)
            order_note = "ImageFolder class/file order"
        else:
            paths = collect_images(image_root)
            print(
                "Using v2 preprocessing over a recursively sorted file list; keep this order for pairing.",
                file=sys.stderr,
            )
            features = extract_paths_v2(paths, model, device, args.batch_size, input_size, args.tta)
            order_note = "recursive path order"
    else:
        image_file = Path(args.image_file).expanduser().resolve()
        if not image_file.exists():
            raise SystemExit(f"--image-file does not exist: {image_file}")
        paths = [image_file]
        if preprocess == "v1":
            features = extract_paths_v1(paths, model, device, args.batch_size, input_size, args.tta)
        else:
            features = extract_paths_v2(paths, model, device, args.batch_size, input_size, args.tta)
        order_note = "single image"

    if features.ndim != 2:
        raise SystemExit(f"Expected a 2-D feature matrix, got shape {features.shape}")

    output_path = Path(args.output_npy).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, features.astype("float32"))

    print(
        f"Wrote embeddings to {output_path} | shape={tuple(features.shape)} | "
        f"backbone={backbone_name} | preprocess={preprocess} | tta={args.tta} | "
        f"device={device} | order={order_note}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
