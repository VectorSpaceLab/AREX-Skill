#!/usr/bin/env python3
"""Safe FastReID feature-extraction smoke.

The script validates demo-style BGR->RGB preprocessing, builds a FastReID model
on CPU with backbone pretraining disabled, optionally loads a user-supplied local
checkpoint, and prints feature tensor shapes. It never downloads weights.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Iterable


URL_PREFIXES = ("http://", "https://", "s3://", "ftp://")


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate FastReID feature extraction preprocessing and run a CPU "
            "model forward with optional explicit local checkpoint loading."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Optional path to a FastReID source checkout. Use this when the "
            "fastreid package is not otherwise importable."
        ),
    )
    parser.add_argument(
        "--config-file",
        default=None,
        help=(
            "Optional FastReID YAML config path. Relative paths are resolved "
            "first from the current directory, then from --repo-root if set."
        ),
    )
    parser.add_argument("--image", default=None, help="Optional local image path read with OpenCV in BGR order.")
    parser.add_argument(
        "--weights",
        default=None,
        help="Optional local checkpoint (.pth) path. URLs are rejected to avoid downloads.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use no checkpoint even if --weights is supplied; still builds the model and runs preprocessing/forward.",
    )
    parser.add_argument(
        "--num-classes",
        type=positive_int,
        default=1,
        help="NUM_CLASSES placeholder for head construction when not loading a matching training config. Default: 1.",
    )
    parser.add_argument(
        "--size-test",
        type=positive_int,
        nargs=2,
        metavar=("HEIGHT", "WIDTH"),
        default=None,
        help="Optional override for INPUT.SIZE_TEST used during preprocessing.",
    )
    parser.add_argument("--seed", type=int, default=11, help="Torch RNG seed for deterministic synthetic fallback. Default: 11.")
    parser.add_argument(
        "--opts",
        nargs=argparse.REMAINDER,
        default=[],
        help="Optional KEY VALUE config overrides applied before safe CPU/no-pretrain/no-config-weights overrides.",
    )
    return parser


def add_repo_root(repo_root: str | None) -> Path | None:
    if not repo_root:
        return None
    root = Path(repo_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"ERROR: --repo-root does not exist: {root}")
    if not (root / "fastreid").is_dir():
        raise SystemExit(f"ERROR: --repo-root must contain a fastreid/ package directory: {root}")
    sys.path.insert(0, str(root))
    return root


def resolve_optional_file(path_text: str | None, repo_root: Path | None, label: str) -> Path | None:
    if not path_text:
        return None
    if path_text.lower().startswith(URL_PREFIXES):
        raise SystemExit(f"ERROR: {label} must be a local file; URLs are not loaded by this no-download smoke.")
    raw = Path(path_text).expanduser()
    candidates = [raw]
    if not raw.is_absolute() and repo_root is not None:
        candidates.append(repo_root / raw)
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    tried = ", ".join(str(c) for c in candidates)
    raise SystemExit(f"ERROR: {label} not found. Tried: {tried}")


def import_runtime() -> tuple[Any, Any, Any, Any, Any, Any]:
    try:
        import cv2
    except Exception as exc:  # pragma: no cover - environment-specific.
        raise SystemExit(
            "ERROR: OpenCV (cv2) is required for image resize/preprocessing validation. "
            f"Original error: {type(exc).__name__}: {exc}"
        ) from exc
    try:
        import numpy as np
        import torch
        import torch.nn.functional as F
        from fastreid.config import get_cfg
        from fastreid.modeling import build_model
        from fastreid.utils.checkpoint import Checkpointer
    except Exception as exc:  # pragma: no cover - environment-specific.
        raise SystemExit(
            "ERROR: failed to import FastReID feature extraction runtime. Provide --repo-root "
            "for a source checkout and ensure torch/yacs/PyYAML/numpy dependencies are installed. "
            f"Original error: {type(exc).__name__}: {exc}"
        ) from exc
    return cv2, np, torch, F, get_cfg, (build_model, Checkpointer)


def read_or_make_bgr_image(cv2: Any, np: Any, image_path: Path | None, target_hw: tuple[int, int]) -> tuple[Any, str]:
    if image_path is not None:
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise SystemExit(f"ERROR: OpenCV could not read --image as a color image: {image_path}")
        return image, str(image_path)

    target_h, target_w = target_hw
    synthetic_h = max(32, target_h // 2)
    synthetic_w = max(32, target_w // 2)
    image = np.zeros((synthetic_h, synthetic_w, 3), dtype=np.uint8)
    image[..., 0] = np.linspace(0, 255, synthetic_w, dtype=np.uint8)[None, :]
    image[..., 1] = np.linspace(255, 0, synthetic_h, dtype=np.uint8)[:, None]
    image[..., 2] = 127
    return image, "<synthetic-bgr-image>"


def preprocess_bgr_image(cv2: Any, torch: Any, image_bgr: Any, size_test: tuple[int, int]) -> Any:
    if getattr(image_bgr, "ndim", None) != 3 or image_bgr.shape[2] != 3:
        raise SystemExit(f"ERROR: expected BGR image shape (H, W, 3), got {getattr(image_bgr, 'shape', None)}")
    height, width = size_test
    image_rgb = image_bgr[:, :, ::-1]
    resized = cv2.resize(image_rgb, (width, height), interpolation=cv2.INTER_CUBIC)
    tensor = torch.as_tensor(resized.astype("float32").transpose(2, 0, 1))[None]
    return tensor


def describe_output(value: Any) -> Any:
    if hasattr(value, "shape"):
        return tuple(int(x) for x in value.shape)
    if isinstance(value, dict):
        return {str(k): describe_output(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [describe_output(v) for v in value]
    return type(value).__name__


def model_device(model: Any, torch: Any) -> Any:
    explicit = getattr(model, "device", None)
    if explicit is not None:
        return explicit
    try:
        return next(model.parameters()).device
    except StopIteration:
        return torch.device("cpu")


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = add_repo_root(args.repo_root)
    config_path = resolve_optional_file(args.config_file, repo_root, "--config-file")
    image_path = resolve_optional_file(args.image, repo_root=None, label="--image")
    weights_path = resolve_optional_file(args.weights, repo_root=None, label="--weights")

    cv2, np, torch, F, get_cfg, runtime = import_runtime()
    build_model, Checkpointer = runtime
    torch.manual_seed(args.seed)

    cfg = get_cfg()
    if config_path is not None:
        cfg.merge_from_file(str(config_path))
    if args.opts:
        if len(args.opts) % 2 != 0:
            raise SystemExit("ERROR: --opts expects KEY VALUE pairs.")
        cfg.merge_from_list(args.opts)

    cfg.defrost()
    cfg.MODEL.DEVICE = "cpu"
    cfg.MODEL.BACKBONE.PRETRAIN = False
    cfg.MODEL.WEIGHTS = ""
    cfg.MODEL.HEADS.NUM_CLASSES = args.num_classes
    if args.size_test is not None:
        cfg.INPUT.SIZE_TEST = list(args.size_test)
    cfg.freeze()

    size_test = (int(cfg.INPUT.SIZE_TEST[0]), int(cfg.INPUT.SIZE_TEST[1]))
    image_bgr, image_label = read_or_make_bgr_image(cv2, np, image_path, size_test)
    tensor = preprocess_bgr_image(cv2, torch, image_bgr, size_test)

    try:
        model = build_model(cfg)
        model.eval()
        loaded_weights = False
        if weights_path is not None and args.dry_run:
            print(f"dry_run=True: ignoring supplied weights path {weights_path}", file=sys.stderr)
        elif weights_path is not None:
            Checkpointer(model).load(str(weights_path))
            loaded_weights = True

        device = model_device(model, torch)
        with torch.no_grad():
            features = model({"images": tensor.to(device)})
            features_cpu = features.cpu() if hasattr(features, "cpu") else features
            if hasattr(features_cpu, "ndim") and features_cpu.ndim >= 2:
                normalized = F.normalize(features_cpu, dim=1)
                normalized_shape = describe_output(normalized)
                norm_values = torch.linalg.vector_norm(normalized, ord=2, dim=1).detach().cpu()
                norm_summary = [float(x) for x in norm_values[: min(5, norm_values.numel())]]
            else:
                normalized_shape = "<not-normalized-non-tensor-output>"
                norm_summary = []
    except Exception as exc:  # pragma: no cover - depends on user configs/checkpoints.
        raise SystemExit(
            "ERROR: FastReID feature extraction smoke failed. Check config/model family, "
            "local checkpoint compatibility, image shape, and CPU/device settings. "
            f"Original error: {type(exc).__name__}: {exc}"
        ) from exc

    print("FastReID feature extraction smoke passed")
    print(f"repo_root={repo_root if repo_root is not None else '<importable-package>'}")
    print(f"config_file={config_path if config_path is not None else '<default-config>'}")
    print(f"image={image_label}")
    print(f"input_bgr_shape={tuple(int(x) for x in image_bgr.shape)}")
    print(f"size_test_height_width={size_test}")
    print(f"preprocessed_tensor_shape={tuple(int(x) for x in tensor.shape)}")
    print(f"device={cfg.MODEL.DEVICE}")
    print(f"pretrain={cfg.MODEL.BACKBONE.PRETRAIN}")
    print(f"weights_loaded={loaded_weights}")
    print(f"output_shape={describe_output(features_cpu)}")
    print(f"normalized_shape={normalized_shape}")
    if norm_summary:
        print(f"normalized_l2_norm_first_values={norm_summary}")
    if not loaded_weights:
        print("note=no checkpoint loaded; output validates plumbing only, not ReID quality")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
