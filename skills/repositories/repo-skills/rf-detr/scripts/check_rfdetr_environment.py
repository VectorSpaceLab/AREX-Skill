#!/usr/bin/env python3
# ------------------------------------------------------------------------
# RF-DETR
# Copyright (c) 2025 Roboflow. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 [see LICENSE for details]
# ------------------------------------------------------------------------
"""Read-only RF-DETR package, optional dependency, CLI, and backend smoke check."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.util
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExtraProbe:
    """Optional dependency group to probe."""

    name: str
    modules: tuple[str, ...]
    install_hint: str


BASE_MODULES = ("rfdetr", "torch", "torchvision", "transformers", "supervision", "pydantic")
EXTRAS: dict[str, ExtraProbe] = {
    "train": ExtraProbe("train", ("pytorch_lightning", "torchmetrics", "pycocotools", "peft"), 'pip install "rfdetr[train]"'),
    "cli": ExtraProbe("cli", ("jsonargparse", "rfdetr.cli"), 'pip install "rfdetr[train,cli]"'),
    "augment": ExtraProbe("augment", ("albumentations", "kornia"), 'pip install "rfdetr[augment]"'),
    "onnx": ExtraProbe("onnx", ("onnx", "onnxsim", "onnxruntime", "onnx_graphsurgeon"), 'pip install "rfdetr[onnx]"'),
    "tensorrt": ExtraProbe("tensorrt", ("tensorrt", "polygraphy"), 'pip install "rfdetr[tensorrt]"'),
    "tflite": ExtraProbe("tflite", ("onnx2tf", "tensorflow"), 'pip install "rfdetr[tflite]"'),
    "executorch": ExtraProbe("executorch", ("executorch",), 'pip install "rfdetr[executorch]"'),
    "coreml": ExtraProbe("coreml", ("coremltools",), 'pip install "rfdetr[coreml]"'),
    "plus": ExtraProbe("plus", ("rfdetr_plus",), 'pip install "rfdetr[plus]"'),
    "loggers": ExtraProbe("loggers", ("tensorboard", "wandb", "mlflow", "clearml"), 'pip install "rfdetr[loggers]"'),
}

DIST_NAMES = {
    "rfdetr": "rfdetr",
    "torchvision": "torchvision",
    "pytorch_lightning": "pytorch-lightning",
    "pycocotools": "pycocotools",
    "onnx_graphsurgeon": "onnx-graphsurgeon",
    "rfdetr_plus": "rfdetr-plus",
    "coremltools": "coremltools",
}


def module_status(module_name: str) -> dict[str, str | bool]:
    """Return importability and package version for a module."""
    present = importlib.util.find_spec(module_name) is not None
    result: dict[str, str | bool] = {"present": present}
    if not present:
        return result
    dist = DIST_NAMES.get(module_name, module_name.replace("_", "-"))
    try:
        result["version"] = metadata.version(dist)
    except metadata.PackageNotFoundError:
        result["version"] = "present-version-unknown"
    return result


def check_base() -> dict[str, Any]:
    """Probe baseline RF-DETR imports and public class names."""
    modules = {name: module_status(name) for name in BASE_MODULES}
    public: dict[str, Any] = {}
    if modules["rfdetr"]["present"]:
        rfdetr = importlib.import_module("rfdetr")
        public["exports"] = list(getattr(rfdetr, "__all__", []))
        for class_name in ("RFDETRSmall", "RFDETRSegSmall", "RFDETRKeypointPreview"):
            cls = getattr(rfdetr, class_name, None)
            public[class_name] = getattr(cls, "size", None)
    return {"modules": modules, "public": public}


def check_extras(names: list[str]) -> dict[str, Any]:
    """Probe requested extras by import-only module checks."""
    report: dict[str, Any] = {}
    for name in names:
        probe = EXTRAS[name]
        report[name] = {
            "install_hint": probe.install_hint,
            "modules": {module: module_status(module) for module in probe.modules},
        }
    return report


def check_cli(timeout: int) -> dict[str, Any]:
    """Run a safe RF-DETR CLI help check."""
    command = [sys.executable, "-m", "rfdetr", "--help"]
    try:
        completed = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
    except Exception as exc:  # noqa: BLE001
        return {"command": command, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    text = (completed.stdout + completed.stderr).lower()
    return {
        "command": command,
        "ok": completed.returncode == 0 and "fit" in text and "validate" in text,
        "returncode": completed.returncode,
        "signal": "fit/validate/test/predict help" if "fit" in text else "missing expected subcommand text",
    }


def check_cuda() -> dict[str, Any]:
    """Probe torch CUDA with a tiny allocation when available."""
    try:
        import torch
    except ImportError as exc:
        return {"ok": False, "error": f"ImportError: {exc}"}
    result: dict[str, Any] = {
        "torch_version": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count(),
    }
    if torch.cuda.is_available():
        result["device0"] = torch.cuda.get_device_name(0)
        result["capability0"] = torch.cuda.get_device_capability(0)
        try:
            tensor = torch.empty((1,), device="cuda")
            result["tiny_allocation"] = str(tensor.device)
            result["ok"] = True
        except Exception as exc:  # noqa: BLE001
            result["ok"] = False
            result["error"] = f"{type(exc).__name__}: {exc}"
    else:
        result["ok"] = False
    return result


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extras", nargs="*", choices=sorted(EXTRAS), default=[], help="Optional RF-DETR extras to probe by import.")
    parser.add_argument("--check-cli", action="store_true", help="Run python -m rfdetr --help with a timeout.")
    parser.add_argument("--check-cuda", action="store_true", help="Run a tiny torch CUDA allocation check when CUDA is available.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout seconds for CLI help checks.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run environment checks and return a process status."""
    args = build_parser().parse_args(argv)
    report: dict[str, Any] = {"python": sys.version.split()[0], "base": check_base()}
    if args.extras:
        report["extras"] = check_extras(args.extras)
    if args.check_cli:
        report["cli"] = check_cli(args.timeout)
    if args.check_cuda:
        report["cuda"] = check_cuda()

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print("Base modules:")
        for name, status in report["base"]["modules"].items():
            version = status.get("version", "missing")
            print(f"  {name}: {version if status['present'] else 'missing'}")
        public = report["base"].get("public", {})
        for name in ("RFDETRSmall", "RFDETRSegSmall", "RFDETRKeypointPreview"):
            if name in public:
                print(f"  {name}.size: {public[name]}")
        for extra, data in report.get("extras", {}).items():
            print(f"Extra {extra}: {data['install_hint']}")
            for module, status in data["modules"].items():
                print(f"  {module}: {status.get('version', 'missing') if status['present'] else 'missing'}")
        if "cli" in report:
            print(f"CLI help ok: {report['cli'].get('ok')} ({report['cli'].get('signal') or report['cli'].get('error')})")
        if "cuda" in report:
            print(f"CUDA ok: {report['cuda'].get('ok')} available={report['cuda'].get('available')} count={report['cuda'].get('device_count')}")

    base_ok = all(status["present"] for status in report["base"]["modules"].values())
    cli_ok = report.get("cli", {"ok": True}).get("ok", True)
    cuda_required_failed = args.check_cuda and not report.get("cuda", {}).get("ok", False)
    return 0 if base_ok and cli_ok and not cuda_required_failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
