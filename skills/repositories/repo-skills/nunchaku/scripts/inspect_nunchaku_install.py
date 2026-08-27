#!/usr/bin/env python3
"""Inspect an installed Nunchaku runtime without downloading model assets.

The script reports Python, torch/CUDA, nunchaku package metadata, selected public
API availability, and architecture-to-precision hints as JSON. It never loads
model weights, never contacts the network intentionally, and does not depend on a
source checkout.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import platform
import sys
from importlib import metadata as importlib_metadata
from typing import Any


API_TARGETS = {
    "root_exports": [
        ("nunchaku", "NunchakuFluxTransformer2dModel"),
        ("nunchaku", "NunchakuFluxTransformer2DModelV2"),
        ("nunchaku", "NunchakuQwenImageTransformer2DModel"),
        ("nunchaku", "NunchakuSanaTransformer2DModel"),
        ("nunchaku", "NunchakuZImageTransformer2DModel"),
        ("nunchaku", "NunchakuT5EncoderModel"),
    ],
    "methods": [
        ("nunchaku", "NunchakuFluxTransformer2dModel.from_pretrained"),
        ("nunchaku", "NunchakuFluxTransformer2dModel.set_attention_impl"),
        ("nunchaku", "NunchakuFluxTransformer2dModel.update_lora_params"),
        ("nunchaku", "NunchakuFluxTransformer2dModel.set_lora_strength"),
        ("nunchaku", "NunchakuQwenImageTransformer2DModel.from_pretrained"),
        ("nunchaku", "NunchakuQwenImageTransformer2DModel.set_offload"),
        ("nunchaku", "NunchakuT5EncoderModel.from_pretrained"),
    ],
    "helpers": [
        ("nunchaku.caching.diffusers_adapters", "apply_cache_on_pipe"),
        ("nunchaku.models.ip_adapter.diffusers_adapters", "apply_IPA_on_pipe"),
        ("nunchaku.lora.flux.compose", "compose_lora"),
        ("nunchaku.lora.flux.nunchaku_converter", "to_nunchaku"),
        ("nunchaku.merge_safetensors", "merge_safetensors"),
        ("nunchaku.utils", "get_precision"),
        ("nunchaku.utils", "is_turing"),
    ],
}

SUPPORTED_INT4_SMS = {"75", "80", "86", "89"}
SUPPORTED_FP4_SMS = {"120", "121"}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect installed Nunchaku/Torch/CUDA status as JSON.")
    parser.add_argument("--device", default="cuda:0", help="Device for CUDA allocation and precision checks.")
    parser.add_argument("--skip-allocation", action="store_true", help="Do not allocate a scalar CUDA tensor.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    parser.add_argument("--fail-on-warning", action="store_true", help="Exit non-zero when status is warning or error.")
    return parser.parse_args(argv)


def exc_info(exc: BaseException) -> dict[str, str]:
    return {"type": exc.__class__.__name__, "message": str(exc)}


def import_report(module_name: str) -> tuple[Any | None, dict[str, Any]]:
    try:
        module = importlib.import_module(module_name)
    except BaseException as exc:  # noqa: BLE001 - diagnostic command should capture import failures.
        return None, {"ok": False, "error": exc_info(exc)}
    return module, {"ok": True}


def getattr_dotted(root: Any, dotted: str) -> Any:
    value = root
    for part in dotted.split("."):
        value = getattr(value, part)
    return value


def signature(obj: Any) -> str | None:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return None


def distribution_version(name: str) -> str | None:
    try:
        return importlib_metadata.version(name)
    except importlib_metadata.PackageNotFoundError:
        return None


def precision_for_sm(sm: str) -> str:
    if sm in SUPPORTED_FP4_SMS:
        return "fp4"
    if sm in SUPPORTED_INT4_SMS:
        return "int4"
    return "unsupported"


def torch_section(args: argparse.Namespace) -> tuple[dict[str, Any], Any | None]:
    torch, report = import_report("torch")
    if torch is None:
        return report, None

    report.update(
        {
            "version": getattr(torch, "__version__", None),
            "cuda_runtime_version": getattr(getattr(torch, "version", None), "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": 0,
            "devices": [],
        }
    )
    if not torch.cuda.is_available():
        return report, torch

    try:
        report["device_count"] = int(torch.cuda.device_count())
        devices = []
        for index in range(report["device_count"]):
            props = torch.cuda.get_device_properties(index)
            capability = torch.cuda.get_device_capability(index)
            sm = f"{capability[0]}{capability[1]}"
            devices.append(
                {
                    "index": index,
                    "name": props.name,
                    "capability": list(capability),
                    "sm": sm,
                    "total_memory_gib": round(props.total_memory / 1024**3, 3),
                    "recommended_nunchaku_precision": precision_for_sm(sm),
                }
            )
        report["devices"] = devices
    except BaseException as exc:  # noqa: BLE001
        report["device_query_error"] = exc_info(exc)

    if not args.skip_allocation:
        report["allocation_smoke"] = allocation_smoke(torch, args.device)
    return report, torch


def allocation_smoke(torch: Any, device_text: str) -> dict[str, Any]:
    smoke: dict[str, Any] = {"ok": False, "device": device_text}
    try:
        device = torch.device(device_text)
        if device.type != "cuda":
            smoke["skipped"] = "requested device is not CUDA"
            return smoke
        index = 0 if device.index is None else device.index
        if index >= torch.cuda.device_count():
            smoke["error"] = {"type": "IndexError", "message": f"CUDA device index {index} is not visible"}
            return smoke
        with torch.cuda.device(device):
            tensor = torch.zeros((), device=device)
            smoke["value"] = float(tensor.item())
            torch.cuda.synchronize(device)
            del tensor
        smoke.update({"ok": True, "device_index": index})
    except BaseException as exc:  # noqa: BLE001
        smoke["error"] = exc_info(exc)
    return smoke


def nunchaku_section() -> dict[str, Any]:
    nunchaku, report = import_report("nunchaku")
    report["distribution_version"] = distribution_version("nunchaku")
    if nunchaku is not None:
        report["module_version"] = getattr(nunchaku, "__version__", None)
        report["exports"] = list(getattr(nunchaku, "__all__", []))
    return report


def api_section() -> dict[str, Any]:
    result: dict[str, Any] = {}
    module_cache: dict[str, Any | None] = {}
    report_cache: dict[str, dict[str, Any]] = {}
    for group, targets in API_TARGETS.items():
        result[group] = {}
        for module_name, attr_path in targets:
            if module_name not in module_cache:
                module, module_report = import_report(module_name)
                module_cache[module_name] = module
                report_cache[module_name] = module_report
            module = module_cache[module_name]
            key = f"{module_name}.{attr_path}"
            if module is None:
                result[group][key] = {"available": False, "error": report_cache[module_name].get("error")}
                continue
            try:
                obj = getattr_dotted(module, attr_path)
            except BaseException as exc:  # noqa: BLE001
                result[group][key] = {"available": False, "error": exc_info(exc)}
                continue
            entry: dict[str, Any] = {"available": True}
            sig = signature(obj)
            if sig is not None:
                entry["signature"] = sig
            result[group][key] = entry
    return result


def precision_section(torch: Any | None, device_text: str) -> dict[str, Any]:
    report: dict[str, Any] = {"attempted": False}
    if torch is None:
        report["skipped"] = "torch import failed"
        return report
    if not torch.cuda.is_available():
        report["skipped"] = "CUDA unavailable"
        return report
    try:
        utils = importlib.import_module("nunchaku.utils")
        get_precision = getattr(utils, "get_precision")
        report["attempted"] = True
        report["value"] = get_precision(device=torch.device(device_text))
        report["ok"] = True
    except BaseException as exc:  # noqa: BLE001
        report["ok"] = False
        report["error"] = exc_info(exc)
    return report


def summarize(result: dict[str, Any]) -> tuple[str, list[str]]:
    advice: list[str] = []
    status = "ok"
    if not result["torch"].get("ok"):
        return "error", ["PyTorch is not importable in this Python environment."]
    if not result["torch"].get("cuda_available"):
        status = "warning"
        advice.append("CUDA is unavailable; Nunchaku quantized inference has no full CPU substitute.")
    if not result["nunchaku"].get("ok"):
        status = "warning"
        advice.append("Nunchaku is not importable; install a wheel/build matching this Python, PyTorch, CUDA, and GPU architecture.")
    unsupported = [d for d in result["torch"].get("devices", []) if d.get("recommended_nunchaku_precision") == "unsupported"]
    if unsupported:
        status = "warning"
        sms = ", ".join(f"cuda:{d['index']} sm_{d['sm']}" for d in unsupported)
        advice.append(f"Unsupported Nunchaku GPU architecture detected: {sms}.")
    if result["precision"].get("attempted") and not result["precision"].get("ok"):
        status = "warning"
        advice.append("nunchaku.utils.get_precision failed; inspect CUDA visibility and package import errors.")
    return status, advice


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    torch_info, torch_module = torch_section(args)
    result: dict[str, Any] = {
        "python": {
            "version": sys.version.splitlines()[0],
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "requested_device": args.device,
        "torch": torch_info,
        "nunchaku": nunchaku_section(),
        "api": api_section(),
        "precision": precision_section(torch_module, args.device),
    }
    status, advice = summarize(result)
    result["status"] = status
    result["advice"] = advice
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    if args.fail_on_warning and status != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
