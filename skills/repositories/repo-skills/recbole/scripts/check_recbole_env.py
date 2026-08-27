#!/usr/bin/env python3
"""Safe RecBole environment diagnostic helper.

Examples:
  python scripts/check_recbole_env.py
  python scripts/check_recbole_env.py --models BPR SASRec --details --check-optional

The script imports the installed RecBole package, checks PyTorch CPU/CUDA
visibility, optionally probes Hyperopt/Ray, and resolves selected model names.
It performs no training, downloads, network calls, or writes.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from typing import Any


def import_or_error(name: str):
    try:
        return importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise RuntimeError(f"Could not import {name!r}: {exc}") from exc


def model_info(name: str, details: bool = False) -> dict[str, Any]:
    from recbole.utils import get_model, get_trainer

    record: dict[str, Any] = {"name": name}
    try:
        cls = get_model(name)
        record.update(
            {
                "status": "ok",
                "class": cls.__name__,
                "module": cls.__module__,
                "model_type": getattr(getattr(cls, "type", None), "name", str(getattr(cls, "type", None))),
                "input_type": getattr(getattr(cls, "input_type", None), "name", str(getattr(cls, "input_type", None))),
            }
        )
        try:
            trainer = get_trainer(getattr(cls, "type", None), cls.__name__)
            record["trainer"] = f"{trainer.__name__} ({trainer.__module__})"
        except Exception as exc:  # pragma: no cover - diagnostic path
            record["trainer_error"] = str(exc)
        if details:
            record["signature"] = str(inspect.signature(cls.__init__))
            record["mro"] = [base.__name__ for base in cls.mro()[:5]]
    except Exception as exc:
        record.update({"status": "error", "error": str(exc)})
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check installed RecBole import, backend, and model registry state.")
    parser.add_argument("--models", nargs="*", default=["BPR"], help="Model names to resolve, e.g. BPR SASRec FM KGAT")
    parser.add_argument("--details", action="store_true", help="Print constructor signatures and short MRO for models")
    parser.add_argument("--check-optional", action="store_true", help="Probe optional Hyperopt and Ray imports")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    out: dict[str, Any] = {"ok": True, "errors": []}

    try:
        recbole = import_or_error("recbole")
        out["recbole"] = {
            "version": getattr(recbole, "__version__", "<unknown>"),
            "module": getattr(recbole, "__name__", "recbole"),
        }
    except RuntimeError as exc:
        out["ok"] = False
        out["errors"].append(str(exc))

    try:
        torch = import_or_error("torch")
        cuda_available = bool(torch.cuda.is_available())
        cuda_devices: list[str] = []
        if cuda_available:
            for idx in range(torch.cuda.device_count()):
                cuda_devices.append(torch.cuda.get_device_name(idx))
        out["torch"] = {
            "version": getattr(torch, "__version__", "<unknown>"),
            "cuda_runtime": getattr(getattr(torch, "version", None), "cuda", None),
            "cuda_available": cuda_available,
            "cuda_devices": cuda_devices,
        }
    except RuntimeError as exc:
        out["ok"] = False
        out["errors"].append(str(exc))

    if out["ok"]:
        try:
            from recbole.config import Config

            original_argv = sys.argv[:]
            try:
                # RecBole's Config inspects sys.argv for command-line overrides.
                # Hide this helper's own flags so diagnostics do not emit
                # "command line args ... will not be used" warnings.
                sys.argv = [sys.argv[0]]
                cfg = Config(model="BPR", dataset="ml-100k", config_dict={"use_gpu": False, "epochs": 1, "show_progress": False})
            finally:
                sys.argv = original_argv
            out["config_smoke"] = {
                "model": cfg["model"],
                "dataset": cfg["dataset"],
                "use_gpu": cfg["use_gpu"],
                "device": str(cfg["device"]),
            }
        except Exception as exc:
            out["ok"] = False
            out["errors"].append(f"Config smoke failed: {exc}")

        out["models"] = [model_info(name, args.details) for name in args.models]
        if any(item.get("status") != "ok" for item in out["models"]):
            out["ok"] = False

    if args.check_optional:
        optional: dict[str, Any] = {}
        for mod_name in ["hyperopt", "ray"]:
            try:
                mod = import_or_error(mod_name)
                optional[mod_name] = {"status": "ok", "version": getattr(mod, "__version__", "<unknown>")}
            except RuntimeError as exc:
                optional[mod_name] = {"status": "missing-or-error", "error": str(exc)}
        out["optional"] = optional

    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(f"RecBole: {out.get('recbole', {}).get('version', '<failed>')}")
        torch_info = out.get("torch", {})
        print(
            "Torch: {version} | CUDA runtime: {cuda_runtime} | CUDA available: {cuda_available}".format(
                **{
                    "version": torch_info.get("version", "<failed>"),
                    "cuda_runtime": torch_info.get("cuda_runtime"),
                    "cuda_available": torch_info.get("cuda_available"),
                }
            )
        )
        if "config_smoke" in out:
            print(f"Config smoke: {out['config_smoke']}")
        for item in out.get("models", []):
            if item.get("status") == "ok":
                print(f"Model {item['name']}: {item['class']} | type={item['model_type']} | input={item['input_type']} | trainer={item.get('trainer')}")
                if args.details:
                    print(f"  signature={item.get('signature')}")
                    print(f"  mro={' -> '.join(item.get('mro', []))}")
            else:
                print(f"Model {item['name']}: ERROR {item.get('error')}")
        if "optional" in out:
            for name, item in out["optional"].items():
                print(f"Optional {name}: {item['status']} {item.get('version', item.get('error', ''))}")
        if out["errors"]:
            print("Errors:", file=sys.stderr)
            for error in out["errors"]:
                print(f"- {error}", file=sys.stderr)

    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
