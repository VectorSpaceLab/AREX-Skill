#!/usr/bin/env python3
"""Safely diagnose a DeepKE-LLM workflow environment.

The script checks imports, CUDA visibility, environment-variable presence, and
optional file paths. It never loads model weights, calls an API, downloads data,
or starts fine-tuning.
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
    ("torch", "torch"),
    ("transformers", "transformers"),
    ("datasets", "datasets"),
)

WORKFLOWS: Dict[str, Dict[str, Any]] = {
    "oneke": {
        "optional_imports": [("accelerate", "accelerate"), ("peft", "peft"), ("sentencepiece", "sentencepiece")],
        "env": [],
        "note": "OneKE requires local model/tokenizer assets and GPU memory for real inference; imports alone do not prove readiness.",
    },
    "instructkgc": {
        "optional_imports": [("peft", "peft"), ("accelerate", "accelerate"), ("deepspeed", "deepspeed"), ("opendelta", "opendelta"), ("sentencepiece", "sentencepiece")],
        "env": [],
        "note": "InstructKGC fine-tuning depends on the selected model family, adapter method, and GPU resources.",
    },
    "llmicl": {
        "optional_imports": [("openai", "openai"), ("httpx", "httpx"), ("tiktoken", "tiktoken")],
        "env": ["OPENAI_API_KEY", "API_KEY", "BASE_URL", "MODEL"],
        "note": "LLMICL/API workflows require credentials, endpoint/model compatibility, and a cost budget for real calls.",
    },
    "unleashllmre": {
        "optional_imports": [("openai", "openai"), ("httpx", "httpx"), ("sklearn", "scikit-learn")],
        "env": ["OPENAI_API_KEY", "API_KEY", "BASE_URL", "MODEL"],
        "note": "UnleashLLMRE uses LLM prompting/augmentation around few-shot relation extraction.",
    },
    "codekgc": {
        "optional_imports": [("openai", "openai"), ("httpx", "httpx")],
        "env": ["OPENAI_API_KEY", "API_KEY", "BASE_URL", "MODEL"],
        "note": "CodeKGC needs schema prompt, in-context examples, a code-capable model, and safe parsing of generated code-like text.",
    },
    "cpm-bee": {
        "optional_imports": [("opendelta", "opendelta"), ("accelerate", "accelerate"), ("sentencepiece", "sentencepiece"), ("deepspeed", "deepspeed")],
        "env": [],
        "note": "CPM-Bee workflows should use a separate environment and verified model assets.",
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
        return {"torch_imported": False, "torch_version": None, "available": False, "device_count": 0, "devices": [], "error": f"{type(exc).__name__}: {exc}"}


def env_record(name: str) -> Dict[str, Any]:
    value = os.environ.get(name)
    return {"name": name, "present": bool(value), "length": len(value) if value else 0}


def path_record(path: str, kind: str) -> Dict[str, Any]:
    p = Path(path).expanduser()
    rec: Dict[str, Any] = {"kind": kind, "path": str(p), "exists": p.exists(), "is_file": p.is_file(), "is_dir": p.is_dir()}
    if p.is_dir():
        try:
            rec["children_preview"] = sorted(child.name for child in p.iterdir())[:20]
        except OSError as exc:
            rec["list_error"] = str(exc)
    return rec


def selected_workflows(workflow: str) -> List[str]:
    return sorted(WORKFLOWS) if workflow == "all" else [workflow]


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    workflows = selected_workflows(args.workflow)
    imports = [import_record(module, dist) for module, dist in COMMON_IMPORTS]
    optional_imports = []
    env_vars: List[str] = []
    notes: Dict[str, str] = {}
    for workflow in workflows:
        info = WORKFLOWS[workflow]
        optional_imports.extend(import_record(module, dist) for module, dist in info.get("optional_imports", []))
        env_vars.extend(info.get("env", []))
        notes[workflow] = info["note"]

    report: Dict[str, Any] = {
        "script": "check_llm_workflow_env.py",
        "python": {"version": sys.version.split()[0], "executable": sys.executable, "platform": platform.platform()},
        "selected_workflows": workflows,
        "imports": imports,
        "optional_imports": optional_imports,
        "cuda": cuda_info(),
        "environment_variables": [env_record(name) for name in sorted(set(env_vars))],
        "paths": {},
        "workflow_notes": notes,
        "notes": [],
    }
    if args.model_path:
        report["paths"]["model_path"] = path_record(args.model_path, "model_path")
    else:
        report["notes"].append("No --model-path supplied; local model/tokenizer/checkpoint assets were not checked.")
    if args.data_path:
        report["paths"]["data_path"] = path_record(args.data_path, "data_path")
    else:
        report["notes"].append("No --data-path supplied; instruction dataset files were not checked.")
    if args.config_path:
        report["paths"]["config_path"] = path_record(args.config_path, "config_path")
    else:
        report["notes"].append("No --config-path supplied; model/API/fine-tuning config files were not checked.")
    if args.require_cuda and not report["cuda"].get("available"):
        report["notes"].append("--require-cuda was set but torch.cuda.is_available() is false.")
    if args.require_api and not any(item["present"] for item in report["environment_variables"] if item["name"] in {"OPENAI_API_KEY", "API_KEY"}):
        report["notes"].append("--require-api was set but no OPENAI_API_KEY or API_KEY is present.")
    return report


def has_failures(report: Dict[str, Any], args: argparse.Namespace) -> bool:
    failures: List[bool] = []
    failures.extend(not item.get("ok") for item in report.get("imports", []) if item.get("module") in {"torch", "transformers"})
    if args.require_cuda and not report.get("cuda", {}).get("available"):
        failures.append(True)
    if args.require_api and not any(item["present"] for item in report.get("environment_variables", []) if item["name"] in {"OPENAI_API_KEY", "API_KEY"}):
        failures.append(True)
    paths = report.get("paths", {})
    for flag_name, key in ((args.model_path, "model_path"), (args.data_path, "data_path"), (args.config_path, "config_path")):
        if flag_name and not paths.get(key, {}).get("exists"):
            failures.append(True)
    return any(failures)


def print_text(report: Dict[str, Any]) -> None:
    print("DeepKE-LLM workflow diagnostic")
    print(f"Python: {report['python']['version']} ({report['python']['platform']})")
    print(f"Executable: {report['python']['executable']}")
    print("\nCore imports:")
    for item in report["imports"]:
        status = "OK" if item["ok"] else "MISSING"
        version = f" version={item['version']}" if item.get("version") else ""
        error = f" error={item['error']}" if item.get("error") else ""
        print(f"  [{status}] {item['module']}{version}{error}")
    print("\nOptional workflow imports:")
    for item in report["optional_imports"]:
        status = "OK" if item["ok"] else "missing/optional"
        version = f" version={item['version']}" if item.get("version") else ""
        print(f"  [{status}] {item['module']}{version}")
    cuda = report["cuda"]
    print("\nCUDA:")
    print(f"  torch_imported={cuda.get('torch_imported')} available={cuda.get('available')} device_count={cuda.get('device_count')} torch_version={cuda.get('torch_version')}")
    for index, device in enumerate(cuda.get("devices") or []):
        print(f"  device[{index}]={device}")
    if report.get("environment_variables"):
        print("\nEnvironment variables (values hidden):")
        for item in report["environment_variables"]:
            print(f"  {item['name']}: present={item['present']} length={item['length']}")
    if report.get("paths"):
        print("\nPath checks:")
        print(json.dumps(report["paths"], ensure_ascii=False, indent=2))
    print("\nWorkflow notes:")
    for name, note in report.get("workflow_notes", {}).items():
        print(f"  {name}: {note}")
    if report.get("notes"):
        print("\nGeneral notes:")
        for note in report["notes"]:
            print(f"  - {note}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely check a DeepKE-LLM workflow environment without model loads, API calls, downloads, or training.")
    parser.add_argument("--workflow", choices=["all", *sorted(WORKFLOWS)], default="all", help="workflow expectations to check")
    parser.add_argument("--model-path", help="optional local model/tokenizer/checkpoint path to check")
    parser.add_argument("--data-path", help="optional instruction dataset path to check")
    parser.add_argument("--config-path", help="optional workflow config path to check")
    parser.add_argument("--require-cuda", action="store_true", help="treat absent CUDA as a strict failure")
    parser.add_argument("--require-api", action="store_true", help="treat absent API key variables as a strict failure")
    parser.add_argument("--strict", action="store_true", help="exit nonzero on strict import, backend, API, or path failures")
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
