#!/usr/bin/env python3
"""Check SaProt runtime prerequisites without downloading assets or launching training."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional


OPTIONAL_IMPORTS = {
    "yaml": "PyYAML; needed for full YAML config validation",
    "easydict": "needed by repository launchers",
    "Bio": "Biopython; needed for pLDDT parsing in structure conversion",
    "numpy": "needed by structure conversion and scientific utilities",
    "lmdb": "needed for LMDB dataset checks and conversion",
    "pandas": "needed by original ClinVar AUC script and some analysis workflows",
    "torch": "needed for model execution and training",
    "transformers": "needed for Hugging Face SaProt loading",
    "pytorch_lightning": "needed for training/evaluation launchers",
    "torchmetrics": "needed by task models",
    "esm": "provided by fair-esm; needed for ESM-style .pt loading",
    "peft": "needed only for LoRA workflows",
}

HF_CONFIG_FILES = ("config.json",)
HF_TOKENIZER_HINTS = ("tokenizer_config.json", "special_tokens_map.json", "vocab.txt", "tokenizer.json", "vocab.json")
HF_WEIGHT_HINTS = ("pytorch_model.bin", "model.safetensors", "pytorch_model.bin.index.json", "model.safetensors.index.json")


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def import_report() -> Dict[str, Dict[str, Any]]:
    return {
        name: {"available": module_available(name), "purpose": purpose}
        for name, purpose in OPTIONAL_IMPORTS.items()
    }


def existing_files(directory: Path, names: tuple[str, ...]) -> List[str]:
    return [name for name in names if (directory / name).exists()]


def model_dir_report(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    model_dir = Path(os.path.expanduser(path))
    report: Dict[str, Any] = {"path": str(model_dir), "exists": model_dir.exists(), "is_dir": model_dir.is_dir()}
    if not model_dir.exists() or not model_dir.is_dir():
        report["ok"] = False
        report["missing"] = ["local Hugging Face model directory"]
        return report
    present = {
        "config": existing_files(model_dir, HF_CONFIG_FILES),
        "tokenizer": existing_files(model_dir, HF_TOKENIZER_HINTS),
        "weights": existing_files(model_dir, HF_WEIGHT_HINTS),
        "sharded_weights": [path.name for pattern in ("pytorch_model-*.bin", "model-*.safetensors") for path in sorted(model_dir.glob(pattern))],
    }
    missing = []
    if not present["config"]:
        missing.append("config.json")
    if not present["tokenizer"]:
        missing.append("tokenizer metadata")
    if not present["weights"] and not present["sharded_weights"]:
        missing.append("model weights")
    report.update({"ok": not missing, "present": present, "missing": missing})
    return report


def foldseek_report(command: Optional[str]) -> Optional[Dict[str, Any]]:
    if not command:
        return None
    candidate = Path(os.path.expanduser(command))
    if candidate.exists():
        resolved = str(candidate)
        executable = candidate.is_file() and os.access(candidate, os.X_OK)
    else:
        resolved = shutil.which(command)
        executable = resolved is not None
    report: Dict[str, Any] = {"requested": command, "resolved": resolved, "ok": bool(executable)}
    if executable and resolved:
        try:
            completed = subprocess.run([resolved, "version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10, check=False)
            report["version_exit_code"] = completed.returncode
            report["version_output"] = (completed.stdout or completed.stderr).strip().splitlines()[:3]
        except Exception as exc:  # noqa: BLE001 - diagnostic only
            report["version_error"] = repr(exc)
    else:
        report["missing"] = "Foldseek executable not found or not executable"
    return report


def cuda_report(enabled: bool) -> Optional[Dict[str, Any]]:
    if not enabled:
        return None
    report: Dict[str, Any] = {}
    try:
        completed = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version,compute_cap", "--format=csv,noheader,nounits"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
        report["nvidia_smi_exit_code"] = completed.returncode
        report["gpus"] = completed.stdout.strip().splitlines() if completed.returncode == 0 else []
        if completed.returncode != 0:
            report["nvidia_smi_error"] = completed.stderr.strip()
    except Exception as exc:  # noqa: BLE001 - diagnostic only
        report["nvidia_smi_error"] = repr(exc)

    if module_available("torch"):
        try:
            import torch  # type: ignore

            report["torch"] = {
                "version": getattr(torch, "__version__", None),
                "cuda_version": getattr(torch.version, "cuda", None),
                "cuda_available": bool(torch.cuda.is_available()),
                "device_count": int(torch.cuda.device_count()),
            }
            if torch.cuda.is_available():
                report["torch"]["first_device"] = torch.cuda.get_device_name(0)
                report["torch"]["first_capability"] = torch.cuda.get_device_capability(0)
        except Exception as exc:  # noqa: BLE001 - diagnostic only
            report["torch_error"] = repr(exc)
    else:
        report["torch"] = {"available": False}
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check SaProt optional dependencies and local assets safely.")
    parser.add_argument("--check-python-imports", action="store_true", help="Report optional Python package import availability.")
    parser.add_argument("--model-dir", help="Local Hugging Face SaProt model directory to validate.")
    parser.add_argument("--foldseek", help="Foldseek executable path or command name to validate.")
    parser.add_argument("--check-cuda", action="store_true", help="Report nvidia-smi and torch CUDA facts when available.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args()


def print_text(report: Dict[str, Any]) -> None:
    if "imports" in report:
        print("Python imports:")
        for name, info in report["imports"].items():
            status = "ok" if info["available"] else "missing"
            print(f"  - {name}: {status}; {info['purpose']}")
    if report.get("model_dir") is not None:
        model = report["model_dir"]
        print(f"Model directory: {model['path']}")
        print(f"  ok: {model.get('ok', False)}")
        if model.get("missing"):
            print(f"  missing: {', '.join(model['missing'])}")
    if report.get("foldseek") is not None:
        foldseek = report["foldseek"]
        print(f"Foldseek: {foldseek['requested']}")
        print(f"  resolved: {foldseek.get('resolved')}")
        print(f"  ok: {foldseek.get('ok', False)}")
        if foldseek.get("missing"):
            print(f"  missing: {foldseek['missing']}")
    if report.get("cuda") is not None:
        print("CUDA:")
        print(json.dumps(report["cuda"], indent=2))


def main() -> int:
    args = parse_args()
    report: Dict[str, Any] = {"ok": True}
    if args.check_python_imports:
        report["imports"] = import_report()
    if args.model_dir:
        report["model_dir"] = model_dir_report(args.model_dir)
        report["ok"] = report["ok"] and bool(report["model_dir"].get("ok"))
    if args.foldseek:
        report["foldseek"] = foldseek_report(args.foldseek)
        report["ok"] = report["ok"] and bool(report["foldseek"].get("ok"))
    if args.check_cuda:
        report["cuda"] = cuda_report(True)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
