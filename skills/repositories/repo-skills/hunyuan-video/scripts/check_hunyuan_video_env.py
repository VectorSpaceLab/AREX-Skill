#!/usr/bin/env python3
"""Read-only HunyuanVideo environment diagnostic.

This helper checks Python imports, CUDA visibility, and optional acceleration
packages without downloading checkpoints or loading HunyuanVideo weights.

Example:
  python check_hunyuan_video_env.py --json
  python check_hunyuan_video_env.py --require-cuda --check-optional
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
from typing import Any, Dict


def probe_import(name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    return {"ok": True, "version": version}


def probe_torch(require_cuda: bool) -> Dict[str, Any]:
    result: Dict[str, Any] = probe_import("torch")
    if not result.get("ok"):
        result["cuda_ok"] = False
        return result

    import torch  # type: ignore

    result.update(
        {
            "version": torch.__version__,
            "cuda_compiled": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
            "devices": [],
        }
    )
    if torch.cuda.is_available():
        for idx in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(idx)
            result["devices"].append(
                {
                    "index": idx,
                    "name": torch.cuda.get_device_name(idx),
                    "total_memory_gb": round(props.total_memory / (1024**3), 2),
                    "capability": f"{props.major}.{props.minor}",
                }
            )
        try:
            tensor = torch.zeros((1,), device="cuda")
            result["cuda_tensor_smoke"] = float(tensor.sum().item()) == 0.0
        except Exception as exc:  # pragma: no cover - hardware dependent
            result["cuda_tensor_smoke"] = False
            result["cuda_tensor_error"] = f"{type(exc).__name__}: {exc}"
    else:
        result["cuda_tensor_smoke"] = False
    result["cuda_ok"] = bool(result.get("cuda_available")) and (
        not require_cuda or bool(result.get("cuda_tensor_smoke"))
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check HunyuanVideo runtime dependencies without loading checkpoints.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    parser.add_argument("--require-cuda", action="store_true", help="Exit non-zero when CUDA is not usable.")
    parser.add_argument("--check-optional", action="store_true", help="Also check optional flash-attn and xfuser imports.")
    args = parser.parse_args()

    required_modules = [
        "torch",
        "torchvision",
        "diffusers",
        "transformers",
        "tokenizers",
        "accelerate",
        "einops",
        "imageio",
        "safetensors",
        "gradio",
    ]
    optional_modules = ["flash_attn", "xfuser"] if args.check_optional else []

    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "required_imports": {},
        "optional_imports": {},
        "torch": probe_torch(args.require_cuda),
    }
    for name in required_modules:
        if name == "torch":
            report["required_imports"][name] = {"ok": report["torch"].get("ok"), "version": report["torch"].get("version")}
        else:
            report["required_imports"][name] = probe_import(name)
    for name in optional_modules:
        report["optional_imports"][name] = probe_import(name)

    missing_required = [name for name, item in report["required_imports"].items() if not item.get("ok")]
    cuda_failed = args.require_cuda and not report["torch"].get("cuda_ok")
    ok = not missing_required and not cuda_failed
    report["ok"] = ok
    report["missing_required"] = missing_required
    if cuda_failed:
        report["cuda_failure"] = "CUDA was required but torch could not complete a CUDA availability/tensor smoke check."

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print(f"Platform: {report['platform']}")
        print(f"Torch: {report['torch'].get('version')} CUDA compiled={report['torch'].get('cuda_compiled')} available={report['torch'].get('cuda_available')} devices={report['torch'].get('device_count')}")
        for device in report["torch"].get("devices", []):
            print(f"  GPU {device['index']}: {device['name']} ({device['total_memory_gb']} GB, cc {device['capability']})")
        if missing_required:
            print("Missing required imports: " + ", ".join(missing_required))
        if optional_modules:
            for name, item in report["optional_imports"].items():
                print(f"Optional {name}: {'ok' if item.get('ok') else item.get('error')}")
        print("Status: " + ("OK" if ok else "FAILED"))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
