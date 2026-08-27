#!/usr/bin/env python3
"""Check a Baichuan2 workflow environment without loading model weights."""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from typing import Any, Dict, Iterable, List

WORKFLOW_MODULES = {
    "inference": ["torch", "transformers", "accelerate", "sentencepiece", "colorama", "flask", "streamlit"],
    "deployment": ["torch", "transformers", "sentencepiece", "bitsandbytes"],
    "fine-tuning": ["torch", "transformers", "accelerate", "sentencepiece", "deepspeed", "peft"],
}
DIST_NAMES = {
    "torch": "torch",
    "transformers": "transformers",
    "accelerate": "accelerate",
    "sentencepiece": "sentencepiece",
    "colorama": "colorama",
    "flask": "flask",
    "streamlit": "streamlit",
    "bitsandbytes": "bitsandbytes",
    "deepspeed": "deepspeed",
    "peft": "peft",
}


def workflow_modules(workflow: str) -> List[str]:
    if workflow == "all":
        ordered: List[str] = []
        for modules in WORKFLOW_MODULES.values():
            for module in modules:
                if module not in ordered:
                    ordered.append(module)
        return ordered
    return list(WORKFLOW_MODULES[workflow])


def package_version(module_name: str) -> str:
    dist_name = DIST_NAMES.get(module_name, module_name)
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return "not-installed"


def check_import(module_name: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "module": module_name,
        "distribution": DIST_NAMES.get(module_name, module_name),
        "version": package_version(module_name),
        "import_ok": False,
        "error": None,
    }
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - environment dependent
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result
    result["import_ok"] = True
    if module_name == "torch":
        result["torch_cuda"] = getattr(module.version, "cuda", None)
        result["cuda_available"] = bool(module.cuda.is_available())
        result["cuda_device_count"] = int(module.cuda.device_count()) if module.cuda.is_available() else 0
        if module.cuda.is_available():
            result["cuda_device_name_0"] = module.cuda.get_device_name(0)
            result["cuda_device_capability_0"] = list(module.cuda.get_device_capability(0))
    return result


def bitsandbytes_smoke() -> Dict[str, Any]:
    result: Dict[str, Any] = {"status": "not-run"}
    try:
        import torch
        import bitsandbytes as bnb
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    if not torch.cuda.is_available():
        return {"status": "failed", "error": "CUDA is not available"}
    try:
        layer = bnb.nn.Linear8bitLt(4, 4).cuda()
        x = torch.randn(2, 4, device="cuda")
        y = layer(x)
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    result.update({"status": "passed", "output_shape": list(y.shape), "output_device": str(y.device)})
    return result


def print_text(report: Dict[str, Any]) -> None:
    print(f"workflow: {report['workflow']}")
    print(f"modules: {', '.join(report['modules'])}")
    for item in report["imports"]:
        status = "ok" if item["import_ok"] else "FAILED"
        print(f"{item['module']}: {status} version={item['version']}")
        if item.get("error"):
            print(f"  error: {item['error']}")
        if item["module"] == "torch" and item["import_ok"]:
            print(f"  torch_cuda={item.get('torch_cuda')} cuda_available={item.get('cuda_available')} cuda_device_count={item.get('cuda_device_count')}")
            if item.get("cuda_device_name_0"):
                print(f"  cuda_device_name_0={item['cuda_device_name_0']} cap={item.get('cuda_device_capability_0')}")
    if report.get("bitsandbytes_smoke"):
        print(f"bitsandbytes_smoke: {report['bitsandbytes_smoke']}")
    if report["errors"]:
        print("errors:")
        for error in report["errors"]:
            print(f"- {error}")


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    modules = workflow_modules(args.workflow)
    report: Dict[str, Any] = {
        "workflow": args.workflow,
        "modules": modules,
        "imports": [],
        "bitsandbytes_smoke": None,
        "errors": [],
    }
    if args.dry_run:
        report["dry_run"] = True
        return report

    for module in modules:
        item = check_import(module)
        report["imports"].append(item)
        if not item["import_ok"]:
            report["errors"].append(f"import failed for {module}: {item['error']}")

    torch_items = [item for item in report["imports"] if item["module"] == "torch"]
    torch_item = torch_items[0] if torch_items else None
    if args.require_cuda:
        if not torch_item or not torch_item.get("import_ok"):
            report["errors"].append("--require-cuda was set but torch did not import")
        elif not torch_item.get("cuda_available"):
            report["errors"].append("--require-cuda was set but torch.cuda.is_available() is false")

    if args.check_bitsandbytes_op:
        report["bitsandbytes_smoke"] = bitsandbytes_smoke()
        if report["bitsandbytes_smoke"].get("status") != "passed":
            report["errors"].append(f"bitsandbytes smoke failed: {report['bitsandbytes_smoke'].get('error')}")
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", choices=("inference", "deployment", "fine-tuning", "all"), default="inference")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if torch CUDA is unavailable.")
    parser.add_argument("--check-bitsandbytes-op", action="store_true", help="Run a tiny BitsAndBytes CUDA linear layer smoke check.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned module checks without importing anything.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print_text(report)
    return 1 if report.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
