#!/usr/bin/env python3
"""Report Kornia model/deployment optional dependencies without downloads.

The probe uses importlib discovery and metadata only. It does not import optional
model backends unless they are base requirements and it does not trigger lazy
loader installation prompts.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ModuleEntry:
    module: str
    role: str
    feature: str
    install_when: str
    dist: str | None = None


MODULES = (
    ModuleEntry("kornia", "required", "Kornia package", "Always required for this skill."),
    ModuleEntry("torch", "required", "PyTorch model runtime", "Always required for Kornia models."),
    ModuleEntry("numpy", "required", "Array dependency and ONNX output conversion", "Base Kornia dependency."),
    ModuleEntry("packaging", "required", "Version/compatibility helpers", "Base Kornia dependency."),
    ModuleEntry("kornia_rs", "required", "Kornia Rust extension package", "Base Kornia dependency."),
    ModuleEntry(
        "PIL",
        "optional",
        "PIL output_type and image conversions",
        "Needed for PIL image outputs.",
        "Pillow",
    ),
    ModuleEntry(
        "onnx",
        "optional",
        "ONNX ModelProto export/load/composition",
        "Needed for to_onnx and ONNX loaders.",
    ),
    ModuleEntry(
        "onnxruntime",
        "optional",
        "ONNX Runtime execution providers",
        "Needed for ONNXModule/ONNXSequential inference.",
    ),
    ModuleEntry(
        "onnxscript",
        "optional",
        "Modern PyTorch ONNX export support",
        "Needed by some torch.onnx export paths.",
    ),
    ModuleEntry(
        "requests",
        "optional",
        "Remote ONNX/model metadata queries",
        "Needed by online ONNX listing/config fetches.",
    ),
    ModuleEntry(
        "huggingface_hub",
        "optional",
        "HF safetensors weight downloads",
        "Needed by some HF pretrained builders.",
    ),
    ModuleEntry(
        "safetensors",
        "optional",
        "Safetensors checkpoint loading",
        "Needed by some HF pretrained builders.",
    ),
    ModuleEntry(
        "ivy",
        "optional",
        "Kornia to NumPy/JAX/TensorFlow transpilation",
        "Needed for kornia.to_numpy/to_jax/to_tensorflow.",
    ),
    ModuleEntry("jax", "optional", "JAX execution target", "Needed only when using the JAX-transpiled module."),
    ModuleEntry(
        "tensorflow",
        "optional",
        "TensorFlow execution target",
        "Needed only when using the TensorFlow-transpiled module.",
    ),
    ModuleEntry(
        "transformers",
        "optional",
        "HF/VLM ecosystem integration",
        "Needed only for model paths that explicitly use transformers.",
    ),
    ModuleEntry(
        "diffusers",
        "optional",
        "Diffusion-model image effects",
        "Needed only for diffusers-backed features.",
    ),
    ModuleEntry(
        "segmentation_models_pytorch",
        "optional",
        "SegmentationModelsBuilder backend",
        "Needed for segmentation-models wrappers.",
    ),
    ModuleEntry(
        "basicsr",
        "optional",
        "RRDB/super-resolution backend",
        "Needed for BasicSR-backed super-resolution wrappers.",
    ),
    ModuleEntry(
        "boxmot",
        "optional",
        "BoxMotTracker backend",
        "Needed for optional multi-object tracking wrappers.",
    ),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Report requested/selected PyTorch device; does not run model smokes.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args()


def _present(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _version(entry: ModuleEntry) -> str | None:
    if not _present(entry.module):
        return None
    dist_name = entry.dist or entry.module
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None


def _device_report(requested: str) -> dict[str, Any]:
    report: dict[str, Any] = {"requested": requested, "torch_present": _present("torch")}
    if not report["torch_present"]:
        report.update({"selected": None, "cuda_available": False, "error": "torch is not importable"})
        return report
    try:
        import torch
    except Exception as exc:  # pragma: no cover - diagnostic path for broken runtimes
        report.update({"selected": None, "cuda_available": False, "error": f"{type(exc).__name__}: {exc}"})
        return report

    cuda_available = bool(torch.cuda.is_available())
    if requested == "cuda" and not cuda_available:
        selected = None
        error = "--device cuda requested, but torch.cuda.is_available() is False"
    else:
        selected = "cuda" if requested == "auto" and cuda_available else ("cpu" if requested == "auto" else requested)
        error = None
    report.update(
        {
            "selected": selected,
            "cuda_available": cuda_available,
            "torch_version": getattr(torch, "__version__", "unknown"),
            "error": error,
        }
    )
    return report


def main() -> int:
    args = _parse_args()
    rows = []
    for entry in MODULES:
        rows.append(
            {
                **asdict(entry),
                "present": _present(entry.module),
                "version": _version(entry),
            }
        )

    missing_required = [row["module"] for row in rows if row["role"] == "required" and not row["present"]]
    device = _device_report(args.device)
    if device.get("error") and args.device == "cuda":
        missing_required.append("cuda-device")

    payload = {
        "status": "failed" if missing_required else "ok",
        "missing_required": missing_required,
        "device": device,
        "modules": rows,
        "policy": (
            "No optional dependency is required unless its feature is selected; "
            "this probe performs no downloads."
        ),
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"optional_dependency_probe {payload['status']}")
        print(
            "device: "
            f"requested={device.get('requested')} selected={device.get('selected')} "
            f"cuda_available={device.get('cuda_available')}"
        )
        if device.get("error"):
            print(f"device_error: {device['error']}")
        print("modules:")
        for row in rows:
            status = "present" if row["present"] else "missing"
            version = f" {row['version']}" if row["version"] else ""
            print(f"  {row['module']:<28} {row['role']:<8} {status}{version} - {row['feature']}")
        if missing_required:
            print("missing required: " + ", ".join(missing_required), file=sys.stderr)
        else:
            missing_optional = [row["module"] for row in rows if row["role"] == "optional" and not row["present"]]
            print("missing optional: " + (", ".join(missing_optional) if missing_optional else "none"))
        print(payload["policy"])

    return 1 if missing_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
