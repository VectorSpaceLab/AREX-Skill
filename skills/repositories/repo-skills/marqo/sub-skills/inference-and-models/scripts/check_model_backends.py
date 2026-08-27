#!/usr/bin/env python3
"""Safely inspect Marqo model backend dependencies.

This script imports optional backend libraries when available and reports CPU/CUDA
facts. It does not download models and does not contact Triton unless --triton-url
is provided explicitly.
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


MODULES_TO_IMPORT = [
    "torch",
    "open_clip",
    "transformers",
    "tritonclient",
    "tritonclient.grpc",
    "tritonclient.http",
]


@dataclass
class ImportResult:
    module: str
    available: bool
    version: str | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "module": self.module,
            "available": self.available,
        }
        if self.version is not None:
            data["version"] = self.version
        if self.error is not None:
            data["error"] = self.error
        return data


def _safe_version(module: Any) -> str | None:
    version = getattr(module, "__version__", None)
    if version is None:
        return None
    try:
        return str(version)
    except Exception:
        return None


def safe_import(module_name: str) -> ImportResult:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic script should not crash on optional imports
        return ImportResult(
            module=module_name,
            available=False,
            error=f"{type(exc).__name__}: {exc}",
        )
    return ImportResult(
        module=module_name,
        available=True,
        version=_safe_version(module),
    )


def collect_torch_status() -> dict[str, Any]:
    result: dict[str, Any] = {
        "available": False,
        "cuda_available": False,
        "cuda_device_count": 0,
        "devices": [],
    }
    try:
        torch = importlib.import_module("torch")
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    result["available"] = True
    result["version"] = _safe_version(torch)
    result["compiled_cuda"] = getattr(getattr(torch, "version", None), "cuda", None)

    try:
        cuda_available = bool(torch.cuda.is_available())
        device_count = int(torch.cuda.device_count()) if cuda_available else 0
        result["cuda_available"] = cuda_available
        result["cuda_device_count"] = device_count
    except Exception as exc:  # noqa: BLE001
        result["cuda_error"] = f"{type(exc).__name__}: {exc}"
        return result

    devices: list[dict[str, Any]] = []
    for idx in range(result["cuda_device_count"]):
        try:
            props = torch.cuda.get_device_properties(idx)
            devices.append(
                {
                    "index": idx,
                    "name": getattr(props, "name", "unknown"),
                    "total_memory_bytes": int(getattr(props, "total_memory", 0)),
                    "major": int(getattr(props, "major", 0)),
                    "minor": int(getattr(props, "minor", 0)),
                }
            )
        except Exception as exc:  # noqa: BLE001
            devices.append(
                {
                    "index": idx,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    result["devices"] = devices
    return result


def normalize_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return "http://" + url
    return url


def probe_triton_ready(base_url: str, timeout: float) -> dict[str, Any]:
    """Probe Triton REST readiness. Called only when --triton-url is supplied."""
    started = time.perf_counter()
    normalized = normalize_url(base_url).rstrip("/")
    ready_url = f"{normalized}/v2/health/ready"
    request = urllib.request.Request(
        ready_url,
        headers={"User-Agent": "marqo-model-backend-check/1"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - explicit user-supplied probe URL
            body = response.read(512)
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            return {
                "probed": True,
                "url": ready_url,
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "elapsed_ms": elapsed_ms,
                "body_preview": body.decode("utf-8", errors="replace"),
            }
    except urllib.error.HTTPError as exc:
        body = exc.read(512) if hasattr(exc, "read") else b""
        return {
            "probed": True,
            "url": ready_url,
            "ok": False,
            "status": exc.code,
            "error": f"HTTPError: {exc}",
            "body_preview": body.decode("utf-8", errors="replace"),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "probed": True,
            "url": ready_url,
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def collect_report(args: argparse.Namespace) -> dict[str, Any]:
    imports = {name: safe_import(name).as_dict() for name in MODULES_TO_IMPORT}
    report: dict[str, Any] = {
        "python": {
            "version": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "imports": imports,
        "torch": collect_torch_status(),
        "triton_probe": {"probed": False},
        "notes": [
            "No model downloads are performed by this script.",
            "Triton is not contacted unless --triton-url is provided.",
        ],
    }
    if args.triton_url:
        report["triton_probe"] = probe_triton_ready(args.triton_url, args.timeout)
    return report


def print_text_report(report: dict[str, Any]) -> None:
    py = report["python"]
    print(f"Python: {py['version']} ({py['implementation']}, {py['machine']})")
    print(f"Platform: {py['platform']}")
    print("\nImports:")
    for name, data in report["imports"].items():
        if data["available"]:
            suffix = f" version={data['version']}" if "version" in data else ""
            print(f"  OK   {name}{suffix}")
        else:
            print(f"  MISS {name}: {data.get('error', 'not available')}")

    torch_status = report["torch"]
    print("\nTorch/CUDA:")
    if not torch_status.get("available"):
        print(f"  torch unavailable: {torch_status.get('error', 'not available')}")
    else:
        print(f"  torch version: {torch_status.get('version', 'unknown')}")
        print(f"  compiled CUDA: {torch_status.get('compiled_cuda')}")
        print(f"  cuda available: {torch_status.get('cuda_available')}")
        print(f"  cuda device count: {torch_status.get('cuda_device_count')}")
        for device in torch_status.get("devices", []):
            if "error" in device:
                print(f"    [{device['index']}] ERROR {device['error']}")
            else:
                gb = device.get("total_memory_bytes", 0) / (1024 ** 3)
                print(
                    f"    [{device['index']}] {device.get('name', 'unknown')} "
                    f"capability={device.get('major')}.{device.get('minor')} "
                    f"memory={gb:.2f} GiB"
                )

    triton = report["triton_probe"]
    print("\nTriton probe:")
    if not triton.get("probed"):
        print("  skipped (pass --triton-url to probe REST readiness)")
    elif triton.get("ok"):
        print(f"  OK {triton.get('url')} status={triton.get('status')} elapsed_ms={triton.get('elapsed_ms')}")
    else:
        print(f"  FAIL {triton.get('url')} {triton.get('error', '')} status={triton.get('status')}")

    print("\nNotes:")
    for note in report.get("notes", []):
        print(f"  - {note}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Safely report torch/open_clip/transformers/tritonclient import status, "
            "CPU/CUDA facts, and optionally Triton REST readiness."
        )
    )
    parser.add_argument(
        "--triton-url",
        help="Explicit Triton REST base URL to probe with GET /v2/health/ready. Without this flag no network call is made.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=3.0,
        help="Timeout in seconds for the optional Triton REST probe. Default: 3.0.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of text.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any optional import is missing or the optional Triton probe fails.",
    )
    args = parser.parse_args(argv)

    report = collect_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    if args.strict:
        missing = [name for name, data in report["imports"].items() if not data.get("available")]
        triton_failed = report["triton_probe"].get("probed") and not report["triton_probe"].get("ok")
        if missing or triton_failed:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
