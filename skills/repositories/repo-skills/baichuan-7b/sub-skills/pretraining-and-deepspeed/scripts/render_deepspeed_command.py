#!/usr/bin/env python3
"""Render a Baichuan-7B DeepSpeed training command without executing it.

The source repository's scripts/train.sh launches DeepSpeed immediately. This
bundled helper keeps the reusable part: validate enough config/hostfile shape to
avoid obvious mistakes, then print a shell command that a human or future agent
can review before running in an appropriate GPU/cluster environment.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Iterable

HOSTFILE_RE = re.compile(r"^(?P<host>\S+)\s+(?P<rest>.*)$")
SLOTS_RE = re.compile(r"(?:^|\s)slots=(?P<slots>\d+)(?:\s|$)")


def path_arg(value: str) -> Path:
    return Path(value).expanduser()


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def parse_deepspeed_config(path: Path) -> tuple[dict[str, Any] | None, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not path.exists():
        return None, [f"DeepSpeed config missing: {path}"], warnings
    if not path.is_file():
        return None, [f"DeepSpeed config is not a file: {path}"], warnings
    try:
        with path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as exc:
        return None, [f"DeepSpeed config is not parseable JSON: {path}: {exc}"], warnings
    if not isinstance(cfg, dict):
        return None, [f"DeepSpeed config root must be an object: {path}"], warnings

    if not positive_int(cfg.get("train_micro_batch_size_per_gpu")):
        errors.append("DeepSpeed config needs positive integer train_micro_batch_size_per_gpu; train.py indexes it directly.")
    if not positive_int(cfg.get("gradient_accumulation_steps")):
        errors.append("DeepSpeed config needs positive integer gradient_accumulation_steps.")
    zero = cfg.get("zero_optimization")
    if not isinstance(zero, dict) or not isinstance(zero.get("stage"), int):
        errors.append("DeepSpeed config needs zero_optimization.stage.")
    elif zero.get("stage") != 2:
        warnings.append(f"zero_optimization.stage is {zero.get('stage')}; Baichuan demo config used stage 2.")
    optimizer = cfg.get("optimizer")
    if not isinstance(optimizer, dict) or not optimizer.get("type"):
        errors.append("DeepSpeed config needs optimizer.type; source config used AdamW.")
    bf16 = cfg.get("bf16")
    fp16 = cfg.get("fp16")
    if not (isinstance(bf16, dict) and bf16.get("enabled") is True) and not (isinstance(fp16, dict) and fp16.get("enabled") is True):
        warnings.append("No enabled bf16/fp16 block was found; source config enabled bf16.")
    return cfg, errors, warnings


def parse_hostfile(path: Path, allow_placeholders: bool) -> tuple[int | None, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not path.exists():
        return None, [f"Hostfile missing: {path}"], warnings
    if not path.is_file():
        return None, [f"Hostfile is not a file: {path}"], warnings
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        return None, [f"Hostfile could not be read as UTF-8: {path}: {exc}"], warnings

    total = 0
    entries = 0
    for line_no, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "..." or line.startswith("..."):
            if allow_placeholders:
                warnings.append(f"Ignoring placeholder line in hostfile: {path}:{line_no}: {raw}")
            else:
                errors.append(f"Hostfile contains ellipsis placeholder: {path}:{line_no}: {raw}")
            continue
        if ("[" in line or "]" in line) and not allow_placeholders:
            errors.append(f"Hostfile contains bracketed placeholder text: {path}:{line_no}: {raw}")
            continue
        match = HOSTFILE_RE.match(line)
        if not match:
            errors.append(f"Malformed hostfile line: {path}:{line_no}: {raw}")
            continue
        slot_match = SLOTS_RE.search(match.group("rest"))
        if not slot_match:
            errors.append(f"Hostfile line missing slots=N: {path}:{line_no}: {raw}")
            continue
        slots = int(slot_match.group("slots"))
        if slots <= 0:
            errors.append(f"Hostfile line has non-positive slots: {path}:{line_no}: {raw}")
            continue
        total += slots
        entries += 1
    if entries == 0:
        errors.append(f"Hostfile has no runnable entries: {path}")
        return None, errors, warnings
    return total, errors, warnings


def build_command(args: argparse.Namespace) -> list[str]:
    parts = [str(args.deepspeed_binary)]
    if args.hostfile is not None:
        parts.extend(["--hostfile", str(args.hostfile)])
    if not args.no_force_multi:
        parts.append("--force_multi")
    parts.extend(args.extra_launch_arg or [])
    parts.append(str(args.train_script))
    parts.append("--deepspeed")
    parts.extend(["--deepspeed_config", str(args.deepspeed_config)])
    if not args.omit_default_train_args:
        parts.extend(["--data_dir", str(args.data_dir)])
        parts.extend(["--tokenizer_path", str(args.tokenizer_path)])
        parts.extend(["--max_length", str(args.max_length)])
        parts.extend(["--steps_per_epoch", str(args.steps_per_epoch)])
        parts.extend(["--checkpoint_saving_path", str(args.checkpoint_saving_path)])
    parts.extend(args.extra_train_arg or [])
    return parts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render, but do not run, the Baichuan-7B DeepSpeed pretraining launch command."
    )
    parser.add_argument("--deepspeed-binary", default="deepspeed", help="DeepSpeed launcher executable name or path.")
    parser.add_argument("--hostfile", type=path_arg, default=Path("config/hostfile"), help="DeepSpeed hostfile path.")
    parser.add_argument("--deepspeed-config", type=path_arg, default=Path("config/deepspeed.json"), help="DeepSpeed JSON config path.")
    parser.add_argument("--train-script", type=path_arg, default=Path("train.py"), help="Training entrypoint to render into the command; not imported or executed.")
    parser.add_argument("--data-dir", type=path_arg, default=Path("data_dir"), help="Corpus shard directory argument for train.py.")
    parser.add_argument("--tokenizer-path", type=path_arg, default=Path("tokenizer.model"), help="SentencePiece tokenizer model argument for train.py.")
    parser.add_argument("--checkpoint-saving-path", type=path_arg, default=Path("checkpoints"), help="Checkpoint output directory argument for train.py.")
    parser.add_argument("--max-length", type=int, default=4096, help="--max_length value for train.py.")
    parser.add_argument("--steps-per-epoch", type=int, default=4096, help="--steps_per_epoch value for train.py.")
    parser.add_argument("--no-force-multi", action="store_true", help="Omit the source launcher's --force_multi flag.")
    parser.add_argument("--omit-default-train-args", action="store_true", help="Render only the original script's explicit --deepspeed and --deepspeed_config train.py args.")
    parser.add_argument("--extra-launch-arg", action="append", default=[], help="Additional argument inserted before train.py; repeat for multiple args.")
    parser.add_argument("--extra-train-arg", action="append", default=[], help="Additional argument appended after train.py arguments; repeat for multiple args.")
    parser.add_argument("--require-train-script", action="store_true", help="Fail if --train-script does not exist locally.")
    parser.add_argument("--allow-placeholder-hostfile", action="store_true", help="Allow bracket/ellipsis placeholders in hostfile and render anyway with warnings.")
    parser.add_argument("--skip-validation", action="store_true", help="Render command without checking config, hostfile, or train-script path.")
    parser.add_argument("--plain", action="store_true", help="Print only the shell command.")
    parser.add_argument("--json", action="store_true", help="Emit JSON containing command, warnings, and slot summary.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []
    slot_total: int | None = None
    cfg: dict[str, Any] | None = None

    if args.max_length <= 0:
        errors.append("--max-length must be positive.")
    if args.steps_per_epoch <= 0:
        errors.append("--steps-per-epoch must be positive.")

    if not args.skip_validation:
        cfg, cfg_errors, cfg_warnings = parse_deepspeed_config(args.deepspeed_config)
        errors.extend(cfg_errors)
        warnings.extend(cfg_warnings)
        slot_total, host_errors, host_warnings = parse_hostfile(args.hostfile, args.allow_placeholder_hostfile)
        errors.extend(host_errors)
        warnings.extend(host_warnings)
        if args.require_train_script and not args.train_script.is_file():
            errors.append(f"Training entrypoint does not exist: {args.train_script}")
    else:
        warnings.append("Validation skipped; command may reference missing or malformed files.")

    command_parts = build_command(args)
    command = shell_join(command_parts)

    if args.json:
        payload = {
            "ok": not errors,
            "command": command,
            "errors": errors,
            "warnings": warnings,
            "hostfileTotalSlots": slot_total,
            "effectiveGlobalBatch": (
                int(cfg["train_micro_batch_size_per_gpu"]) * int(cfg["gradient_accumulation_steps"]) * int(slot_total)
                if cfg and slot_total and positive_int(cfg.get("train_micro_batch_size_per_gpu")) and positive_int(cfg.get("gradient_accumulation_steps"))
                else None
            ),
            "note": "Command was rendered only; DeepSpeed was not launched.",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif args.plain:
        if errors:
            for err in errors:
                print(f"ERROR: {err}", file=sys.stderr)
        else:
            print(command)
    else:
        print("Baichuan-7B DeepSpeed command render")
        for warning in warnings:
            print(f"WARN: {warning}")
        if errors:
            for err in errors:
                print(f"ERROR: {err}")
            print("No runnable command emitted because validation failed. Use --skip-validation only for documentation previews.")
        else:
            if slot_total:
                print(f"Hostfile total slots: {slot_total}")
            if cfg and slot_total and positive_int(cfg.get("train_micro_batch_size_per_gpu")) and positive_int(cfg.get("gradient_accumulation_steps")):
                effective = int(cfg["train_micro_batch_size_per_gpu"]) * int(cfg["gradient_accumulation_steps"]) * int(slot_total)
                print(f"Estimated global batch: {effective} samples")
            print("Command (not executed):")
            print(command)
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
