#!/usr/bin/env python3
"""Check a Ludwig environment without running downloads, training, or services."""
import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Ludwig import, CLI help, optional packages, and optional CUDA.")
    parser.add_argument("--check-cli", action="store_true", help="Run `ludwig --help` with a short timeout.")
    parser.add_argument("--check-optional", action="store_true", help="Report selected optional dependency availability.")
    parser.add_argument("--check-cuda", action="store_true", help="Query torch CUDA availability without allocating large tensors.")
    args = parser.parse_args()
    result = {"python": sys.version.split()[0]}
    try:
        import ludwig
        result["ludwig_version"] = getattr(ludwig, "__version__", None)
        result["ludwig_import"] = True
    except Exception as exc:
        result["ludwig_import"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"
        print(json.dumps(result, indent=2))
        return 2
    if args.check_cli:
        ludwig_exe = shutil.which("ludwig") or str(Path(sys.executable).with_name("ludwig"))
        try:
            proc = subprocess.run([ludwig_exe, "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
            result["cli_help"] = {"executable": ludwig_exe, "exit_code": proc.returncode, "has_train": "train" in proc.stdout, "has_serve": "serve" in proc.stdout}
        except FileNotFoundError:
            result["cli_help"] = {"executable": ludwig_exe, "exit_code": 127, "error": "ludwig console script not found on PATH or beside the current Python"}
    if args.check_optional:
        names = ["fastapi", "uvicorn", "ray", "optuna", "kserve", "vllm", "onnx", "mlflow", "anthropic", "openai", "captum"]
        result["optional_packages"] = {name: bool(importlib.util.find_spec(name)) for name in names}
    if args.check_cuda:
        try:
            import torch
            result["torch"] = {"version": torch.__version__, "cuda_version": torch.version.cuda, "cuda_available": torch.cuda.is_available(), "device_count": torch.cuda.device_count()}
            if torch.cuda.is_available():
                result["torch"]["device0"] = torch.cuda.get_device_name(0)
        except Exception as exc:
            result["torch"] = {"error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
