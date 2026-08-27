#!/usr/bin/env python3
"""Validate LitGPT inference inputs without loading weights or downloading models."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

TOKENIZER_FILE_GROUPS = (
    ("tokenizer.json",),
    ("tokenizer.model",),
    ("tokenizer.yaml",),
    ("tokenizer_config.json",),
    ("vocab.json", "merges.txt"),
)
PROMPT_STYLE_FILES = ("prompt_style.json", "prompt_style.yaml")
BNB_QUANTIZE_VALUES = {"bnb.nf4", "bnb.nf4-dq", "bnb.fp4", "bnb.fp4-dq", "bnb.int8"}
SEQUENTIAL_TP_QUANTIZE_VALUES = {"bnb.nf4", "bnb.nf4-dq", "bnb.fp4", "bnb.fp4-dq"}
TRUE_PRECISION_VALUES = {"16-true", "bf16-true", "32-true"}
MIXED_PRECISION_MARKERS = ("mixed",)
CUDA_VISIBLE_EMPTY_VALUES = {"", "-1", "none", "None", "NONE"}


class CheckResult:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.info.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely validate LitGPT inference/chat inputs. The checker inspects paths and scalar options only; "
            "it never imports LitGPT, loads model weights, downloads checkpoints, starts servers, or writes outputs."
        )
    )
    parser.add_argument("--checkpoint-dir", type=Path, help="Local LitGPT checkpoint directory for generation/chat.")
    parser.add_argument("--tokenizer-dir", type=Path, help="Optional tokenizer directory to validate instead of checkpoint-dir.")
    parser.add_argument("--draft-checkpoint-dir", type=Path, help="Draft checkpoint for speculative decoding.")
    parser.add_argument("--target-checkpoint-dir", type=Path, help="Target checkpoint for speculative decoding.")
    parser.add_argument("--prompt", default=None, help="Prompt text planned for generation.")
    parser.add_argument("--sys-prompt", default=None, help="Optional system prompt text.")
    parser.add_argument("--max-new-tokens", type=int, default=50, help="Planned max_new_tokens value.")
    parser.add_argument("--num-samples", type=int, default=1, help="Planned num_samples value.")
    parser.add_argument("--top-k", type=int, default=None, help="Planned top_k value. Omit to disable top-k validation.")
    parser.add_argument("--top-p", type=float, default=1.0, help="Planned top_p value.")
    parser.add_argument("--temperature", type=float, default=1.0, help="Planned temperature value.")
    parser.add_argument("--quantize", choices=sorted(BNB_QUANTIZE_VALUES), help="Optional bitsandbytes quantization value.")
    parser.add_argument("--precision", help="Optional Lightning/Fabric precision string, e.g. bf16-true.")
    parser.add_argument(
        "--route",
        choices=("generate", "chat", "generate_full", "generate_adapter", "generate_adapter_v2", "sequential", "tensor_parallel", "speculative", "api"),
        default="generate",
        help="Inference route to validate route-specific constraints.",
    )
    parser.add_argument("--adapter-path", type=Path, help="Adapter or adapter-v2 file for adapter generation routes.")
    parser.add_argument("--finetuned-path", type=Path, help="Full finetuned model file for generate_full.")
    parser.add_argument("--speculative-k", type=int, default=3, help="Speculative decoding k value.")
    parser.add_argument("--devices", type=int, default=None, help="Planned device count for multi-device/API distribution.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if CUDA appears unavailable or hidden.")
    parser.add_argument("--allow-model-name", action="store_true", help="Allow checkpoint-dir to be a non-local model identifier.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    return parser.parse_args(argv)


def has_any_file(directory: Path, groups: tuple[tuple[str, ...], ...]) -> bool:
    return any(all((directory / filename).is_file() for filename in group) for group in groups)


def present_files(directory: Path, names: tuple[str, ...]) -> list[str]:
    return [name for name in names if (directory / name).is_file()]


def read_yaml_name(config_path: Path) -> str | None:
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError:
        return None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"\'') or None
    return None


def read_tokenizer_vocab_size(directory: Path) -> int | None:
    tokenizer_config = directory / "tokenizer_config.json"
    if not tokenizer_config.is_file():
        return None
    try:
        data: dict[str, Any] = json.loads(tokenizer_config.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    for key in ("vocab_size", "model_max_length"):
        value = data.get(key)
        if isinstance(value, int):
            return value
    return None


def looks_like_model_identifier(value: str) -> bool:
    path = Path(value)
    return not path.exists() and "/" in value and not value.startswith(("./", "../", "/"))


def cuda_visible() -> bool:
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible in CUDA_VISIBLE_EMPTY_VALUES:
        return False
    if visible is not None:
        return True
    if platform.system().lower() == "darwin":
        return False
    dev_dir = Path("/dev")
    if (dev_dir / "nvidiactl").exists() or any(dev_dir.glob("nvidia[0-9]*")):
        return True
    proc_gpus = Path("/proc/driver/nvidia/gpus")
    return proc_gpus.is_dir() and any(proc_gpus.iterdir())


def validate_checkpoint_dir(result: CheckResult, path: Path | None, label: str, allow_model_name: bool) -> dict[str, Any]:
    summary: dict[str, Any] = {"label": label, "path": str(path) if path is not None else None, "exists": False}
    if path is None:
        result.error(f"{label}: missing checkpoint directory")
        return summary

    path_text = str(path)
    if allow_model_name and looks_like_model_identifier(path_text):
        result.warn(f"{label}: {path_text!r} looks like a remote model identifier; this can trigger network access")
        summary["model_identifier"] = True
        return summary

    if not path.exists():
        result.error(f"{label}: path does not exist: {path}")
        return summary
    if not path.is_dir():
        result.error(f"{label}: path is not a directory: {path}")
        return summary

    summary["exists"] = True
    model_file = path / "lit_model.pth"
    config_file = path / "model_config.yaml"
    if not model_file.is_file():
        result.error(f"{label}: missing lit_model.pth")
    if not config_file.is_file():
        result.error(f"{label}: missing model_config.yaml")
    else:
        config_name = read_yaml_name(config_file)
        if config_name:
            summary["model_config_name"] = config_name
            result.note(f"{label}: model_config.yaml name={config_name}")

    if has_any_file(path, TOKENIZER_FILE_GROUPS):
        result.note(f"{label}: tokenizer files detected")
        summary["tokenizer_files_detected"] = True
    else:
        result.error(
            f"{label}: no tokenizer files detected; expected tokenizer.json, tokenizer.model, tokenizer.yaml, "
            "tokenizer_config.json, or vocab.json+merges.txt"
        )
        summary["tokenizer_files_detected"] = False

    prompt_files = present_files(path, PROMPT_STYLE_FILES)
    if prompt_files:
        result.note(f"{label}: prompt style file(s) detected: {', '.join(prompt_files)}")
        summary["prompt_style_files"] = prompt_files
    else:
        result.warn(f"{label}: no prompt_style file detected; LitGPT will derive PromptStyle.from_config when possible")

    lora_file = path / "lit_model.pth.lora"
    if lora_file.is_file() and not model_file.is_file():
        result.warn(f"{label}: raw LoRA file found without lit_model.pth; merge or choose the correct generation route")

    vocab_size = read_tokenizer_vocab_size(path)
    if vocab_size is not None:
        summary["tokenizer_config_size_hint"] = vocab_size

    return summary


def validate_tokenizer_dir(result: CheckResult, path: Path | None) -> None:
    if path is None:
        return
    if not path.exists():
        result.error(f"tokenizer-dir: path does not exist: {path}")
        return
    if not path.is_dir():
        result.error(f"tokenizer-dir: path is not a directory: {path}")
        return
    if has_any_file(path, TOKENIZER_FILE_GROUPS):
        result.note("tokenizer-dir: tokenizer files detected")
    else:
        result.error("tokenizer-dir: no supported tokenizer files detected")


def validate_sampling(result: CheckResult, args: argparse.Namespace) -> None:
    if args.prompt is not None and args.prompt == "":
        result.warn("prompt is an empty string; chat mode uses empty input as an exit signal")
    if args.max_new_tokens < 1:
        result.error("max-new-tokens must be >= 1")
    if args.num_samples < 1:
        result.error("num-samples must be >= 1")
    if args.top_k is not None and args.top_k < 1:
        result.error("top-k must be a positive integer when provided")
    if args.top_p < 0.0 or args.top_p > 1.0:
        result.error(f"top-p must be in [0, 1], got {args.top_p}")
    if args.temperature < 0.0:
        result.error("temperature must be >= 0")
    if args.temperature == 0.0 or args.top_p == 0.0:
        result.note("sampling: temperature=0 or top_p=0 selects greedy decoding")
    if args.top_k == 1:
        result.note("sampling: top_k=1 strongly restricts generation to the most likely token")


def validate_quantization(result: CheckResult, args: argparse.Namespace) -> None:
    if args.quantize is None:
        return
    if args.route in {"sequential", "tensor_parallel"} and args.quantize not in SEQUENTIAL_TP_QUANTIZE_VALUES:
        result.error(f"{args.route}: supports 4-bit bitsandbytes values, not {args.quantize}")
    if args.precision and any(marker in args.precision for marker in MIXED_PRECISION_MARKERS):
        result.error("quantization and mixed precision are not supported together; use a true precision")
    if args.precision and args.precision not in TRUE_PRECISION_VALUES:
        result.warn(f"precision {args.precision!r} is not one of common true precision values {sorted(TRUE_PRECISION_VALUES)}")
    if importlib.util.find_spec("bitsandbytes") is None:
        result.warn("bitsandbytes is not importable; bnb quantization will fail unless installed in the runtime environment")
    if not cuda_visible():
        result.warn("CUDA does not appear visible; bitsandbytes inference quantization is CUDA-oriented")


def validate_hardware_route(result: CheckResult, args: argparse.Namespace) -> None:
    cuda_needed = args.require_cuda or args.route in {"sequential", "tensor_parallel"}
    if cuda_needed and not cuda_visible():
        result.error("CUDA appears unavailable or hidden; this route requires CUDA/GPU")
    if args.route in {"sequential", "tensor_parallel"}:
        if args.devices is not None and args.devices < 2:
            result.warn(f"{args.route}: devices={args.devices}; multi-device route is usually useful with at least 2 CUDA devices")
        if args.route == "tensor_parallel":
            result.warn("tensor_parallel: verify model dimensions divide evenly by the number of devices before launch")
        if args.route == "sequential":
            result.warn("sequential: verify the model has at least as many transformer layers as visible devices")


def validate_route_artifacts(result: CheckResult, args: argparse.Namespace) -> None:
    if args.route == "generate_full":
        if args.finetuned_path is None:
            result.warn("generate_full: --finetuned-path not provided; LitGPT default path must exist at runtime")
        elif not args.finetuned_path.is_file():
            result.error(f"generate_full: finetuned path is not a file: {args.finetuned_path}")
    if args.route in {"generate_adapter", "generate_adapter_v2"}:
        expected_suffix = ".adapter_v2" if args.route == "generate_adapter_v2" else ".adapter"
        if args.adapter_path is None:
            result.warn(f"{args.route}: --adapter-path not provided; LitGPT default path must exist at runtime")
        elif not args.adapter_path.is_file():
            result.error(f"{args.route}: adapter path is not a file: {args.adapter_path}")
        elif not str(args.adapter_path).endswith(expected_suffix):
            result.warn(f"{args.route}: adapter path does not end with expected suffix {expected_suffix!r}")
    if args.route == "speculative" and args.speculative_k < 1:
        result.error("speculative-k must be >= 1")


def emit_text(result: CheckResult, summaries: list[dict[str, Any]]) -> None:
    status = "PASS" if result.ok else "FAIL"
    print(f"LitGPT inference input check: {status}")
    for summary in summaries:
        print(f"- {summary['label']}: {summary.get('path')}")
    for message in result.info:
        print(f"INFO: {message}")
    for message in result.warnings:
        print(f"WARN: {message}")
    for message in result.errors:
        print(f"ERROR: {message}")


def emit_json(result: CheckResult, summaries: list[dict[str, Any]]) -> None:
    payload = {
        "ok": result.ok,
        "summaries": summaries,
        "info": result.info,
        "warnings": result.warnings,
        "errors": result.errors,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = CheckResult()
    summaries: list[dict[str, Any]] = []

    validate_sampling(result, args)
    validate_tokenizer_dir(result, args.tokenizer_dir)
    validate_quantization(result, args)
    validate_hardware_route(result, args)
    validate_route_artifacts(result, args)

    if args.route == "speculative":
        draft_summary = validate_checkpoint_dir(result, args.draft_checkpoint_dir, "draft-checkpoint-dir", args.allow_model_name)
        target_summary = validate_checkpoint_dir(result, args.target_checkpoint_dir, "target-checkpoint-dir", args.allow_model_name)
        summaries.extend([draft_summary, target_summary])
        draft_vocab = draft_summary.get("tokenizer_config_size_hint")
        target_vocab = target_summary.get("tokenizer_config_size_hint")
        if draft_vocab is not None and target_vocab is not None and draft_vocab != target_vocab:
            result.error(f"speculative: tokenizer size hints differ: draft={draft_vocab}, target={target_vocab}")
    else:
        summaries.append(validate_checkpoint_dir(result, args.checkpoint_dir, "checkpoint-dir", args.allow_model_name))

    if args.json:
        emit_json(result, summaries)
    else:
        emit_text(result, summaries)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
