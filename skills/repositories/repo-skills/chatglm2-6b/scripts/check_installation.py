#!/usr/bin/env python3
"""Check ChatGLM2-6B dependency metadata and backend availability.

This is a no-download preflight. It does not load model weights or start a
service. Use the more detailed helper under sub-skills/chat-and-demos when a
local model path or Gradio compatibility check is needed.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("auto", "cpu", "cuda", "mps"), default="auto")
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    required = ["torch", "transformers"]
    packages = {}
    missing = []
    for name in required + ["accelerate", "cpm_kernels"]:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
            if name in required:
                missing.append(name)
    backend_ok = True
    details: dict[str, object] = {}
    try:
        import torch  # type: ignore
        details["torch"] = torch.__version__
        details["cuda_available"] = bool(torch.cuda.is_available())
        details["cuda_devices"] = int(torch.cuda.device_count())
        details["mps_available"] = bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
        if args.backend == "cuda":
            backend_ok = bool(torch.cuda.is_available())
        elif args.backend == "mps":
            backend_ok = bool(details["mps_available"])
    except Exception as exc:
        details["error"] = f"{type(exc).__name__}: {exc}"
        backend_ok = args.backend in {"auto", "cpu"}
    path_ok = args.model_path is None or args.model_path.is_dir()
    result = {"python": sys.version.split()[0], "packages": packages, "backend": args.backend, "backend_details": details, "model_path_ok": path_ok, "ok": not missing and backend_ok and path_ok}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
