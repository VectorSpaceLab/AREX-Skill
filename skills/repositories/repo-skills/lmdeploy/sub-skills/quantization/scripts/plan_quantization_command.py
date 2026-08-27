#!/usr/bin/env python3
"""Plan LMDeploy quantization commands without executing them."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import dataclass, field
from typing import Iterable

CALIBRATION_DATASETS = (
    "wikitext2",
    "c4",
    "pileval",
    "gsm8k",
    "neuralmagic_calibration",
    "open-platypus",
    "openwebtext",
)

KV_POLICY_ALIASES = {
    "none": 0,
    "0": 0,
    "int4": 4,
    "4": 4,
    "int8": 8,
    "8": 8,
    "fp8": 16,
    "fp8_e4m3": 16,
    "16": 16,
    "fp8_e5m2": 17,
    "17": 17,
    "turbo_quant": 42,
    "turboquant": 42,
    "42": 42,
}

QUANT_DTYPE_BITS = {
    "int8": 8,
    "fp8": 8,
    "float8_e4m3fn": 8,
    "float8_e5m2": 8,
}


@dataclass
class CommandPlan:
    purpose: str
    args: list[str]
    notes: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, object]:
        return {
            "purpose": self.purpose,
            "args": self.args,
            "shell": shlex.join(self.args),
            "notes": self.notes,
        }


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def kv_policy(value: str) -> int:
    normalized = value.lower()
    if normalized not in KV_POLICY_ALIASES:
        allowed = ", ".join(sorted(KV_POLICY_ALIASES))
        raise argparse.ArgumentTypeError(f"invalid quant policy {value!r}; use one of: {allowed}")
    return KV_POLICY_ALIASES[normalized]


def extend_optional(command: list[str], flag: str, value: object | None) -> None:
    if value is not None:
        command.extend([flag, str(value)])


def extend_bool(command: list[str], flag: str, enabled: bool) -> None:
    if enabled:
        command.append(flag)


def add_common_calibration_args(parser: argparse.ArgumentParser, allow_zero_samples: bool) -> None:
    sample_type = nonnegative_int if allow_zero_samples else positive_int
    parser.add_argument("--calib-dataset", choices=CALIBRATION_DATASETS, default="wikitext2")
    parser.add_argument("--calib-samples", type=sample_type, default=128)
    parser.add_argument("--calib-seqlen", type=positive_int, default=2048)
    parser.add_argument("--batch-size", type=positive_int, default=1)
    parser.add_argument("--dtype", choices=("auto", "float16", "bfloat16"), default="auto")
    parser.add_argument("--trust-remote-code", action="store_true")


def add_remote_model_args(parser: argparse.ArgumentParser, include_download_dir: bool) -> None:
    parser.add_argument("--revision")
    if include_download_dir:
        parser.add_argument("--download-dir")


def add_handoff_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--include-handoff", action="store_true", help="also print chat and api_server load commands")
    parser.add_argument("--server-port", type=positive_int, default=23333)


def base_lite_command(subcommand: str, args: argparse.Namespace) -> list[str]:
    command = ["lmdeploy", "lite", subcommand, args.model]
    extend_optional(command, "--work-dir", args.work_dir)
    extend_optional(command, "--calib-dataset", args.calib_dataset)
    extend_optional(command, "--calib-samples", args.calib_samples)
    extend_optional(command, "--calib-seqlen", args.calib_seqlen)
    extend_optional(command, "--batch-size", args.batch_size)
    extend_optional(command, "--dtype", args.dtype)
    extend_bool(command, "--trust-remote-code", args.trust_remote_code)
    return command


def add_awq_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("awq", help="plan lmdeploy lite auto_awq")
    parser.add_argument("--model", required=True)
    parser.add_argument("--work-dir", required=True)
    add_common_calibration_args(parser, allow_zero_samples=True)
    add_remote_model_args(parser, include_download_dir=True)
    parser.add_argument("--device", choices=("cuda", "npu"), default="cuda")
    parser.add_argument("--w-bits", type=positive_int, default=4)
    parser.add_argument("--w-group-size", type=positive_int, default=128)
    parser.add_argument("--w-sym", action="store_true")
    parser.add_argument("--search-scale", action="store_true")
    add_handoff_args(parser)
    parser.set_defaults(builder=build_awq_plan)


def add_gptq_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("gptq", help="plan lmdeploy lite auto_gptq")
    parser.add_argument("--model", required=True)
    parser.add_argument("--work-dir", required=True)
    add_common_calibration_args(parser, allow_zero_samples=False)
    add_remote_model_args(parser, include_download_dir=False)
    parser.add_argument("--w-bits", type=positive_int, default=4)
    parser.add_argument("--w-group-size", type=positive_int, default=128)
    add_handoff_args(parser)
    parser.set_defaults(builder=build_gptq_plan)


def add_calibrate_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("calibrate", help="plan lmdeploy lite calibrate")
    parser.add_argument("--model", required=True)
    parser.add_argument("--work-dir", required=True)
    add_common_calibration_args(parser, allow_zero_samples=False)
    parser.add_argument("--device", choices=("cuda", "npu"), default="cuda")
    parser.add_argument("--search-scale", action="store_true")
    parser.set_defaults(builder=build_calibrate_plan)


def add_smooth_quant_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("smooth-quant", help="plan lmdeploy lite smooth_quant")
    parser.add_argument("--model", required=True)
    parser.add_argument("--work-dir", required=True)
    add_common_calibration_args(parser, allow_zero_samples=False)
    add_remote_model_args(parser, include_download_dir=True)
    parser.add_argument("--device", choices=("cuda", "npu"), default="cuda")
    parser.add_argument("--w-bits", type=positive_int, default=8)
    parser.add_argument("--quant-dtype", choices=tuple(QUANT_DTYPE_BITS), default="int8")
    parser.add_argument("--search-scale", action="store_true")
    add_handoff_args(parser)
    parser.set_defaults(builder=build_smooth_quant_plan)


def add_kv_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("kv", help="plan online KV-cache quantization load commands")
    parser.add_argument("--model", required=True)
    parser.add_argument("--backend", choices=("pytorch", "turbomind"), default="turbomind")
    parser.add_argument("--quant-policy", type=kv_policy, required=True)
    parser.add_argument("--device", choices=("cuda", "ascend", "maca", "camb"), default="cuda")
    parser.add_argument("--mode", choices=("chat", "serve", "both"), default="both")
    parser.add_argument("--server-port", type=positive_int, default=23333)
    parser.set_defaults(builder=build_kv_plan)


def build_awq_plan(args: argparse.Namespace) -> list[CommandPlan]:
    command = base_lite_command("auto_awq", args)
    extend_optional(command, "--device", args.device)
    extend_optional(command, "--w-bits", args.w_bits)
    extend_optional(command, "--w-group-size", args.w_group_size)
    extend_optional(command, "--revision", args.revision)
    extend_optional(command, "--download-dir", args.download_dir)
    extend_bool(command, "--w-sym", args.w_sym)
    extend_bool(command, "--search-scale", args.search_scale)
    notes = ["AWQ handoff should use --model-format awq when loading with TurboMind."]
    if args.w_bits != 4:
        notes.append("LMDeploy documentation focuses on 4-bit AWQ/GPTQ inference; validate non-4-bit output before serving.")
    plans = [CommandPlan("create AWQ quantized artifact", command, notes)]
    if args.include_handoff:
        plans.extend(quantized_handoff(args.work_dir, "turbomind", "awq", args.server_port))
    return plans


def build_gptq_plan(args: argparse.Namespace) -> list[CommandPlan]:
    command = base_lite_command("auto_gptq", args)
    extend_optional(command, "--w-bits", args.w_bits)
    extend_optional(command, "--w-group-size", args.w_group_size)
    extend_optional(command, "--revision", args.revision)
    notes = ["Requires auto-gptq to be installed.", "GPTQ handoff should use --model-format gptq, not awq."]
    if args.w_bits != 4:
        notes.append("LMDeploy documentation focuses on 4-bit AWQ/GPTQ inference; validate non-4-bit output before serving.")
    plans = [CommandPlan("create GPTQ quantized artifact", command, notes)]
    if args.include_handoff:
        plans.extend(quantized_handoff(args.work_dir, "turbomind", "gptq", args.server_port))
    return plans


def build_calibrate_plan(args: argparse.Namespace) -> list[CommandPlan]:
    command = base_lite_command("calibrate", args)
    extend_optional(command, "--device", args.device)
    extend_bool(command, "--search-scale", args.search_scale)
    return [CommandPlan("collect calibration statistics", command, ["This creates calibration stats, not a final quantized model."])]


def build_smooth_quant_plan(args: argparse.Namespace) -> list[CommandPlan]:
    expected_bits = QUANT_DTYPE_BITS[args.quant_dtype]
    if args.w_bits != expected_bits:
        raise ValueError(f"smooth_quant --w-bits {args.w_bits} is incompatible with --quant-dtype {args.quant_dtype}; use {expected_bits}")
    command = base_lite_command("smooth_quant", args)
    extend_optional(command, "--device", args.device)
    extend_optional(command, "--quant-dtype", args.quant_dtype)
    extend_optional(command, "--w-bits", args.w_bits)
    extend_optional(command, "--revision", args.revision)
    extend_optional(command, "--download-dir", args.download_dir)
    extend_bool(command, "--search-scale", args.search_scale)
    notes = ["SmoothQuant INT8/FP8 artifacts are documented with PyTorch backend loading."]
    plans = [CommandPlan("create SmoothQuant quantized artifact", command, notes)]
    if args.include_handoff:
        plans.extend(quantized_handoff(args.work_dir, "pytorch", None, args.server_port))
    return plans


def build_kv_plan(args: argparse.Namespace) -> list[CommandPlan]:
    if args.backend == "turbomind" and args.quant_policy in (16, 17):
        raise ValueError("TurboMind rejects FP8 KV-cache policies 16 and 17; use --backend pytorch")
    if args.backend == "turbomind" and args.quant_policy == 42:
        raise ValueError("TurboQuant policy 42 is documented as PyTorch-only; use --backend pytorch")
    if args.backend == "pytorch" and args.quant_policy > 0 and args.device not in ("cuda", "ascend"):
        raise ValueError("PyTorch KV-cache quantization requires --device cuda or ascend")

    plans: list[CommandPlan] = []
    if args.mode in ("chat", "both"):
        plans.append(CommandPlan("chat with online KV-cache quantization", [
            "lmdeploy",
            "chat",
            args.model,
            "--backend",
            args.backend,
            "--quant-policy",
            str(args.quant_policy),
        ]))
    if args.mode in ("serve", "both"):
        plans.append(CommandPlan("serve with online KV-cache quantization", [
            "lmdeploy",
            "serve",
            "api_server",
            args.model,
            "--backend",
            args.backend,
            "--quant-policy",
            str(args.quant_policy),
            "--server-port",
            str(args.server_port),
        ]))
    if args.quant_policy == 42:
        for plan in plans:
            plan.notes.append("TurboQuant is PyTorch-only and does not support speculative decoding or MLA models.")
    return plans


def quantized_handoff(work_dir: str, backend: str, model_format: str | None, server_port: int) -> list[CommandPlan]:
    chat_command = ["lmdeploy", "chat", work_dir, "--backend", backend]
    serve_command = ["lmdeploy", "serve", "api_server", work_dir, "--backend", backend, "--server-port", str(server_port)]
    if model_format:
        chat_command.extend(["--model-format", model_format])
        serve_command.extend(["--model-format", model_format])
    return [
        CommandPlan("chat smoke test for quantized artifact", chat_command),
        CommandPlan("api_server smoke test for quantized artifact", serve_command),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Construct safe LMDeploy quantization commands without running quantization."
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_awq_parser(subparsers)
    add_gptq_parser(subparsers)
    add_calibrate_parser(subparsers)
    add_smooth_quant_parser(subparsers)
    add_kv_parser(subparsers)
    return parser


def emit_text(plans: Iterable[CommandPlan]) -> None:
    for index, plan in enumerate(plans, start=1):
        print(f"[{index}] {plan.purpose}")
        print(shlex.join(plan.args))
        for note in plan.notes:
            print(f"note: {note}")
        print()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        plans = args.builder(args)
    except ValueError as error:
        parser.error(str(error))
    if args.format == "json":
        print(json.dumps([plan.to_payload() for plan in plans], indent=2))
    else:
        emit_text(plans)
    return 0


if __name__ == "__main__":
    sys.exit(main())
