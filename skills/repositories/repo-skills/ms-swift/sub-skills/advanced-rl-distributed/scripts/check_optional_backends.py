#!/usr/bin/env python3
"""Report optional ms-swift advanced backend availability.

The script uses import specs and package metadata by default, so it does not
require GPUs and does not launch training, Ray clusters, vLLM servers, or
Megatron initialization.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import json
import platform
import shutil
import sys
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional


@dataclass
class ModuleStatus:
    key: str
    import_name: str
    package_name: str
    available: bool
    version: Optional[str]
    note: str


@dataclass
class CommandStatus:
    command: str
    available: bool
    path: Optional[str]


MODULES = [
    ("swift", "swift", "ms-swift", "Base ms-swift Python package."),
    ("trl", "trl", "trl", "Required by standard RLHF trainers."),
    ("ray", "ray", "ray", "Required for Ray orchestration."),
    ("megatron-core", "megatron.core", "megatron-core", "Required for Megatron-SWIFT."),
    ("mcore-bridge", "mcore_bridge", "mcore-bridge", "Recommended Megatron-SWIFT bridge."),
    ("transformer-engine", "transformer_engine", "transformer-engine", "Common Megatron CUDA dependency."),
    ("apex", "apex", "apex", "Optional; some fusion paths need it."),
    ("flash-attn", "flash_attn", "flash-attn", "Optional FlashAttention kernels."),
    ("vllm", "vllm", "vllm", "GRPO/GKD rollout and deployment backend."),
    ("lmdeploy", "lmdeploy", "lmdeploy", "Optional sampling/inference backend."),
    ("sglang", "sglang", "sglang", "Optional sampling/inference backend."),
    ("evalscope", "evalscope", "evalscope", "Optional evaluation backend."),
    ("math-verify", "math_verify", "math-verify", "Needed by built-in math accuracy reward."),
    ("deepspeed", "deepspeed", "deepspeed", "Optional distributed optimizer/runtime backend."),
]

COMMANDS = ["swift", "megatron", "ray"]


def version_for(package_name: str, import_name: str) -> Optional[str]:
    candidates = [package_name, package_name.replace("-", "_"), import_name.split(".")[0]]
    for candidate in candidates:
        try:
            return importlib.metadata.version(candidate)
        except importlib.metadata.PackageNotFoundError:
            continue
    return None


def module_available(import_name: str) -> bool:
    try:
        return importlib.util.find_spec(import_name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def collect_modules(import_check: bool = False) -> List[ModuleStatus]:
    statuses: List[ModuleStatus] = []
    for key, import_name, package_name, description in MODULES:
        available = module_available(import_name)
        note = description
        if import_check and available:
            try:
                importlib.import_module(import_name)
                note = f"import ok; {description}"
            except Exception as exc:  # noqa: BLE001 - diagnostic script should report any import failure.
                available = False
                note = f"import failed: {exc.__class__.__name__}: {exc}"
        statuses.append(ModuleStatus(
            key=key,
            import_name=import_name,
            package_name=package_name,
            available=available,
            version=version_for(package_name, import_name),
            note=note,
        ))
    return statuses


def collect_commands() -> List[CommandStatus]:
    statuses = []
    for command in COMMANDS:
        path = shutil.which(command)
        statuses.append(CommandStatus(command=command, available=path is not None, path=path))
    return statuses


def collect_torch() -> Dict[str, object]:
    info: Dict[str, object] = {"available": module_available("torch")}
    if not info["available"]:
        return info
    try:
        import torch

        info.update({
            "version": getattr(torch, "__version__", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "cuda_version": getattr(torch.version, "cuda", None),
        })
    except Exception as exc:  # noqa: BLE001
        info.update({"probe_error": f"{exc.__class__.__name__}: {exc}"})
    return info


def render_table(rows: Iterable[Iterable[object]], headers: List[str]) -> str:
    materialized = [["" if cell is None else str(cell) for cell in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in materialized:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    header_line = "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
    sep_line = "  ".join("-" * width for width in widths)
    row_lines = ["  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)) for row in materialized]
    return "\n".join([header_line, sep_line, *row_lines])


def print_human(modules: List[ModuleStatus], commands: List[CommandStatus], torch_info: Dict[str, object]) -> None:
    print("Python")
    print(f"  executable: {sys.executable}")
    print(f"  version:    {platform.python_version()}")
    print(f"  platform:   {platform.platform()}")
    print()

    print("Console scripts")
    print(render_table(
        ([cmd.command, "yes" if cmd.available else "no", cmd.path or "-"] for cmd in commands),
        ["command", "found", "path"],
    ))
    print()

    print("Python modules")
    print(render_table(
        ([status.key, status.import_name, "yes" if status.available else "no", status.version or "-", status.note]
         for status in modules),
        ["backend", "import", "found", "version", "note"],
    ))
    print()

    print("Torch/CUDA probe")
    for key, value in torch_info.items():
        print(f"  {key}: {value}")

    missing = [status.key for status in modules if not status.available]
    missing_commands = [cmd.command for cmd in commands if not cmd.available]
    if missing or missing_commands:
        print()
        print("Missing optional surfaces")
        if missing_commands:
            print(f"  commands: {', '.join(missing_commands)}")
        if missing:
            print(f"  modules:  {', '.join(missing)}")
        print("  Install only the extras required by the workflow you plan to run.")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--import-check",
        action="store_true",
        help="Actually import available optional modules. Default only checks import specs and metadata.",
    )
    args = parser.parse_args(argv)

    modules = collect_modules(import_check=args.import_check)
    commands = collect_commands()
    torch_info = collect_torch()

    if args.json:
        print(json.dumps({
            "python": {
                "executable": sys.executable,
                "version": platform.python_version(),
                "platform": platform.platform(),
            },
            "commands": [asdict(command) for command in commands],
            "modules": [asdict(module) for module in modules],
            "torch": torch_info,
        }, indent=2, sort_keys=True))
    else:
        print_human(modules, commands, torch_info)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
