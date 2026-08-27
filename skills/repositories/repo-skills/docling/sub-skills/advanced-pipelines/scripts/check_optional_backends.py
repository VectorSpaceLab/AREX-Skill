#!/usr/bin/env python3
"""Check optional Docling advanced-pipeline backends without loading models.

This script is intentionally read-only. It checks imports, package versions,
platform facts, and common binaries, but it does not instantiate converters,
download model weights, contact remote APIs, or convert documents.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import platform
import shutil
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str
    version: str | None = None


def package_version(package_name: str) -> str | None:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None
    except Exception as exc:  # noqa: BLE001 - report unexpected metadata issues.
        return f"metadata-error: {exc.__class__.__name__}: {exc}"


def check_import(name: str, module_name: str, package_name: str | None = None) -> CheckResult:
    try:
        importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - optional imports may fail for many reasons.
        return CheckResult(
            name=name,
            ok=False,
            detail=f"could not import {module_name}: {exc.__class__.__name__}: {exc}",
            version=package_version(package_name or module_name.split(".")[0]),
        )
    return CheckResult(
        name=name,
        ok=True,
        detail=f"imported {module_name}",
        version=package_version(package_name or module_name.split(".")[0]),
    )


def check_binary(name: str, binary: str) -> CheckResult:
    path = shutil.which(binary)
    if path is None:
        return CheckResult(name=name, ok=False, detail=f"{binary!r} not found on PATH")
    return CheckResult(name=name, ok=True, detail=f"found {binary!r} at {path}")


def check_torch() -> list[CheckResult]:
    result = check_import("torch", "torch")
    checks = [result]
    if not result.ok:
        return checks

    try:
        import torch

        cuda_available = bool(torch.cuda.is_available())
        checks.append(
            CheckResult(
                name="torch-cuda",
                ok=cuda_available,
                detail=(
                    "torch reports CUDA available"
                    if cuda_available
                    else "torch imports, but CUDA is not available"
                ),
                version=getattr(torch.version, "cuda", None),
            )
        )
        mps_available = bool(
            getattr(getattr(torch.backends, "mps", None), "is_available", lambda: False)()
        )
        checks.append(
            CheckResult(
                name="torch-mps",
                ok=mps_available,
                detail=(
                    "torch reports MPS available"
                    if mps_available
                    else "torch imports, but MPS is not available"
                ),
            )
        )
    except Exception as exc:  # noqa: BLE001 - keep preflight non-fatal.
        checks.append(
            CheckResult(
                name="torch-runtime",
                ok=False,
                detail=f"torch imported but runtime query failed: {exc.__class__.__name__}: {exc}",
            )
        )
    return checks


def check_docling_symbols() -> list[CheckResult]:
    checks = [
        check_import("docling", "docling"),
        check_import("document-converter", "docling.document_converter", "docling"),
        check_import("vlm-pipeline", "docling.pipeline.vlm_pipeline", "docling"),
        check_import("asr-pipeline", "docling.pipeline.asr_pipeline", "docling"),
        check_import("asr-model-specs", "docling.datamodel.asr_model_specs", "docling"),
        check_import("vlm-engine-options", "docling.datamodel.vlm_engine_options", "docling"),
    ]

    try:
        from docling.datamodel.pipeline_options import (  # noqa: PLC0415
            AsrPipelineOptions,
            PdfPipelineOptions,
            VlmConvertOptions,
            VlmPipelineOptions,
        )

        symbols = [
            AsrPipelineOptions.__name__,
            PdfPipelineOptions.__name__,
            VlmConvertOptions.__name__,
            VlmPipelineOptions.__name__,
        ]
        checks.append(
            CheckResult(
                name="pipeline-option-symbols",
                ok=True,
                detail="available: " + ", ".join(symbols),
                version=package_version("docling"),
            )
        )
    except Exception as exc:  # noqa: BLE001 - import failures are the signal.
        checks.append(
            CheckResult(
                name="pipeline-option-symbols",
                ok=False,
                detail=f"could not import advanced option classes: {exc.__class__.__name__}: {exc}",
                version=package_version("docling"),
            )
        )

    return checks


def collect_checks() -> dict[str, Any]:
    system = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "is_apple_silicon": platform.system() == "Darwin" and platform.machine() == "arm64",
    }

    checks: list[CheckResult] = []
    checks.extend(check_docling_symbols())
    checks.extend(check_torch())
    checks.extend(
        [
            check_import("torchvision", "torchvision"),
            check_import("transformers", "transformers"),
            check_import("mlx", "mlx"),
            check_import("mlx-vlm", "mlx_vlm", "mlx-vlm"),
            check_import("openai-whisper", "whisper", "openai-whisper"),
            check_import("mlx-whisper", "mlx_whisper", "mlx-whisper"),
            check_import("requests", "requests"),
            check_binary("ffmpeg", "ffmpeg"),
        ]
    )

    return {
        "system": system,
        "checks": [asdict(check) for check in checks],
        "summary": {
            "ok": sum(1 for check in checks if check.ok),
            "failed": sum(1 for check in checks if not check.ok),
        },
        "notes": [
            "No models were loaded or downloaded.",
            "No converters were instantiated.",
            "No remote endpoints were contacted.",
        ],
    }


def print_text(report: dict[str, Any]) -> None:
    system = report["system"]
    print("# Docling advanced backend preflight")
    print(f"Python: {system['python']}")
    print(f"Platform: {system['platform']}")
    print(f"Machine: {system['machine']}")
    print(f"Apple Silicon: {system['is_apple_silicon']}")
    print()

    for check in report["checks"]:
        marker = "OK" if check["ok"] else "MISSING"
        version = f" (version: {check['version']})" if check.get("version") else ""
        print(f"[{marker}] {check['name']}{version}")
        print(f"  {check['detail']}")

    summary = report["summary"]
    print()
    print(f"Summary: {summary['ok']} ok, {summary['failed']} missing or unavailable")
    print("Safety: " + "; ".join(report["notes"]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--as-json",
        action="store_true",
        help="Print machine-readable JSON instead of text.",
    )
    args = parser.parse_args()

    report = collect_checks()
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
