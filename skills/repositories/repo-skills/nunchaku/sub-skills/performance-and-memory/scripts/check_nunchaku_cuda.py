#!/usr/bin/env python3
"""Safe JSON diagnostics for an installed Nunchaku CUDA runtime.

This script imports torch, nunchaku, and lightweight public API modules; reports
CUDA/device capability, API availability, and precision selection; and never
loads or downloads model weights.
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


API_TARGETS = [
    ("nunchaku", "NunchakuFluxTransformer2dModel"),
    ("nunchaku", "NunchakuFluxTransformer2dModel.from_pretrained"),
    ("nunchaku", "NunchakuFluxTransformer2dModel.set_attention_impl"),
    ("nunchaku", "NunchakuFluxTransformer2DModelV2"),
    ("nunchaku", "NunchakuFluxTransformer2DModelV2.from_pretrained"),
    ("nunchaku", "NunchakuQwenImageTransformer2DModel"),
    ("nunchaku", "NunchakuQwenImageTransformer2DModel.from_pretrained"),
    ("nunchaku", "NunchakuQwenImageTransformer2DModel.set_offload"),
    ("nunchaku", "NunchakuT5EncoderModel"),
    ("nunchaku", "NunchakuT5EncoderModel.from_pretrained"),
    ("nunchaku.caching.diffusers_adapters", "apply_cache_on_pipe"),
    ("nunchaku.utils", "get_precision"),
    ("nunchaku.utils", "is_turing"),
    ("nunchaku.utils", "get_gpu_memory"),
]

SUPPORTED_INT4_SMS = {"75", "80", "86", "89"}
SUPPORTED_FP4_SMS = {"120", "121"}


def exception_dict(exc: BaseException) -> dict[str, str]:
    return {"type": exc.__class__.__name__, "message": str(exc)}


def precision_from_sm(sm: str) -> str:
    if sm in SUPPORTED_FP4_SMS:
        return "fp4"
    if sm in SUPPORTED_INT4_SMS:
        return "int4"
    return "unsupported"


def import_module_report(name: str) -> tuple[Any | None, dict[str, Any]]:
    report: dict[str, Any] = {"import_ok": False}
    try:
        module = importlib.import_module(name)
    except BaseException as exc:  # noqa: BLE001 - diagnostics should capture import failures.
        report["error"] = exception_dict(exc)
        return None, report
    report["import_ok"] = True
    return module, report


def getattr_path(root: Any, dotted: str) -> Any:
    value = root
    for part in dotted.split("."):
        value = getattr(value, part)
    return value


def signature_or_none(obj: Any) -> str | None:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return None


def api_report() -> dict[str, Any]:
    modules: dict[str, Any] = {}
    targets: dict[str, Any] = {}
    cache: dict[str, Any] = {}

    for module_name, attr_path in API_TARGETS:
        module = cache.get(module_name)
        module_report = modules.get(module_name)
        if module is None and module_report is None:
            module, module_report = import_module_report(module_name)
            cache[module_name] = module
            modules[module_name] = module_report

        key = f"{module_name}.{attr_path}"
        if module is None:
            targets[key] = {"available": False, "error": module_report.get("error")}
            continue
        try:
            obj = getattr_path(module, attr_path)
        except BaseException as exc:  # noqa: BLE001 - diagnostics should capture availability failures.
            targets[key] = {"available": False, "error": exception_dict(exc)}
            continue
        targets[key] = {"available": True}
        sig = signature_or_none(obj)
        if sig is not None:
            targets[key]["signature"] = sig

    return {"modules": modules, "targets": targets}


def distribution_version(dist_name: str) -> str | None:
    try:
        return importlib_metadata.version(dist_name)
    except importlib_metadata.PackageNotFoundError:
        return None
    except BaseException:  # noqa: BLE001 - best-effort metadata only.
        return None


def nunchaku_report() -> dict[str, Any]:
    module, report = import_module_report("nunchaku")
    report["distribution_version"] = distribution_version("nunchaku")
    if module is not None:
        report["module_version"] = getattr(module, "__version__", None)
        exported = getattr(module, "__all__", None)
        if exported is not None:
            report["exported_symbols"] = list(exported)
    return report


def torch_report(args: argparse.Namespace) -> tuple[dict[str, Any], Any | None]:
    torch, report = import_module_report("torch")
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
        count = torch.cuda.device_count()
        report["device_count"] = count
        devices = []
        for index in range(count):
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
                    "nunchaku_precision_by_sm": precision_from_sm(sm),
                }
            )
        report["devices"] = devices
    except BaseException as exc:  # noqa: BLE001
        report["device_query_error"] = exception_dict(exc)

    if not args.skip_allocation:
        report["allocation_smoke"] = allocation_smoke(torch, args.device)

    return report, torch


def allocation_smoke(torch: Any, device_text: str) -> dict[str, Any]:
    smoke: dict[str, Any] = {"ok": False, "device": device_text}
    try:
        device = torch.device(device_text)
        if device.type != "cuda":
            smoke["skipped"] = "device is not CUDA"
            return smoke
        index = 0 if device.index is None else device.index
        if index >= torch.cuda.device_count():
            smoke["error"] = {"type": "IndexError", "message": f"CUDA device index {index} is not visible"}
            return smoke
        with torch.cuda.device(device):
            tensor = torch.zeros((), device=device)
            value = float(tensor.item())
            torch.cuda.synchronize(device)
            del tensor
        smoke.update({"ok": True, "device_index": index, "value": value})
    except BaseException as exc:  # noqa: BLE001
        smoke["error"] = exception_dict(exc)
    return smoke


def nunchaku_precision_report(torch: Any | None, device_text: str) -> dict[str, Any]:
    report: dict[str, Any] = {"attempted": False}
    if torch is None:
        report["skipped"] = "torch import failed"
        return report
    if not torch.cuda.is_available():
        report["skipped"] = "CUDA is unavailable"
        return report
    try:
        device = torch.device(device_text)
    except BaseException as exc:  # noqa: BLE001
        report["error"] = exception_dict(exc)
        return report
    if device.type != "cuda":
        report["skipped"] = "device is not CUDA"
        return report

    try:
        utils = importlib.import_module("nunchaku.utils")
        get_precision = getattr(utils, "get_precision")
        report["attempted"] = True
        report["value"] = get_precision(device=device)
        report["ok"] = True
    except BaseException as exc:  # noqa: BLE001
        report["ok"] = False
        report["error"] = exception_dict(exc)
    return report


def summarize_status(result: dict[str, Any]) -> tuple[str, list[str]]:
    advice: list[str] = []
    status = "ok"

    torch_info = result.get("torch", {})
    if not torch_info.get("import_ok"):
        return "error", ["Install PyTorch in the active environment before using Nunchaku diagnostics."]
    if not torch_info.get("cuda_available"):
        status = "warning"
        advice.append("CUDA is unavailable; Nunchaku quantized inference requires a supported NVIDIA CUDA backend.")

    nunchaku_info = result.get("nunchaku", {})
    if not nunchaku_info.get("import_ok"):
        status = "warning" if status == "ok" else status
        advice.append("Nunchaku did not import; install a wheel/build matching this Python, PyTorch, CUDA, and GPU architecture.")

    devices = torch_info.get("devices") or []
    unsupported = [d for d in devices if d.get("nunchaku_precision_by_sm") == "unsupported"]
    if unsupported:
        status = "warning" if status == "ok" else status
        sms = ", ".join(f"cuda:{d['index']} sm_{d['sm']}" for d in unsupported)
        advice.append(f"Unsupported Nunchaku 4-bit GPU architecture detected: {sms}.")

    precision = result.get("precision", {})
    if precision.get("attempted") and not precision.get("ok", False):
        status = "warning" if status == "ok" else status
        advice.append("Nunchaku get_precision failed; inspect CUDA visibility, device index, and package import errors.")

    return status, advice


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print safe JSON diagnostics for Nunchaku CUDA/API availability without downloading models."
    )
    parser.add_argument("--device", default="cuda:0", help="Device for allocation and get_precision checks, e.g. cuda:0.")
    parser.add_argument("--skip-allocation", action="store_true", help="Do not allocate a scalar CUDA tensor.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON with indentation.")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit non-zero when status is not ok.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result: dict[str, Any] = {
        "python": {
            "version": sys.version.splitlines()[0],
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "requested_device": args.device,
        "torch": {},
        "nunchaku": {},
        "api": {},
        "precision": {},
    }

    torch_info, torch_module = torch_report(args)
    result["torch"] = torch_info
    result["nunchaku"] = nunchaku_report()
    result["api"] = api_report()
    result["precision"] = nunchaku_precision_report(torch_module, args.device)

    status, advice = summarize_status(result)
    result["status"] = status
    result["advice"] = advice

    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    if args.fail_on_error and status != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
