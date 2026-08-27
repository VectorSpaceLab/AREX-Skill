#!/usr/bin/env python3
"""Inspect an installed Scenic package without launching training or loading data.

Examples:
  python inspect_scenic_package.py
  python inspect_scenic_package.py --json
  python inspect_scenic_package.py --modules scenic.app scenic.train_lib.lr_schedules
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import platform
import sys
from typing import Any


def import_status(module: str) -> dict[str, Any]:
    try:
        mod = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostic UI should catch all imports.
        return {"module": module, "ok": False, "error_type": type(exc).__name__, "error": str(exc)}
    return {"module": module, "ok": True, "file": getattr(mod, "__file__", None)}


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def jax_status() -> dict[str, Any]:
    try:
        import jax  # type: ignore
        import jax.numpy as jnp  # type: ignore
        value = float(jnp.sum(jnp.asarray([1.0, 2.0])))
        return {
            "ok": True,
            "version": getattr(jax, "__version__", None),
            "devices": [str(d) for d in jax.devices()],
            "tiny_sum": value,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def dataset_registry_status() -> dict[str, Any]:
    try:
        from scenic.dataset_lib import datasets  # type: ignore
        return {
            "ok": True,
            "lazy_dataset_names": sorted(getattr(datasets, "_IMPORT_TABLE", {}).keys()),
            "registered_now": sorted(datasets.DatasetRegistry.list()),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def model_registry_status(model_name: str | None = None) -> dict[str, Any]:
    try:
        from scenic.model_lib import models  # type: ignore
        result: dict[str, Any] = {"ok": True, "model_names": sorted(models.ALL_MODELS.keys())}
        if model_name:
            cls = models.get_model_cls(model_name)
            result["resolved_model"] = {"name": model_name, "module": cls.__module__, "class": cls.__name__}
        return result
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def trainer_status() -> dict[str, Any]:
    try:
        from scenic.train_lib import trainers  # type: ignore
        return {"ok": True, "trainer_names": sorted(trainers.ALL_TRAINERS.keys())}
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "hint": "Trainer import touches optional transfer/BigTransfer/TensorFlow Addons paths in some Scenic versions. If core imports pass, treat this as an optional training-stack dependency issue and inspect the troubleshooting references.",
        }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    modules = args.modules or [
        "scenic",
        "scenic.app",
        "scenic.dataset_lib.datasets",
        "scenic.model_lib.base_models.base_model",
        "scenic.train_lib.lr_schedules",
        "scenic.train_lib.train_utils",
    ]
    report = {
        "python": {"version": sys.version.split()[0], "platform": platform.platform()},
        "packages": {name: package_version(name) for name in ["scenic", "jax", "jaxlib", "flax", "tensorflow", "tensorflow-datasets", "ml-collections", "clu", "optax"]},
        "imports": [import_status(m) for m in modules],
        "jax": jax_status(),
        "dataset_registry": dataset_registry_status(),
        "model_registry": model_registry_status(args.model_name),
    }
    if args.check_trainers:
        report["trainer_registry"] = trainer_status()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect an installed Scenic package without launching training or loading datasets.")
    parser.add_argument("--modules", nargs="*", help="Specific modules to import instead of the default safe set.")
    parser.add_argument("--model-name", help="Optionally resolve one registered model class without instantiating it.")
    parser.add_argument("--check-trainers", action="store_true", help="Also import scenic.train_lib.trainers; may expose optional dependency issues.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args()
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Scenic package inspection")
        print("packages:")
        for name, version in report["packages"].items():
            print(f"  {name}: {version or 'not installed'}")
        print("imports:")
        for item in report["imports"]:
            status = "ok" if item["ok"] else f"FAIL {item['error_type']}: {item['error']}"
            print(f"  {item['module']}: {status}")
        print("jax:", "ok" if report["jax"].get("ok") else report["jax"].get("error"), report["jax"].get("devices", ""))
        if report["dataset_registry"].get("ok"):
            print("lazy datasets:", ", ".join(report["dataset_registry"]["lazy_dataset_names"]))
        if report["model_registry"].get("ok"):
            print("models:", ", ".join(report["model_registry"]["model_names"]))
        if "trainer_registry" in report:
            tr = report["trainer_registry"]
            print("trainers:", tr.get("trainer_names") if tr.get("ok") else f"FAIL {tr.get('error_type')}: {tr.get('error')}")
            if not tr.get("ok"):
                print("hint:", tr.get("hint"))
    failed_default_import = any(not item["ok"] for item in report["imports"])
    return 1 if failed_default_import or not report["jax"].get("ok") else 0


if __name__ == "__main__":
    raise SystemExit(main())
