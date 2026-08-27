#!/usr/bin/env python3
"""Report torchtune training/RLHF runtime health without launching training.

The checker is intentionally side-effect-light: it imports packages, reads version
and device availability flags, and avoids distributed initialization, Ray/vLLM
startup, checkpoint loading, downloads, and training.
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
from dataclasses import asdict, dataclass
from importlib import metadata
from typing import Any


@dataclass
class Probe:
    name: str
    status: str
    detail: str = ""


def _probe_import(module_name: str, *, attr: str | None = None) -> Probe:
    try:
        module = importlib.import_module(module_name)
        if attr is not None:
            getattr(module, attr)
        version = getattr(module, "__version__", None)
        detail = f"version={version}" if version else "import ok"
        return Probe(module_name if attr is None else f"{module_name}.{attr}", "ok", detail)
    except Exception as exc:  # noqa: BLE001 - diagnostics should report import-time failures.
        return Probe(
            module_name if attr is None else f"{module_name}.{attr}",
            "error",
            f"{type(exc).__name__}: {exc}",
        )


def _probe_distribution(distribution_name: str) -> Probe:
    try:
        return Probe(
            f"distribution:{distribution_name}",
            "ok",
            f"version={metadata.version(distribution_name)}",
        )
    except metadata.PackageNotFoundError:
        return Probe(f"distribution:{distribution_name}", "missing", "not installed")
    except Exception as exc:  # noqa: BLE001
        return Probe(
            f"distribution:{distribution_name}",
            "error",
            f"{type(exc).__name__}: {exc}",
        )


def _torch_summary() -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "detail": f"{type(exc).__name__}: {exc}"}

    summary: dict[str, Any] = {
        "status": "ok",
        "version": getattr(torch, "__version__", "unknown"),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": 0,
        "cuda_version": getattr(torch.version, "cuda", None),
        "distributed_available": bool(torch.distributed.is_available()),
        "distributed_initialized": bool(
            torch.distributed.is_available() and torch.distributed.is_initialized()
        ),
    }

    if torch.cuda.is_available():
        try:
            summary["cuda_device_count"] = torch.cuda.device_count()
            summary["cuda_devices"] = [
                torch.cuda.get_device_name(index)
                for index in range(torch.cuda.device_count())
            ]
            summary["cuda_bf16_supported"] = bool(torch.cuda.is_bf16_supported())
        except Exception as exc:  # noqa: BLE001
            summary["cuda_detail_error"] = f"{type(exc).__name__}: {exc}"

    try:
        summary["mps_available"] = bool(torch.backends.mps.is_available())
        summary["mps_built"] = bool(torch.backends.mps.is_built())
    except Exception:
        summary["mps_available"] = False
        summary["mps_built"] = False

    try:
        summary["xpu_available"] = bool(torch.xpu.is_available())
    except Exception:
        summary["xpu_available"] = False

    return summary


def collect_report() -> dict[str, Any]:
    probes: list[Probe] = []
    probes.append(_probe_distribution("torchtune"))
    probes.append(_probe_import("torch"))
    probes.append(_probe_import("torchao"))
    probes.append(_probe_import("torchtune"))
    probes.append(_probe_import("torchtune.training"))
    probes.append(_probe_import("torchtune.rlhf"))
    probes.append(_probe_import("torchtune.rlhf", attr="truncate_sequence_at_first_stop_token"))
    probes.append(_probe_import("torchtune.rlhf.loss"))
    probes.append(_probe_import("torchtune.rlhf.loss", attr="DPOLoss"))
    probes.append(_probe_import("torchtune.dev.grpo"))
    probes.append(_probe_import("torchtune.dev.rl"))

    optional_async_modules = ["ray", "vllm", "torchrl", "tensordict"]
    async_probes = [_probe_import(name) for name in optional_async_modules]

    return {
        "python": {
            "version": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "executable_basename": sys.executable.rsplit("/", 1)[-1].rsplit("\\", 1)[-1],
        },
        "torch": _torch_summary(),
        "imports": [asdict(probe) for probe in probes],
        "async_rl_optional": [asdict(probe) for probe in async_probes],
        "side_effects": [
            "no distributed initialization",
            "no checkpoint loading",
            "no Ray or vLLM startup",
            "no training or downloads",
        ],
    }


def _print_text(report: dict[str, Any]) -> None:
    python = report["python"]
    print("Python:")
    print(f"  version: {python['version']} ({python['implementation']})")
    print(f"  platform: {python['platform']}")
    print(f"  executable basename: {python['executable_basename']}")

    torch_summary = report["torch"]
    print("\nTorch:")
    for key, value in torch_summary.items():
        print(f"  {key}: {value}")

    print("\nCore imports:")
    for probe in report["imports"]:
        print(f"  [{probe['status']}] {probe['name']}: {probe['detail']}")

    print("\nAsync RL optional imports:")
    for probe in report["async_rl_optional"]:
        print(f"  [{probe['status']}] {probe['name']}: {probe['detail']}")

    print("\nSide effects avoided:")
    for item in report["side_effects"]:
        print(f"  - {item}")

    loss_probe = next(
        (
            probe
            for probe in report["imports"]
            if probe["name"] == "torchtune.rlhf.loss" and probe["status"] != "ok"
        ),
        None,
    )
    known_dpo_markers = ("TypeVar", "dataclass", "Optional", "Tuple")
    if loss_probe is not None and any(
        marker in loss_probe["detail"] for marker in known_dpo_markers
    ):
        print("\nNote:")
        print(
            "  torchtune.rlhf.loss failed with a known current-code DPO loss "
            "import gap; public torchtune.rlhf utilities may still be usable."
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Report torchtune training/RLHF runtime health without initializing "
            "distributed process groups or launching training."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = collect_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
