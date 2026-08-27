#!/usr/bin/env python3
"""Build a safe EasyR1 training command without executing it."""

from __future__ import annotations

import argparse
import re
import shlex
import sys
from pathlib import Path
from typing import Any

KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+$")
BOOL_TRUE = {"true", "yes", "1", "on"}
BOOL_FALSE = {"false", "no", "0", "off"}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print a shell-quoted EasyR1 training command of the form "
            "python -m verl.trainer.main config=... key=value ... without running it."
        )
    )
    parser.add_argument("config", type=Path, help="Path to the EasyR1 YAML config to pass as config=...")
    parser.add_argument(
        "-o",
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="OmegaConf CLI override. Repeat for multiple overrides, e.g. -o trainer.n_gpus_per_node=8.",
    )
    parser.add_argument("--python", default="python", help="Python executable name to print. Default: python")
    parser.add_argument("--module", default="verl.trainer.main", help="Python module to run. Default: verl.trainer.main")
    parser.add_argument("--multiline", action="store_true", help="Print a backslash-continued multi-line command.")
    parser.add_argument(
        "--require-config",
        action="store_true",
        help="Fail if the config path does not exist. By default the command is printed even for a future path.",
    )
    parser.add_argument(
        "--no-runtime-note",
        action="store_true",
        help="Suppress the standard stderr note that the command is not executed and full training needs CUDA/Ray/vLLM.",
    )
    return parser.parse_args(argv)


def split_override(text: str) -> tuple[str, str]:
    if "\x00" in text or "\n" in text or "\r" in text:
        raise ValueError("Overrides must be single-line text without NUL bytes.")
    if "=" not in text:
        raise ValueError(f"Override {text!r} must have KEY=VALUE form.")
    key, value = text.split("=", 1)
    key = key.strip()
    if not key:
        raise ValueError(f"Override {text!r} has an empty key.")
    if key == "config":
        raise ValueError("Pass the config path as the positional argument, not as an override.")
    if not KEY_RE.fullmatch(key):
        raise ValueError(
            f"Override key {key!r} is not a dotted EasyR1/OmegaConf key. "
            "Use names like trainer.n_gpus_per_node or worker.actor.model.model_path."
        )
    if value == "":
        raise ValueError(f"Override {key!r} has an empty value. Use null explicitly when needed.")
    return key, value


def parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = value.strip().strip('"\'').lower()
    if lowered in BOOL_TRUE:
        return True
    if lowered in BOOL_FALSE:
        return False
    return None


def parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    text = value.strip().strip('"\'')
    if re.fullmatch(r"[-+]?\d+", text):
        return int(text)
    return None


def is_vl_model(value: str | None) -> bool:
    if not value:
        return False
    lowered = value.lower()
    return any(marker in lowered for marker in ("-vl", "_vl", "vl-", "qwen2.5-vl", "qwen3-vl", "vision"))


def collect_warnings(overrides: dict[str, str]) -> list[str]:
    warnings: list[str] = []

    adv = overrides.get("algorithm.adv_estimator")
    rollout_n = parse_int(overrides.get("worker.rollout.n"))
    if adv in {"grpo", "grpo_passk", "rloo"} and rollout_n is not None and rollout_n <= 1:
        warnings.append(f"{adv} requires worker.rollout.n > 1.")

    online_filtering = parse_bool(overrides.get("algorithm.online_filtering"))
    if online_filtering:
        if "algorithm.filter_key" not in overrides:
            warnings.append("DAPO-style online filtering needs algorithm.filter_key to match a reward metric.")
        low = overrides.get("algorithm.filter_low")
        high = overrides.get("algorithm.filter_high")
        if low is None or high is None:
            warnings.append("Consider setting algorithm.filter_low and algorithm.filter_high explicitly for online filtering.")
        if "data.mini_rollout_batch_size" not in overrides:
            warnings.append("DAPO-style recipes often set data.mini_rollout_batch_size to bound generation chunks.")

    loss_type = overrides.get("worker.actor.loss_type")
    if loss_type == "gspo_token" and overrides.get("worker.actor.loss_avg_mode") != "seq":
        warnings.append("GSPO token recipes commonly set worker.actor.loss_avg_mode=seq.")

    lora_rank = parse_int(overrides.get("worker.actor.model.lora.rank"))
    model_path = overrides.get("worker.actor.model.model_path")
    tensor_parallel_size = parse_int(overrides.get("worker.rollout.tensor_parallel_size"))
    if lora_rank is not None and lora_rank > 0:
        exclude_modules = overrides.get("worker.actor.model.lora.exclude_modules")
        if is_vl_model(model_path) and (not exclude_modules or "visual" not in exclude_modules.lower()):
            warnings.append("VL LoRA should usually add worker.actor.model.lora.exclude_modules='.*visual.*'.")
        if tensor_parallel_size is not None and tensor_parallel_size > 1:
            warnings.append("LoRA examples use conservative worker.rollout.tensor_parallel_size=1; verify vLLM LoRA support before increasing TP.")

    nnodes = parse_int(overrides.get("trainer.nnodes"))
    gpus_per_node = parse_int(overrides.get("trainer.n_gpus_per_node"))
    tp = parse_int(overrides.get("worker.rollout.tensor_parallel_size"))
    if nnodes and gpus_per_node and tp:
        world_size = nnodes * gpus_per_node
        if tp > world_size:
            warnings.append("worker.rollout.tensor_parallel_size exceeds trainer.nnodes * trainer.n_gpus_per_node.")
        elif world_size % tp != 0:
            warnings.append("worker.rollout.tensor_parallel_size should divide trainer.nnodes * trainer.n_gpus_per_node.")

    return warnings


def quote_command(tokens: list[str], multiline: bool) -> str:
    quoted = [shlex.quote(token) for token in tokens]
    if not multiline:
        return " ".join(quoted)
    if len(quoted) <= 1:
        return " ".join(quoted)
    lines = [" ".join(quoted[:3]) + " \\"]
    rest = quoted[3:]
    for index, token in enumerate(rest):
        suffix = " \\" if index < len(rest) - 1 else ""
        lines.append(f"  {token}{suffix}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if "\x00" in str(args.config) or "\n" in str(args.config) or "\r" in str(args.config):
        print("ERROR: config path must be single-line text without NUL bytes.", file=sys.stderr)
        return 1
    if args.require_config and not args.config.exists():
        print(f"ERROR: config path does not exist: {args.config}", file=sys.stderr)
        return 1
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", args.module):
        print("ERROR: module must be a Python module path such as verl.trainer.main.", file=sys.stderr)
        return 1

    overrides: list[tuple[str, str]] = []
    override_map: dict[str, str] = {}
    try:
        for raw in args.override:
            key, value = split_override(raw)
            overrides.append((key, value))
            override_map[key] = value
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    tokens = [args.python, "-m", args.module, f"config={args.config}"]
    tokens.extend(f"{key}={value}" for key, value in overrides)

    print(quote_command(tokens, args.multiline))

    for warning in collect_warnings(override_map):
        print(f"WARNING: {warning}", file=sys.stderr)

    if not args.no_runtime_note:
        print(
            "NOTE: command printed only; not executed. Full EasyR1 training requires CUDA GPUs plus Ray, vLLM, flash-attn, model/data access, and sufficient memory.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
