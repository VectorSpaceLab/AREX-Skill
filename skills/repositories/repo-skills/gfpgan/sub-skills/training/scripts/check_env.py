#!/usr/bin/env python3
"""Check GFPGAN training imports, signatures, and optional config readability.

Example:
    python scripts/check_env.py --config options/train_gfpgan_v1_simple.yml --json
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Dict


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate GFPGAN training dependencies without starting a training run.")
    parser.add_argument("--config", help="Optional training YAML to validate for parse/readability.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    result: Dict[str, Any] = {}
    for name in ["gfpgan", "torch", "torchvision", "basicsr", "facexlib", "cv2", "lmdb", "yaml"]:
        try:
            module = importlib.import_module(name)
            result[name] = {"ok": True, "version": getattr(module, "__version__", None)}
        except Exception as exc:
            result[name] = {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}

    try:
        from gfpgan.models.gfpgan_model import GFPGANModel
        from gfpgan.data.ffhq_degradation_dataset import FFHQDegradationDataset
        from gfpgan.archs.gfpganv1_arch import GFPGANv1, FacialComponentDiscriminator
        from gfpgan.archs.gfpganv1_clean_arch import GFPGANv1Clean
        from gfpgan.archs.gfpgan_bilinear_arch import GFPGANBilinear
        from gfpgan.archs.stylegan2_clean_arch import StyleGAN2GeneratorClean
        from gfpgan.archs.stylegan2_bilinear_arch import StyleGAN2GeneratorBilinear
        from gfpgan.archs.arcface_arch import ResNetArcFace

        result["signatures"] = {
            "GFPGANModel": str(inspect.signature(GFPGANModel.__init__)),
            "FFHQDegradationDataset": str(inspect.signature(FFHQDegradationDataset.__init__)),
            "GFPGANv1": str(inspect.signature(GFPGANv1.__init__)),
            "GFPGANv1Clean": str(inspect.signature(GFPGANv1Clean.__init__)),
            "GFPGANBilinear": str(inspect.signature(GFPGANBilinear.__init__)),
            "StyleGAN2GeneratorClean": str(inspect.signature(StyleGAN2GeneratorClean.__init__)),
            "StyleGAN2GeneratorBilinear": str(inspect.signature(StyleGAN2GeneratorBilinear.__init__)),
            "ResNetArcFace": str(inspect.signature(ResNetArcFace.__init__)),
            "FacialComponentDiscriminator": str(inspect.signature(FacialComponentDiscriminator.__init__)),
        }
    except Exception as exc:
        result["signatures"] = {"error": f"{exc.__class__.__name__}: {exc}"}

    try:
        import torch

        result["torch"] = {
            "ok": True,
            "version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_version": getattr(torch.version, "cuda", None),
        }
    except Exception as exc:
        result["torch"] = {"error": f"{exc.__class__.__name__}: {exc}"}

    if args.config:
        config_path = Path(args.config)
        if not config_path.is_file():
            result["config"] = {"ok": False, "error": f"missing config: {config_path}"}
        else:
            try:
                import yaml

                with config_path.open("r") as f:
                    data = yaml.load(f, Loader=yaml.FullLoader)
                result["config"] = {
                    "ok": True,
                    "keys": sorted(list(data.keys())) if isinstance(data, dict) else None,
                }
            except Exception as exc:
                result["config"] = {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}

    ok = all(v.get("ok", False) for k, v in result.items() if k in {"gfpgan", "torch", "torchvision", "basicsr", "facexlib", "cv2", "lmdb", "yaml"})
    if "error" in result.get("signatures", {}):
        ok = False
    if "config" in result and not result["config"].get("ok", False):
        ok = False

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            marker = "OK" if value.get("ok", True) else "FAIL"
            print(f"{marker:10} {key}: {value}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
