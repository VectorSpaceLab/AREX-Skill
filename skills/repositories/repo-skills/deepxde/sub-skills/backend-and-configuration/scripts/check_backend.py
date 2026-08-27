#!/usr/bin/env python3
"""Safe DeepXDE backend diagnostic.

The script selects a backend before importing DeepXDE, checks required optional
packages, reports visible devices, and exits with actionable messages. It does
not create models, start training, install packages, or write DeepXDE config.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import os
import platform
import sys
from dataclasses import dataclass
from typing import Any

VALID_BACKENDS = [
    "tensorflow.compat.v1",
    "tensorflow",
    "pytorch",
    "jax",
    "paddle",
]

DEPENDENCIES = {
    "tensorflow.compat.v1": [
        ("tensorflow", "tensorflow>=2.7.0 exposing tensorflow.compat.v1"),
    ],
    "tensorflow": [
        ("tensorflow", "tensorflow>=2.3.0"),
        ("tensorflow_probability", "tensorflow-probability>=0.11.0"),
    ],
    "pytorch": [
        ("torch", "torch>=2.0.0"),
    ],
    "jax": [
        ("jax", "jax"),
        ("flax", "flax"),
        ("optax", "optax"),
    ],
    "paddle": [
        ("paddle", "paddlepaddle>=2.6.0"),
    ],
}

DIST_NAMES = {
    "tensorflow": "tensorflow",
    "tensorflow_probability": "tensorflow-probability",
    "torch": "torch",
    "jax": "jax",
    "flax": "flax",
    "optax": "optax",
    "paddle": "paddlepaddle",
    "deepxde": "DeepXDE",
}


@dataclass
class ModuleProbe:
    module: str
    requirement: str
    ok: bool
    version: str | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "requirement": self.requirement,
            "ok": self.ok,
            "version": self.version,
            "error": self.error,
        }


def module_version(module_name: str, module: Any | None = None) -> str | None:
    """Return a best-effort package/module version without failing diagnostics."""
    if module is not None:
        version = getattr(module, "__version__", None)
        if version:
            return str(version)
    dist_name = DIST_NAMES.get(module_name, module_name)
    try:
        return importlib.metadata.version(dist_name)
    except importlib.metadata.PackageNotFoundError:
        return None
    except Exception:
        return None


def probe_modules(backend: str) -> list[ModuleProbe]:
    probes: list[ModuleProbe] = []
    for module_name, requirement in DEPENDENCIES[backend]:
        try:
            module = importlib.import_module(module_name)
            probes.append(
                ModuleProbe(
                    module=module_name,
                    requirement=requirement,
                    ok=True,
                    version=module_version(module_name, module),
                )
            )
        except Exception as exc:  # ImportError plus broken binary/package errors.
            probes.append(
                ModuleProbe(
                    module=module_name,
                    requirement=requirement,
                    ok=False,
                    version=module_version(module_name),
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
    return probes


def collect_backend_devices(backend: str) -> dict[str, Any]:
    """Collect non-training device information for the selected backend."""
    devices: dict[str, Any] = {"backend": backend, "gpu_available": False}

    if backend == "pytorch":
        import torch

        cuda_available = bool(torch.cuda.is_available())
        mps_available = bool(
            hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        )
        devices.update(
            {
                "torch_version": module_version("torch", torch),
                "cuda_available": cuda_available,
                "cuda_device_count": torch.cuda.device_count() if cuda_available else 0,
                "cuda_devices": [
                    torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())
                ]
                if cuda_available
                else [],
                "mps_available": mps_available,
                "default_dtype": str(torch.get_default_dtype()),
                "gpu_available": cuda_available,
            }
        )
        if hasattr(torch, "get_default_device"):
            try:
                devices["default_device"] = str(torch.get_default_device())
            except Exception as exc:
                devices["default_device_error"] = f"{type(exc).__name__}: {exc}"
        return devices

    if backend in {"tensorflow", "tensorflow.compat.v1"}:
        import tensorflow as tf

        physical = []
        try:
            physical = tf.config.list_physical_devices()
        except Exception as exc:
            devices["device_list_error"] = f"{type(exc).__name__}: {exc}"
        gpus = [str(device) for device in physical if getattr(device, "device_type", None) == "GPU"]
        devices.update(
            {
                "tensorflow_version": module_version("tensorflow", tf),
                "physical_devices": [str(device) for device in physical],
                "gpu_devices": gpus,
                "gpu_available": bool(gpus),
                "tf_force_gpu_allow_growth": os.environ.get("TF_FORCE_GPU_ALLOW_GROWTH"),
            }
        )
        try:
            devices["eager_execution"] = bool(tf.executing_eagerly())
        except Exception:
            pass
        return devices

    if backend == "jax":
        import jax

        jax_devices = []
        try:
            jax_devices = [str(device) for device in jax.devices()]
        except Exception as exc:
            devices["device_list_error"] = f"{type(exc).__name__}: {exc}"
        devices.update(
            {
                "jax_version": module_version("jax", jax),
                "default_backend": jax.default_backend(),
                "devices": jax_devices,
                "gpu_available": any("gpu" in device.lower() for device in jax_devices),
            }
        )
        return devices

    if backend == "paddle":
        import paddle

        current_device = None
        try:
            current_device = paddle.device.get_device()
        except Exception as exc:
            devices["device_query_error"] = f"{type(exc).__name__}: {exc}"
        compiled_cuda = False
        try:
            compiled_cuda = bool(paddle.device.is_compiled_with_cuda())
        except Exception as exc:
            devices["cuda_query_error"] = f"{type(exc).__name__}: {exc}"
        devices.update(
            {
                "paddle_version": module_version("paddle", paddle),
                "current_device": current_device,
                "compiled_with_cuda": compiled_cuda,
                "gpu_available": bool(current_device and "gpu" in current_device),
            }
        )
        return devices

    return devices


def actionable_missing_dependency(backend: str, probes: list[ModuleProbe]) -> list[str]:
    missing = [probe for probe in probes if not probe.ok]
    if not missing:
        return []
    messages = [
        f"Backend '{backend}' cannot be used until required package imports succeed."
    ]
    for probe in missing:
        messages.append(
            f"Install or fix {probe.requirement} (Python import '{probe.module}' failed: {probe.error})."
        )
    if backend != "pytorch":
        messages.append(
            "If the task does not require this backend, retry with '--backend pytorch' for the CPU-verified path."
        )
    return messages


def human_report(result: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("DeepXDE backend diagnostic")
    lines.append(f"  requested backend: {result['requested_backend']}")
    lines.append(f"  effective DDE_BACKEND: {result['environment'].get('DDE_BACKEND')}")
    lines.append(f"  python: {result['python']}")
    lines.append(f"  platform: {result['platform']}")
    lines.append("")
    lines.append("Required package imports:")
    for dep in result["dependencies"]:
        status = "ok" if dep["ok"] else "missing/broken"
        version = f" version={dep['version']}" if dep.get("version") else ""
        lines.append(f"  - {dep['module']}: {status}{version} ({dep['requirement']})")
        if dep.get("error"):
            lines.append(f"      {dep['error']}")
    lines.append("")
    if result.get("deepxde_import", {}).get("ok"):
        dde = result["deepxde_import"]
        lines.append("DeepXDE import: ok")
        lines.append(f"  deepxde version: {dde.get('version')}")
        lines.append(f"  reported backend: {dde.get('backend_name')}")
        config = result.get("config", {})
        if config:
            lines.append(
                "  config: "
                + ", ".join(f"{key}={value}" for key, value in sorted(config.items()))
            )
        devices = result.get("devices", {})
        if devices:
            lines.append("Devices:")
            for key, value in sorted(devices.items()):
                lines.append(f"  {key}: {value}")
    else:
        lines.append("DeepXDE import: failed")
        error = result.get("deepxde_import", {}).get("error")
        if error:
            lines.append(f"  {error}")
    lines.append("")
    if result.get("messages"):
        lines.append("Actionable messages:")
        for message in result["messages"]:
            lines.append(f"  - {message}")
    lines.append(f"\nStatus: {'ok' if result['ok'] else 'failed'}")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a DeepXDE backend import and visible devices without training. "
            "Defaults to DDE_BACKEND from the environment, or pytorch when unset."
        )
    )
    parser.add_argument(
        "--backend",
        choices=VALID_BACKENDS,
        default=None,
        help="Backend to select before importing DeepXDE. Default: current DDE_BACKEND or pytorch.",
    )
    parser.add_argument(
        "--require-gpu",
        action="store_true",
        help="Fail if the selected backend imports but reports no visible GPU.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON report to stdout.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    backend = args.backend or os.environ.get("DDE_BACKEND") or "pytorch"

    result: dict[str, Any] = {
        "ok": False,
        "requested_backend": backend,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "environment": {"DDE_BACKEND": backend},
        "dependencies": [],
        "deepxde_import": {"ok": False},
        "devices": {},
        "config": {},
        "messages": [],
    }

    if backend not in VALID_BACKENDS:
        result["messages"].append(
            "Unsupported backend. Choose one of: " + ", ".join(VALID_BACKENDS)
        )
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(human_report(result))
        return 2

    # DeepXDE resolves backend during import. Force a process-local selection and
    # avoid auto-detection or writes to the saved backend config.
    os.environ["DDE_BACKEND"] = backend
    result["environment"]["DDE_BACKEND"] = os.environ["DDE_BACKEND"]

    probes = probe_modules(backend)
    result["dependencies"] = [probe.as_dict() for probe in probes]
    if not all(probe.ok for probe in probes):
        result["messages"].extend(actionable_missing_dependency(backend, probes))
        if args.require_gpu:
            result["messages"].append(
                "GPU requirement was not evaluated because backend dependencies failed to import."
            )
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(human_report(result))
        return 2

    try:
        import deepxde as dde

        backend_name = getattr(dde.backend, "backend_name", None)
        result["deepxde_import"] = {
            "ok": True,
            "version": getattr(dde, "__version__", None)
            or module_version("deepxde"),
            "backend_name": backend_name,
        }
        try:
            result["config"] = {
                "default_float": dde.config.default_float(),
                "autodiff": getattr(dde.config, "autodiff", None),
                "xla_jit": getattr(dde.config, "xla_jit", None),
                "parallel_scaling": getattr(dde.config, "parallel_scaling", None),
                "world_size": getattr(dde.config, "world_size", None),
                "rank": getattr(dde.config, "rank", None),
            }
        except Exception as exc:
            result["config"] = {"error": f"{type(exc).__name__}: {exc}"}
        result["devices"] = collect_backend_devices(backend)
        if backend_name != backend:
            result["messages"].append(
                f"DeepXDE reported backend '{backend_name}', expected '{backend}'. Ensure DDE_BACKEND is set before every DeepXDE import."
            )
    except Exception as exc:
        result["deepxde_import"] = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
        result["messages"].append(
            f"DeepXDE import failed for backend '{backend}'. Ensure DeepXDE itself is installed/importable in this Python environment, then fix the selected backend package stack. Retry with '--backend pytorch' if CPU PyTorch is acceptable."
        )
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(human_report(result))
        return 2

    gpu_available = bool(result.get("devices", {}).get("gpu_available"))
    if args.require_gpu and not gpu_available:
        result["messages"].append(
            "No GPU was reported by the selected backend. Install a GPU-enabled backend build and matching driver/runtime, or omit --require-gpu for CPU-safe checks."
        )
        result["ok"] = False
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(human_report(result))
        return 3

    if backend == "pytorch" and not gpu_available:
        result["messages"].append(
            "PyTorch imported successfully with no GPU required; this matches the CPU-verified construction path."
        )
    elif gpu_available:
        result["messages"].append(
            "A GPU was reported by the backend, but this generated skill does not by itself verify task-level GPU correctness."
        )

    result["ok"] = True
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(human_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
