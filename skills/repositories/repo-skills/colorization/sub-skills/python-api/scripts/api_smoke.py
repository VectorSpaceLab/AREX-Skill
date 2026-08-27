#!/usr/bin/env python3
"""No-download Python API smoke check for the colorizers package.

The script imports colorizers after optional --repo-root handling, constructs both
public model wrappers with pretrained=False, exercises preprocessing and
postprocessing helpers, and can optionally run small forward passes. It prints a
JSON summary and makes no network calls by default.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict


DEPENDENCY_HINTS = {
    "torch": "Install torch for PyTorch model construction.",
    "numpy": "Install numpy.",
    "PIL": "Install pillow; the import name is PIL but the package name is pillow.",
    "skimage": "Install scikit-image; the import name is skimage but the package name is scikit-image.",
    "IPython": "Install ipython; the modules import IPython.embed even for normal API use.",
    "matplotlib": "Install matplotlib if your workflow imports plotting or display utilities.",
}


class SmokeFailure(Exception):
    """Expected diagnostic failure with a clear user-facing message."""

    def __init__(self, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.message = message
        self.extra = extra


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Construct colorizers.eccv16(pretrained=False) and "
            "colorizers.siggraph17(pretrained=False), exercise Lab helpers, "
            "and optionally run a no-download forward smoke test."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Optional clone root containing the colorizers/ package; prepended to sys.path before import.",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="cpu",
        help="Device for optional --forward. 'auto' selects CUDA when torch reports it is available.",
    )
    parser.add_argument(
        "--forward",
        action="store_true",
        help="Run tiny ECCV and SIGGRAPH forward passes in addition to constructor/helper checks.",
    )
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="Optional image path. If omitted, a synthetic RGB fixture is used.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=32,
        help="Resized fixture/model height for preprocessing and optional forward; default is a tiny 32.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=32,
        help="Resized fixture/model width for preprocessing and optional forward; default is a tiny 32.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include exception type and traceback details in failure JSON.",
    )
    return parser.parse_args()


def emit(payload: Dict[str, Any], exit_code: int) -> int:
    print(json.dumps(payload, indent=2, sort_keys=True))
    return exit_code


def fail(message: str, **extra: Any) -> None:
    raise SmokeFailure(message, **extra)


def add_repo_root(repo_root: str | None) -> bool:
    if not repo_root:
        return False
    path = Path(repo_root).expanduser().resolve()
    if not path.exists():
        fail("--repo-root does not exist", repo_root=str(path))
    if not path.is_dir():
        fail("--repo-root is not a directory", repo_root=str(path))
    if not (path / "colorizers").is_dir():
        fail("--repo-root must contain a colorizers/ package directory", repo_root=str(path))
    sys.path.insert(0, str(path))
    return True


def import_runtime_modules() -> tuple[Any, Any, Any]:
    try:
        import colorizers  # type: ignore
        import numpy as np  # type: ignore
        import torch  # type: ignore
    except ModuleNotFoundError as exc:
        hint = DEPENDENCY_HINTS.get(exc.name or "", "Install the missing dependency in the active Python environment.")
        fail(
            "Failed to import required module",
            missing_module=exc.name,
            hint=hint,
        )
    except ImportError as exc:
        fail("Import failed", error=str(exc))
    return colorizers, np, torch


def resolve_device(torch: Any, requested: str) -> Any:
    if requested == "auto":
        requested = "cuda" if torch.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        fail(
            "CUDA was requested but torch.cuda.is_available() is false",
            hint="Use --device cpu or install a CUDA-capable PyTorch build on a CUDA-capable machine.",
        )
    return torch.device(requested)


def synthetic_rgb(np: Any, height: int, width: int) -> Any:
    yy, xx = np.mgrid[0:height, 0:width]
    denom_x = max(width - 1, 1)
    denom_y = max(height - 1, 1)
    denom_xy = max(width + height - 2, 1)
    red = (xx * 255.0 / denom_x)
    green = (yy * 255.0 / denom_y)
    blue = ((xx + yy) * 255.0 / denom_xy)
    return np.stack([red, green, blue], axis=2).astype("uint8")


def shape_of(value: Any) -> list[int]:
    return [int(dim) for dim in tuple(value.shape)]


def check_exports(colorizers: Any) -> Dict[str, bool]:
    names = [
        "BaseColor",
        "ECCVGenerator",
        "SIGGRAPHGenerator",
        "eccv16",
        "siggraph17",
        "load_img",
        "resize_img",
        "preprocess_img",
        "postprocess_tens",
    ]
    checks = {name: hasattr(colorizers, name) for name in names}
    missing = [name for name, present in checks.items() if not present]
    if missing:
        fail("The colorizers package is missing expected public exports", missing_exports=missing)
    return checks


def signature_text(callable_obj: Any) -> str:
    try:
        return str(inspect.signature(callable_obj))
    except (TypeError, ValueError):
        return "<unavailable>"


def main() -> int:
    args = parse_args()
    try:
        if args.height <= 0 or args.width <= 0:
            fail("--height and --width must be positive integers", height=args.height, width=args.width)
        if args.forward and (args.height % 8 != 0 or args.width % 8 != 0):
            fail(
                "--forward uses the tiny model path and requires --height/--width divisible by 8",
                height=args.height,
                width=args.width,
                hint="Use the defaults, 256x256, or another size divisible by 8.",
            )

        repo_root_added = add_repo_root(args.repo_root)
        colorizers, np, torch = import_runtime_modules()
        device = resolve_device(torch, args.device)
        exports = check_exports(colorizers)

        summary: Dict[str, Any] = {
            "ok": True,
            "network_calls_requested": False,
            "pretrained": False,
            "repo_root_added": repo_root_added,
            "device": str(device),
            "exports_present": exports,
            "signatures": {
                "BaseColor": signature_text(colorizers.BaseColor),
                "ECCVGenerator": signature_text(colorizers.ECCVGenerator),
                "SIGGRAPHGenerator": signature_text(colorizers.SIGGRAPHGenerator),
                "eccv16": signature_text(colorizers.eccv16),
                "siggraph17": signature_text(colorizers.siggraph17),
                "load_img": signature_text(colorizers.load_img),
                "resize_img": signature_text(colorizers.resize_img),
                "preprocess_img": signature_text(colorizers.preprocess_img),
                "postprocess_tens": signature_text(colorizers.postprocess_tens),
            },
        }

        base = colorizers.BaseColor()
        summary["base_color"] = {
            "l_cent": float(base.l_cent),
            "l_norm": float(base.l_norm),
            "ab_norm": float(base.ab_norm),
        }

        try:
            eccv = colorizers.eccv16(pretrained=False).eval()
            siggraph = colorizers.siggraph17(pretrained=False).eval()
        except Exception as exc:  # noqa: BLE001 - converted to clear JSON below
            fail("Model construction with pretrained=False failed", error=str(exc), exception_type=type(exc).__name__)

        summary["constructors"] = {
            "eccv16_pretrained_false": type(eccv).__name__,
            "siggraph17_pretrained_false": type(siggraph).__name__,
        }

        if args.image:
            image_source = "file"
            try:
                img_rgb = colorizers.load_img(args.image)
            except Exception as exc:  # noqa: BLE001
                fail("Failed to load --image with colorizers.load_img", image=args.image, error=str(exc))
        else:
            image_source = "synthetic"
            img_rgb = synthetic_rgb(np, args.height, args.width)

        if getattr(img_rgb, "ndim", None) != 3 or int(img_rgb.shape[2]) != 3:
            fail(
                "preprocess_img expects an RGB image shaped H x W x 3",
                observed_shape=shape_of(img_rgb),
                hint="Convert grayscale/RGBA/palette images to 3-channel RGB before preprocessing.",
            )

        try:
            tens_orig_l, tens_rs_l = colorizers.preprocess_img(img_rgb, HW=(args.height, args.width))
        except Exception as exc:  # noqa: BLE001
            fail("preprocess_img failed", error=str(exc), exception_type=type(exc).__name__)

        summary["image"] = {
            "source": image_source,
            "input_shape": shape_of(img_rgb),
            "resized_HW": [int(args.height), int(args.width)],
        }
        summary["preprocess"] = {
            "tens_orig_l_shape": shape_of(tens_orig_l),
            "tens_rs_l_shape": shape_of(tens_rs_l),
            "tens_rs_l_dtype": str(tens_rs_l.dtype),
        }

        try:
            zero_ab = torch.zeros(
                (1, 2, int(tens_rs_l.shape[2]), int(tens_rs_l.shape[3])),
                dtype=tens_rs_l.dtype,
            )
            rgb_post = colorizers.postprocess_tens(tens_orig_l, zero_ab)
        except Exception as exc:  # noqa: BLE001
            fail("postprocess_tens failed with a zero ab tensor", error=str(exc), exception_type=type(exc).__name__)

        summary["postprocess"] = {
            "zero_ab_rgb_shape": shape_of(rgb_post),
            "zero_ab_rgb_min": float(np.min(rgb_post)),
            "zero_ab_rgb_max": float(np.max(rgb_post)),
        }

        forward_summary: Dict[str, Any] = {"requested": bool(args.forward)}
        if args.forward:
            try:
                eccv = eccv.to(device)
                siggraph = siggraph.to(device)
                input_l = tens_rs_l.to(device)
                with torch.no_grad():
                    out_eccv = eccv(input_l)
                    input_B = torch.zeros(
                        (input_l.shape[0], 2, input_l.shape[2], input_l.shape[3]),
                        dtype=input_l.dtype,
                        device=device,
                    )
                    mask_B = torch.zeros(
                        (input_l.shape[0], 1, input_l.shape[2], input_l.shape[3]),
                        dtype=input_l.dtype,
                        device=device,
                    )
                    out_siggraph_auto = siggraph(input_l)
                    out_siggraph_hints = siggraph(input_l, input_B, mask_B)
                rgb_forward = colorizers.postprocess_tens(tens_orig_l.cpu(), out_eccv.cpu())
            except Exception as exc:  # noqa: BLE001
                fail("Optional forward smoke failed", error=str(exc), exception_type=type(exc).__name__)

            forward_summary.update(
                {
                    "eccv16_out_ab_shape": shape_of(out_eccv),
                    "siggraph17_auto_out_ab_shape": shape_of(out_siggraph_auto),
                    "siggraph17_zero_hint_out_ab_shape": shape_of(out_siggraph_hints),
                    "postprocessed_eccv_rgb_shape": shape_of(rgb_forward),
                }
            )
        summary["forward"] = forward_summary

        return emit(summary, 0)
    except SmokeFailure as exc:
        payload: Dict[str, Any] = {"ok": False, "error": exc.message}
        payload.update(exc.extra)
        if args.verbose:
            payload["traceback"] = traceback.format_exc()
        return emit(payload, 2)
    except Exception as exc:  # noqa: BLE001 - top-level diagnostic conversion
        payload = {"ok": False, "error": str(exc), "exception_type": type(exc).__name__}
        if args.verbose:
            payload["traceback"] = traceback.format_exc()
        return emit(payload, 2)


if __name__ == "__main__":
    raise SystemExit(main())
