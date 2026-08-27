#!/usr/bin/env python3
"""Safe PEFT adapter-core environment check.

This script imports PEFT and common optional dependencies, verifies enum/config
construction, and optionally reports CUDA facts. It does not download models or
load checkpoints.
"""

import argparse
import importlib
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ImportResult:
    name: str
    ok: bool
    version: str | None = None
    error: str | None = None


def import_package(name: str) -> tuple[ImportResult, Any | None]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return ImportResult(name=name, ok=False, error=f"{type(exc).__name__}: {exc}"), None
    version = getattr(module, "__version__", None)
    return ImportResult(name=name, ok=True, version=str(version) if version is not None else None), module


def collect_cuda_facts(torch_module: Any | None) -> dict[str, Any]:
    if torch_module is None:
        return {"checked": False, "reason": "torch is not importable"}
    cuda = getattr(torch_module, "cuda", None)
    if cuda is None:
        return {"checked": True, "available": False, "reason": "torch.cuda is not present"}
    try:
        available = bool(cuda.is_available())
    except Exception as exc:
        return {"checked": True, "available": False, "error": f"{type(exc).__name__}: {exc}"}
    facts: dict[str, Any] = {"checked": True, "available": available}
    if available:
        try:
            facts["device_count"] = int(cuda.device_count())
            facts["current_device"] = int(cuda.current_device())
            facts["device_name"] = str(cuda.get_device_name(cuda.current_device()))
        except Exception as exc:
            facts["device_error"] = f"{type(exc).__name__}: {exc}"
    return facts


def check_peft_core(peft_module: Any | None) -> dict[str, Any]:
    if peft_module is None:
        return {"ok": False, "error": "peft is not importable"}
    try:
        from peft import LoraConfig, PeftConfig, PeftType, TaskType
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    checks: dict[str, Any] = {
        "has_peft_config": isinstance(PeftConfig.__name__, str),
        "task_types": [item.value for item in TaskType],
        "peft_type_count": len(list(PeftType)),
        "has_lora": "LORA" in PeftType.__members__,
    }
    try:
        config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=8,
            lora_alpha=8,
            lora_dropout=0.0,
            target_modules=["q_proj", "v_proj"],
        )
        checks.update(
            {
                "lora_config_constructed": True,
                "lora_peft_type": str(config.peft_type.value),
                "target_modules": sorted(config.target_modules),
            }
        )
    except Exception as exc:
        checks.update({"lora_config_constructed": False, "error": f"{type(exc).__name__}: {exc}"})
    checks["ok"] = bool(checks.get("has_lora") and checks.get("lora_config_constructed"))
    return checks


def build_report(include_cuda: bool) -> dict[str, Any]:
    imports: list[ImportResult] = []
    modules: dict[str, Any | None] = {}
    for package_name in ("peft", "torch", "transformers", "accelerate"):
        result, module = import_package(package_name)
        imports.append(result)
        modules[package_name] = module

    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "imports": [asdict(result) for result in imports],
        "peft_core": check_peft_core(modules["peft"]),
    }
    if include_cuda:
        report["cuda"] = collect_cuda_facts(modules["torch"])
    return report


def print_text_report(report: dict[str, Any]) -> None:
    print(f"Python: {report['python']}")
    print("Imports:")
    for result in report["imports"]:
        if result["ok"]:
            version = result["version"] or "unknown version"
            print(f"  OK   {result['name']} ({version})")
        else:
            print(f"  FAIL {result['name']}: {result['error']}")
    core = report["peft_core"]
    print("PEFT core:")
    if core.get("ok"):
        print(f"  OK   TaskType values: {', '.join(core['task_types'])}")
        print(f"  OK   PeftType count: {core['peft_type_count']} (LORA present: {core['has_lora']})")
        print(f"  OK   LoraConfig target_modules: {', '.join(core['target_modules'])}")
    else:
        print(f"  FAIL {core.get('error', 'core checks failed')}")
    if "cuda" in report:
        cuda = report["cuda"]
        if not cuda.get("checked"):
            print(f"CUDA: not checked ({cuda.get('reason')})")
        elif cuda.get("available"):
            details = f"{cuda.get('device_count')} device(s)"
            if cuda.get("device_name"):
                details += f", current: {cuda['device_name']}"
            print(f"CUDA: available ({details})")
        else:
            reason = cuda.get("reason") or cuda.get("error") or "torch reports CUDA unavailable"
            print(f"CUDA: unavailable ({reason})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe PEFT adapter-core import and config smoke check.")
    parser.add_argument("--json", action="store_true", help="Print the report as JSON instead of human-readable text.")
    parser.add_argument(
        "--include-cuda",
        action="store_true",
        help="Also query torch CUDA availability and device facts. This does not allocate model weights.",
    )
    args = parser.parse_args()

    report = build_report(include_cuda=args.include_cuda)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    peft_import_ok = next(item for item in report["imports"] if item["name"] == "peft")["ok"]
    return 0 if peft_import_ok and report["peft_core"].get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
