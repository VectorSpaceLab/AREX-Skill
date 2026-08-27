#!/usr/bin/env python3
"""Safe offline smoke checks for LLM Foundry inference/conversion plans.

This bundled helper is self-contained. It validates environment modules, local
Hugging Face checkpoint folders, Composer checkpoint path/URI shape, and obvious
backend option conflicts. It never downloads models, loads weights, calls remote
endpoints, uploads artifacts, runs ONNX export, or runs FasterTransformer.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REMOTE_URI_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
PACKAGE_PROBES = {
    "llmfoundry": "llmfoundry",
    "torch": "torch",
    "transformers": "transformers",
    "composer": "composer",
    "accelerate": "accelerate",
    "huggingface_hub": "huggingface_hub",
    "onnx": "onnx",
    "onnxruntime": "onnxruntime",
    "flash_attn": "flash_attn",
    "mpi4py": "mpi4py",
}
HF_TOKEN_ENV_NAMES = ("HF_TOKEN", "HUGGINGFACE_HUB_TOKEN", "HUGGING_FACE_HUB_TOKEN")
LOCAL_HF_CONFIG = {"config.json"}
TOKENIZER_HINTS = {
    "tokenizer.json",
    "tokenizer.model",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "vocab.json",
    "merges.txt",
}
WEIGHT_PATTERNS = (
    "pytorch_model.bin",
    "model.safetensors",
    "pytorch_model.bin.index.json",
    "model.safetensors.index.json",
)


def is_remote_uri(value: str | None) -> bool:
    return bool(value and REMOTE_URI_RE.match(value))


def module_available(module_name: str) -> dict[str, Any]:
    try:
        spec = importlib.util.find_spec(module_name)
    except Exception as exc:
        return {"module": module_name, "available": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"module": module_name, "available": spec is not None, "origin": getattr(spec, "origin", None) if spec else None}


def pathish(value: str) -> Path:
    return Path(value).expanduser()


def add(report: dict[str, Any], kind: str, msg: str) -> None:
    report[kind].append(msg)


def check_modules(report: dict[str, Any]) -> None:
    modules = {label: module_available(mod) for label, mod in PACKAGE_PROBES.items()}
    report["modules"] = modules
    for required in ("llmfoundry", "torch", "transformers", "composer"):
        if not modules[required]["available"]:
            add(report, "errors", f"required runtime module not import-discoverable: {required}")
    if not modules["flash_attn"]["available"]:
        add(report, "warnings", "flash_attn is not import-discoverable; use attn_impl=torch or install a torch/CUDA/Python-matched flash-attn build before claiming flash attention")
    if not modules["onnx"]["available"] or not modules["onnxruntime"]["available"]:
        add(report, "warnings", "onnx or onnxruntime is not import-discoverable; ONNX export/verification may be unavailable")


def check_torch(report: dict[str, Any]) -> None:
    if not report.get("modules", {}).get("torch", {}).get("available"):
        return
    try:
        import torch
    except Exception as exc:
        add(report, "errors", f"torch import failed: {type(exc).__name__}: {exc}")
        return
    item: dict[str, Any] = {
        "version": getattr(torch, "__version__", "unknown"),
        "cuda_runtime": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()),
    }
    if torch.cuda.is_available():
        try:
            item["device_0"] = torch.cuda.get_device_name(0)
            item["capability_0"] = torch.cuda.get_device_capability(0)
        except Exception as exc:
            item["device_error"] = f"{type(exc).__name__}: {exc}"
    report["torch"] = item


def check_hf_folder(report: dict[str, Any], folder_arg: str | None) -> None:
    if not folder_arg:
        return
    folder = pathish(folder_arg)
    item: dict[str, Any] = {"path": str(folder), "exists": folder.exists(), "is_dir": folder.is_dir()}
    if not folder.exists() or not folder.is_dir():
        add(report, "errors", f"HF folder does not exist or is not a directory: {folder_arg}")
        report["hf_folder"] = item
        return
    names = {p.name for p in folder.iterdir() if p.is_file()}
    item["has_config"] = bool(LOCAL_HF_CONFIG & names)
    item["tokenizer_files"] = sorted(TOKENIZER_HINTS & names)
    item["weight_files"] = sorted(name for name in names if name in WEIGHT_PATTERNS or name.startswith("pytorch_model-") or name.startswith("model-") and name.endswith(".safetensors"))
    if not item["has_config"]:
        add(report, "errors", "HF folder is missing config.json")
    if not item["tokenizer_files"]:
        add(report, "warnings", "HF folder has no obvious tokenizer files; generation/chat may need a separate tokenizer")
    if not item["weight_files"]:
        add(report, "warnings", "HF folder has no obvious PyTorch/safetensors weights; this may be a config-only folder")
    report["hf_folder"] = item


def check_checkpoint(report: dict[str, Any], checkpoint: str | None) -> None:
    if not checkpoint:
        return
    item: dict[str, Any] = {"value": checkpoint, "remote_uri": is_remote_uri(checkpoint)}
    if item["remote_uri"]:
        add(report, "warnings", "Composer checkpoint is a remote URI; confirm credentials, transfer cost, and staging disk before conversion")
    else:
        path = pathish(checkpoint)
        item["exists"] = path.exists()
        item["is_file"] = path.is_file()
        if not path.exists():
            add(report, "errors", f"Composer checkpoint path does not exist: {checkpoint}")
        elif not path.is_file():
            add(report, "errors", f"Composer checkpoint path is not a file: {checkpoint}")
        elif path.suffix not in {".pt", ".pth", ".bin"}:
            add(report, "warnings", f"Composer checkpoint extension {path.suffix!r} is unusual; verify it is a Composer Trainer checkpoint")
    report["composer_checkpoint"] = item


def check_options(report: dict[str, Any], args: argparse.Namespace) -> None:
    if args.device and args.device_map:
        add(report, "errors", "Do not set both --device and --device-map; choose an explicit single device or a placement strategy")
    if args.model_dtype in {"bf16", "fp16"} and args.device == "cpu":
        add(report, "warnings", f"{args.model_dtype} on CPU may be unsupported or slow; prefer fp32 CPU or a CUDA device")
    if args.attn_impl == "flash" and not report.get("modules", {}).get("flash_attn", {}).get("available"):
        add(report, "errors", "--attn-impl flash requested but flash_attn is not import-discoverable")
    if args.device and str(args.device).startswith("cuda") and not report.get("torch", {}).get("cuda_available"):
        add(report, "errors", f"CUDA device requested ({args.device}) but torch.cuda.is_available() is false")
    if args.use_auth_token and not any(os.environ.get(name) for name in HF_TOKEN_ENV_NAMES):
        add(report, "warnings", "Hub auth requested but no common HF token environment variable is set; ensure login/token before accessing gated assets")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {"errors": [], "warnings": [], "info": [], "modules": {}, "torch": {}}
    if args.check_env or True:
        check_modules(report)
        check_torch(report)
    check_hf_folder(report, args.hf_folder)
    check_checkpoint(report, args.composer_checkpoint)
    check_options(report, args)
    if not args.hf_folder and not args.composer_checkpoint:
        add(report, "info", "No local HF folder or Composer checkpoint supplied; performed environment/backend option checks only")
    report["ok"] = not report["errors"] and not (args.strict and report["warnings"])
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely probe LLM Foundry inference/conversion prerequisites without loading weights or using network.")
    parser.add_argument("--check-env", action="store_true", help="Check import-discoverability of common runtime modules (default behavior)")
    parser.add_argument("--hf-folder", help="Local Hugging Face checkpoint folder to inspect without loading weights")
    parser.add_argument("--composer-checkpoint", help="Local Composer checkpoint path or remote URI to validate superficially")
    parser.add_argument("--model-dtype", choices=["fp32", "fp16", "bf16"], default="bf16", help="Planned model dtype for warning checks")
    parser.add_argument("--device", help="Planned explicit device, e.g. cpu or cuda:0")
    parser.add_argument("--device-map", help="Planned HF/Accelerate device_map, e.g. auto or balanced")
    parser.add_argument("--attn-impl", choices=["torch", "flash"], default=None, help="Planned MPT attention implementation")
    parser.add_argument("--use-auth-token", action="store_true", help="Warn if common HF token environment variables are absent")
    parser.add_argument("--strict", action="store_true", help="Return non-zero on warnings as well as errors")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)

    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(f"LLM Foundry inference smoke: {'PASS' if report['ok'] else 'FAIL'}")
        for key in ("modules", "torch", "hf_folder", "composer_checkpoint"):
            if key in report and report[key]:
                print(f"\n{key}:")
                print(json.dumps(report[key], indent=2, default=str))
        for msg in report["errors"]:
            print(f"ERROR: {msg}")
        for msg in report["warnings"]:
            print(f"WARNING: {msg}")
        for msg in report["info"]:
            print(f"INFO: {msg}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
