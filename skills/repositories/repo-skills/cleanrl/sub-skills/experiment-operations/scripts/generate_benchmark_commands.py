#!/usr/bin/env python3
"""Generate CleanRL benchmark command matrices without executing them."""

from __future__ import annotations

import argparse
import json
import math
import re
import shlex
import sys
from dataclasses import dataclass
from typing import Iterable

SENSITIVE_ENV_NAMES = {
    "WANDB_API_KEY",
    "WANDB_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "HF_TOKEN",
    "HUGGINGFACE_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
}


@dataclass(frozen=True)
class GeneratedMatrix:
    commands: list[str]
    env_ids: list[str]
    seeds: list[int]
    warnings: list[str]
    wandb_tags: str


def split_tags(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def combine_tags(existing: str, new: str) -> str:
    tags: list[str] = []
    for candidate in split_tags(existing) + split_tags(new):
        if candidate not in tags:
            tags.append(candidate)
    return ",".join(tags)


def redact_sensitive_assignments(command: str) -> str:
    redacted = command
    for name in sorted(SENSITIVE_ENV_NAMES, key=len, reverse=True):
        redacted = re.sub(rf"(?<![A-Za-z0-9_]){name}=([^\s]+)", f"{name}=<redacted>", redacted)
    redacted = re.sub(r"(--(?:wandb-key|wandb-api-key|aws-secret-access-key|hf-token))\s+\S+", r"\1 <redacted>", redacted)
    redacted = re.sub(r"(--(?:wandb-key|wandb-api-key|aws-secret-access-key|hf-token))=\S+", r"\1=<redacted>", redacted)
    return redacted


def detect_duplicate_flags(command: str) -> list[str]:
    warnings: list[str] = []
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        return [f"could not parse command for duplicate flag detection: {exc}"]
    for flag in ("--env-id", "--seed"):
        if flag in parts or any(part.startswith(f"{flag}=") for part in parts):
            warnings.append(f"base command already contains {flag}; generated commands append another value")
    return warnings


def generate_matrix(
    command: str,
    env_ids: Iterable[str],
    num_seeds: int,
    start_seed: int,
    existing_wandb_tags: str = "",
    wandb_tags: str = "",
) -> GeneratedMatrix:
    env_id_list = list(env_ids)
    if not env_id_list:
        raise ValueError("at least one --env-ids value is required")
    if num_seeds < 1:
        raise ValueError("--num-seeds must be at least 1")

    combined_tags = combine_tags(existing_wandb_tags, wandb_tags)
    seeds = list(range(start_seed, start_seed + num_seeds))
    warnings = detect_duplicate_flags(command)
    commands: list[str] = []
    prefix = f"WANDB_TAGS={shlex.quote(combined_tags)} " if combined_tags else ""
    for seed in seeds:
        for env_id in env_id_list:
            command_line = f"{prefix}{command.rstrip()} --env-id {shlex.quote(env_id)} --seed {seed}"
            commands.append(redact_sensitive_assignments(command_line))
    return GeneratedMatrix(commands=commands, env_ids=env_id_list, seeds=seeds, warnings=warnings, wandb_tags=combined_tags)


def render_text(matrix: GeneratedMatrix) -> str:
    lines = [
        f"# command_count={len(matrix.commands)} env_count={len(matrix.env_ids)} seed_count={len(matrix.seeds)}",
    ]
    if matrix.wandb_tags:
        lines.append(f"# WANDB_TAGS={matrix.wandb_tags}")
    for warning in matrix.warnings:
        lines.append(f"# WARNING: {warning}")
    lines.extend(matrix.commands)
    return "\n".join(lines) + "\n"


def bash_array(items: Iterable[str]) -> str:
    return "(" + " ".join(shlex.quote(str(item)) for item in items) + ")"


def render_slurm(matrix: GeneratedMatrix, args: argparse.Namespace) -> str:
    total = len(matrix.commands)
    concurrency = args.workers if args.workers > 0 else total
    if concurrency < 1:
        concurrency = 1
    if args.slurm_gpus_per_task < 1:
        raise ValueError("--slurm-gpus-per-task must be at least 1 for Slurm preview")
    if args.slurm_ntasks < 1:
        raise ValueError("--slurm-ntasks must be at least 1 for Slurm preview")
    total_gpus = args.slurm_gpus_per_task * args.slurm_ntasks
    cpus_per_gpu = math.ceil(args.slurm_total_cpus / total_gpus)
    nodes_line = f"#SBATCH --nodes={args.slurm_nodes}" if args.slurm_nodes is not None else ""
    tags_line = f"export WANDB_TAGS={shlex.quote(matrix.wandb_tags)}" if matrix.wandb_tags else ""
    warning_lines = "\n".join(f"# WARNING: {warning}" for warning in matrix.warnings)
    command = redact_sensitive_assignments(args.command.rstrip())
    sections = [
        "#!/bin/bash",
        "# Generated preview only; review before saving or submitting with sbatch.",
        "#SBATCH --job-name=cleanrl-benchmark",
        f"#SBATCH --gpus-per-task={args.slurm_gpus_per_task}",
        f"#SBATCH --cpus-per-gpu={cpus_per_gpu}",
        f"#SBATCH --ntasks={args.slurm_ntasks}",
        "#SBATCH --output=slurm/logs/%x_%j.out",
        f"#SBATCH --array=0-{total - 1}%{concurrency}",
    ]
    if nodes_line:
        sections.append(nodes_line)
    if warning_lines:
        sections.append(warning_lines)
    sections.extend(
        [
            "",
            f"env_ids={bash_array(matrix.env_ids)}",
            f"seeds={bash_array(str(seed) for seed in matrix.seeds)}",
            f"len_seeds={len(matrix.seeds)}",
            'env_id=${env_ids[$SLURM_ARRAY_TASK_ID / $len_seeds]}',
            'seed=${seeds[$SLURM_ARRAY_TASK_ID % $len_seeds]}',
            "",
            'echo "Running task $SLURM_ARRAY_TASK_ID with env_id: $env_id and seed: $seed"',
        ]
    )
    if tags_line:
        sections.append(tags_line)
    sections.append(f'srun {command} --env-id "$env_id" --seed "$seed"')
    return "\n".join(sections) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely generate CleanRL benchmark command matrices without execution.")
    parser.add_argument("--env-ids", nargs="+", required=True, help="Environment ids to expand.")
    parser.add_argument("--command", required=True, help="Base training command; --env-id and --seed are appended.")
    parser.add_argument("--num-seeds", type=int, default=3, help="Number of seeds to generate.")
    parser.add_argument("--start-seed", type=int, default=1, help="First seed value.")
    parser.add_argument("--workers", type=int, default=0, help="Previewed concurrency for Slurm array output; never executes.")
    parser.add_argument("--wandb-tags", default="", help="Comma-separated W&B tags to include in previews.")
    parser.add_argument("--existing-wandb-tags", default="", help="Existing comma-separated W&B tags to merge before new tags.")
    parser.add_argument("--output-format", choices=["text", "json", "slurm"], default="text", help="Preview format.")
    parser.add_argument("--output", help="Optional file to write the preview to; stdout is always safe and no commands are run.")
    parser.add_argument("--slurm-gpus-per-task", type=int, default=1, help="Slurm preview GPUs per task.")
    parser.add_argument("--slurm-total-cpus", type=int, default=1, help="Slurm preview total CPUs across GPUs/tasks.")
    parser.add_argument("--slurm-ntasks", type=int, default=1, help="Slurm preview task count.")
    parser.add_argument("--slurm-nodes", type=int, help="Optional Slurm preview node count.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        matrix = generate_matrix(
            command=args.command,
            env_ids=args.env_ids,
            num_seeds=args.num_seeds,
            start_seed=args.start_seed,
            existing_wandb_tags=args.existing_wandb_tags,
            wandb_tags=args.wandb_tags,
        )
        if args.output_format == "json":
            rendered = json.dumps(
                {
                    "command_count": len(matrix.commands),
                    "env_ids": matrix.env_ids,
                    "seeds": matrix.seeds,
                    "wandb_tags": matrix.wandb_tags,
                    "warnings": matrix.warnings,
                    "commands": matrix.commands,
                },
                indent=2,
            ) + "\n"
        elif args.output_format == "slurm":
            rendered = render_slurm(matrix, args)
        else:
            rendered = render_text(matrix)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.output:
        with open(args.output, "w", encoding="utf-8") as output_file:
            output_file.write(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
