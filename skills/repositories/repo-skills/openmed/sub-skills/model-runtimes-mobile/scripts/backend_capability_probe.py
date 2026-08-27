#!/usr/bin/env python3
"""Probe OpenMed model/runtime capabilities without downloads or inference.

The probe is intentionally read-only. It checks imports, optional backend extras,
hardware/toolchain signals, registry metadata, and artifact directory layout. It
does not download models, load weights, tokenize text, or invoke a model.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import warnings
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

BACKEND_MODULES: Mapping[str, tuple[str, ...]] = {
    "hf": ("transformers", "huggingface_hub", "tokenizers"),
    "mlx": (
        "mlx",
        "mlx_lm",
        "huggingface_hub",
        "transformers",
        "tokenizers",
        "safetensors",
        "tiktoken",
    ),
    "coreml": ("coremltools", "huggingface_hub", "torch", "transformers"),
    "onnx": ("onnx", "onnxruntime", "onnxscript", "torch", "transformers"),
    "onnx-runtime": ("huggingface_hub", "numpy", "onnxruntime", "tokenizers"),
    "openvino": ("openvino", "nncf", "onnxruntime", "transformers"),
    "torch": ("torch",),
    "android-toolchain": (),
    "browser-toolchain": (),
    "swift-toolchain": (),
}

MODULE_DISTRIBUTIONS: Mapping[str, str] = {
    "PIL": "Pillow",
    "coremltools": "coremltools",
    "huggingface_hub": "huggingface-hub",
    "mlx": "mlx",
    "mlx_lm": "mlx-lm",
    "nncf": "nncf",
    "numpy": "numpy",
    "onnx": "onnx",
    "onnxruntime": "onnxruntime",
    "onnxscript": "onnxscript",
    "openmed": "openmed",
    "openvino": "openvino",
    "safetensors": "safetensors",
    "tiktoken": "tiktoken",
    "tokenizers": "tokenizers",
    "torch": "torch",
    "transformers": "transformers",
}

INSTALL_HINTS: Mapping[str, str] = {
    "hf": 'pip install "openmed[hf]"',
    "mlx": 'pip install "openmed[mlx]"',
    "coreml": 'pip install "openmed[coreml]"',
    "onnx": 'pip install "openmed[onnx]"',
    "onnx-runtime": 'pip install "openmed[onnx-runtime]"',
    "openvino": 'pip install "openmed[openvino]"',
    "torch": 'pip install "openmed[hf]" or a platform-specific torch wheel',
    "android-toolchain": "Install a JDK, Android SDK/Gradle, and ONNX Runtime Mobile artifacts.",
    "browser-toolchain": "Install Node/npm plus browser WebGPU or local WASM assets.",
    "swift-toolchain": "Install Xcode and Swift Package Manager on an Apple host.",
}

OFFLINE_ENV_VARS = (
    "OPENMED_OFFLINE",
    "HF_HUB_OFFLINE",
    "TRANSFORMERS_OFFLINE",
    "HF_DATASETS_OFFLINE",
)
CACHE_ENV_VARS = ("HF_HOME", "HF_HUB_CACHE", "OPENMED_AIRGAP_CACHE")
TOKEN_ENV_VARS = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HF_WRITE_TOKEN")


def module_available(module_name: str) -> bool:
    """Return whether a module can be found without importing it."""

    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):
        return False


def dist_version_for_module(module_name: str) -> str | None:
    """Return an installed distribution version for a module, if known."""

    dist_name = MODULE_DISTRIBUTIONS.get(module_name, module_name)
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None


def module_status(module_name: str) -> dict[str, Any]:
    """Return importless status for one module."""

    available = module_available(module_name)
    return {
        "module": module_name,
        "available": available,
        "version": dist_version_for_module(module_name) if available else None,
    }


def backend_status(name: str) -> dict[str, Any]:
    """Return availability status for a backend or external toolchain."""

    modules = BACKEND_MODULES[name]
    module_reports = [module_status(module) for module in modules]
    missing = [report["module"] for report in module_reports if not report["available"]]
    available = not missing

    if name == "android-toolchain":
        java_ok = shutil.which("java") is not None or shutil.which("javac") is not None
        gradle_ok = shutil.which("gradle") is not None or Path("gradlew").exists()
        sdk_ok = bool(os.getenv("ANDROID_HOME") or os.getenv("ANDROID_SDK_ROOT"))
        available = java_ok and (gradle_ok or sdk_ok)
        missing = []
        if not java_ok:
            missing.append("java-or-javac")
        if not gradle_ok:
            missing.append("gradle-or-gradlew")
        if not sdk_ok:
            missing.append("ANDROID_HOME-or-ANDROID_SDK_ROOT")
    elif name == "browser-toolchain":
        node_ok = shutil.which("node") is not None
        npm_ok = shutil.which("npm") is not None
        available = node_ok and npm_ok
        missing = [item for item, ok in (("node", node_ok), ("npm", npm_ok)) if not ok]
    elif name == "swift-toolchain":
        swift_ok = shutil.which("swift") is not None
        xcode_ok = shutil.which("xcodebuild") is not None or shutil.which("xcrun") is not None
        available = swift_ok and xcode_ok and platform.system() == "Darwin"
        missing = []
        if not swift_ok:
            missing.append("swift")
        if not xcode_ok:
            missing.append("xcodebuild-or-xcrun")
        if platform.system() != "Darwin":
            missing.append("Darwin-host")

    return {
        "name": name,
        "available": available,
        "modules": module_reports,
        "missing": missing,
        "install_hint": INSTALL_HINTS[name],
    }


def command_output(command: Sequence[str], timeout: float = 3.0) -> dict[str, Any]:
    """Run a harmless version/query command with a short timeout."""

    executable = shutil.which(command[0])
    if executable is None:
        return {"available": False, "command": command[0], "output": None}
    try:
        completed = subprocess.run(
            [executable, *command[1:]],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:  # pragma: no cover - platform dependent
        return {
            "available": True,
            "command": " ".join(command),
            "error": f"{type(exc).__name__}: {exc}",
        }
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return {
        "available": True,
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "output": output[:8],
    }


def probe_torch() -> dict[str, Any]:
    """Import torch if available and report device signals."""

    if not module_available("torch"):
        return {"available": False, "reason": "torch module not importable"}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import torch  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - depends on local wheel
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    cuda_available = bool(getattr(torch.cuda, "is_available", lambda: False)())
    cuda_devices: list[dict[str, Any]] = []
    if cuda_available:
        for index in range(int(torch.cuda.device_count())):
            props = torch.cuda.get_device_properties(index)
            cuda_devices.append(
                {
                    "index": index,
                    "name": props.name,
                    "total_memory_mb": round(props.total_memory / 1_000_000),
                }
            )

    mps_backend = getattr(getattr(torch, "backends", None), "mps", None)
    mps_available = bool(
        getattr(mps_backend, "is_available", lambda: False)()
        if mps_backend is not None
        else False
    )

    return {
        "available": True,
        "version": getattr(torch, "__version__", None),
        "cuda_available": cuda_available,
        "cuda_device_count": len(cuda_devices),
        "cuda_devices": cuda_devices,
        "mps_available": mps_available,
    }


def probe_onnxruntime() -> dict[str, Any]:
    """Report ONNX Runtime providers without opening a model."""

    if not module_available("onnxruntime"):
        return {"available": False, "reason": "onnxruntime module not importable"}
    try:
        import onnxruntime as ort  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - depends on local wheel
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "available": True,
        "version": getattr(ort, "__version__", None),
        "providers": list(ort.get_available_providers()),
    }


def probe_openvino() -> dict[str, Any]:
    """Report OpenVINO devices without compiling a graph."""

    if not module_available("openvino"):
        return {"available": False, "reason": "openvino module not importable"}
    try:
        try:
            from openvino.runtime import Core  # type: ignore[import-not-found]
        except Exception:
            from openvino import Core  # type: ignore[import-not-found,no-redef]
        core = Core()
        devices = list(getattr(core, "available_devices", []))
    except Exception as exc:  # pragma: no cover - platform dependent
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"available": True, "devices": devices}


def probe_apple() -> dict[str, Any]:
    """Report Apple runtime/toolchain hints."""

    return {
        "host_is_darwin": platform.system() == "Darwin",
        "host_machine": platform.machine(),
        "apple_silicon_host": platform.system() == "Darwin"
        and platform.machine() in {"arm64", "aarch64"},
        "mlx_module_available": module_available("mlx"),
        "coremltools_available": module_available("coremltools"),
        "swift": command_output(("swift", "--version")),
        "xcodebuild": command_output(("xcodebuild", "-version")),
    }


def probe_android() -> dict[str, Any]:
    """Report Android build/deployment toolchain hints."""

    return {
        "ANDROID_HOME_set": bool(os.getenv("ANDROID_HOME")),
        "ANDROID_SDK_ROOT_set": bool(os.getenv("ANDROID_SDK_ROOT")),
        "java": command_output(("java", "-version")),
        "javac": command_output(("javac", "-version")),
        "gradle": command_output(("gradle", "--version")),
        "adb": command_output(("adb", "version")),
    }


def probe_browser() -> dict[str, Any]:
    """Report browser build toolchain hints available from the shell."""

    return {
        "node": command_output(("node", "--version")),
        "npm": command_output(("npm", "--version")),
        "webgpu_runtime_note": (
            "WebGPU and SharedArrayBuffer support must be checked inside the "
            "target browser; this CLI can only report build tools."
        ),
    }


def registry_summary(model_name: str | None) -> dict[str, Any]:
    """Summarize OpenMed registry metadata without downloads."""

    if not module_available("openmed"):
        return {"available": False, "reason": "openmed module not importable"}
    try:
        from openmed.core.model_registry import get_all_models, get_model_info
    except Exception as exc:  # pragma: no cover - install dependent
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    all_models = get_all_models()
    format_counts: Counter[str] = Counter()
    task_counts: Counter[str] = Counter()
    license_counts: Counter[str] = Counter()
    for info in all_models.values():
        format_counts.update(info.formats or ["<none>"])
        task_counts.update([info.task or "<none>"])
        license_counts.update([info.license or "<none>"])

    payload: dict[str, Any] = {
        "available": True,
        "model_count": len(all_models),
        "formats": dict(sorted(format_counts.items())),
        "tasks": dict(sorted(task_counts.items())),
        "licenses": dict(sorted(license_counts.items())),
    }

    if model_name:
        info = get_model_info(model_name)
        if info is None:
            payload["selected_model"] = {
                "query": model_name,
                "found": False,
                "note": "Not a registry alias/key. A full repo id or local path may still be valid.",
            }
        else:
            payload["selected_model"] = {
                "query": model_name,
                "found": True,
                "model_id": info.model_id,
                "category": info.category,
                "task": info.task,
                "family": info.family,
                "languages": info.languages,
                "tier": info.tier,
                "param_count": info.param_count,
                "architecture": info.architecture,
                "formats": info.formats,
                "license": info.license,
                "download_mb": info.download_mb,
                "disk_mb": info.disk_mb,
                "peak_ram_mb": info.peak_ram_mb,
                "recommended_tier": info.recommended_tier,
                "reproducibility_hash_present": bool(info.reproducibility_hash),
                "script_coverage_keys": sorted(info.script_coverage),
            }
    return payload


def safe_read_json(path: Path) -> dict[str, Any] | None:
    """Read a small JSON manifest, returning None on failure."""

    if not path.exists() or path.stat().st_size > 2_000_000:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def inspect_artifact_dir(path_text: str | None) -> dict[str, Any] | None:
    """Inspect runtime artifact layout without loading weights."""

    if not path_text:
        return None
    root = Path(path_text).expanduser()
    result: dict[str, Any] = {
        "path_provided": True,
        "exists": root.exists(),
        "is_dir": root.is_dir(),
    }
    if not root.is_dir():
        return result

    filenames = {child.name for child in root.iterdir() if child.is_file()}
    directories = {child.name for child in root.iterdir() if child.is_dir()}
    manifests = {
        name: safe_read_json(root / name)
        for name in ("openmed-onnx.json", "openmed-mlx.json", "openmed-coreml.json")
        if (root / name).exists()
    }
    tokenizer_present = bool(
        filenames
        & {
            "tokenizer.json",
            "vocab.txt",
            "merges.txt",
            "tokenizer.model",
            "sentencepiece.bpe.model",
        }
    )
    label_present = "id2label.json" in filenames or bool(
        (safe_read_json(root / "config.json") or {}).get("id2label")
        if (root / "config.json").exists()
        else False
    )

    result.update(
        {
            "files": sorted(list(filenames))[:80],
            "directories": sorted(list(directories))[:40],
            "manifest_files": sorted(manifests),
            "tokenizer_assets_present": tokenizer_present,
            "label_metadata_present": label_present,
            "onnx_files": sorted(name for name in filenames if name.endswith(".onnx")),
            "coreml_packages": sorted(
                name for name in filenames | directories if name.endswith((".mlpackage", ".mlmodelc"))
            ),
            "mlx_weights_present": bool(
                filenames & {"weights.safetensors", "weights.npz", "model.safetensors"}
            ),
            "transformersjs_bundle_present": "transformersjs" in directories,
            "manifests": {
                name: {
                    "format": payload.get("format") if isinstance(payload, dict) else None,
                    "formats": payload.get("formats") if isinstance(payload, dict) else None,
                    "artifact_count": len(payload.get("artifacts", []))
                    if isinstance(payload, dict)
                    else None,
                }
                for name, payload in manifests.items()
            },
        }
    )
    return result


def environment_report() -> dict[str, Any]:
    """Return PHI-free environment and offline/cache flag state."""

    return {
        "python": sys.version.split()[0],
        "executable": Path(sys.executable).name,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "offline_flags": {name: bool(os.getenv(name)) for name in OFFLINE_ENV_VARS},
        "cache_env_set": {name: bool(os.getenv(name)) for name in CACHE_ENV_VARS},
        "hub_token_env_set": {name: bool(os.getenv(name)) for name in TOKEN_ENV_VARS},
    }


def collect_report(args: argparse.Namespace) -> dict[str, Any]:
    """Collect the full no-download capability report."""

    backends = {name: backend_status(name) for name in sorted(BACKEND_MODULES)}
    openmed_status = module_status("openmed")

    openmed_capabilities: dict[str, Any] = {"available": False}
    if openmed_status["available"]:
        try:
            from openmed.core.capabilities import available_backends

            openmed_capabilities = {
                key: value.as_dict() for key, value in available_backends().items()
            }
        except Exception as exc:  # pragma: no cover - install dependent
            openmed_capabilities = {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    required = list(args.require or [])
    missing_required = [
        name for name in required if name in backends and not backends[name]["available"]
    ]

    return {
        "schema_version": 1,
        "mode": "no-download-no-inference",
        "environment": environment_report(),
        "openmed": openmed_status,
        "openmed_capabilities": openmed_capabilities,
        "backends": backends,
        "hardware": {
            "nvidia_smi": command_output(
                (
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,driver_version",
                    "--format=csv,noheader",
                )
            ),
            "torch": probe_torch(),
            "onnxruntime": probe_onnxruntime(),
            "openvino": probe_openvino(),
            "apple": probe_apple(),
            "android": probe_android(),
            "browser": probe_browser(),
        },
        "registry": registry_summary(args.model),
        "artifact_dir": inspect_artifact_dir(args.artifact_dir),
        "required": required,
        "missing_required": missing_required,
        "status": "ok" if not missing_required else "missing-required-backend",
    }


def print_human(report: Mapping[str, Any]) -> None:
    """Print a compact human-readable report."""

    print(f"OpenMed runtime capability probe: {report['status']}")
    print(f"Mode: {report['mode']}")
    env = report["environment"]
    print(f"Python: {env['python']} on {env['platform']} ({env['machine']})")
    print(f"openmed importable: {report['openmed']['available']} version={report['openmed'].get('version')}")
    print("Offline flags:", env["offline_flags"])
    print("Cache env set:", env["cache_env_set"])
    print("Hub token env set:", env["hub_token_env_set"])
    print("\nBackends:")
    for name, status in report["backends"].items():
        state = "available" if status["available"] else "missing"
        missing = ", ".join(status["missing"]) if status["missing"] else "-"
        print(f"  - {name}: {state}; missing={missing}; hint={status['install_hint']}")
    print("\nHardware/toolchains:")
    torch = report["hardware"]["torch"]
    print(f"  - torch: {torch}")
    ort = report["hardware"]["onnxruntime"]
    print(f"  - onnxruntime: {ort}")
    ov = report["hardware"]["openvino"]
    print(f"  - openvino: {ov}")
    apple = report["hardware"]["apple"]
    print(
        "  - apple: "
        f"darwin={apple['host_is_darwin']} apple_silicon={apple['apple_silicon_host']} "
        f"mlx_module={apple['mlx_module_available']} coremltools={apple['coremltools_available']}"
    )
    print("\nRegistry:")
    registry = report["registry"]
    print(f"  - available={registry.get('available')} model_count={registry.get('model_count')}")
    if "selected_model" in registry:
        print(f"  - selected_model={registry['selected_model']}")
    artifact = report.get("artifact_dir")
    if artifact is not None:
        print("\nArtifact directory:")
        print(f"  - {artifact}")
    if report["missing_required"]:
        print("\nMissing required backends:", ", ".join(report["missing_required"]))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Probe OpenMed model runtime dependencies, hardware, registry metadata, "
            "and artifact layout without downloads or inference."
        )
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    parser.add_argument(
        "--require",
        action="append",
        choices=sorted(BACKEND_MODULES),
        help="Backend/toolchain that must be available; repeat as needed.",
    )
    parser.add_argument(
        "--model",
        help="Optional OpenMed registry key/alias to summarize without downloading.",
    )
    parser.add_argument(
        "--artifact-dir",
        help="Optional local artifact directory to inspect without loading weights.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the capability probe."""

    args = parse_args(argv)
    report = collect_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 2 if report["missing_required"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
