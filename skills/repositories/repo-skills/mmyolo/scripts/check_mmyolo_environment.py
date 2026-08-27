#!/usr/bin/env python3
"""Check whether an environment can inspect/use MMYOLO safely.

This helper performs import/version checks, optional backend probes, and an
optional MMEngine config parse. It does not download checkpoints, run inference,
train, evaluate, export, or write artifacts beyond normal Python stdout.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_IMPORTS = ["torch", "mmcv", "mmengine", "mmdet", "mmyolo", "prettytable"]
OPTIONAL_IMPORTS = ["albumentations", "sahi", "onnx", "onnxruntime", "mmdeploy", "tensorrt", "grad_cam"]


def import_status(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic should catch import-time version assertions
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "name": name,
        "ok": True,
        "version": getattr(module, "__version__", None),
        "module": getattr(module, "__name__", name),
    }


def torch_backend_status() -> dict[str, Any]:
    status: dict[str, Any] = {"import_ok": False}
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        status["error"] = f"{type(exc).__name__}: {exc}"
        return status
    status.update(
        {
            "import_ok": True,
            "version": getattr(torch, "__version__", None),
            "cuda_version": getattr(getattr(torch, "version", None), "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
    )
    if torch.cuda.is_available():
        try:
            status["cuda_device_name_0"] = torch.cuda.get_device_name(0)
            status["cuda_capability_0"] = list(torch.cuda.get_device_capability(0))
        except Exception as exc:  # noqa: BLE001
            status["cuda_probe_error"] = f"{type(exc).__name__}: {exc}"
    return status


def config_status(config_path: str | None) -> dict[str, Any] | None:
    if not config_path:
        return None
    p = Path(config_path)
    if not p.is_file():
        return {"path": config_path, "ok": False, "error": "config file does not exist"}
    try:
        from mmengine.config import Config

        cfg = Config.fromfile(str(p))
    except Exception as exc:  # noqa: BLE001
        return {"path": config_path, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    model = cfg.get("model", {})
    train_cfg = cfg.get("train_cfg", {})
    return {
        "path": config_path,
        "ok": True,
        "model_type": model.get("type") if isinstance(model, dict) else None,
        "backbone_type": model.get("backbone", {}).get("type") if isinstance(model, dict) else None,
        "neck_type": model.get("neck", {}).get("type") if isinstance(model, dict) else None,
        "head_type": model.get("bbox_head", {}).get("type") if isinstance(model, dict) else None,
        "max_epochs": train_cfg.get("max_epochs") if isinstance(train_cfg, dict) else None,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check MMYOLO import/version/backend readiness without running workloads.")
    parser.add_argument("--config", help="optional MMEngine config file to parse")
    parser.add_argument("--include-optional", action="store_true", help="probe optional deployment/visualization imports")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "required_imports": [import_status(name) for name in REQUIRED_IMPORTS],
        "torch_backend": torch_backend_status(),
    }
    if args.include_optional:
        report["optional_imports"] = [import_status(name) for name in OPTIONAL_IMPORTS]
    cfg = config_status(args.config)
    if cfg is not None:
        report["config"] = cfg

    ok = all(item["ok"] for item in report["required_imports"])
    if cfg is not None:
        ok = ok and bool(cfg.get("ok"))
    report["ok"] = ok

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        for item in report["required_imports"]:
            if item["ok"]:
                version = item.get("version") or "unknown-version"
                print(f"OK   {item['name']} {version}")
            else:
                print(f"FAIL {item['name']} {item['error']}")
        tb = report["torch_backend"]
        if tb.get("import_ok"):
            print(f"Torch CUDA available: {tb.get('cuda_available')} count={tb.get('cuda_device_count')}")
        if cfg is not None:
            if cfg.get("ok"):
                print(
                    "Config OK: "
                    f"model={cfg.get('model_type')} backbone={cfg.get('backbone_type')} "
                    f"neck={cfg.get('neck_type')} head={cfg.get('head_type')} max_epochs={cfg.get('max_epochs')}"
                )
            else:
                print(f"Config FAIL: {cfg.get('error')}")
        if args.include_optional:
            for item in report.get("optional_imports", []):
                label = "OK  " if item["ok"] else "MISS"
                print(f"{label} optional {item['name']}: {item.get('version') or item.get('error')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
