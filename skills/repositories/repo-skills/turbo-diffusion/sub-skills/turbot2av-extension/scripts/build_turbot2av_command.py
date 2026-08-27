#!/usr/bin/env python3
"""Render TurboT2AV student/teacher inference commands without executing them.

This helper is intentionally side-effect free: it performs argument validation,
constructs an `ltx_distillation.tools.run_av_inference_eval` command, and prints
that command. It does not download checkpoints, install packages, create output
directories, or run model inference.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ATTENTION_TYPES = ("default", "sageattn", "sla", "sagesla")
ATTENTION_SCOPES = ("self", "video_self", "self_av")
QUANT_LINEAR_SCOPES = (
    "all",
    "transformer_blocks",
    "ffn",
    "video_ffn",
    "audio_ffn",
    "video_heavy",
    "non_attention",
)
QUANT_LINEAR_BACKENDS = ("turbodiffusion", "tilelang_postscale")
STUDENT_PARAMS = ("auto", "native_rf", "rcm_trig")
TEACHER_MODES = ("native_rf", "rcm_trig")


@dataclass(frozen=True)
class AccelerationPlan:
    attention_type: str | None = None
    attention_scope: str | None = None
    sla_topk: float | None = None
    sla_topk_schedule: str | None = None
    sla_block_q: int | None = None
    sla_block_k: int | None = None
    trim_text_context: bool = False
    fast_norm: bool = False
    quant_linear: bool = False
    quant_linear_scope: str | None = None
    quant_linear_backend: str | None = None


def positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return value


def nonnegative_int(text: str) -> int:
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return value


def positive_sla_topk(text: str) -> float:
    value = float(text)
    if not (0.0 < value <= 1.0):
        raise argparse.ArgumentTypeError("must be in (0, 1]")
    return value


def non_empty_path(label: str, value: str | None) -> str:
    if value is None or not str(value).strip():
        raise SystemExit(f"error: {label} is required and must be non-empty")
    return str(value)


def add_value(argv: list[str], flag: str, value: Any | None) -> None:
    if value is not None:
        argv.extend([flag, str(value)])


def add_bool(argv: list[str], flag: str, enabled: bool) -> None:
    if enabled:
        argv.append(flag)


def resolve_preset(args: argparse.Namespace) -> AccelerationPlan:
    preset = args.acceleration_preset
    if preset == "auto":
        preset = "student-recommended" if args.model_kind == "student" else "none"

    if preset == "student-recommended":
        plan = AccelerationPlan(
            attention_type="sagesla",
            attention_scope="self",
            sla_topk=0.3,
            trim_text_context=True,
            fast_norm=True,
            quant_linear=True,
            quant_linear_scope="all",
            quant_linear_backend="tilelang_postscale",
        )
    elif preset == "teacher-w8a8-fastnorm":
        plan = AccelerationPlan(
            attention_type="default",
            fast_norm=True,
            quant_linear=True,
            quant_linear_scope="all",
            quant_linear_backend="tilelang_postscale",
        )
    elif preset == "none":
        plan = AccelerationPlan(attention_type="default")
    elif preset == "custom":
        plan = AccelerationPlan()
    else:  # defensive; argparse should prevent this.
        raise SystemExit(f"error: unsupported acceleration preset: {preset}")

    return AccelerationPlan(
        attention_type=args.attention_type if args.attention_type is not None else plan.attention_type,
        attention_scope=args.attention_scope if args.attention_scope is not None else plan.attention_scope,
        sla_topk=args.sla_topk if args.sla_topk is not None else plan.sla_topk,
        sla_topk_schedule=(
            args.sla_topk_schedule if args.sla_topk_schedule is not None else plan.sla_topk_schedule
        ),
        sla_block_q=args.sla_block_q if args.sla_block_q is not None else plan.sla_block_q,
        sla_block_k=args.sla_block_k if args.sla_block_k is not None else plan.sla_block_k,
        trim_text_context=(
            args.trim_text_context if args.trim_text_context is not None else plan.trim_text_context
        ),
        fast_norm=args.fast_norm if args.fast_norm is not None else plan.fast_norm,
        quant_linear=args.quant_linear if args.quant_linear is not None else plan.quant_linear,
        quant_linear_scope=(
            args.quant_linear_scope if args.quant_linear_scope is not None else plan.quant_linear_scope
        ),
        quant_linear_backend=(
            args.quant_linear_backend if args.quant_linear_backend is not None else plan.quant_linear_backend
        ),
    )


def validate_required_args(args: argparse.Namespace) -> None:
    non_empty_path("--config-path", args.config_path)
    non_empty_path("--prompts-file", args.prompts_file)
    non_empty_path("--output-dir", args.output_dir)
    non_empty_path("--base-checkpoint", args.base_checkpoint)
    non_empty_path("--gemma-path", args.gemma_path)
    if args.model_kind == "student":
        non_empty_path("--student-checkpoint", args.student_checkpoint)

    if args.shard_id is not None and args.num_shards is None:
        raise SystemExit("error: --shard-id requires --num-shards")
    if args.num_shards is not None and args.shard_id is not None and args.shard_id >= args.num_shards:
        raise SystemExit("error: --shard-id must be less than --num-shards")

    if args.check_existing_inputs:
        checks = [
            ("--config-path", args.config_path, "file"),
            ("--prompts-file", args.prompts_file, "file"),
            ("--base-checkpoint", args.base_checkpoint, "exists"),
            ("--gemma-path", args.gemma_path, "exists"),
        ]
        if args.model_kind == "student":
            checks.append(("--student-checkpoint", args.student_checkpoint, "exists"))
        for label, raw_path, expected in checks:
            path = Path(str(raw_path)).expanduser()
            if expected == "file" and not path.is_file():
                raise SystemExit(f"error: {label} does not point to an existing file: {raw_path}")
            if expected == "exists" and not path.exists():
                raise SystemExit(f"error: {label} does not exist: {raw_path}")


def build_env(args: argparse.Namespace) -> dict[str, str]:
    env: dict[str, str] = {}
    if args.cuda_visible_devices is not None:
        env["CUDA_VISIBLE_DEVICES"] = args.cuda_visible_devices
    env["TURBO_CHECKPOINT_PATH"] = non_empty_path("--base-checkpoint", args.base_checkpoint)
    env["TURBO_GEMMA_PATH"] = non_empty_path("--gemma-path", args.gemma_path)
    return env


def build_argv(args: argparse.Namespace, accel: AccelerationPlan) -> list[str]:
    if args.launcher == "pixi":
        argv = ["pixi", "run", "python", "-m", "ltx_distillation.tools.run_av_inference_eval"]
    elif args.launcher == "python":
        argv = ["python", "-m", "ltx_distillation.tools.run_av_inference_eval"]
    else:  # defensive; argparse should prevent this.
        raise SystemExit(f"error: unsupported launcher: {args.launcher}")

    add_value(argv, "--config_path", args.config_path)
    add_value(argv, "--prompts_file", args.prompts_file)
    add_value(argv, "--output_dir", args.output_dir)
    add_value(argv, "--model_kind", args.model_kind)

    if args.model_kind == "student":
        add_value(argv, "--student_checkpoint", args.student_checkpoint)
        add_value(argv, "--student_param", args.student_param)
        add_bool(argv, "--student_strict", args.student_strict)
    else:
        add_value(argv, "--teacher_mode", args.teacher_mode)
        add_value(argv, "--teacher_steps", args.teacher_steps)

    add_value(argv, "--num_prompts", args.num_prompts)
    add_value(argv, "--seed", args.seed)
    add_value(argv, "--num_seeds", args.num_seeds)
    add_bool(argv, "--same_seed_for_all_prompts", args.same_seed_for_all_prompts)
    add_value(argv, "--num_shards", args.num_shards)
    add_value(argv, "--shard_id", args.shard_id)
    add_bool(argv, "--overwrite", args.overwrite)
    add_bool(argv, "--cache_state_dicts", args.cache_state_dicts)
    add_value(argv, "--init_lock_path", args.init_lock_path)
    add_bool(argv, "--no_init_lock", args.no_init_lock)

    add_value(argv, "--attention_type", accel.attention_type)
    add_value(argv, "--attention_scope", accel.attention_scope)
    add_value(argv, "--sla_topk", accel.sla_topk)
    add_value(argv, "--sla_topk_schedule", accel.sla_topk_schedule)
    add_value(argv, "--sla_block_q", accel.sla_block_q)
    add_value(argv, "--sla_block_k", accel.sla_block_k)
    add_bool(argv, "--trim_text_context", accel.trim_text_context)
    add_bool(argv, "--fast_norm", accel.fast_norm)
    add_bool(argv, "--quant_linear", accel.quant_linear)
    if accel.quant_linear or accel.quant_linear_scope is not None:
        add_value(argv, "--quant_linear_scope", accel.quant_linear_scope)
    if accel.quant_linear or accel.quant_linear_backend is not None:
        add_value(argv, "--quant_linear_backend", accel.quant_linear_backend)

    add_bool(argv, "--skip_decode", args.skip_decode)
    add_value(argv, "--warmup_samples", args.warmup_samples)
    add_value(argv, "--timing_json", args.timing_json)
    add_value(argv, "--video_height", args.video_height)
    add_value(argv, "--video_width", args.video_width)
    add_value(argv, "--num_frames", args.num_frames)
    return argv


def shell_env_assignment(key: str, value: str) -> str:
    return f"{key}={shlex.quote(value)}"


def shell_pythonpath_assignment(entries: list[str]) -> str:
    prefix = ":".join(entries)
    if prefix:
        return f"PYTHONPATH={shlex.quote(prefix)}:${{PYTHONPATH:-}}"
    return ""


def format_shell(env: dict[str, str], pythonpath_entries: list[str], argv: list[str], comments: bool) -> str:
    parts: list[str] = []
    for key, value in env.items():
        parts.append(shell_env_assignment(key, value))
    pythonpath_assignment = shell_pythonpath_assignment(pythonpath_entries)
    if pythonpath_assignment:
        parts.append(pythonpath_assignment)
    parts.extend(shlex.quote(part) for part in argv)
    command = " \\\n  ".join(parts)
    if not comments:
        return command
    launcher_note = "Run from the LTX-2 Pixi workspace." if argv[:2] == ["pixi", "run"] else (
        "Run in an environment where ltx_distillation is importable."
    )
    return "\n".join(
        [
            "# Rendered command only; review paths before running.",
            f"# {launcher_note}",
            "# This helper did not download weights, install packages, or execute inference.",
            command,
        ]
    )


def emit(args: argparse.Namespace, env: dict[str, str], argv: list[str]) -> None:
    pythonpath_entries = args.pythonpath or []
    if args.format == "shell":
        print(format_shell(env, pythonpath_entries, argv, comments=not args.no_comments))
    elif args.format == "json":
        payload = {
            "note": "Rendered only; no downloads, installs, or model execution were performed.",
            "run_context": "LTX-2 Pixi workspace" if argv[:2] == ["pixi", "run"] else "Python environment",
            "env": env,
            "pythonpath_prefix": pythonpath_entries,
            "inherit_pythonpath": bool(pythonpath_entries),
            "argv": argv,
        }
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    elif args.format == "argv-json":
        json.dump(argv, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:  # defensive; argparse should prevent this.
        raise SystemExit(f"error: unsupported format: {args.format}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render a TurboT2AV student or teacher run_av_inference_eval command. "
            "The command is printed only; it is not executed."
        ),
        epilog=(
            "Use --launcher pixi from an LTX-2 Pixi workspace, or --launcher python "
            "inside an environment where ltx_distillation is already importable. "
            "Use --pythonpath for source-layout TurboDiffusion/LTX imports."
        ),
    )

    required = parser.add_argument_group("required path inputs")
    required.add_argument("--config-path", required=True, help="LTX/TurboT2AV config YAML path.")
    required.add_argument("--prompts-file", required=True, help="Text or CSV prompts file.")
    required.add_argument("--output-dir", required=True, help="Inference output directory path to pass through.")
    required.add_argument(
        "--base-checkpoint",
        required=True,
        help="LTX-2 base checkpoint path; rendered as TURBO_CHECKPOINT_PATH.",
    )
    required.add_argument(
        "--gemma-path",
        required=True,
        help="Local Gemma model directory; rendered as TURBO_GEMMA_PATH. Do not pass tokens here.",
    )

    model = parser.add_argument_group("student/teacher selection")
    model.add_argument("--model-kind", choices=("student", "teacher"), default="student")
    model.add_argument("--student-checkpoint", help="Required for --model-kind student.")
    model.add_argument("--student-param", choices=STUDENT_PARAMS, default="auto")
    model.add_argument("--student-strict", action="store_true", help="Require strict student state-dict loading.")
    model.add_argument("--teacher-mode", choices=TEACHER_MODES, default="native_rf")
    model.add_argument("--teacher-steps", type=positive_int, default=40)

    run = parser.add_argument_group("run controls")
    run.add_argument("--num-prompts", type=positive_int)
    run.add_argument("--seed", type=int)
    run.add_argument("--num-seeds", type=positive_int)
    run.add_argument("--same-seed-for-all-prompts", action="store_true")
    run.add_argument("--num-shards", type=positive_int)
    run.add_argument("--shard-id", type=nonnegative_int)
    run.add_argument("--overwrite", action="store_true")
    run.add_argument("--cache-state-dicts", action="store_true")
    run.add_argument("--init-lock-path")
    run.add_argument("--no-init-lock", action="store_true")
    run.add_argument("--skip-decode", action="store_true")
    run.add_argument("--warmup-samples", type=nonnegative_int)
    run.add_argument("--timing-json")
    run.add_argument("--video-height", type=positive_int)
    run.add_argument("--video-width", type=positive_int)
    run.add_argument("--num-frames", type=positive_int)

    accel = parser.add_argument_group("TurboT2AV acceleration")
    accel.add_argument(
        "--acceleration-preset",
        choices=("auto", "student-recommended", "teacher-w8a8-fastnorm", "none", "custom"),
        default="auto",
        help=(
            "auto expands to student-recommended for student runs and none for teacher runs. "
            "custom emits only explicitly supplied acceleration flags."
        ),
    )
    accel.add_argument("--attention-type", choices=ATTENTION_TYPES)
    accel.add_argument("--attention-scope", choices=ATTENTION_SCOPES)
    accel.add_argument("--sla-topk", type=positive_sla_topk)
    accel.add_argument("--sla-topk-schedule")
    accel.add_argument("--sla-block-q", type=positive_int)
    accel.add_argument("--sla-block-k", type=positive_int)
    accel.add_argument("--trim-text-context", dest="trim_text_context", action=argparse.BooleanOptionalAction)
    accel.add_argument("--fast-norm", dest="fast_norm", action=argparse.BooleanOptionalAction)
    accel.add_argument("--quant-linear", dest="quant_linear", action=argparse.BooleanOptionalAction)
    accel.add_argument("--quant-linear-scope", choices=QUANT_LINEAR_SCOPES)
    accel.add_argument("--quant-linear-backend", choices=QUANT_LINEAR_BACKENDS)

    render = parser.add_argument_group("rendering")
    render.add_argument("--launcher", choices=("pixi", "python"), default="pixi")
    render.add_argument(
        "--cuda-visible-devices",
        default="0",
        help="CUDA_VISIBLE_DEVICES value to render. Use an empty string only if that is intentional.",
    )
    render.add_argument(
        "--pythonpath",
        action="append",
        default=[],
        help="Source-layout PYTHONPATH entry to prefix; repeat for multiple entries.",
    )
    render.add_argument(
        "--format",
        choices=("shell", "json", "argv-json"),
        default="shell",
        help="Output format. shell is a copy/paste command; json separates env and argv.",
    )
    render.add_argument("--no-comments", action="store_true", help="Suppress explanatory shell comments.")
    render.add_argument(
        "--check-existing-inputs",
        action="store_true",
        help="Optionally verify input paths exist without creating or modifying anything.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_required_args(args)
    accel = resolve_preset(args)
    env = build_env(args)
    command_argv = build_argv(args, accel)
    emit(args, env, command_argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
