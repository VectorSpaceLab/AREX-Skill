#!/usr/bin/env python3
"""Safe BiRefNet image inference helper.

The helper keeps the default path conservative:
- explicit --repo-root for source imports
- no weights are loaded in --dry-run
- local checkpoints are cleaned with check_state_dict before load
- foreground refinement and comparison panels are opt-in
"""

from __future__ import annotations

import argparse
import sys
from contextlib import nullcontext
from pathlib import Path
from typing import Any

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
IMAGE_NET_MEAN = (0.485, 0.456, 0.406)
IMAGE_NET_STD = (0.229, 0.224, 0.225)


def _eprint(message: str) -> None:
    print(message, file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run BiRefNet inference on one image or an image directory.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Explicit BiRefNet checkout root that provides config.py, models/, and utils.py.",
    )
    parser.add_argument("--input", required=True, help="Image file or image directory to process.")
    parser.add_argument("--output-dir", required=True, help="Directory that will receive masks, optional foregrounds, and comparisons.")
    parser.add_argument("--model-source", choices=("hf", "local"), default="local", help="Load BiRefNet from the hub or from a local checkpoint.")
    parser.add_argument("--hf-repo", default="zhengpeng7/BiRefNet", help="Hub repository to load when --model-source hf is selected.")
    parser.add_argument("--weights", help="Local .pth checkpoint to load when --model-source local is selected.")
    parser.add_argument("--device", default="auto", help="auto, cpu, cuda, cuda:0, ...")
    parser.add_argument(
        "--resolution",
        default="config.size",
        help="Input resolution as WxH, config.size, keep, original, or none.",
    )
    parser.add_argument("--save-comparison", action="store_true", help="Write side-by-side comparison images.")
    parser.add_argument("--foreground-refine", action="store_true", help="Run refine_foreground and save a matting-style PNG with alpha.")
    parser.add_argument("--dry-run", action="store_true", help="Validate paths and print the planned run without loading weights or moving tensors.")
    return parser


def _is_supported_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def _is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _safe_relative_path(src_path: Path, input_root: Path) -> Path:
    try:
        return src_path.relative_to(input_root)
    except ValueError:
        return Path(src_path.name)


def _collect_image_paths(input_path: Path, output_dir: Path) -> tuple[list[Path], Path, list[Path], list[Path]]:
    input_path = input_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    if input_path.is_file():
        if _is_video(input_path):
            raise ValueError(
                f"Video input '{input_path}' was passed to the image helper. Use the video workflow notes instead."
            )
        if not _is_supported_image(input_path):
            raise ValueError(
                f"Unsupported image extension for '{input_path}'. Supported: {', '.join(sorted(IMAGE_EXTENSIONS))}"
            )
        return [input_path], input_path.parent, [], []

    if not input_path.is_dir():
        raise FileNotFoundError(f"Input path is not a file or directory: {input_path}")

    image_paths: list[Path] = []
    video_paths: list[Path] = []
    unsupported_paths: list[Path] = []
    for path in sorted(input_path.rglob("*")):
        if not path.is_file() or _is_under(path, output_dir):
            continue
        if _is_supported_image(path):
            image_paths.append(path)
        elif _is_video(path):
            video_paths.append(path)
        elif not path.name.startswith("."):
            unsupported_paths.append(path)

    if video_paths:
        sample = ", ".join(str(path.relative_to(input_path)) for path in video_paths[:5])
        raise ValueError(
            f"Video files were found inside the image input directory: {sample}. Use the video workflow notes or point --input at image-only folders."
        )

    if not image_paths:
        raise FileNotFoundError(
            f"No supported images were found under '{input_path}'. Supported extensions: {', '.join(sorted(IMAGE_EXTENSIONS))}"
        )

    return image_paths, input_path, unsupported_paths, video_paths


def _parse_resolution_spec(value: str) -> Any:
    token = value.strip().lower()
    if token in {"config.size", "default"}:
        return "config.size"
    if token in {"keep", "original", "none", "null"}:
        return None
    if token.isdigit():
        side = int(token)
        return side, side
    if "x" in token:
        width_text, height_text = [part.strip() for part in token.split("x", 1)]
        if width_text.isdigit() and height_text.isdigit():
            return int(width_text), int(height_text)
    raise ValueError("Unsupported resolution value. Use config.size, original, keep, none, or WxH.")


def _resolve_runtime_resolution(spec: Any, config: Any) -> tuple[int, int] | None:
    if spec == "config.size":
        return tuple(int(value) for value in config.size)
    return spec


def _resolve_device(requested: str, torch_module):
    token = requested.strip().lower()
    if token == "auto":
        return torch_module.device("cuda:0" if torch_module.cuda.is_available() else "cpu")
    if token == "cpu":
        return torch_module.device("cpu")
    if token.isdigit():
        token = f"cuda:{token}"
    if token == "cuda":
        token = "cuda:0"
    if token.startswith("cuda"):
        if not torch_module.cuda.is_available():
            raise RuntimeError(
                "CUDA was requested but is not available. Use --device auto or --device cpu for a fallback run."
            )
        device = torch_module.device(token)
        device_count = torch_module.cuda.device_count()
        if device.index is not None and device.index >= device_count:
            raise RuntimeError(
                f"CUDA device index {device.index} is out of range for the available {device_count} device(s)."
            )
        return device
    raise ValueError("Unsupported --device value. Use auto, cpu, cuda, or cuda:<index>.")


def _load_runtime_modules(repo_root: Path):
    if not repo_root.is_dir():
        raise FileNotFoundError(f"Repo root does not exist or is not a directory: {repo_root}")

    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)

    try:
        import torch
        from PIL import Image
        from torchvision import transforms
        from config import Config
        from models.birefnet import BiRefNet
        from utils import check_state_dict
    except Exception as exc:  # pragma: no cover - surfaced to the user with context
        raise RuntimeError(
            "Could not import the BiRefNet runtime modules from --repo-root. Install the base requirements and confirm that the checkout contains config.py, models/, and utils.py."
        ) from exc

    return {
        "torch": torch,
        "Image": Image,
        "transforms": transforms,
        "Config": Config,
        "BiRefNet": BiRefNet,
        "check_state_dict": check_state_dict,
    }


def _import_refine_foreground(repo_root: Path):
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    try:
        from image_proc import refine_foreground
    except Exception as exc:  # pragma: no cover - surfaced to the user with context
        raise RuntimeError(
            "Foreground refinement was requested but image_proc could not be imported. Install Pillow, numpy, opencv-python, torch, and torchvision, or disable --foreground-refine."
        ) from exc
    return refine_foreground


def _torch_load_checkpoint(torch_module, weights_path: Path):
    try:
        return torch_module.load(str(weights_path), map_location="cpu", weights_only=True)
    except TypeError:
        return torch_module.load(str(weights_path), map_location="cpu")


def _is_tensor_state_dict(candidate, torch_module) -> bool:
    return isinstance(candidate, dict) and bool(candidate) and all(torch_module.is_tensor(value) for value in candidate.values())


def _extract_state_dict(candidate, torch_module):
    if _is_tensor_state_dict(candidate, torch_module):
        return candidate
    if isinstance(candidate, dict):
        for key in ("state_dict", "model_state_dict", "model", "net", "network", "ema_state_dict", "weights"):
            nested = candidate.get(key)
            if _is_tensor_state_dict(nested, torch_module):
                return nested
        for nested in candidate.values():
            if _is_tensor_state_dict(nested, torch_module):
                return nested
    raise RuntimeError("Could not find a tensor state dict in the checkpoint. Provide a BiRefNet .pth file.")


def _build_transform(transforms_module, runtime_resolution):
    ops = []
    if runtime_resolution is not None:
        width, height = runtime_resolution
        ops.append(transforms_module.Resize((height, width)))
    ops.append(transforms_module.ToTensor())
    ops.append(transforms_module.Normalize(IMAGE_NET_MEAN, IMAGE_NET_STD))
    return transforms_module.Compose(ops)


def _build_autocast(torch_module, config, device):
    if device.type != "cuda":
        return nullcontext(), "disabled"

    mixed_precision = str(getattr(config, "mixed_precision", "bf16")).lower()
    if mixed_precision in {"no", "none", "off"}:
        return nullcontext(), "disabled"
    if mixed_precision == "bf16" and getattr(torch_module.cuda, "is_bf16_supported", lambda: False)():
        return torch_module.autocast(device_type="cuda", dtype=torch_module.bfloat16), "bf16"
    return torch_module.autocast(device_type="cuda", dtype=torch_module.float16), "fp16"


def _set_current_cuda_device(torch_module, device) -> None:
    if device.type == "cuda":
        torch_module.cuda.set_device(device.index if device.index is not None else 0)


def _build_comparison_panel(image, mask, refined_subject=None):
    from PIL import Image as PILImage

    subject = (refined_subject if refined_subject is not None else image).convert("RGBA")
    subject.putalpha(mask.convert("L"))
    background = PILImage.new("RGBA", image.size, (0, 177, 64, 255))
    composite = PILImage.alpha_composite(background, subject).convert("RGB")
    panel = PILImage.new("RGB", (image.width * 3, image.height))
    panel.paste(mask.convert("RGB"), (0, 0))
    panel.paste(image, (image.width, 0))
    panel.paste(composite, (image.width * 2, 0))
    return panel


def _save_image(image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def run(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.is_dir():
        raise FileNotFoundError(f"Repo root does not exist or is not a directory: {repo_root}")

    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    resolution_spec = _parse_resolution_spec(args.resolution)
    image_paths, input_root, unsupported_paths, _ = _collect_image_paths(input_path, output_dir)

    if args.dry_run:
        try:
            import torch
        except Exception as exc:  # pragma: no cover - surfaced to the user with context
            raise RuntimeError("Dry-run needs torch to validate device choices.") from exc

        device = _resolve_device(args.device, torch)
        dry_run_weight_note = "not supplied; required for a real local run"
        if args.model_source == "local" and args.weights:
            weights_path = Path(args.weights).expanduser().resolve()
            if not weights_path.is_file():
                raise FileNotFoundError(f"Local checkpoint does not exist: {weights_path}")
            dry_run_weight_note = str(weights_path)

        planned_resolution = "config.size" if resolution_spec == "config.size" else resolution_spec
        print("Dry run: no weights were loaded and no tensors were moved.")
        print(f"repo_root={repo_root}")
        print(f"input_root={input_root}")
        print(f"output_dir={output_dir}")
        print(f"model_source={args.model_source}")
        if args.model_source == "local":
            print(f"local_weights={dry_run_weight_note}")
        print(f"device={device}")
        print(f"resolution={planned_resolution}")
        print(f"foreground_refine={args.foreground_refine}")
        print(f"save_comparison={args.save_comparison}")
        print(f"discovered_images={len(image_paths)}")
        if unsupported_paths:
            print(f"ignored_non_image_files={len(unsupported_paths)}")
        for src_path in image_paths[:10]:
            rel_path = _safe_relative_path(src_path, input_root)
            print(f"  {src_path} -> masks/{rel_path.with_suffix('.png')}")
            if args.foreground_refine:
                print(f"       -> foregrounds/{rel_path.with_suffix('.png')}")
            if args.save_comparison:
                print(f"       -> comparisons/{rel_path.with_suffix('.png')}")
        if len(image_paths) > 10:
            print(f"  ... {len(image_paths) - 10} more")
        return 0

    modules = _load_runtime_modules(repo_root)
    torch = modules["torch"]
    Image = modules["Image"]
    transforms = modules["transforms"]
    Config = modules["Config"]
    BiRefNet = modules["BiRefNet"]
    check_state_dict = modules["check_state_dict"]

    config = Config()
    runtime_resolution = _resolve_runtime_resolution(resolution_spec, config)
    transform_image = _build_transform(transforms, runtime_resolution)
    device = _resolve_device(args.device, torch)
    _set_current_cuda_device(torch, device)

    if hasattr(torch, "set_float32_matmul_precision"):
        torch.set_float32_matmul_precision("high")

    if unsupported_paths:
        _eprint(f"Note: ignored {len(unsupported_paths)} unsupported non-image file(s) under --input.")

    if args.model_source == "hf":
        if args.weights:
            _eprint("Note: --weights was provided but ignored because --model-source hf was selected.")
        try:
            model = BiRefNet.from_pretrained(args.hf_repo, bb_pretrained=False)
            model_source_label = f"hf:{args.hf_repo}"
        except Exception as exc:  # pragma: no cover - surfaced to the user with context
            raise RuntimeError(
                f"Could not load the Hugging Face model '{args.hf_repo}'. Check hub access, cache availability, and the repository id."
            ) from exc
    else:
        if not args.weights:
            raise FileNotFoundError("Local model loading requires --weights.")
        weights_path = Path(args.weights).expanduser().resolve()
        if not weights_path.is_file():
            raise FileNotFoundError(f"Local checkpoint does not exist: {weights_path}")
        try:
            checkpoint = _torch_load_checkpoint(torch, weights_path)
            state_dict = check_state_dict(_extract_state_dict(checkpoint, torch))
            model = BiRefNet(bb_pretrained=False)
            model.load_state_dict(state_dict)
            model_source_label = str(weights_path)
        except Exception as exc:  # pragma: no cover - surfaced to the user with context
            raise RuntimeError(
                f"Could not load the local checkpoint '{weights_path}'. Check the backbone/config match and clean state-dict prefixes with check_state_dict."
            ) from exc

    refine_foreground = None
    if args.foreground_refine:
        refine_foreground = _import_refine_foreground(repo_root)

    model = model.to(device)
    model.eval()
    autocast_ctx, precision_label = _build_autocast(torch, config, device)

    masks_dir = output_dir / "masks"
    foreground_dir = output_dir / "foregrounds"
    comparisons_dir = output_dir / "comparisons"
    masks_dir.mkdir(parents=True, exist_ok=True)
    if args.foreground_refine:
        foreground_dir.mkdir(parents=True, exist_ok=True)
    if args.save_comparison:
        comparisons_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loaded model: {model_source_label}")
    print(f"Resolved device: {device}")
    print(f"Autocast: {precision_label}")
    print(f"Input resolution: {runtime_resolution if runtime_resolution is not None else 'original'}")
    print(f"Images: {len(image_paths)}")

    with torch.inference_mode():
        for src_path in image_paths:
            rel_path = _safe_relative_path(src_path, input_root)
            mask_path = masks_dir / rel_path.with_suffix(".png")
            foreground_path = foreground_dir / rel_path.with_suffix(".png")
            comparison_path = comparisons_dir / rel_path.with_suffix(".png")

            try:
                with Image.open(src_path) as opened_image:
                    image = opened_image.convert("RGB")
                original_size = image.size
                batch = transform_image(image).unsqueeze(0).to(device)

                with autocast_ctx:
                    prediction = model(batch)[-1].sigmoid().to(torch.float32).cpu()

                mask = transforms.ToPILImage()(prediction[0]).resize(original_size)
                _save_image(mask, mask_path)

                refined_subject = None
                if args.foreground_refine:
                    refine_device = "cuda" if device.type == "cuda" else "cpu"
                    refined_subject = refine_foreground(image, mask, device=refine_device)
                    refined_rgba = refined_subject.convert("RGBA")
                    refined_rgba.putalpha(mask.convert("L"))
                    _save_image(refined_rgba, foreground_path)

                if args.save_comparison:
                    panel = _build_comparison_panel(image, mask, refined_subject=refined_subject)
                    _save_image(panel, comparison_path)
            except Exception as exc:
                raise RuntimeError(f"Failed to process image '{src_path}': {exc}") from exc

            print(f"Saved: {mask_path}")
            if args.foreground_refine:
                print(f"Saved: {foreground_path}")
            if args.save_comparison:
                print(f"Saved: {comparison_path}")

    print("Inference complete.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
