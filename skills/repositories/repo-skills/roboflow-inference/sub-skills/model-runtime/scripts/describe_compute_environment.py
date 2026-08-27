#!/usr/bin/env python3
"""Read-only runtime probe for inference-models backend selection.

This helper does not import ``inference_models``. It mirrors the same kind of
runtime snapshot that ``AutoModel.describe_compute_environment()`` prints, but
it stays lightweight, deterministic, and safe to run in a partially prepared
environment.
"""

from __future__ import annotations

import ctypes
import json
import os
import platform
import re
import subprocess
from dataclasses import asdict, is_dataclass
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any, Optional

import torch
from packaging.version import InvalidVersion, Version

BACKEND_VALUES = [
    "torch",
    "torch-script",
    "onnx",
    "trt",
    "hugging-face",
    "ultralytics",
    "custom",
]
QUANTIZATION_VALUES = ["fp32", "fp16", "bf16", "int8", "unknown"]
DEFAULT_ONNX_EXECUTION_PROVIDERS = [
    "CUDAExecutionProvider",
    "OpenVINOExecutionProvider",
    "CoreMLExecutionProvider",
    "CPUExecutionProvider",
]
JETSON_DEVICE_PATTERNS = {
    "orin nano": "nvidia-jetson-orin-nano",
    "orin nx": "nvidia-jetson-orin-nx",
    "agx orin": "nvidia-jetson-agx-orin",
    "igx orin": "nvidia-jetson-igx-orin",
    "xavier nx": "nvidia-jetson-xavier-nx",
    "agx xavier industrial": "nvidia-jetson-agx-xavier-industrial",
    "agx xavier": "nvidia-jetson-agx-xavier",
    "nano": "nvidia-jetson-nano",
    "tx2": "nvidia-jetson-tx2",
}


def _parse_bool(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return None


def _parse_csv(value: Optional[str], default: list[str]) -> list[str]:
    if value is None:
        return default
    parts = [item.strip() for item in value.strip().strip("[").strip("]").split(",")]
    return [item for item in parts if item]


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _json_safe(raw) for key, raw in asdict(value).items()}
    if isinstance(value, Version):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(raw) for key, raw in value.items()}
    if isinstance(value, set):
        return sorted(_json_safe(item) for item in value)
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _version_from_string(value: Optional[str]) -> Optional[Version]:
    if not value:
        return None
    try:
        return Version(value)
    except InvalidVersion:
        return None


def _version_from_package(package_name: str) -> Optional[Version]:
    try:
        return _version_from_string(importlib_metadata.version(package_name))
    except importlib_metadata.PackageNotFoundError:
        return None


def _device_string() -> str:
    requested = os.environ.get("DEFAULT_DEVICE")
    if requested:
        return requested
    return "cuda" if torch.cuda.is_available() else "cpu"


def _inference_home() -> str:
    return os.environ.get("INFERENCE_HOME") or os.environ.get("MODEL_CACHE_DIR") or "/tmp/cache"


def _onnx_execution_providers() -> list[str]:
    return _parse_csv(
        os.environ.get("ONNXRUNTIME_EXECUTION_PROVIDERS"),
        DEFAULT_ONNX_EXECUTION_PROVIDERS,
    )


def _roboflow_region() -> str:
    region = os.environ.get("ROBOFLOW_REGION", "us").strip().lower()
    return region if region in {"us", "eu"} else "us"


def _roboflow_environment() -> str:
    environment = os.environ.get("ROBOFLOW_ENVIRONMENT", "prod").strip().lower()
    return environment if environment in {"prod", "staging"} else "prod"


def _roboflow_api_host() -> str:
    explicit = os.environ.get("ROBOFLOW_API_HOST")
    if explicit:
        return explicit
    region = _roboflow_region()
    environment = _roboflow_environment()
    hosts = {
        ("us", "prod"): "https://api.roboflow.com",
        ("us", "staging"): "https://api.roboflow.one",
        ("eu", "prod"): "https://api.roboflow.eu",
        ("eu", "staging"): "https://api.roboflow-eu.one",
    }
    return hosts[(region, environment)]


def _cuda_version() -> Optional[Version]:
    # Runtime / toolkit version via libcudart when available.
    try:
        lib = ctypes.CDLL("libcudart.so")
        version_holder = ctypes.c_int()
        if lib.cudaRuntimeGetVersion(ctypes.byref(version_holder)) == 0:
            raw = version_holder.value
            return Version(f"{raw // 1000}.{(raw % 1000) // 10}.{raw % 10}")
    except Exception:
        pass
    try:
        return _version_from_string(torch.version.cuda)
    except Exception:
        return None


def _driver_version() -> Optional[Version]:
    try:
        lib = ctypes.CDLL("libcudart.so")
        version_holder = ctypes.c_int()
        if lib.cudaDriverGetVersion(ctypes.byref(version_holder)) != 0:
            return None
        raw = version_holder.value
        if raw == 0:
            return None
        return Version(f"{raw // 1000}.{(raw % 1000) // 10}.{raw % 10}")
    except Exception:
        return None


def _trt_version() -> Optional[Version]:
    version = _version_from_package("tensorrt")
    if version is not None:
        return version
    try:
        result = subprocess.run(
            "dpkg -l | grep libnvinfer-bin",
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        chunks = result.stdout.strip().split()
        if len(chunks) < 3:
            return None
        first = chunks[2].split("+cuda")[0]
        return _version_from_string(first)
    except Exception:
        return None


def _onnxruntime_info() -> tuple[Optional[Version], Optional[list[str]]]:
    try:
        import onnxruntime  # type: ignore
    except Exception:
        return None, None
    version = _version_from_string(getattr(onnxruntime, "__version__", None))
    try:
        providers = list(onnxruntime.get_available_providers())
    except Exception:
        providers = None
    return version, providers


def _jetson_type_from_text(text: str) -> Optional[str]:
    lowered = text.lower()
    for pattern, jetson_name in JETSON_DEVICE_PATTERNS.items():
        if pattern in lowered:
            return jetson_name
    return None


def _jetson_type() -> Optional[str]:
    declared = os.environ.get("JETSON_MODULE")
    if declared:
        resolved = _jetson_type_from_text(declared)
        if resolved:
            return resolved
    try:
        with open("/proc/device-tree/model") as file_handle:
            text = file_handle.read().strip().split("\n", 1)[0]
        resolved = _jetson_type_from_text(text)
        if resolved:
            return resolved
    except Exception:
        pass
    try:
        result = subprocess.run(
            "lshw | grep 'product: NVIDIA Jetson'",
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                resolved = _jetson_type_from_text(line)
                if resolved:
                    return resolved
    except Exception:
        pass
    return None


def _l4t_version() -> Optional[Version]:
    declared = os.environ.get("L4T_VERSION")
    if declared:
        return _version_from_string(declared)
    for candidate in ("/etc/nv_tegra_release", "/proc/device-tree/nvidia,dtsfilename"):
        try:
            with open(candidate) as file_handle:
                text = file_handle.read()
            match = re.search(r"R(\d+)\s*\((?:release)?\).*REVISION:\s*(\d+)\.(\d+)", text, re.IGNORECASE)
            if match:
                return Version(f"{match.group(1)}.{match.group(2)}.{match.group(3)}")
        except Exception:
            continue
    return None


def _torch_version() -> Optional[Version]:
    return _version_from_string(getattr(torch, "__version__", None))


def _torchvision_version() -> Optional[Version]:
    return _version_from_package("torchvision")


def _hf_transformers_available() -> bool:
    return _version_from_package("transformers") is not None


def _trt_python_package_available() -> bool:
    return _version_from_package("tensorrt") is not None


def build_snapshot() -> dict[str, Any]:
    onnxruntime_version, available_onnx_execution_providers = _onnxruntime_info()
    gpu_devices = []
    gpu_devices_cc = []
    for index in range(torch.cuda.device_count()):
        device_name = torch.cuda.get_device_name(index)
        gpu_devices.append(device_name.replace(" ", "-").lower())
        major, minor = torch.cuda.get_device_capability(index)
        gpu_devices_cc.append(f"{major}.{minor}")
    default_device = _device_string()
    inference_home = _inference_home()
    offline_mode = _parse_bool(os.environ.get("OFFLINE_MODE"))
    onnx_execution_providers = _onnx_execution_providers()
    roboflow_api_host = _roboflow_api_host()
    roboflow_environment = _roboflow_environment()
    roboflow_region = _roboflow_region()
    driver_version = _driver_version()
    cuda_version = _cuda_version()
    trt_version = _trt_version()
    jetson_type = _jetson_type()
    l4t_version = _l4t_version()
    torch_version = _torch_version()
    torchvision_version = _torchvision_version()
    hf_transformers_available = _hf_transformers_available()
    trt_python_package_available = _trt_python_package_available()
    return {
        "configuration": {
            "default_device": default_device,
            "inference_home": inference_home,
            "offline_mode": offline_mode,
            "onnxruntime_execution_providers": onnx_execution_providers,
            "roboflow_api_host": roboflow_api_host,
            "roboflow_environment": roboflow_environment,
            "roboflow_region": roboflow_region,
        },
        "runtime": {
            "gpu_available": len(gpu_devices) > 0,
            "gpu_devices": gpu_devices,
            "gpu_devices_cc": gpu_devices_cc,
            "driver_version": str(driver_version) if driver_version else None,
            "cuda_version": str(cuda_version) if cuda_version else None,
            "trt_version": str(trt_version) if trt_version else None,
            "jetson_type": jetson_type,
            "l4t_version": str(l4t_version) if l4t_version else None,
            "os_version": platform.platform(),
            "torch_available": True,
            "torch_version": str(torch_version) if torch_version else None,
            "torchvision_version": str(torchvision_version) if torchvision_version else None,
            "onnxruntime_version": str(onnxruntime_version) if onnxruntime_version else None,
            "available_onnx_execution_providers": available_onnx_execution_providers,
            "hf_transformers_available": hf_transformers_available,
            "trt_python_package_available": trt_python_package_available,
        },
        "supported_backend_values": BACKEND_VALUES,
        "supported_quantization_values": QUANTIZATION_VALUES,
    }


def main() -> None:
    print(json.dumps(_json_safe(build_snapshot()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
