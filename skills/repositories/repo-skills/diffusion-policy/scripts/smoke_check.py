#!/usr/bin/env python3
"""Safe Diffusion Policy environment and routing smoke checks.

This helper never starts training, downloads data, launches Ray, opens cameras,
or commands a robot. It checks importability, package metadata, optional CUDA
visibility, and (when supplied) the existence of a Diffusion Policy-style config
root.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_MODULES = [
    "diffusion_policy.workspace.base_workspace",
    "diffusion_policy.dataset.base_dataset",
    "diffusion_policy.policy.base_lowdim_policy",
    "diffusion_policy.policy.base_image_policy",
    "diffusion_policy.model.common.normalizer",
]


def check_distribution(name: str) -> Dict[str, Any]:
    try:
        version = metadata.version(name)
        return {"name": name, "present": True, "version": version}
    except metadata.PackageNotFoundError:
        return {"name": name, "present": False, "error": "distribution metadata not found"}


def check_import(module: str) -> Dict[str, Any]:
    try:
        mod = importlib.import_module(module)
        return {"module": module, "ok": True, "file": getattr(mod, "__file__", None)}
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def check_torch(cuda: bool) -> Dict[str, Any]:
    try:
        import torch  # type: ignore
    except Exception as exc:  # pragma: no cover
        return {"present": False, "error": f"{type(exc).__name__}: {exc}"}

    result: Dict[str, Any] = {
        "present": True,
        "version": getattr(torch, "__version__", None),
        "cuda_build": getattr(getattr(torch, "version", None), "cuda", None),
    }
    if cuda:
        try:
            result["cuda_available"] = bool(torch.cuda.is_available())
            result["cuda_device_count"] = int(torch.cuda.device_count()) if torch.cuda.is_available() else 0
            if torch.cuda.is_available():
                result["cuda_device_name_0"] = torch.cuda.get_device_name(0)
                result["cuda_capability_0"] = list(torch.cuda.get_device_capability(0))
                torch.empty((1,), device="cuda")
                result["cuda_tiny_allocation"] = True
        except Exception as exc:  # pragma: no cover
            result["cuda_error"] = f"{type(exc).__name__}: {exc}"
    return result


def check_config_root(config_root: Path) -> Dict[str, Any]:
    root = config_root.expanduser()
    result: Dict[str, Any] = {"path": str(root), "exists": root.exists(), "task_dir_exists": (root / "task").exists()}
    if root.exists():
        result["workspace_config_count"] = len(list(root.glob("train_*.yaml")))
        result["task_config_count"] = len(list((root / "task").glob("*.yaml"))) if (root / "task").exists() else 0
    return result


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run safe Diffusion Policy import/config smoke checks.")
    parser.add_argument("--distribution", default="diffusion_policy", help="Installed distribution name to check")
    parser.add_argument("--module", action="append", default=[], help="Additional module to import; repeatable")
    parser.add_argument("--config-root", default=None, help="Optional config root to inspect, e.g. a diffusion_policy/config directory")
    parser.add_argument("--cuda", action="store_true", help="Also probe torch CUDA visibility and tiny allocation")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args(argv)

    modules = DEFAULT_MODULES + args.module
    report: Dict[str, Any] = {
        "distribution": check_distribution(args.distribution),
        "imports": [check_import(m) for m in modules],
        "torch": check_torch(args.cuda),
    }
    if args.config_root:
        report["config_root"] = check_config_root(Path(args.config_root))

    failed = []
    if not report["distribution"].get("present"):
        failed.append("distribution")
    failed.extend(item["module"] for item in report["imports"] if not item.get("ok"))
    report["ok"] = not failed
    report["failed_checks"] = failed

    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"distribution {args.distribution}: {'ok' if report['distribution'].get('present') else 'missing'}")
        if report["distribution"].get("version"):
            print(f"  version: {report['distribution']['version']}")
        for item in report["imports"]:
            print(f"import {item['module']}: {'ok' if item.get('ok') else item.get('error')}")
        torch_info = report["torch"]
        print(f"torch: {torch_info.get('version') if torch_info.get('present') else torch_info.get('error')}")
        if args.cuda:
            print(f"torch cuda available: {torch_info.get('cuda_available')} count={torch_info.get('cuda_device_count')}")
            if torch_info.get("cuda_error"):
                print(f"torch cuda error: {torch_info['cuda_error']}")
        if "config_root" in report:
            cfg = report["config_root"]
            print(f"config root: exists={cfg['exists']} task_dir={cfg['task_dir_exists']} workspaces={cfg.get('workspace_config_count', 0)} tasks={cfg.get('task_config_count', 0)}")
        if failed:
            print("failed checks: " + ", ".join(failed), file=sys.stderr)

    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
