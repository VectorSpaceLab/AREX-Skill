#!/usr/bin/env python3
"""Read-only LeRobot policy/dependency/device probe.

This script imports registries and policy classes only. It never constructs a model,
loads a checkpoint, contacts the Hub, downloads assets, or starts a CLI workflow.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import sys
from typing import Any

POLICY_EXTRAS = {
    "act": None, "diffusion": "diffusion", "eo1": "eo1", "evo1": "evo1",
    "groot": "groot", "molmoact2": "molmoact2", "fastwam": "fastwam",
    "gaussian_actor": None, "lingbot_va": "lingbot_va", "multi_task_dit": "multi_task_dit",
    "pi0": "pi", "pi0_fast": "pi", "pi05": "pi", "smolvla": "smolvla",
    "tdmpc": None, "vla_jepa": "vla_jepa", "vqbet": None, "wall_x": "wallx", "xvla": "xvla",
}
POLICY_PACKAGES = {
    "diffusion": [("diffusers", "diffusers")],
    "eo1": [("transformers", "transformers"), ("qwen-vl-utils", "qwen_vl_utils")],
    "evo1": [("transformers", "transformers")],
    "groot": [("transformers", "transformers"), ("peft", "peft"), ("diffusers", "diffusers"), ("datasets", "datasets"), ("dm-tree", "dm_tree"), ("timm", "timm")],
    "molmoact2": [("transformers", "transformers"), ("peft", "peft"), ("scipy", "scipy")],
    "fastwam": [("transformers", "transformers"), ("diffusers", "diffusers")],
    "lingbot_va": [("transformers", "transformers"), ("diffusers", "diffusers")],
    "multi_task_dit": [("transformers", "transformers"), ("diffusers", "diffusers")],
    "pi0": [("transformers", "transformers"), ("scipy", "scipy")],
    "pi0_fast": [("transformers", "transformers"), ("scipy", "scipy")],
    "pi05": [("transformers", "transformers")],
    "smolvla": [("transformers", "transformers"), ("accelerate", "accelerate"), ("num2words", "num2words")],
    "vla_jepa": [("transformers", "transformers"), ("diffusers", "diffusers"), ("qwen-vl-utils", "qwen_vl_utils")],
    "wall_x": [("transformers", "transformers"), ("peft", "peft"), ("torchdiffeq", "torchdiffeq"), ("qwen-vl-utils", "qwen_vl_utils")],
    "xvla": [("transformers", "transformers")],
}


def package_status(distribution: str, import_name: str) -> dict[str, Any]:
    spec = importlib.util.find_spec(import_name)
    try:
        version = importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        version = None
    return {"distribution": distribution, "import": import_name, "available": spec is not None, "version": version}


def device_status(requested: str) -> dict[str, Any]:
    result: dict[str, Any] = {"requested": requested, "available": requested == "cpu"}
    try:
        import torch
        result.update({
            "torch": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()),
            "mps_available": bool(torch.backends.mps.is_available()),
            "xpu_available": bool(torch.xpu.is_available()),
        })
        if requested.startswith("cuda"):
            result["available"] = bool(torch.cuda.is_available())
            if ":" in requested and result["available"]:
                result["available"] = int(requested.split(":", 1)[1]) < result["cuda_device_count"]
        elif requested == "mps":
            result["available"] = bool(torch.backends.mps.is_available())
        elif requested == "xpu":
            result["available"] = bool(torch.xpu.is_available())
        elif requested != "cpu":
            result["available"] = False
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["available"] = False
    return result


def probe(policy_name: str, requested_device: str) -> dict[str, Any]:
    report: dict[str, Any] = {"policy": policy_name, "requested_device": requested_device}
    try:
        from lerobot.configs import PreTrainedConfig
        from lerobot.policies import get_policy_class
        choices = sorted(PreTrainedConfig.get_known_choices())
        report["registry_available"] = policy_name in choices
        report["registered_choices"] = choices
        if report["registry_available"]:
            try:
                cls = get_policy_class(policy_name)
                report["policy_class"] = f"{cls.__module__}.{cls.__name__}"
                report["class_importable"] = True
            except Exception as exc:
                report["class_importable"] = False
                report["class_import_error"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        report["registry_available"] = False
        report["class_importable"] = False
        report["lerobot_import_error"] = f"{type(exc).__name__}: {exc}"
    report["device"] = device_status(requested_device)
    packages = [("lerobot", "lerobot")]
    extra = POLICY_EXTRAS.get(policy_name)
    if extra:
        report["scoped_extra"] = extra
    packages.extend(POLICY_PACKAGES.get(policy_name, []))
    report["packages"] = [package_status(*item) for item in packages]
    report["execution_ready"] = bool(
        report.get("registry_available") and report.get("class_importable")
        and report["device"].get("available") and all(item["available"] for item in report["packages"])
    )
    report["note"] = (
        "Import/dependency/device probe only; checkpoint features, processor files, tokenizer assets, "
        "memory, and a real batch remain unverified."
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", required=True, choices=sorted(POLICY_EXTRAS), help="registered policy choice")
    parser.add_argument("--device", default="cpu", help="requested device: cpu, cuda[:N], mps, or xpu")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    report = probe(args.policy, args.device)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"policy={args.policy} registry={report.get('registry_available', False)} class_importable={report.get('class_importable', False)}")
        print(f"device={args.device} available={report['device'].get('available', False)} cuda_available={report['device'].get('cuda_available', 'unknown')}")
        if report.get("scoped_extra"):
            print(f"scoped_extra=lerobot[{report['scoped_extra']}]")
        for item in report["packages"]:
            print(f"package={item['distribution']} available={item['available']} version={item['version'] or 'unknown'}")
        for key in ("class_import_error", "lerobot_import_error"):
            if report.get(key):
                print(f"{key}={report[key]}")
        print(f"execution_ready={report['execution_ready']}")
        print(report["note"])
    return 0 if report["execution_ready"] else 2


if __name__ == "__main__":
    sys.exit(main())
