#!/usr/bin/env python3
"""Validate Lightning accelerator/strategy/precision configuration syntax safely.

This script imports public Lightning packages and attempts to construct a Trainer
or Fabric object with the requested settings. It never calls fit(), launch(),
or any distributed worker-spawning API.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Any


_PRECISION_CHOICES = [
    "64-true",
    "32-true",
    "16-mixed",
    "bf16-mixed",
    "16-true",
    "bf16-true",
    "transformer-engine",
    "transformer-engine-float16",
]

_STRATEGY_ALIASES = {
    "auto",
    "ddp",
    "ddp_spawn",
    "fsdp",
    "deepspeed",
    "deepspeed_stage_1",
    "deepspeed_stage_2",
    "deepspeed_stage_2_offload",
    "deepspeed_stage_3",
    "deepspeed_stage_3_offload",
    "single_device",
}


class CheckError(RuntimeError):
    """Configuration check failed with actionable guidance."""


def _parse_devices(raw: str) -> Any:
    value = raw.strip()
    if value in {"auto", "-1"}:
        return value if value == "auto" else -1
    if "," in value:
        return [int(part.strip()) for part in value.split(",") if part.strip()]
    try:
        return int(value)
    except ValueError:
        return value


def _import_attr(module_name: str, attr: str) -> Any:
    try:
        module = importlib.import_module(module_name)
    except Exception as ex:
        raise CheckError(
            f"Could not import {module_name!r}: {type(ex).__name__}: {ex}. "
            "Install Lightning in the active Python environment before validating configuration."
        ) from ex
    try:
        return getattr(module, attr)
    except AttributeError as ex:
        raise CheckError(f"Imported {module_name!r}, but it has no attribute {attr!r}.") from ex


def _strategy_object(mode: str, strategy: str, kwargs: dict[str, Any]) -> Any:
    if strategy in _STRATEGY_ALIASES and not kwargs:
        return strategy

    strategy_modules = {
        "trainer": "lightning.pytorch.strategies",
        "fabric": "lightning.fabric.strategies",
    }
    class_names = {
        "ddp": "DDPStrategy",
        "fsdp": "FSDPStrategy",
        "deepspeed": "DeepSpeedStrategy",
        "model_parallel": "ModelParallelStrategy",
        "single_device": "SingleDeviceStrategy",
    }
    normalized = strategy.replace("-", "_")
    if normalized not in class_names:
        if kwargs:
            raise CheckError(f"Strategy kwargs were provided, but {strategy!r} is not a supported strategy class key.")
        return strategy

    cls = _import_attr(strategy_modules[mode], class_names[normalized])
    try:
        return cls(**kwargs)
    except Exception as ex:
        raise CheckError(
            f"Could not instantiate {class_names[normalized]} with {kwargs}: {type(ex).__name__}: {ex}"
        ) from ex


def _json_kwargs(items: list[str]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise CheckError(f"Invalid --strategy-kwarg {item!r}; expected key=value with a JSON value when possible.")
        key, raw_value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise CheckError("Strategy kwarg key cannot be empty.")
        try:
            values[key] = json.loads(raw_value)
        except json.JSONDecodeError:
            values[key] = raw_value
    return values


def _hardware_notes(accelerator: str, devices: Any, strategy: str, precision: str) -> list[str]:
    notes: list[str] = []
    if accelerator in {"cuda", "gpu", "auto"}:
        try:
            torch = importlib.import_module("torch")
            cuda_count = torch.cuda.device_count() if hasattr(torch, "cuda") else 0
            cuda_available = bool(torch.cuda.is_available()) if hasattr(torch, "cuda") else False
            notes.append(f"torch.cuda.is_available={cuda_available}; torch.cuda.device_count={cuda_count}")
            if accelerator == "cuda" and not cuda_available:
                notes.append("requested accelerator='cuda', but CUDA is not visible in this Python process")
            if isinstance(devices, int) and devices > max(cuda_count, 0) and accelerator == "cuda":
                notes.append("requested CUDA devices exceed visible CUDA device count")
        except Exception as ex:
            notes.append(f"could not inspect torch CUDA state: {type(ex).__name__}: {ex}")
    if accelerator == "cpu" and precision == "16-mixed":
        notes.append("Lightning docs list 16-mixed as GPU-oriented; prefer bf16-mixed or 32-true on CPU")
    if strategy.startswith("deepspeed"):
        try:
            importlib.import_module("deepspeed")
            notes.append("deepspeed import succeeded")
        except Exception as ex:
            notes.append(f"deepspeed import failed: {type(ex).__name__}: {ex}")
    if precision.startswith("transformer-engine"):
        try:
            importlib.import_module("transformer_engine")
            notes.append("transformer_engine import succeeded")
        except Exception as ex:
            notes.append(f"transformer_engine import failed: {type(ex).__name__}: {ex}")
    return notes


def _construct(args: argparse.Namespace) -> Any:
    devices = _parse_devices(args.devices)
    strategy_kwargs = _json_kwargs(args.strategy_kwarg)
    strategy = _strategy_object(args.mode, args.strategy, strategy_kwargs)

    common = {
        "accelerator": args.accelerator,
        "devices": devices,
        "strategy": strategy,
        "precision": args.precision,
    }
    if args.mode == "trainer":
        Trainer = _import_attr("lightning.pytorch", "Trainer")
        kwargs = dict(common)
        kwargs.update({"num_nodes": args.num_nodes, "logger": False, "enable_checkpointing": False})
        try:
            return Trainer(**kwargs), devices
        except Exception as ex:
            raise CheckError(f"Trainer construction failed: {type(ex).__name__}: {ex}") from ex

    Fabric = _import_attr("lightning", "Fabric")
    kwargs = dict(common)
    kwargs.update({"num_nodes": args.num_nodes})
    try:
        return Fabric(**kwargs), devices
    except Exception as ex:
        raise CheckError(f"Fabric construction failed: {type(ex).__name__}: {ex}") from ex


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["trainer", "fabric"], default="trainer", help="Lightning frontend to construct")
    parser.add_argument("--accelerator", default="auto", help="Lightning accelerator value, for example cpu, cuda, gpu, mps, tpu, auto")
    parser.add_argument("--devices", default="auto", help="Device count/list string, for example 1, 4, auto, -1, or 0,1")
    parser.add_argument("--num-nodes", type=int, default=1, help="Number of nodes for distributed strategies")
    parser.add_argument("--strategy", default="auto", help="Strategy alias or class key: auto, ddp, fsdp, deepspeed, model_parallel, single_device")
    parser.add_argument("--precision", choices=_PRECISION_CHOICES, default="32-true", help="Lightning precision setting")
    parser.add_argument(
        "--strategy-kwarg",
        action="append",
        default=[],
        metavar="KEY=JSON",
        help="Instantiate a strategy class with an extra kwarg, e.g. static_graph=true or stage=2",
    )
    parser.add_argument("--dry-run-summary", action="store_true", help="Print a JSON-like summary of the requested configuration")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        constructed, devices = _construct(args)
    except CheckError as ex:
        print(f"CONFIG_CHECK_FAILED: {ex}", file=sys.stderr)
        return 2

    notes = _hardware_notes(args.accelerator, devices, args.strategy, args.precision)
    print("CONFIG_CHECK_OK")
    print(f"mode={args.mode}")
    print(f"constructed={constructed.__class__.__module__}.{constructed.__class__.__name__}")
    print(f"accelerator={args.accelerator}")
    print(f"devices={devices!r}")
    print(f"num_nodes={args.num_nodes}")
    print(f"strategy={args.strategy}")
    print(f"precision={args.precision}")
    if notes:
        print("notes:")
        for note in notes:
            print(f"- {note}")
    print("validation_level=import-and-constructor-only; no fit/launch/distributed workers were started")
    if args.dry_run_summary:
        print(
            "summary="
            + json.dumps(
                {
                    "mode": args.mode,
                    "accelerator": args.accelerator,
                    "devices": devices,
                    "num_nodes": args.num_nodes,
                    "strategy": args.strategy,
                    "precision": args.precision,
                    "notes": notes,
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
