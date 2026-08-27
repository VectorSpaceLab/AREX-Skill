#!/usr/bin/env python3
"""Read-only prerequisite probe for Outlines local model integrations.

The script checks optional Python modules and device visibility. It never
installs packages, downloads model weights, starts services, or mutates state.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import shutil
import subprocess
from typing import Iterable

TARGETS = {
    "transformers": {
        "modules": ["transformers", "torch"],
        "notes": "Hugging Face text and multimodal wrappers; model download not checked.",
    },
    "llamacpp": {
        "modules": ["llama_cpp"],
        "notes": "llama.cpp wrapper; GGUF model files and build flags not checked.",
    },
    "mlxlm": {
        "modules": ["mlx", "mlx_lm"],
        "notes": "MLX-LM requires Apple Silicon/macOS; import alone is not runtime proof.",
    },
    "vllm-offline": {
        "modules": ["vllm"],
        "notes": "In-process vLLM; GPU/CUDA/model initialization not checked.",
    },
    "backends": {
        "modules": ["outlines_core", "llguidance", "xgrammar"],
        "notes": "Structured-generation backend packages; optional backends may be absent.",
    },
}

ALIASES = {"llama.cpp": "llamacpp", "vllm": "vllm-offline", "all": "all"}


def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def nvidia_smi_summary() -> dict[str, object]:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return {"available": False, "gpus": []}
    cmd = [exe, "--query-gpu=name,memory.total,driver_version,compute_cap", "--format=csv,noheader,nounits"]
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=5, check=False)
    except Exception as exc:  # pragma: no cover - host dependent
        return {"available": True, "error": str(exc), "gpus": []}
    gpus = []
    for line in proc.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) >= 4:
            gpus.append({"name": parts[0], "memory_mib": parts[1], "driver": parts[2], "compute_capability": parts[3]})
    return {"available": proc.returncode == 0, "gpus": gpus, "stderr": proc.stderr.strip()}


def torch_summary() -> dict[str, object]:
    if not module_available("torch"):
        return {"available": False}
    try:
        import torch  # type: ignore

        info: dict[str, object] = {
            "available": True,
            "version": getattr(torch, "__version__", "unknown"),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
        if torch.cuda.is_available():
            info["cuda_version"] = getattr(torch.version, "cuda", None)
            info["device0"] = torch.cuda.get_device_name(0)
            info["capability0"] = list(torch.cuda.get_device_capability(0))
        if hasattr(torch.backends, "mps"):
            info["mps_available"] = bool(torch.backends.mps.is_available())
        return info
    except Exception as exc:  # pragma: no cover - host dependent
        return {"available": True, "error": str(exc)}


def normalize_targets(raw: Iterable[str]) -> list[str]:
    selected: list[str] = []
    for name in raw:
        key = ALIASES.get(name.strip().lower(), name.strip().lower())
        if key == "all":
            return list(TARGETS)
        if key not in TARGETS:
            choices = ", ".join(sorted(TARGETS))
            raise SystemExit(f"Unknown target {name!r}. Choose from: {choices}, all")
        if key not in selected:
            selected.append(key)
    return selected or list(TARGETS)


def inspect_target(name: str) -> dict[str, object]:
    spec = TARGETS[name]
    modules = {module: module_available(module) for module in spec["modules"]}
    return {
        "target": name,
        "modules": modules,
        "missing_modules": [module for module, ok in modules.items() if not ok],
        "notes": spec["notes"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="No-network local Outlines model prerequisite checker.")
    parser.add_argument("--targets", nargs="+", default=["all"], help="Targets: transformers, llamacpp, mlxlm, vllm-offline, backends, all")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = [inspect_target(name) for name in normalize_targets(args.targets)]
    payload = {
        "platform": {"system": platform.system(), "machine": platform.machine()},
        "nvidia_smi": nvidia_smi_summary(),
        "torch": torch_summary(),
        "targets": results,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"platform: {payload['platform']['system']} {payload['platform']['machine']}")
        print(f"nvidia-smi available: {payload['nvidia_smi'].get('available')}")
        if payload["nvidia_smi"].get("gpus"):
            for gpu in payload["nvidia_smi"]["gpus"]:  # type: ignore[index]
                print(f"  gpu: {gpu['name']} memory={gpu['memory_mib']}MiB driver={gpu['driver']} cc={gpu['compute_capability']}")
        print(f"torch: {payload['torch']}")
        for result in results:
            print(f"[{result['target']}]")
            for module, ok in result["modules"].items():  # type: ignore[index, union-attr]
                print(f"  {module}: {'available' if ok else 'missing'}")
            print(f"  notes: {result['notes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
