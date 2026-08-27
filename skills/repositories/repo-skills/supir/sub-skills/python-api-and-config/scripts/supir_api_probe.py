#!/usr/bin/env python3
"""Safe SUPIR API probe.

Imports key SUPIR modules, prints signatures, and optionally reports CUDA/config
metadata. It does not instantiate SUPIRModel from YAML and does not load model
weights.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
from pathlib import Path
from typing import Any, Dict, List

MODULES = [
    "SUPIR.util",
    "SUPIR.models.SUPIR_model",
    "SUPIR.modules.SUPIR_v0",
    "sgm.util",
    "sgm.modules.diffusionmodules.sampling",
    "llava.llava_agent",
]

SIGNATURES = [
    ("SUPIR.util", "create_model"),
    ("SUPIR.util", "create_SUPIR_model"),
    ("SUPIR.util", "PIL2Tensor"),
    ("SUPIR.util", "Tensor2PIL"),
    ("SUPIR.util", "HWC3"),
    ("SUPIR.util", "upscale_image"),
    ("SUPIR.util", "fix_resize"),
    ("SUPIR.util", "convert_dtype"),
    ("SUPIR.models.SUPIR_model", "SUPIRModel.batchify_denoise"),
    ("SUPIR.models.SUPIR_model", "SUPIRModel.batchify_sample"),
    ("SUPIR.models.SUPIR_model", "SUPIRModel.init_tile_vae"),
    ("llava.llava_agent", "LLavaAgent.__init__"),
    ("llava.llava_agent", "LLavaAgent.gen_image_caption"),
]


def _object(module: Any, dotted: str) -> Any:
    obj = module
    for part in dotted.split("."):
        obj = getattr(obj, part)
    return obj


def _import_modules(skip_llava: bool = False) -> Dict[str, Dict[str, Any]]:
    results: Dict[str, Dict[str, Any]] = {}
    for name in MODULES:
        if skip_llava and name.startswith("llava"):
            results[name] = {"status": "skipped", "file": "--skip-llava"}
            continue
        try:
            mod = importlib.import_module(name)
            results[name] = {"status": "ok", "file": getattr(mod, "__file__", None)}
        except Exception as exc:
            results[name] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
    return results


def _signatures(imports: Dict[str, Dict[str, Any]], skip_llava: bool = False) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for module_name, dotted in SIGNATURES:
        if skip_llava and module_name.startswith("llava"):
            rows.append({"object": f"{module_name}.{dotted}", "status": "skipped", "signature": "--skip-llava"})
            continue
        if imports.get(module_name, {}).get("status") != "ok":
            rows.append({"object": f"{module_name}.{dotted}", "status": "skipped", "signature": "module import failed"})
            continue
        mod = importlib.import_module(module_name)
        try:
            obj = _object(mod, dotted)
            rows.append({"object": f"{module_name}.{dotted}", "status": "ok", "signature": str(inspect.signature(obj))})
        except Exception as exc:
            rows.append({"object": f"{module_name}.{dotted}", "status": "error", "signature": f"{type(exc).__name__}: {exc}"})
    return rows


def _cuda() -> Dict[str, Any]:
    try:
        import torch

        out: Dict[str, Any] = {
            "torch_version": getattr(torch, "__version__", None),
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
        }
        if torch.cuda.is_available():
            x = torch.zeros(1, device="cuda")
            out["allocation_device"] = str(x.device)
        return out
    except Exception as exc:  # pragma: no cover - depends on host env
        return {"error": f"{type(exc).__name__}: {exc}"}


def _config(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover
        return {"path": str(path), "error": f"PyYAML import failed: {exc}"}
    if not path.exists():
        return {"path": str(path), "error": "config not found"}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    model = data.get("model", {}) if isinstance(data, dict) else {}
    params = model.get("params", {}) if isinstance(model, dict) else {}
    sampler = params.get("sampler_config", {}) if isinstance(params, dict) else {}
    return {
        "path": str(path),
        "model_target": model.get("target") if isinstance(model, dict) else None,
        "sampler_target": sampler.get("target") if isinstance(sampler, dict) else None,
        "default_setting": data.get("default_setting") if isinstance(data, dict) else None,
        "checkpoint_fields": {k: data.get(k) for k in ["SDXL_CKPT", "SUPIR_CKPT", "SUPIR_CKPT_Q", "SUPIR_CKPT_F"]} if isinstance(data, dict) else {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe SUPIR imports, signatures, CUDA, and YAML metadata without loading weights.")
    parser.add_argument("--signatures", action="store_true", help="Print key API signatures.")
    parser.add_argument("--check-cuda", action="store_true", help="Report torch/CUDA availability and run a one-element allocation if CUDA is visible.")
    parser.add_argument("--config", type=Path, action="append", default=[], help="SUPIR YAML config to summarize. Repeatable.")
    parser.add_argument("--skip-llava", action="store_true", help="Treat LLaVA as optional and skip llava.llava_agent import/signature checks.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of readable text.")
    args = parser.parse_args()

    imports = _import_modules(skip_llava=args.skip_llava)
    result: Dict[str, Any] = {"imports": imports}
    if args.signatures:
        result["signatures"] = _signatures(imports, skip_llava=args.skip_llava)
    if args.check_cuda:
        result["cuda"] = _cuda()
    if args.config:
        result["configs"] = [_config(p) for p in args.config]

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("# imports")
        for name, row in imports.items():
            print(f"{name}: {row['status']} {row.get('error', row.get('file', ''))}")
        if args.signatures:
            print("\n# signatures")
            for row in result["signatures"]:
                print(f"{row['object']}: {row['status']} {row['signature']}")
        if args.check_cuda:
            print("\n# cuda")
            for k, v in result["cuda"].items():
                print(f"{k}: {v}")
        if args.config:
            print("\n# configs")
            for cfg in result["configs"]:
                print(json.dumps(cfg, indent=2, sort_keys=True))

    return 0 if all(row["status"] in {"ok", "skipped"} for row in imports.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
