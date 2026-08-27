#!/usr/bin/env python3
"""Safe Swin-Transformer environment probe.

Example:
  python check_env.py --repo-root /path/to/Swin-Transformer

The script imports baseline dependencies and optional backends. It does not
train, download, compile CUDA extensions, or mutate the environment.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path


def probe_import(name: str):
    stream = io.StringIO()
    try:
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            mod = importlib.import_module(name)
        version = getattr(mod, "__version__", None)
        item = {"name": name, "ok": True, "version": version}
    except Exception as exc:  # keep broad: optional imports may raise runtime errors
        item = {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    captured = stream.getvalue().strip()
    if captured:
        item["messages"] = captured.splitlines()[:5]
    return item


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe Swin-Transformer imports and optional backends safely.")
    ap.add_argument("--repo-root", type=Path, help="Swin-Transformer checkout root to add to sys.path for local modules.")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of a readable summary.")
    args = ap.parse_args()

    if args.repo_root:
        root = args.repo_root.resolve()
        if not root.exists():
            raise SystemExit(f"repo root does not exist: {root}")
        sys.path.insert(0, str(root))

    required = ["torch", "torchvision", "timm", "yacs", "yaml", "numpy", "scipy", "termcolor"]
    repo_modules = ["config", "models", "data", "optimizer", "lr_scheduler", "utils"] if args.repo_root else []
    optional = ["apex", "tutel", "swin_window_process"]

    result = {
        "required": [probe_import(x) for x in required],
        "repo_modules": [probe_import(x) for x in repo_modules],
        "optional": [probe_import(x) for x in optional],
        "cuda": {},
        "nvcc": shutil.which("nvcc"),
    }
    torch_info = next((x for x in result["required"] if x["name"] == "torch" and x["ok"]), None)
    if torch_info:
        import torch
        result["cuda"] = {
            "torch_cuda_version": getattr(torch.version, "cuda", None),
            "is_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
        if torch.cuda.is_available():
            result["cuda"]["device_0"] = torch.cuda.get_device_name(0)
            result["cuda"]["capability_0"] = torch.cuda.get_device_capability(0)
    if result["nvcc"]:
        try:
            out = subprocess.run([result["nvcc"], "--version"], text=True, capture_output=True, timeout=10)
            result["nvcc_version"] = (out.stdout or out.stderr).strip().splitlines()[-1:]
        except Exception as exc:
            result["nvcc_error"] = str(exc)

    failed_required = [x for x in result["required"] + result["repo_modules"] if not x["ok"]]
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Swin-Transformer environment probe")
        for group in ["required", "repo_modules", "optional"]:
            if result[group]:
                print(f"\n{group}:")
                for item in result[group]:
                    status = "OK" if item["ok"] else "MISSING"
                    detail = item.get("version") or item.get("error") or ""
                    print(f"  {status:7} {item['name']}: {detail}")
        print("\nCUDA:", result["cuda"])
        print("nvcc:", result["nvcc"] or "not found")
        if failed_required:
            print("\nRequired import failures were found. Install missing baseline dependencies before running Swin workflows.")
    return 1 if failed_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
