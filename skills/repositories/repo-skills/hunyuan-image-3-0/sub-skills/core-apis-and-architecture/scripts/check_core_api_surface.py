#!/usr/bin/env python3
"""Import and signature smoke for the HunyuanImage-3.0 core API surface.

Safe by default:
- no checkpoint download
- no model generation
- no network access
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
from dataclasses import dataclass, asdict
from typing import Any

TOP_LEVEL_EXPORTS = [
    "HunyuanImage3Config",
    "HunyuanImage3ImageProcessor",
    "HunyuanImage3TokenizerFast",
    "ImageInfo",
    "ImageTensor",
    "JointImageInfo",
    "CondImage",
    "ResolutionGroup",
    "get_system_prompt",
]

TORCH_EXPORTS = [
    "HunyuanImage3ForCausalMM",
    "HunyuanImage3Model",
    "HunyuanImage3PreTrainedModel",
    "CachedRoPE",
    "TimestepEmbedder",
    "UNetDown",
    "UNetUp",
    "apply_rotary_pos_emb",
    "build_batch_2d_rope",
]

DIRECT_IMPORTS = {
    "hunyuan_image_3.hunyuan_image_3_pipeline": [
        "HunyuanImage3Text2ImagePipeline",
        "FlowMatchDiscreteScheduler",
    ],
    "hunyuan_image_3.cache_utils": [
        "cache_init",
        "TaylorCacheContainer",
        "CacheWithFreqsContainer",
    ],
}

@dataclass
class SymbolReport:
    module: str
    signature: str | None = None
    status: str = "ok"
    note: str | None = None

def short_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError) as exc:
        return f"<signature unavailable: {exc}>"

def report_symbol(module_name: str, name: str, obj: Any) -> SymbolReport:
    note = None
    if inspect.isclass(obj):
        note = "class"
    elif inspect.isfunction(obj):
        note = "function"
    return SymbolReport(module=module_name, signature=short_signature(obj), note=note)

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import and signature smoke for the HunyuanImage-3.0 core API surface."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    summary: dict[str, Any] = {
        "package": {},
        "exports": {},
        "direct_imports": {},
        "smoke": {},
        "errors": [],
    }

    pkg = importlib.import_module("hunyuan_image_3")
    summary["package"] = {
        "module_type": type(pkg).__name__,
        "module_file": getattr(pkg, "__file__", None),
    }

    for name in TOP_LEVEL_EXPORTS:
        try:
            obj = getattr(pkg, name)
            summary["exports"][name] = asdict(report_symbol("hunyuan_image_3", name, obj))
        except Exception as exc:  # noqa: BLE001 - smoke helper should capture import failures
            summary["exports"][name] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
            summary["errors"].append(f"{name}: {type(exc).__name__}: {exc}")

    for name in TORCH_EXPORTS:
        try:
            obj = getattr(pkg, name)
            summary["exports"][name] = asdict(report_symbol("hunyuan_image_3", name, obj))
        except Exception as exc:  # noqa: BLE001
            summary["exports"][name] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
            summary["errors"].append(f"{name}: {type(exc).__name__}: {exc}")

    for module_name, names in DIRECT_IMPORTS.items():
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001
            summary["direct_imports"][module_name] = {
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
            }
            summary["errors"].append(f"{module_name}: {type(exc).__name__}: {exc}")
            continue

        module_report: dict[str, Any] = {"status": "ok", "symbols": {}}
        for name in names:
            try:
                obj = getattr(module, name)
                module_report["symbols"][name] = asdict(report_symbol(module_name, name, obj))
            except Exception as exc:  # noqa: BLE001
                module_report["symbols"][name] = {
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                }
                summary["errors"].append(f"{module_name}.{name}: {type(exc).__name__}: {exc}")
        summary["direct_imports"][module_name] = module_report

    try:
        cfg = pkg.HunyuanImage3Config()
        summary["smoke"]["config"] = {
            "model_type": cfg.model_type,
            "model_version": cfg.model_version,
            "image_base_size": cfg.image_base_size,
            "cond_image_type": cfg.cond_image_type,
            "cfg_distilled": cfg.cfg_distilled,
            "use_meanflow": cfg.use_meanflow,
        }
    except Exception as exc:  # noqa: BLE001
        summary["smoke"]["config"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
        summary["errors"].append(f"config smoke: {type(exc).__name__}: {exc}")

    try:
        prompt_none = pkg.get_system_prompt("None", "image")
        prompt_dynamic = pkg.get_system_prompt("dynamic", "image")
        summary["smoke"]["system_prompt"] = {
            "none_is_none": prompt_none is None,
            "dynamic_image_has_text": bool(prompt_dynamic),
            "dynamic_image_prefix": prompt_dynamic[:48] if isinstance(prompt_dynamic, str) else None,
        }
    except Exception as exc:  # noqa: BLE001
        summary["smoke"]["system_prompt"] = {
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }
        summary["errors"].append(f"system prompt smoke: {type(exc).__name__}: {exc}")

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    else:
        print(f"package_module_type: {summary['package'].get('module_type')}")
        for name, result in summary["exports"].items():
            if result.get("status") == "ok":
                print(f"{name}: {result.get('signature')}")
            else:
                print(f"{name}: ERROR {result.get('error')}")
        for module_name, result in summary["direct_imports"].items():
            if result.get("status") != "ok":
                print(f"{module_name}: ERROR {result.get('error')}")
            else:
                for name, symbol in result["symbols"].items():
                    if symbol.get("status") == "ok":
                        print(f"{module_name}.{name}: {symbol.get('signature')}")
                    else:
                        print(f"{module_name}.{name}: ERROR {symbol.get('error')}")
        if "config" in summary["smoke"] and summary["smoke"]["config"].get("status") != "error":
            print(f"config_smoke: {summary['smoke']['config']}")
        else:
            print(f"config_smoke: ERROR {summary['smoke'].get('config')}")
        print(f"system_prompt_smoke: {summary['smoke'].get('system_prompt')}")

    return 0 if not summary["errors"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
