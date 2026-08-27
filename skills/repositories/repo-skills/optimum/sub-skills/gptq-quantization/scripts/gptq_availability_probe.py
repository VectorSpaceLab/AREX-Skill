#!/usr/bin/env python3
"""Safe Optimum GPTQ availability/config probe.

This script performs import and configuration checks only. It does not download
models or datasets, run quantization, train, or write checkpoint files.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import json
import platform
import sys
from typing import Any, Dict, Optional, Tuple

MIN_GPTQMODEL_VERSION = "7.0.0"


def package_version(distribution: str) -> Optional[str]:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None
    except Exception:
        return None


def module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False


def try_import(module_name: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "module": module_name,
        "found": module_available(module_name),
        "importable": False,
        "version": package_version(module_name.split(".")[0]),
        "error": None,
    }
    try:
        module = importlib.import_module(module_name)
        result["importable"] = True
        result["module_version_attr"] = getattr(module, "__version__", None)
    except Exception as exc:  # keep probe non-throwing by default
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def version_at_least(version_text: Optional[str], minimum: str) -> Tuple[Optional[bool], Optional[str]]:
    if not version_text:
        return None, "version unknown"
    try:
        from packaging.version import Version

        return Version(version_text) >= Version(minimum), None
    except Exception as exc:
        # Fallback for simple dotted numeric versions if packaging is unavailable.
        try:
            def parts(text: str):
                return tuple(int(piece) for piece in text.split("+")[0].split(".")[:3])

            return parts(version_text) >= parts(minimum), None
        except Exception:
            return None, f"could not compare versions: {type(exc).__name__}: {exc}"


def probe_gptqmodel() -> Dict[str, Any]:
    version = package_version("gptqmodel")
    found = module_available("gptqmodel")
    compatible, compare_error = version_at_least(version, MIN_GPTQMODEL_VERSION)
    result: Dict[str, Any] = {
        "module": "gptqmodel",
        "found": found,
        "version": version,
        "minimum": MIN_GPTQMODEL_VERSION,
        "compatible": compatible is True,
        "compatibility_unknown": compatible is None,
        "error": compare_error,
        "importable": False,
        "import_error": None,
    }
    if found:
        try:
            importlib.import_module("gptqmodel")
            result["importable"] = True
        except Exception as exc:
            result["import_error"] = f"{type(exc).__name__}: {exc}"
    return result


def probe_torch() -> Dict[str, Any]:
    result = try_import("torch")
    cuda: Dict[str, Any] = {"available": False, "device_count": 0, "devices": []}
    if result["importable"]:
        try:
            import torch

            result["version"] = getattr(torch, "__version__", result.get("version"))
            cuda["available"] = bool(torch.cuda.is_available())
            cuda["device_count"] = int(torch.cuda.device_count()) if cuda["available"] else 0
            if cuda["available"]:
                cuda["devices"] = [torch.cuda.get_device_name(i) for i in range(cuda["device_count"])]
        except Exception as exc:
            cuda["error"] = f"{type(exc).__name__}: {exc}"
    result["cuda"] = cuda
    return result


def quantizer_config_probe(optimum_gptq: Dict[str, Any], gptqmodel: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "attempted": False,
        "ok": False,
        "reason": None,
        "serialized_keys": [],
        "serialized_config": None,
    }
    if not optimum_gptq.get("importable"):
        result["reason"] = "optimum.gptq is not importable"
        return result
    if not gptqmodel.get("compatible"):
        result["reason"] = "gptqmodel>=7.0.0 is not available; skipping constructor to avoid unsafe failure"
        return result

    result["attempted"] = True
    try:
        from optimum.gptq import GPTQQuantizer

        quantizer = GPTQQuantizer(
            bits=4,
            dataset=["probe calibration text"],
            group_size=128,
            damp_percent=0.1,
            desc_act=False,
            act_group_aware=True,
            sym=True,
            true_sequential=True,
            model_seqlen=16,
            block_name_to_quantize="model.layers",
            modules_in_block_to_quantize=[["self_attn.q_proj"]],
            format="gptq",
            meta={"probe": "optimum-gptq-availability"},
            backend="auto",
        )
        serialized = quantizer.to_dict()
        result["ok"] = True
        result["serialized_keys"] = sorted(serialized.keys())
        result["serialized_config"] = serialized
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
    return result


def build_report() -> Dict[str, Any]:
    optimum = try_import("optimum")
    optimum_gptq = try_import("optimum.gptq")
    gptqmodel = probe_gptqmodel()
    accelerate = try_import("accelerate")
    transformers = try_import("transformers")
    torch = probe_torch()
    config_probe = quantizer_config_probe(optimum_gptq, gptqmodel)

    blocking = []
    warnings = []

    if not optimum_gptq.get("importable"):
        blocking.append("optimum.gptq is not importable")
    if not gptqmodel.get("compatible"):
        blocking.append("gptqmodel>=7.0.0 is not available")
    if not accelerate.get("importable"):
        blocking.append("accelerate is not importable")
    if not transformers.get("importable"):
        blocking.append("transformers is not importable")
    if not torch.get("importable"):
        blocking.append("torch is not importable")
    elif not torch.get("cuda", {}).get("available"):
        blocking.append("torch CUDA is not available for full GPTQ workflows")

    if optimum_gptq.get("importable") and not config_probe.get("ok"):
        warnings.append(f"GPTQQuantizer config probe not run/passed: {config_probe.get('reason')}")
    if torch.get("cuda", {}).get("available") and not gptqmodel.get("compatible"):
        warnings.append("CUDA is visible, but GPT-QModel is missing or incompatible")

    full_ready = len(blocking) == 0

    return {
        "probe": "optimum-gptq-availability",
        "safe_by_default": {
            "downloads": False,
            "quantization_run": False,
            "training": False,
            "checkpoint_writes": False,
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "packages": {
            "optimum": optimum,
            "optimum.gptq": optimum_gptq,
            "gptqmodel": gptqmodel,
            "accelerate": accelerate,
            "transformers": transformers,
            "torch": torch,
        },
        "quantizer_config_probe": config_probe,
        "full_gptq_ready": full_ready,
        "blocking": blocking,
        "warnings": warnings,
        "next_steps": next_steps(full_ready, blocking),
    }


def next_steps(full_ready: bool, blocking: list[str]) -> list[str]:
    if full_ready:
        return [
            "Confirm user approval for model/tokenizer/dataset access and GPU time before quantization.",
            "Load text CausalLM models with torch_dtype=torch.float16.",
            "Keep load_quantized_model backend='auto' unless an explicit GPT-QModel backend is required.",
        ]
    steps = ["Resolve blocking items before claiming full GPTQ readiness."]
    if any("gptqmodel" in item for item in blocking):
        steps.append("Install or upgrade to gptqmodel>=7.0.0 if optional GPTQ dependencies are approved.")
    if any("accelerate" in item for item in blocking):
        steps.append("Install accelerate before using load_quantized_model.")
    if any("CUDA" in item for item in blocking):
        steps.append("Use a CUDA/GPT-QModel-supported accelerator for full quantization or report CPU-only partial coverage.")
    return steps


def print_human(report: Dict[str, Any]) -> None:
    print("Optimum GPTQ availability probe")
    print("Safe actions: no downloads, no quantization, no training, no checkpoint writes")
    print(f"Full GPTQ ready: {report['full_gptq_ready']}")
    print("")
    for name, info in report["packages"].items():
        version = info.get("version") or info.get("module_version_attr") or "unknown"
        if name == "gptqmodel":
            status = "compatible" if info.get("compatible") else "missing/incompatible"
            print(f"- {name}: found={info.get('found')} importable={info.get('importable')} version={version} status={status}")
        elif name == "torch":
            cuda = info.get("cuda", {})
            print(
                f"- {name}: importable={info.get('importable')} version={version} "
                f"cuda_available={cuda.get('available')} cuda_devices={cuda.get('device_count')}"
            )
        else:
            print(f"- {name}: importable={info.get('importable')} version={version}")
        if info.get("error"):
            print(f"  error: {info['error']}")
        if info.get("import_error"):
            print(f"  import_error: {info['import_error']}")

    config_probe = report["quantizer_config_probe"]
    print("")
    print(
        "Quantizer config probe: "
        f"attempted={config_probe.get('attempted')} ok={config_probe.get('ok')}"
    )
    if config_probe.get("reason"):
        print(f"  reason: {config_probe['reason']}")
    if config_probe.get("serialized_keys"):
        print(f"  serialized_keys: {', '.join(config_probe['serialized_keys'])}")

    if report["blocking"]:
        print("")
        print("Blocking for full GPTQ:")
        for item in report["blocking"]:
            print(f"- {item}")
    if report["warnings"]:
        print("")
        print("Warnings:")
        for item in report["warnings"]:
            print(f"- {item}")
    print("")
    print("Next steps:")
    for item in report["next_steps"]:
        print(f"- {item}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely probe Optimum GPTQ/GPT-QModel availability without downloads or quantization."
    )
    parser.add_argument("--json", action="store_true", help="Print the full probe report as JSON.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when full GPTQ requirements are not ready.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    if args.strict and not report["full_gptq_ready"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
