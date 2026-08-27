#!/usr/bin/env python3
"""Check whether the current Python environment can use MMOCR safely.

This read-only helper imports MMOCR and core OpenMMLab dependencies, reports
versions and backend availability, and optionally loads a caller-provided
MMEngine config. It does not download models, build runners, open windows,
write outputs, or require an MMOCR source checkout.
"""
from __future__ import annotations

import argparse
import json
import sys
from importlib import import_module
from typing import Any, Dict, Optional


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check MMOCR imports, dependency versions, backend availability, and optional config loading."
    )
    parser.add_argument("--config", help="Optional MMEngine/MMOCR config path to load read-only.")
    parser.add_argument("--require-default-scope", default="mmocr", help="Expected config default_scope; default: mmocr.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser


def import_version(name: str) -> Dict[str, Any]:
    try:
        mod = import_module(name)
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "version": getattr(mod, "__version__", None)}


def check_torch() -> Dict[str, Any]:
    result = import_version("torch")
    if not result.get("ok"):
        return result
    import torch  # type: ignore

    result.update(
        {
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
    )
    if torch.cuda.is_available():
        try:
            result["cuda_device_name_0"] = torch.cuda.get_device_name(0)
            result["cuda_device_capability_0"] = list(torch.cuda.get_device_capability(0))
        except Exception as exc:
            result["cuda_probe_error"] = f"{type(exc).__name__}: {exc}"
    return result


def load_config(path: Optional[str], expected_scope: str) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    try:
        from mmengine import Config  # type: ignore
    except Exception as exc:
        return {"ok": False, "error": f"failed to import mmengine.Config: {type(exc).__name__}: {exc}"}
    try:
        cfg = Config.fromfile(path)
    except Exception as exc:
        return {"ok": False, "error": f"failed to load config: {type(exc).__name__}: {exc}"}
    model = cfg.get("model", {}) if hasattr(cfg, "get") else {}
    default_scope = cfg.get("default_scope", None)
    return {
        "ok": default_scope == expected_scope,
        "path": path,
        "default_scope": default_scope,
        "expected_default_scope": expected_scope,
        "model_type": model.get("type") if hasattr(model, "get") else None,
        "has_train_dataloader": "train_dataloader" in cfg,
        "has_val_evaluator": "val_evaluator" in cfg,
        "has_test_evaluator": "test_evaluator" in cfg,
    }


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    deps = {name: import_version(name) for name in ["mmcv", "mmengine", "mmdet", "mmocr", "cv2"]}
    deps["torch"] = check_torch()
    api_ok = False
    api_error = None
    try:
        from mmocr.apis import MMOCRInferencer, TextDetInferencer, TextRecInferencer, KIEInferencer  # noqa: F401
        api_ok = True
    except Exception as exc:
        api_error = f"{type(exc).__name__}: {exc}"
    report = {
        "python": sys.version.split()[0],
        "dependencies": deps,
        "mmocr_api_imports": {"ok": api_ok, "error": api_error},
        "config": load_config(args.config, args.require_default_scope),
    }
    report["ok"] = all(v.get("ok") for v in deps.values()) and api_ok and (report["config"] is None or report["config"].get("ok"))
    return report


def print_text(report: Dict[str, Any]) -> None:
    print(f"python: {report['python']}")
    for name, info in report["dependencies"].items():
        if info.get("ok"):
            extra = ""
            if name == "torch":
                extra = f" cuda={info.get('cuda_version')} cuda_available={info.get('cuda_available')} devices={info.get('cuda_device_count')}"
            print(f"{name}: OK version={info.get('version')}{extra}")
        else:
            print(f"{name}: FAIL {info.get('error')}")
    print(f"mmocr_api_imports: {'OK' if report['mmocr_api_imports']['ok'] else 'FAIL'}")
    if report.get("config") is not None:
        cfg = report["config"]
        if cfg.get("ok"):
            print(f"config: OK default_scope={cfg.get('default_scope')} model_type={cfg.get('model_type')}")
        else:
            print(f"config: FAIL {cfg.get('error') or cfg}")
    print(f"overall: {'OK' if report['ok'] else 'FAIL'}")


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(args)
    if args.json:
        print(json.dumps(report, sort_keys=True, indent=2))
    else:
        print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
