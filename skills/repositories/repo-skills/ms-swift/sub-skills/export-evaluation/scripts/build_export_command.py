#!/usr/bin/env python3
"""Build safe ms-swift export command skeletons.

This helper does not run ms-swift. It prints shell commands with required flags
for common merge, quantize, push, and cached-dataset export plans.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable, List


QUANT_METHODS = {"awq", "gptq", "gptq_v2", "bnb", "fp8"}
CALIBRATION_METHODS = {"awq", "gptq", "gptq_v2"}
BIT_REQUIRED_METHODS = {"awq", "gptq", "gptq_v2", "bnb"}


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def bool_value(value: bool) -> str:
    return "true" if value else "false"


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cuda-visible-devices", help="Optional CUDA_VISIBLE_DEVICES value to prefix.")
    parser.add_argument("--dry-run", action="store_true", help="Accepted for compatibility; commands are never run.")


def prefix(parts: List[str], cuda_visible_devices: str | None) -> List[str]:
    if cuda_visible_devices:
        return [f"CUDA_VISIBLE_DEVICES={cuda_visible_devices}"] + parts
    return parts


def command_lines(parts: List[str]) -> str:
    assignments = []
    command_start = 0
    for index, part in enumerate(parts):
        if "=" in part and not part.startswith("--"):
            assignments.append(part)
            command_start = index + 1
        else:
            break

    command = parts[command_start:]
    if len(command) <= 3:
        return shell_join(assignments + command)

    lines = []
    first = assignments + command[:2]
    lines.append(shell_join(first))
    index = 2
    while index < len(command):
        flag = command[index]
        if flag.startswith("--") and index + 1 < len(command) and not command[index + 1].startswith("--"):
            lines.append("  " + shell_join([flag, command[index + 1]]))
            index += 2
        else:
            lines.append("  " + shell_join([flag]))
            index += 1
    return " \\\n".join(lines)


def build_merge(args: argparse.Namespace) -> List[str]:
    parts = ["swift", "export", "--adapters", args.adapters, "--merge_lora", "true"]
    if args.output_dir:
        parts.extend(["--output_dir", args.output_dir])
    if args.exist_ok:
        parts.extend(["--exist_ok", "true"])
    return prefix(parts, args.cuda_visible_devices)


def build_quantize(args: argparse.Namespace) -> List[str]:
    method = args.method.lower()
    if method not in QUANT_METHODS:
        raise SystemExit(f"unsupported quant method: {args.method}")
    if method in BIT_REQUIRED_METHODS and args.bits is None:
        raise SystemExit(f"--bits is required for {method}")
    if method in CALIBRATION_METHODS and not args.dataset:
        raise SystemExit(f"--dataset is required for calibration-based {method}")

    parts = ["swift", "export"]
    if args.adapters:
        parts.extend(["--adapters", args.adapters, "--merge_lora", "true"])
    else:
        parts.extend(["--model", args.model])
    for dataset in args.dataset or []:
        parts.extend(["--dataset", dataset])
    if args.quant_n_samples is not None:
        parts.extend(["--quant_n_samples", str(args.quant_n_samples)])
    if args.quant_batch_size is not None:
        parts.extend(["--quant_batch_size", str(args.quant_batch_size)])
    if args.max_length is not None:
        parts.extend(["--max_length", str(args.max_length)])
    parts.extend(["--quant_method", method])
    if args.bits is not None:
        parts.extend(["--quant_bits", str(args.bits)])
    if args.group_size is not None:
        parts.extend(["--group_size", str(args.group_size)])
    if method == "bnb":
        if args.bnb_4bit_quant_type:
            parts.extend(["--bnb_4bit_quant_type", args.bnb_4bit_quant_type])
        if args.bnb_4bit_use_double_quant is not None:
            parts.extend(["--bnb_4bit_use_double_quant", bool_value(args.bnb_4bit_use_double_quant)])
    if args.output_dir:
        parts.extend(["--output_dir", args.output_dir])
    if args.exist_ok:
        parts.extend(["--exist_ok", "true"])
    return prefix(parts, args.cuda_visible_devices)


def build_push(args: argparse.Namespace) -> List[str]:
    if bool(args.model) == bool(args.adapters):
        raise SystemExit("provide exactly one of --model or --adapters")
    parts = ["swift", "export"]
    if args.model:
        parts.extend(["--model", args.model])
    else:
        parts.extend(["--adapters", args.adapters])
    parts.extend(["--push_to_hub", "true", "--hub_model_id", args.hub_model_id])
    if args.use_hf:
        parts.extend(["--use_hf", "true"])
    if args.token_env:
        parts.extend(["--hub_token", f"${args.token_env}"])
    if args.private:
        parts.extend(["--hub_private_repo", "true"])
    if args.commit_message:
        parts.extend(["--commit_message", args.commit_message])
    return prefix(parts, args.cuda_visible_devices)


def build_cached_dataset(args: argparse.Namespace) -> List[str]:
    parts = ["swift", "export", "--model", args.model]
    for dataset in args.dataset:
        parts.extend(["--dataset", dataset])
    if args.template:
        parts.extend(["--template", args.template])
    if args.val_dataset:
        for dataset in args.val_dataset:
            parts.extend(["--val_dataset", dataset])
    if args.split_dataset_ratio is not None:
        parts.extend(["--split_dataset_ratio", str(args.split_dataset_ratio)])
    parts.extend(["--to_cached_dataset", "true"])
    if args.output_dir:
        parts.extend(["--output_dir", args.output_dir])
    if args.exist_ok:
        parts.extend(["--exist_ok", "true"])
    return prefix(parts, args.cuda_visible_devices)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build ms-swift export command skeletons without running them.")
    subparsers = parser.add_subparsers(dest="operation", required=True)

    merge = subparsers.add_parser("merge-lora", help="Build a LoRA merge command.")
    add_common(merge)
    merge.add_argument("--adapters", required=True, help="LoRA adapter checkpoint directory.")
    merge.add_argument("--output-dir", dest="output_dir", help="Merged model output directory.")
    merge.add_argument("--exist-ok", action="store_true", help="Append --exist_ok true.")
    merge.set_defaults(builder=build_merge)

    quant = subparsers.add_parser("quantize", help="Build a quantization export command.")
    add_common(quant)
    source = quant.add_mutually_exclusive_group(required=True)
    source.add_argument("--model", help="Base, merged, or full model path/ID to quantize.")
    source.add_argument("--adapters", help="Adapter checkpoint to merge before quantization.")
    quant.add_argument("--method", required=True, choices=sorted(QUANT_METHODS), help="Quantization method.")
    quant.add_argument("--bits", type=int, help="Quantization bit width when required.")
    quant.add_argument("--dataset", action="append", help="Calibration dataset; repeat for multiple datasets.")
    quant.add_argument("--quant-n-samples", type=int, default=256)
    quant.add_argument("--quant-batch-size", type=int, default=1)
    quant.add_argument("--max-length", type=int, default=2048)
    quant.add_argument("--group-size", type=int, default=128)
    quant.add_argument("--bnb-4bit-quant-type", choices=["fp4", "nf4"], default="nf4")
    quant.add_argument("--bnb-4bit-use-double-quant", action=argparse.BooleanOptionalAction, default=None)
    quant.add_argument("--output-dir", dest="output_dir", help="Quantized model output directory.")
    quant.add_argument("--exist-ok", action="store_true", help="Append --exist_ok true.")
    quant.set_defaults(builder=build_quantize)

    push = subparsers.add_parser("push", help="Build a hub push command.")
    add_common(push)
    push_source = push.add_mutually_exclusive_group(required=True)
    push_source.add_argument("--model", help="Model/checkpoint directory to push.")
    push_source.add_argument("--adapters", help="Adapter/checkpoint directory to push.")
    push.add_argument("--hub-model-id", required=True, help="Hub repository ID, for example owner/model.")
    push.add_argument("--use-hf", action="store_true", help="Push to Hugging Face instead of ModelScope.")
    push.add_argument("--token-env", help="Environment variable name holding the hub token; value is not expanded.")
    push.add_argument("--private", action="store_true", help="Create/use a private hub repo.")
    push.add_argument("--commit-message", help="Optional hub commit message.")
    push.set_defaults(builder=build_push)

    cached = subparsers.add_parser("cached-dataset", help="Build a cached dataset export command.")
    add_common(cached)
    cached.add_argument("--model", required=True, help="Model ID/path whose template/tokenizer should be used.")
    cached.add_argument("--dataset", action="append", required=True, help="Dataset; repeat for multiple datasets.")
    cached.add_argument("--val-dataset", action="append", help="Optional validation dataset; repeat if needed.")
    cached.add_argument("--template", help="Template name when it cannot be inferred.")
    cached.add_argument("--split-dataset-ratio", type=float, help="Optional split ratio.")
    cached.add_argument("--output-dir", dest="output_dir", help="Cached dataset output directory.")
    cached.add_argument("--exist-ok", action="store_true", help="Append --exist_ok true.")
    cached.set_defaults(builder=build_cached_dataset)

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    parts = args.builder(args)
    print(command_lines(parts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
