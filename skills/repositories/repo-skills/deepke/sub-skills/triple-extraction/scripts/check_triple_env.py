#!/usr/bin/env python3
"""Safely diagnose a DeepKE triple-extraction runtime.

This script imports packages/modules and checks optional paths. It never trains,
downloads, launches DeepSpeed, builds Apex, or mutates DeepKE configs.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

COMMON_IMPORTS: Sequence[Tuple[str, str | None]] = (
    ("deepke", "deepke"),
    ("torch", "torch"),
    ("transformers", "transformers"),
    ("hydra", "hydra-core"),
)

TASKS: Dict[str, Dict[str, Any]] = {
    "prgc": {
        "modules": ["deepke.triple_extraction.PRGC"],
        "optional_imports": [("sklearn", "scikit-learn"), ("pandas", "pandas"), ("jieba", "jieba"), ("wandb", "wandb")],
        "data": ["rel2id.json", "train_triples.json", "val_triples.json", "test_triples.json"],
        "note": "PRGC usually needs CMeIE/NYT/WebNLG-style triples plus a local BERT/RoBERTa model directory.",
    },
    "pure": {
        "modules": ["deepke.triple_extraction.PURE"],
        "optional_imports": [("allennlp", "allennlp"), ("overrides", "overrides"), ("requests", "requests")],
        "data": ["train.json", "dev.json", "test.json"],
        "note": "PURE is sensitive to AllenNLP, Transformers, Hugging Face Hub, and PyTorch version compatibility.",
    },
    "asp": {
        "modules": ["deepke.triple_extraction.ASP"],
        "optional_imports": [("apex", "apex"), ("sentencepiece", "sentencepiece"), ("pyhocon", "pyhocon"), ("truecase", "truecase")],
        "data": ["train.json", "dev.json", "test.json"],
        "note": "ASP is CUDA/Apex-oriented; CPU-only checks do not prove ASP runtime readiness.",
    },
    "mt5": {
        "modules": [],
        "optional_imports": [("deepspeed", "deepspeed"), ("datasets", "datasets"), ("sentencepiece", "sentencepiece"), ("accelerate", "accelerate")],
        "data": ["train.json", "valid.json"],
        "note": "MT5/CCKS training and prediction are DeepSpeed/generative workflows; the bundled converter can be checked on CPU.",
    },
    "cnschema": {
        "modules": ["deepke.triple_extraction.PRGC"],
        "optional_imports": [("jieba", "jieba"), ("pandas", "pandas")],
        "data": ["schema.json", "rel2id.json"],
        "note": "cnSchema workflows require the intended Chinese schema inventory and compatible checkpoints.",
    },
}


def import_record(module: str, dist: str | None = None) -> Dict[str, Any]:
    rec: Dict[str, Any] = {"module": module, "distribution": dist, "ok": False, "version": None, "error": None}
    try:
        importlib.import_module(module)
        rec["ok"] = True
    except Exception as exc:  # noqa: BLE001 - diagnostic should preserve import errors
        rec["error"] = f"{type(exc).__name__}: {exc}"
    if dist:
        try:
            rec["version"] = metadata.version(dist)
        except metadata.PackageNotFoundError:
            if rec["ok"]:
                rec["version"] = "imported; distribution metadata not found"
        except Exception as exc:  # noqa: BLE001
            rec["version_error"] = f"{type(exc).__name__}: {exc}"
    return rec


def cuda_info() -> Dict[str, Any]:
    try:
        import torch  # type: ignore

        devices = []
        if torch.cuda.is_available():
            for index in range(torch.cuda.device_count()):
                try:
                    devices.append(torch.cuda.get_device_name(index))
                except Exception as exc:  # noqa: BLE001
                    devices.append(f"<error: {exc}>")
        return {
            "torch_imported": True,
            "torch_version": getattr(torch, "__version__", None),
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "devices": devices,
        }
    except Exception as exc:  # noqa: BLE001
        return {"torch_imported": False, "available": False, "device_count": 0, "devices": [], "error": f"{type(exc).__name__}: {exc}"}


def path_record(path: str, kind: str) -> Dict[str, Any]:
    p = Path(path).expanduser()
    rec: Dict[str, Any] = {"kind": kind, "path": str(p), "exists": p.exists(), "is_file": p.is_file(), "is_dir": p.is_dir()}
    if p.is_dir():
        try:
            rec["children_preview"] = sorted(child.name for child in p.iterdir())[:20]
        except OSError as exc:
            rec["list_error"] = str(exc)
    return rec


def data_checks(data_dir: str, expected: Sequence[str]) -> List[Dict[str, Any]]:
    base = Path(data_dir).expanduser()
    checks = []
    for name in expected:
        path = base / name
        checks.append({"name": name, "path": str(path), "exists": path.exists(), "required": True})
    return checks


def selected_tasks(task: str) -> List[str]:
    return sorted(TASKS) if task == "all" else [task]


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    tasks = selected_tasks(args.task)
    imports = [import_record(module, dist) for module, dist in COMMON_IMPORTS]
    task_imports = []
    optional_imports = []
    for task in tasks:
        info = TASKS[task]
        task_imports.extend(import_record(module, "deepke") for module in info.get("modules", []))
        optional_imports.extend(import_record(module, dist) for module, dist in info.get("optional_imports", []))

    report: Dict[str, Any] = {
        "script": "check_triple_env.py",
        "python": {"version": sys.version.split()[0], "executable": sys.executable, "platform": platform.platform()},
        "environment": {
            "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE"),
            "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE"),
        },
        "selected_tasks": tasks,
        "imports": imports,
        "task_imports": task_imports,
        "optional_imports": optional_imports,
        "cuda": cuda_info(),
        "paths": {},
        "task_notes": {task: TASKS[task]["note"] for task in tasks},
        "notes": [],
    }

    if args.data_dir:
        report["paths"]["data_dir"] = path_record(args.data_dir, "data_dir")
        report["paths"]["data_expectations"] = {task: data_checks(args.data_dir, TASKS[task]["data"]) for task in tasks}
    else:
        report["notes"].append("No --data-dir supplied; triple dataset filenames were not checked.")
    if args.pretrained_model:
        report["paths"]["pretrained_model"] = path_record(args.pretrained_model, "pretrained_model")
    else:
        report["notes"].append("No --pretrained-model supplied; PLM/tokenizer assets were not checked.")
    if args.checkpoint:
        report["paths"]["checkpoint"] = path_record(args.checkpoint, "checkpoint")
    else:
        report["notes"].append("No --checkpoint supplied; trained model/checkpoint artifacts were not checked.")
    if args.require_cuda and not report["cuda"].get("available"):
        report["notes"].append("--require-cuda was set but torch.cuda.is_available() is false.")
    return report


def has_failures(report: Dict[str, Any], args: argparse.Namespace) -> bool:
    failures: List[bool] = []
    failures.extend(not item.get("ok") for item in report.get("imports", []) if item.get("module") in {"deepke", "torch", "transformers"})
    failures.extend(not item.get("ok") for item in report.get("task_imports", []))
    if args.require_cuda and not report.get("cuda", {}).get("available"):
        failures.append(True)
    paths = report.get("paths", {})
    if args.data_dir:
        for checks in paths.get("data_expectations", {}).values():
            failures.extend(item.get("required") and not item.get("exists") for item in checks)
    if args.pretrained_model and not paths.get("pretrained_model", {}).get("exists"):
        failures.append(True)
    if args.checkpoint and not paths.get("checkpoint", {}).get("exists"):
        failures.append(True)
    return any(failures)


def print_text(report: Dict[str, Any]) -> None:
    print("DeepKE triple-extraction diagnostic")
    print(f"Python: {report['python']['version']} ({report['python']['platform']})")
    print(f"Executable: {report['python']['executable']}")
    print("\nCore imports:")
    for item in report["imports"]:
        status = "OK" if item["ok"] else "MISSING"
        version = f" version={item['version']}" if item.get("version") else ""
        error = f" error={item['error']}" if item.get("error") else ""
        print(f"  [{status}] {item['module']}{version}{error}")
    print("\nDeepKE task imports:")
    if not report["task_imports"]:
        print("  (no task-specific package import for selected task)")
    for item in report["task_imports"]:
        status = "OK" if item["ok"] else "MISSING"
        error = f" error={item['error']}" if item.get("error") else ""
        print(f"  [{status}] {item['module']}{error}")
    print("\nOptional imports:")
    for item in report["optional_imports"]:
        status = "OK" if item["ok"] else "missing/optional"
        version = f" version={item['version']}" if item.get("version") else ""
        print(f"  [{status}] {item['module']}{version}")
    cuda = report["cuda"]
    print("\nCUDA:")
    print(f"  torch_imported={cuda.get('torch_imported')} available={cuda.get('available')} device_count={cuda.get('device_count')} torch_version={cuda.get('torch_version')}")
    for index, device in enumerate(cuda.get("devices") or []):
        print(f"  device[{index}]={device}")
    if report.get("paths"):
        print("\nPath checks:")
        print(json.dumps(report["paths"], ensure_ascii=False, indent=2))
    print("\nTask notes:")
    for task, note in report.get("task_notes", {}).items():
        print(f"  {task}: {note}")
    if report.get("notes"):
        print("\nGeneral notes:")
        for note in report["notes"]:
            print(f"  - {note}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely check a DeepKE triple-extraction environment without training, downloading, or building CUDA extensions.")
    parser.add_argument("--task", choices=["all", *sorted(TASKS)], default="all", help="triple workflow expectations to check")
    parser.add_argument("--data-dir", help="optional dataset directory to check for selected task filenames")
    parser.add_argument("--pretrained-model", help="optional local pretrained model/tokenizer directory to check")
    parser.add_argument("--checkpoint", help="optional model/checkpoint path to check")
    parser.add_argument("--require-cuda", action="store_true", help="treat absent CUDA as a strict failure")
    parser.add_argument("--strict", action="store_true", help="exit nonzero on missing required imports, files, or CUDA")
    parser.add_argument("--json", action="store_true", help="print JSON instead of human-readable text")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(args)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 1 if args.strict and has_failures(report, args) else 0


if __name__ == "__main__":
    raise SystemExit(main())
