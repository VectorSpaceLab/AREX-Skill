#!/usr/bin/env python3
"""Build safe torchtune inference/eval/quantization commands without executing them.

The script is intentionally side-effect free: it does not import torchtune, read
configs, load checkpoints, download assets, or launch model work. It validates a
small amount of command shape and prints the `tune run ...` command for review.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from dataclasses import dataclass
from enum import Enum


class Mode(str, Enum):
    GENERATE = "generate"
    EVAL = "eval"
    QUANTIZE = "quantize"


@dataclass(frozen=True)
class ModeInfo:
    recipe: str
    note: str
    optional_dependency: str | None = None


MODE_INFO: dict[Mode, ModeInfo] = {
    Mode.GENERATE: ModeInfo(
        recipe="generate",
        note="single-device torchtune generation from an existing checkpoint",
    ),
    Mode.EVAL: ModeInfo(
        recipe="eleuther_eval",
        note="single-device EleutherAI Eval Harness evaluation",
        optional_dependency="lm-eval in the supported recipe range",
    ),
    Mode.QUANTIZE: ModeInfo(
        recipe="quantize",
        note="torchao-backed quantization conversion that writes a checkpoint",
        optional_dependency="torchao-backed quantizer components",
    ),
}


WARNING_NEEDLES: tuple[tuple[str, str], ...] = (
    (
        "adapter_model",
        "adapter weights are not full-model checkpoint files for torchtune generate/eval recipes",
    ),
    (
        "FullModelHFCheckpointer",
        "HF checkpointers are not compatible with quantized eval/generation when a quantizer is set",
    ),
    (
        "FullModelTorchTuneCheckpointer",
        "TorchTune checkpointer is required for quantized eval/generation checkpoints",
    ),
    (
        "Int8DynActInt4WeightQATQuantizer",
        "QAT quantizer belongs in QAT training or quantize conversion, not later eval/generation",
    ),
    (
        "Int8DynActInt4WeightQuantizer",
        "post-training quantizer requires torchao support and matching quantized checkpoint flow",
    ),
    (
        "quantizer._component_",
        "setting a quantizer changes checkpointer requirements for eval/generation",
    ),
    (
        "tasks=",
        "Eleuther task names require lm-eval support and may download task data",
    ),
    (
        "include_path=",
        "custom Eleuther task paths should be reviewed before execution",
    ),
    (
        "device=cuda",
        "confirm GPU memory, dtype support, and model size before execution",
    ),
    (
        "dtype=bf16",
        "bf16 requires supported GPU/accelerator hardware",
    ),
    (
        "output_dir=/tmp",
        "temporary output directories may be deleted; avoid for important quantized checkpoints",
    ),
    (
        "hf-token",
        "never place Hugging Face tokens in reusable commands or configs",
    ),
)


MODE_SPECIFIC_WARNINGS: dict[Mode, tuple[str, ...]] = {
    Mode.GENERATE: (
        "generation logs decoded text; verify prompt format and tokenizer before long runs",
        "stable generate recipe is single-device and may compile a warmup path for quantized models",
    ),
    Mode.EVAL: (
        "start with a small limit and one task before full Eleuther evaluation",
        "Eleuther evaluation imports optional lm-eval and checks its supported version range",
    ),
    Mode.QUANTIZE: (
        "quantize writes a new checkpoint under output_dir; choose a durable writable path",
        "quantization can still load the dense model before conversion, so confirm memory headroom",
    ),
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a safe torchtune command for generation, Eleuther evaluation, or quantization without executing it.",
        epilog=(
            "Examples:\n"
            "  build_inference_eval_command.py generate ./custom_generation_config.yaml --override prompt.user='Tell me a joke.'\n"
            "  build_inference_eval_command.py eval ./custom_eval_config.yaml --override tasks=[truthfulqa_mc2] --override limit=10\n"
            "  build_inference_eval_command.py quantize ./custom_quantization_config.yaml --override output_dir=./quantized"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "mode",
        choices=[mode.value for mode in Mode],
        help="Workflow to build: generate, eval, or quantize.",
    )
    parser.add_argument(
        "config",
        help="Registry config name or local YAML path to pass after --config.",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Recipe/config override appended after --config; repeatable. Deletions such as '~field' are allowed.",
    )
    parser.add_argument(
        "--dry-run-prefix",
        default="",
        help="Optional text prefix such as 'echo' for user-specific review workflows. Empty by default.",
    )
    parser.add_argument(
        "--print-notes",
        action="store_true",
        help="Print safety notes and warnings after the command.",
    )
    return parser.parse_args(argv)


def validate_override(override: str) -> None:
    if override.startswith("~"):
        if len(override) == 1:
            raise SystemExit("Override '~' is incomplete; use '~field.path'.")
        return
    if "=" not in override:
        raise SystemExit(
            f"Override {override!r} is not KEY=VALUE or ~KEY deletion syntax. "
            "torchtune recipe options after --config are OmegaConf overrides, not arbitrary flags."
        )
    key, _value = override.split("=", 1)
    if not key:
        raise SystemExit(f"Override {override!r} has an empty key.")
    if key.startswith("--"):
        raise SystemExit(
            f"Override {override!r} looks like a CLI flag. Use key=value syntax after --config."
        )


def collect_warnings(mode: Mode, config: str, overrides: list[str]) -> list[str]:
    warnings: list[str] = []
    text = " ".join([config, *overrides])
    for needle, warning in WARNING_NEEDLES:
        if needle in text:
            warnings.append(warning)

    has_quantizer = "quantizer._component_" in text or "quantizer:" in text
    has_hf_checkpointer = "FullModelHFCheckpointer" in text
    has_torchtune_checkpointer = "FullModelTorchTuneCheckpointer" in text
    has_qat_quantizer = "Int8DynActInt4WeightQATQuantizer" in text

    if mode in {Mode.GENERATE, Mode.EVAL} and has_quantizer and has_hf_checkpointer:
        warnings.append(
            "quantized eval/generation requires FullModelTorchTuneCheckpointer, not FullModelHFCheckpointer"
        )
    if mode in {Mode.GENERATE, Mode.EVAL} and has_qat_quantizer:
        warnings.append(
            "replace QAT quantizer with Int8DynActInt4WeightQuantizer for eval/generation of quantized checkpoints"
        )
    if mode in {Mode.GENERATE, Mode.EVAL} and has_quantizer and not has_torchtune_checkpointer:
        warnings.append(
            "if this is a quantized checkpoint, ensure the config uses FullModelTorchTuneCheckpointer"
        )
    if mode is Mode.QUANTIZE and "output_dir=" not in text:
        warnings.append("quantize writes to output_dir; confirm the config uses a durable writable directory")
    if mode is Mode.EVAL and "limit=" not in text:
        warnings.append("consider limit=1 or another small value for the first eval smoke run")
    if mode is Mode.GENERATE and "prompt.user=" not in text:
        warnings.append("confirm prompt.user or the config prompt before running generation")

    warnings.extend(MODE_SPECIFIC_WARNINGS[mode])
    return dedupe(warnings)


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def quote_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts if part)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    mode = Mode(args.mode)
    for override in args.override:
        validate_override(override)

    info = MODE_INFO[mode]
    command = ["tune", "run", info.recipe, "--config", args.config, *args.override]
    if args.dry_run_prefix:
        command.insert(0, args.dry_run_prefix)

    print(quote_command(command))

    if args.print_notes:
        print("\nSafety notes:")
        print("- This script only prints a command; it never executes torchtune recipes.")
        print(f"- Mode: {mode.value} -> {info.recipe} ({info.note}).")
        if info.optional_dependency:
            print(f"- Optional dependency to confirm: {info.optional_dependency}.")
        print("- Confirm checkpoint files, tokenizer files, credentials, device, dtype, and output_dir before running.")
        for warning in collect_warnings(mode, args.config, args.override):
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
