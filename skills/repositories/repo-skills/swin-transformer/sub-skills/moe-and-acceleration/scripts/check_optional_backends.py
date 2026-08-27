#!/usr/bin/env python3
"""Probe optional Swin-Transformer backends without installing or building anything."""
from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import shutil
import subprocess


def imp(name: str):
    stream = io.StringIO()
    try:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            mod = importlib.import_module(name)
        item = {"ok": True, "version": getattr(mod, "__version__", None)}
    except Exception as exc:
        item = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    captured = stream.getvalue().strip()
    if captured:
        item["messages"] = captured.splitlines()[:5]
    return item


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe optional Swin-Transformer CUDA/MoE/Apex backends safely.")
    ap.add_argument("--text", action="store_true", help="Print a short human-readable note after the JSON summary.")
    args = ap.parse_args()
    result = {"torch": imp("torch"), "tutel": imp("tutel"), "apex": imp("apex"), "swin_window_process": imp("swin_window_process")}
    if result["torch"]["ok"]:
        import torch
        result["cuda"] = {
            "torch_cuda_version": getattr(torch.version, "cuda", None),
            "is_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
        if torch.cuda.is_available():
            result["cuda"]["device_0"] = torch.cuda.get_device_name(0)
            result["cuda"]["capability_0"] = torch.cuda.get_device_capability(0)
    result["nvcc"] = shutil.which("nvcc")
    if result["nvcc"]:
        try:
            out = subprocess.run([result["nvcc"], "--version"], text=True, capture_output=True, timeout=10)
            result["nvcc_version_tail"] = (out.stdout or out.stderr).strip().splitlines()[-1:]
        except Exception as exc:
            result["nvcc_error"] = str(exc)
    result["note"] = "CUDA unavailable; MoE/fused CUDA runtime is unverified." if not result.get("cuda", {}).get("is_available") else "CUDA is visible; still verify Tutel/Apex/fused extension before claiming optional runtime support."
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.text:
        print("NOTE:", result["note"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
