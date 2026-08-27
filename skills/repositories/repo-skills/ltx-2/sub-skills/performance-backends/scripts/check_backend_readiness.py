#!/usr/bin/env python3
"""Safely inspect LTX-2 backend readiness.

This script is read-only. It imports torch and a small set of optional modules if
available, prints CUDA/device facts, and reports conservative next steps.
It never builds kernels, downloads models, or runs generation/training.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any

OPTIONAL_PROBES: tuple[str, ...] = (
    "ltx_core",
    "ltx_pipelines",
    "ltx_kernels",
    "ltx_kernels.nvfp4",
    "ltx_kernels.vae",
    "natten",
    "flash_attn_interface",
    "flash_attn.cute",
    "mps_sdpa",
)


@dataclass
class ModuleProbe:
    name: str
    available: bool
    detail: str | None = None


@dataclass
class ReadinessReport:
    python: str
    torch_version: str | None
    cuda_available: bool
    cuda_version: str | None
    device_count: int
    devices: list[dict[str, Any]]
    modules: list[ModuleProbe]
    next_steps: list[str]


def _try_import(name: str) -> ModuleProbe:
    try:
        mod = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - read-only probe
        return ModuleProbe(name=name, available=False, detail=f"{type(exc).__name__}: {exc}")
    detail = getattr(mod, "__version__", None)
    return ModuleProbe(name=name, available=True, detail=str(detail) if detail is not None else None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect CUDA and optional backend readiness without building or downloading anything."
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable summary.")
    return parser


def _empty_report(*, torch_version: str | None, modules: list[ModuleProbe], next_steps: list[str]) -> ReadinessReport:
    return ReadinessReport(
        python=sys.version.split()[0],
        torch_version=torch_version,
        cuda_available=False,
        cuda_version=None,
        device_count=0,
        devices=[],
        modules=modules,
        next_steps=next_steps,
    )


def collect_report() -> ReadinessReport:
    modules = [_try_import(name) for name in OPTIONAL_PROBES]
    torch_probe = _try_import("torch")
    if not torch_probe.available:
        next_steps = [
            "PyTorch is not importable in this environment; install or activate a runtime with torch first.",
            "Without torch, CUDA readiness and optional accelerator checks cannot be completed.",
            "If you only need command help or parser inspection, use a Python environment that can import the package.",
        ]
        return _empty_report(torch_version=None, modules=[torch_probe, *modules], next_steps=next_steps)

    torch = importlib.import_module("torch")
    devices: list[dict[str, Any]] = []
    if torch.cuda.is_available():
        for idx in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(idx)
            devices.append(
                {
                    "index": idx,
                    "name": props.name,
                    "capability": f"{props.major}.{props.minor}",
                    "total_memory_gb": round(props.total_memory / (1024**3), 2),
                }
            )
    next_steps: list[str] = []
    if not torch.cuda.is_available():
        next_steps.append("CUDA is not available; use parser/help inspection or fix the local CUDA wheel/driver stack.")
    else:
        next_steps.append("CUDA runtime is available; you can plan single-GPU inference and compile/offload tradeoffs.")
    if not any(m.name == "ltx_kernels" and m.available for m in modules):
        next_steps.append("Optional kernel backends are absent; treat SP, NVFP4, and Blackwell DSL paths as unavailable.")
    if not any(m.name == "natten" and m.available for m in modules):
        next_steps.append("DiffVAE combined-compile and best-production NA paths will need NATTEN or a fallback mode.")
    if torch.cuda.is_available() and torch.cuda.device_count() > 1:
        next_steps.append("Multi-GPU paths may be possible if the host is Linux/NCCL and the compiled kernels are present.")
    return ReadinessReport(
        python=sys.version.split()[0],
        torch_version=getattr(torch, "__version__", None),
        cuda_available=torch.cuda.is_available(),
        cuda_version=getattr(torch.version, "cuda", None),
        device_count=torch.cuda.device_count() if torch.cuda.is_available() else 0,
        devices=devices,
        modules=[torch_probe, *modules],
        next_steps=next_steps,
    )


def _as_jsonable(report: ReadinessReport) -> dict[str, Any]:
    data = asdict(report)
    data["modules"] = [asdict(m) for m in report.modules]
    return data


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = collect_report()

    if args.json:
        print(json.dumps(_as_jsonable(report), indent=2, sort_keys=True))
        return 0

    print(f"Python: {report.python}")
    print(f"Torch: {report.torch_version}")
    print(f"CUDA available: {report.cuda_available}")
    print(f"CUDA runtime: {report.cuda_version}")
    print(f"CUDA devices: {report.device_count}")
    for device in report.devices:
        print(
            f"  - cuda:{device['index']} {device['name']} "
            f"(sm_{device['capability'].replace('.', '')}, {device['total_memory_gb']} GiB)"
        )
    print("Modules:")
    for mod in report.modules:
        status = "yes" if mod.available else "no"
        detail = f" ({mod.detail})" if mod.detail else ""
        print(f"  - {mod.name}: {status}{detail}")
    print("Next steps:")
    for step in report.next_steps:
        print(f"  - {step}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
