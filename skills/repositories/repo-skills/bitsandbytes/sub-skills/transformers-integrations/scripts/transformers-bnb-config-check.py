#!/usr/bin/env python3
"""Validate Hugging Face bitsandbytes config construction without model downloads."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ImportStatus:
    name: str
    ok: bool
    detail: str


def check_import(module_name: str) -> ImportStatus:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report optional dependency import failures verbatim.
        return ImportStatus(module_name, False, f"{type(exc).__name__}: {exc}")
    version = getattr(module, "__version__", "unknown")
    return ImportStatus(module_name, True, str(version))


def torch_dtype(torch_module: Any, name: str) -> Any:
    try:
        return getattr(torch_module, name)
    except AttributeError as exc:
        raise SystemExit(f"torch has no dtype named {name!r}") from exc


def config_to_dict(config: Any) -> dict[str, Any]:
    if hasattr(config, "to_dict"):
        raw = config.to_dict()
    else:
        raw = dict(vars(config))
    return {key: str(value) for key, value in raw.items() if key.startswith(("load_in_", "bnb_", "llm_int8"))}


def build_config(args: argparse.Namespace, torch_module: Any, bitsandbytes_config_cls: Any) -> Any:
    if args.mode == "8bit":
        return bitsandbytes_config_cls(
            load_in_8bit=True,
            llm_int8_threshold=args.llm_int8_threshold,
            llm_int8_enable_fp32_cpu_offload=args.fp32_cpu_offload,
        )

    compute_dtype = torch_dtype(torch_module, args.compute_dtype)
    common_4bit = {
        "load_in_4bit": True,
        "bnb_4bit_quant_type": args.quant_type,
        "bnb_4bit_compute_dtype": compute_dtype,
        "bnb_4bit_use_double_quant": args.double_quant,
    }
    if args.quant_storage:
        common_4bit["bnb_4bit_quant_storage"] = torch_dtype(torch_module, args.quant_storage)
    return bitsandbytes_config_cls(**common_4bit)


def snippet(args: argparse.Namespace) -> str:
    if args.mode == "8bit":
        offload_line = ",\n    llm_int8_enable_fp32_cpu_offload=True" if args.fp32_cpu_offload else ""
        return (
            "from transformers import BitsAndBytesConfig\n\n"
            "quantization_config = BitsAndBytesConfig(\n"
            "    load_in_8bit=True,\n"
            f"    llm_int8_threshold={args.llm_int8_threshold}{offload_line}\n"
            ")\n"
        )

    lines = [
        "import torch",
        "from transformers import BitsAndBytesConfig",
        "",
        "quantization_config = BitsAndBytesConfig(",
        "    load_in_4bit=True,",
        f"    bnb_4bit_quant_type={args.quant_type!r},",
        f"    bnb_4bit_compute_dtype=torch.{args.compute_dtype},",
        f"    bnb_4bit_use_double_quant={args.double_quant},",
    ]
    if args.quant_storage:
        lines.append(f"    bnb_4bit_quant_storage=torch.{args.quant_storage},")
    lines.append(")")
    if args.mode == "qlora":
        lines.extend(
            [
                "",
                "# PEFT training flow after model load:",
                "# model = prepare_model_for_kbit_training(model)",
                "# peft_config = LoraConfig(target_modules='all-linear', task_type='CAUSAL_LM', ...)",
                "# model = get_peft_model(model, peft_config)",
            ]
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Construct Transformers BitsAndBytesConfig snippets without downloading models.",
    )
    parser.add_argument("--mode", choices=("8bit", "4bit", "qlora"), default="4bit")
    parser.add_argument("--compute-dtype", default="bfloat16", help="torch dtype name for 4-bit compute")
    parser.add_argument("--quant-type", choices=("nf4", "fp4"), default="nf4")
    parser.add_argument("--double-quant", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--quant-storage", default=None, help="optional torch dtype name for FSDP quant storage")
    parser.add_argument("--llm-int8-threshold", type=float, default=6.0)
    parser.add_argument("--fp32-cpu-offload", action="store_true")
    parser.add_argument("--require-peft", action="store_true", help="fail if peft is not importable")
    parser.add_argument("--require-accelerate", action="store_true", help="fail if accelerate is not importable")
    parser.add_argument("--json", action="store_true", help="print machine-readable status")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    required = ["torch", "transformers", "bitsandbytes"]
    optional = ["accelerate"]
    if args.mode == "qlora" or args.require_peft:
        optional.append("peft")
    statuses = {status.name: status for status in [check_import(name) for name in required + optional]}

    failures = [status for name, status in statuses.items() if name in required and not status.ok]
    if args.require_peft and not statuses.get("peft", ImportStatus("peft", False, "not checked")).ok:
        failures.append(statuses["peft"])
    if args.require_accelerate and not statuses.get("accelerate", ImportStatus("accelerate", False, "not checked")).ok:
        failures.append(statuses["accelerate"])

    output: dict[str, Any] = {
        "mode": args.mode,
        "imports": {name: {"ok": status.ok, "detail": status.detail} for name, status in statuses.items()},
        "downloads_model": False,
        "loads_model_weights": False,
        "snippet": snippet(args),
    }

    if not failures:
        torch_module = importlib.import_module("torch")
        transformers_module = importlib.import_module("transformers")
        config_cls = getattr(transformers_module, "BitsAndBytesConfig", None)
        if config_cls is None:
            failures.append(ImportStatus("transformers.BitsAndBytesConfig", False, "attribute missing"))
        else:
            config = build_config(args, torch_module, config_cls)
            output["config_class"] = f"{config.__class__.__module__}.{config.__class__.__name__}"
            output["config"] = config_to_dict(config)

    if args.json:
        output["ok"] = not failures
        output["failures"] = [{"name": failure.name, "detail": failure.detail} for failure in failures]
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        for name, status in output["imports"].items():
            marker = "OK" if status["ok"] else "MISSING"
            print(f"{marker}: {name} ({status['detail']})")
        print("\nNo model download or weight loading is performed by this script.\n")
        if "config" in output:
            print("Constructed config fields:")
            for key, value in sorted(output["config"].items()):
                print(f"  {key}: {value}")
        print("\nSafe snippet:\n")
        print(output["snippet"])
        if failures:
            print("Failures:", file=sys.stderr)
            for failure in failures:
                print(f"  {failure.name}: {failure.detail}", file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
