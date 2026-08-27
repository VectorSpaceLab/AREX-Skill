#!/usr/bin/env python3
"""No-download environment diagnostic for the colorization repo skill.

The check imports the `colorizers` package, reports dependency/backend facts,
constructs ECCV16 and SIGGRAPH17 with pretrained=False, and can optionally run a
small forward pass. It does not download pretrained weights.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check colorization imports, dependencies, and optional backend readiness.")
    parser.add_argument("--repo-root", default=None, help="Clone root containing colorizers/; prepended to sys.path before import.")
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="auto", help="Device for optional --check-forward.")
    parser.add_argument("--check-forward", action="store_true", help="Run tiny no-download forward passes for both models.")
    parser.add_argument("--height", type=int, default=32, help="Synthetic image height for smoke checks.")
    parser.add_argument("--width", type=int, default=32, help="Synthetic image width for smoke checks.")
    return parser.parse_args()


def add_repo_root(repo_root: str | None) -> bool:
    if not repo_root:
        return False
    root = Path(repo_root).expanduser().resolve()
    if not root.is_dir():
        raise RuntimeError(f"--repo-root is not a directory: {repo_root}")
    if not (root / "colorizers").is_dir():
        raise RuntimeError("--repo-root must contain a colorizers/ package directory")
    sys.path.insert(0, str(root))
    return True


def version_or_error(module_name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic conversion
        return {"ok": False, "error": str(exc), "exception_type": type(exc).__name__}
    version = getattr(module, "__version__", None)
    if module_name == "PIL":
        try:
            from PIL import Image

            version = getattr(Image, "__version__", version)
        except Exception:
            pass
    return {"ok": True, "version": version}


def choose_device(torch: Any, requested: str) -> Any:
    if requested == "auto":
        requested = "cuda" if torch.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is false")
    return torch.device(requested)


def synthetic_rgb(np: Any, height: int, width: int) -> Any:
    yy, xx = np.mgrid[0:height, 0:width]
    red = (xx * 255.0 / max(width - 1, 1)).astype("uint8")
    green = (yy * 255.0 / max(height - 1, 1)).astype("uint8")
    blue = (((xx + yy) * 255.0 / max(width + height - 2, 1))).astype("uint8")
    return np.stack([red, green, blue], axis=2)


def shape(value: Any) -> list[int]:
    return [int(x) for x in tuple(value.shape)]


def main() -> int:
    args = parse_args()
    payload: Dict[str, Any] = {"ok": False, "network_calls_requested": False}
    try:
        if args.height <= 0 or args.width <= 0:
            raise RuntimeError("--height and --width must be positive")
        if args.check_forward and (args.height % 8 or args.width % 8):
            raise RuntimeError("--check-forward requires height and width divisible by 8 for the tiny model path")

        payload["repo_root_added"] = add_repo_root(args.repo_root)
        payload["dependencies"] = {
            "torch": version_or_error("torch"),
            "numpy": version_or_error("numpy"),
            "PIL": version_or_error("PIL"),
            "skimage": version_or_error("skimage"),
            "matplotlib": version_or_error("matplotlib"),
            "IPython": version_or_error("IPython"),
        }
        missing = [name for name, info in payload["dependencies"].items() if not info["ok"]]
        if missing:
            raise RuntimeError(f"Missing or broken dependencies: {', '.join(missing)}")

        import colorizers  # type: ignore
        import numpy as np  # type: ignore
        import torch  # type: ignore

        payload["colorizers_imported"] = True
        payload["exports"] = {
            name: hasattr(colorizers, name)
            for name in [
                "BaseColor",
                "ECCVGenerator",
                "SIGGRAPHGenerator",
                "eccv16",
                "siggraph17",
                "load_img",
                "preprocess_img",
                "postprocess_tens",
            ]
        }
        if not all(payload["exports"].values()):
            missing_exports = [name for name, ok in payload["exports"].items() if not ok]
            raise RuntimeError(f"Missing expected colorizers exports: {', '.join(missing_exports)}")

        device = choose_device(torch, args.device)
        payload["torch_cuda_available"] = bool(torch.cuda.is_available())
        payload["selected_device"] = str(device)

        eccv = colorizers.eccv16(pretrained=False).eval()
        siggraph = colorizers.siggraph17(pretrained=False).eval()
        payload["constructors"] = {
            "eccv16_pretrained_false": type(eccv).__name__,
            "siggraph17_pretrained_false": type(siggraph).__name__,
        }

        img = synthetic_rgb(np, args.height, args.width)
        tens_orig_l, tens_rs_l = colorizers.preprocess_img(img, HW=(args.height, args.width))
        payload["preprocess"] = {
            "input_shape": shape(img),
            "tens_orig_l_shape": shape(tens_orig_l),
            "tens_rs_l_shape": shape(tens_rs_l),
        }

        if args.check_forward:
            eccv = eccv.to(device)
            siggraph = siggraph.to(device)
            input_l = tens_rs_l.to(device)
            with torch.no_grad():
                out_eccv = eccv(input_l)
                out_siggraph = siggraph(input_l)
            rgb = colorizers.postprocess_tens(tens_orig_l.cpu(), out_eccv.cpu())
            payload["forward"] = {
                "requested": True,
                "eccv16_out_ab_shape": shape(out_eccv),
                "siggraph17_out_ab_shape": shape(out_siggraph),
                "postprocessed_rgb_shape": shape(rgb),
            }
        else:
            payload["forward"] = {"requested": False}

        payload["ok"] = True
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # noqa: BLE001 - top-level diagnostic conversion
        payload["error"] = str(exc)
        payload["exception_type"] = type(exc).__name__
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
