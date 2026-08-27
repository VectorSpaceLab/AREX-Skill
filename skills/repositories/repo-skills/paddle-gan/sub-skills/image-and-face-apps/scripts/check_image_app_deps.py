#!/usr/bin/env python3
"""Safe dependency and signature check for PaddleGAN image/face workflows.

This helper does not download weights and does not run inference.
It only inspects import availability, backend flags, and predictor signatures.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

CORE_MODULES = ["paddle", "ppgan", "cv2", "numpy", "PIL", "yaml"]
OPTIONAL_MODULES = ["imageio", "scipy", "skimage", "natsort", "dlib", "clip"]

PREDICTOR_MODULES: List[Tuple[str, str]] = [
    ("AnimeGANPredictor", "ppgan.apps.animegan_predictor"),
    ("AOTGANPredictor", "ppgan.apps.aotgan_predictor"),
    ("FaceParsePredictor", "ppgan.apps.face_parse_predictor"),
    ("GPENPredictor", "ppgan.apps.gpen_predictor"),
    ("InvDNPredictor", "ppgan.apps.invdn_predictor"),
    ("LapStylePredictor", "ppgan.apps.lapstyle_predictor"),
    ("MPRPredictor", "ppgan.apps.mpr_predictor"),
    ("MiDaSPredictor", "ppgan.apps.midas_predictor"),
    ("NAFNetPredictor", "ppgan.apps.nafnet_predictor"),
    ("Photo2CartoonPredictor", "ppgan.apps.photo2cartoon_predictor"),
    ("PhotoPenPredictor", "ppgan.apps.photopen_predictor"),
    ("Pixel2Style2PixelPredictor", "ppgan.apps.pixel2style2pixel_predictor"),
    ("PSGANPredictor", "ppgan.apps.psgan_predictor"),
    ("SinGANPredictor", "ppgan.apps.singan_predictor"),
    ("StyleGANv2Predictor", "ppgan.apps.styleganv2_predictor"),
    ("StyleGANv2FittingPredictor", "ppgan.apps.styleganv2fitting_predictor"),
    ("StyleGANv2MixingPredictor", "ppgan.apps.styleganv2mixing_predictor"),
    ("StyleGANv2EditingPredictor", "ppgan.apps.styleganv2editing_predictor"),
    ("SwinIRPredictor", "ppgan.apps.swinir_predictor"),
]

FACE_UTILS: List[Tuple[str, str]] = [
    ("FaceEnhancement", "ppgan.faceutils.face_enhancement.face_enhance"),
    ("gfp_FaceEnhancement", "ppgan.faceutils.face_enhancement.gfpgan_enhance"),
]


def add_local_repo_to_path() -> Path | None:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "ppgan").is_dir():
            sys.path.insert(0, str(parent))
            return parent
    return None


def check_module(name: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {"module": name}
    if importlib.util.find_spec(name) is None:
        info["available"] = False
        info["error"] = "not found"
        return info
    try:
        module = importlib.import_module(name)
        info["available"] = True
        info["file"] = getattr(module, "__file__", None)
        if name == "paddle":
            import paddle  # type: ignore

            info["version"] = getattr(paddle, "__version__", None)
            try:
                info["compiled_with_cuda"] = bool(paddle.is_compiled_with_cuda())
            except Exception as exc:  # pragma: no cover - defensive only
                info["compiled_with_cuda"] = None
                info["cuda_probe_error"] = f"{exc.__class__.__name__}: {exc}"
        return info
    except Exception as exc:
        info["available"] = False
        info["error"] = f"{exc.__class__.__name__}: {exc}"
        return info


def inspect_symbol(module_name: str, symbol: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {"module": module_name, "symbol": symbol}
    try:
        module = importlib.import_module(module_name)
        obj = getattr(module, symbol)
        info["available"] = True
        info["constructor"] = str(inspect.signature(obj))
        run = getattr(obj, "run", None)
        if run is not None:
            info["run"] = str(inspect.signature(run))
        enhance = getattr(obj, "enhance_from_image", None)
        if enhance is not None:
            info["enhance_from_image"] = str(inspect.signature(enhance))
        return info
    except Exception as exc:
        info["available"] = False
        info["error"] = f"{exc.__class__.__name__}: {exc}"
        return info


def human_block(title: str) -> None:
    print(f"\n== {title} ==")


def print_report(report: Dict[str, Any]) -> None:
    human_block("Core modules")
    for item in report["core_modules"]:
        status = "ok" if item.get("available") else "missing"
        extra = []
        if item.get("version"):
            extra.append(f"version={item['version']}")
        if item.get("compiled_with_cuda") is not None:
            extra.append(f"cuda={item['compiled_with_cuda']}")
        if item.get("error"):
            extra.append(f"error={item['error']}")
        suffix = f" ({', '.join(extra)})" if extra else ""
        print(f"{item['module']}: {status}{suffix}")

    human_block("Optional modules")
    for item in report["optional_modules"]:
        status = "ok" if item.get("available") else "missing"
        suffix = f" ({item['error']})" if item.get("error") else ""
        print(f"{item['module']}: {status}{suffix}")

    human_block("Predictor signatures")
    for item in report["predictors"]:
        status = "ok" if item.get("available") else "missing"
        print(f"{item['symbol']}: {status}")
        if item.get("constructor"):
            print(f"  ctor: {item['constructor']}")
        if item.get("run"):
            print(f"  run:  {item['run']}")
        if item.get("enhance_from_image"):
            print(f"  enhance_from_image: {item['enhance_from_image']}")
        if item.get("error"):
            print(f"  error: {item['error']}")

    human_block("Face utilities")
    for item in report["face_utils"]:
        status = "ok" if item.get("available") else "missing"
        print(f"{item['symbol']}: {status}")
        if item.get("constructor"):
            print(f"  ctor: {item['constructor']}")
        if item.get("enhance_from_image"):
            print(f"  enhance_from_image: {item['enhance_from_image']}")
        if item.get("error"):
            print(f"  error: {item['error']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check PaddleGAN image/face app dependencies and predictor signatures safely."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print JSON instead of human-readable text",
    )
    parser.add_argument(
        "--require-gpu",
        action="store_true",
        help="exit non-zero if Paddle is not compiled with CUDA",
    )
    parser.add_argument(
        "--require-face",
        action="store_true",
        help="exit non-zero if the face stack cannot be imported",
    )
    parser.add_argument(
        "--require-clip",
        action="store_true",
        help="exit non-zero if the optional CLIP module is missing",
    )
    args = parser.parse_args()

    add_local_repo_to_path()

    report: Dict[str, Any] = {
        "core_modules": [check_module(name) for name in CORE_MODULES],
        "optional_modules": [check_module(name) for name in OPTIONAL_MODULES],
        "predictors": [
            inspect_symbol(module_name, symbol) for symbol, module_name in PREDICTOR_MODULES
        ],
        "face_utils": [inspect_symbol(module_name, symbol) for symbol, module_name in FACE_UTILS],
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_report(report)

    exit_code = 0
    core = {item["module"]: item for item in report["core_modules"]}
    optional = {item["module"]: item for item in report["optional_modules"]}
    predictors = {item["symbol"]: item for item in report["predictors"]}
    face_utils = {item["symbol"]: item for item in report["face_utils"]}

    paddle_ok = core.get("paddle", {}).get("available", False)
    ppgan_ok = core.get("ppgan", {}).get("available", False)
    if not paddle_ok or not ppgan_ok:
        exit_code = 1

    if args.require_gpu:
        if not core.get("paddle", {}).get("compiled_with_cuda", False):
            exit_code = max(exit_code, 2)

    if args.require_clip and not optional.get("clip", {}).get("available", False):
        exit_code = max(exit_code, 3)

    if args.require_face:
        face_ready = all(
            predictors.get(name, {}).get("available", False)
            for name in ["FaceParsePredictor", "Photo2CartoonPredictor", "Pixel2Style2PixelPredictor"]
        ) and optional.get("dlib", {}).get("available", False)
        if not face_ready:
            exit_code = max(exit_code, 4)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
