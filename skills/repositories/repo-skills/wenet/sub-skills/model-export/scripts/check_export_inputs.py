#!/usr/bin/env python3
"""Safe preflight checks for WeNet export inputs and optional dependencies."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


MODE_DEPS = {
    "jit": [],
    "onnx-cpu": ["onnx", "onnxruntime"],
    "onnx-gpu": ["onnx", "onnxruntime"],
    "ipex": ["intel_extension_for_pytorch"],
    "bpu": ["onnx"],
}


def dep_status(modules: list[str]) -> dict[str, bool]:
    return {name: importlib.util.find_spec(name) is not None for name in modules}


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight WeNet model export inputs without loading a checkpoint.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--model-dir", type=Path, help="Directory containing train.yaml and final.pt or another checkpoint.")
    src.add_argument("--config", type=Path, help="Explicit train.yaml/config path.")
    parser.add_argument("--checkpoint", type=Path, help="Explicit checkpoint path; required when --config is used unless --model-dir has final.pt.")
    parser.add_argument("--mode", choices=sorted(MODE_DEPS), default="jit", help="Export mode to preflight.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    if args.model_dir:
        config = args.model_dir / "train.yaml"
        checkpoint = args.checkpoint or (args.model_dir / "final.pt")
        units = args.model_dir / "units.txt"
        global_cmvn = args.model_dir / "global_cmvn"
    else:
        config = args.config
        checkpoint = args.checkpoint
        units = None
        global_cmvn = None

    checks: dict[str, Any] = {
        "mode": args.mode,
        "config": {"path": str(config), "exists": bool(config and config.is_file())},
        "checkpoint": {"path": str(checkpoint) if checkpoint else None, "exists": bool(checkpoint and checkpoint.is_file())},
        "dependencies": dep_status(MODE_DEPS[args.mode]),
    }
    if units is not None:
        checks["units"] = {"path": str(units), "exists": units.is_file(), "required_for_runtime_bundle": True}
    if global_cmvn is not None:
        checks["global_cmvn"] = {"path": str(global_cmvn), "exists": global_cmvn.exists(), "required": False}

    required_ok = checks["config"]["exists"] and checks["checkpoint"]["exists"]
    deps_ok = all(checks["dependencies"].values())
    # units.txt is not loaded by every export script, but it is important for a complete deployment bundle.
    bundle_warning = units is not None and not units.is_file()
    checks["ok"] = bool(required_ok and deps_ok)
    checks["warnings"] = []
    if bundle_warning:
        checks["warnings"].append("units.txt is missing; export may run, but the runtime/model bundle is incomplete.")
    if args.mode == "onnx-gpu" and deps_ok:
        checks["warnings"].append("onnxruntime importability does not prove CUDAExecutionProvider availability; verify provider list separately.")
    if args.mode in {"ipex", "bpu"}:
        checks["warnings"].append("Python dependency preflight does not prove the vendor SDK/toolchain is installed.")

    print(json.dumps(checks, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if checks["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
