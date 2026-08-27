#!/usr/bin/env python3
"""Build a FastReID train/eval command without executing it.

The helper is safe by default: it validates command structure, prints a shell
command, and exits. The printed command uses the bundled
`run_training_entrypoint.py` wrapper rather than an upstream source-tree script.

Examples
--------
Build a 1-GPU training command:

python train_command_builder.py \
  --repo-root <FASTREID_REPO> \
  --config-file <CONFIG_YAML> \
  --device cuda:0 \
  --output-dir <RUN_OUTPUT_DIR>

Build eval-only and require an explicit checkpoint:

python train_command_builder.py \
  --repo-root <FASTREID_REPO> \
  --config-file <CONFIG_YAML> \
  --eval-only \
  --weights <CHECKPOINT_FILE.pth> \
  --device cuda:0 \
  --output-dir <EVAL_OUTPUT_DIR>
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import urlparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and print a FastReID train/eval command without executing it.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional FastReID checkout root to pass to the bundled entrypoint for source-only imports.",
    )
    parser.add_argument(
        "--entrypoint",
        type=Path,
        default=Path(__file__).with_name("run_training_entrypoint.py"),
        help="Bundled training entrypoint to use in the printed command.",
    )
    parser.add_argument("--python", default="python3", help="Python executable name for the printed command.")
    parser.add_argument("--config-file", required=True, help="FastReID config file to pass to --config-file.")
    parser.add_argument("--resume", action="store_true", help="Include --resume for OUTPUT_DIR/last_checkpoint resume.")
    parser.add_argument("--eval-only", action="store_true", help="Include --eval-only. Requires --weights.")
    parser.add_argument("--weights", default=None, help="Checkpoint path to set as MODEL.WEIGHTS. Required for --eval-only.")
    parser.add_argument("--device", default=None, help="Device override such as cuda, cuda:0, or cpu.")
    parser.add_argument("--num-gpus", type=int, default=1, help="Number of GPUs per machine. Default: 1.")
    parser.add_argument("--num-machines", type=int, default=1, help="Total number of machines. Default: 1.")
    parser.add_argument("--machine-rank", type=int, default=0, help="Rank of this machine. Default: 0.")
    parser.add_argument("--dist-url", default=None, help="Distributed init URL, for example tcp://host:port or auto.")
    parser.add_argument("--output-dir", default=None, help="Optional OUTPUT_DIR config override.")
    parser.add_argument(
        "--disable-pretrain",
        action="store_true",
        help="Append MODEL.BACKBONE.PRETRAIN False; eval-only commands add this automatically.",
    )
    parser.add_argument(
        "--entrypoint-dry-run",
        action="store_true",
        help="Print a command that calls the bundled entrypoint with --dry-run instead of --confirm-run.",
    )
    parser.add_argument(
        "--require-existing-paths",
        action="store_true",
        help="Require repo root, bundled entrypoint, config file, and local checkpoint paths to exist.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human-readable text.")
    parser.add_argument(
        "--opts",
        nargs=argparse.REMAINDER,
        default=[],
        metavar="KEY VALUE",
        help="Additional FastReID config overrides. Put --opts last.",
    )
    return parser


def normalize_remainder(tokens: Sequence[str]) -> list[str]:
    items = list(tokens)
    if items[:1] == ["--"]:
        items = items[1:]
    return items


def opts_to_pairs(tokens: Sequence[str], parser: argparse.ArgumentParser) -> list[tuple[str, str]]:
    items = normalize_remainder(tokens)
    if len(items) % 2 != 0:
        parser.error("--opts must contain an even number of KEY VALUE tokens")
    return [(items[i], items[i + 1]) for i in range(0, len(items), 2)]


def pair_map(pairs: Iterable[tuple[str, str]]) -> dict[str, str]:
    return {key: value for key, value in pairs}


def is_local_existing_candidate(raw: str) -> bool:
    parsed = urlparse(raw)
    return parsed.scheme == "" or parsed.scheme == "file"


def resolve_against_repo(repo_root: Path | None, raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute() or repo_root is None:
        return path
    return repo_root / path


def positive_int(parser: argparse.ArgumentParser, value: int, name: str) -> None:
    if value < 1:
        parser.error(f"{name} must be >= 1")


def add_or_override(pairs: list[tuple[str, str]], key: str, value: str, warnings: list[str], reason: str) -> None:
    if any(existing_key == key for existing_key, _ in pairs):
        warnings.append(f"{reason}: overriding earlier {key} from --opts with {value!r}.")
    pairs.append((key, value))


def parse_int_opt(mapping: dict[str, str], key: str) -> int | None:
    if key not in mapping:
        return None
    try:
        return int(mapping[key])
    except (TypeError, ValueError):
        return None


def quote_command(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    positive_int(parser, args.num_gpus, "--num-gpus")
    positive_int(parser, args.num_machines, "--num-machines")
    if not 0 <= args.machine_rank < args.num_machines:
        parser.error("--machine-rank must satisfy 0 <= rank < --num-machines")
    if args.eval_only and not args.weights:
        parser.error("--eval-only requires --weights so MODEL.WEIGHTS is explicit")

    repo_root = args.repo_root.expanduser().resolve() if args.repo_root else None
    entrypoint = args.entrypoint.expanduser().resolve()
    if args.require_existing_paths:
        if not entrypoint.is_file():
            parser.error(f"bundled entrypoint does not exist: {entrypoint}")
        if repo_root is not None and not repo_root.is_dir():
            parser.error(f"--repo-root does not exist or is not a directory: {repo_root}")
        config_path = resolve_against_repo(repo_root, args.config_file)
        if is_local_existing_candidate(args.config_file) and not config_path.is_file():
            parser.error(f"--config-file does not exist: {config_path}")
        if args.weights and is_local_existing_candidate(args.weights):
            weights_path = resolve_against_repo(repo_root, args.weights)
            if not weights_path.is_file():
                parser.error(f"--weights does not exist: {weights_path}")

    warnings: list[str] = []
    pairs = opts_to_pairs(args.opts, parser)
    if args.weights:
        add_or_override(pairs, "MODEL.WEIGHTS", args.weights, warnings, "checkpoint selection")
    if args.device:
        add_or_override(pairs, "MODEL.DEVICE", args.device, warnings, "device selection")
    if args.output_dir:
        add_or_override(pairs, "OUTPUT_DIR", args.output_dir, warnings, "output directory selection")
    if args.eval_only or args.disable_pretrain:
        add_or_override(pairs, "MODEL.BACKBONE.PRETRAIN", "False", warnings, "pretrain download guard")

    final_opts = pair_map(pairs)
    world_size = args.num_gpus * args.num_machines
    if world_size > 1 and final_opts.get("MODEL.DEVICE", "cuda").lower().startswith("cpu"):
        parser.error("distributed launch with world_size > 1 requires CUDA; do not set MODEL.DEVICE cpu")
    if args.num_machines > 1 and not args.dist_url:
        warnings.append("multi-machine launch should set --dist-url tcp://<rank0_host>:<port> explicitly.")
    if args.num_machines > 1 and args.dist_url == "auto":
        parser.error("--dist-url auto is only suitable for single-machine distributed launch")

    for batch_key in ("SOLVER.IMS_PER_BATCH", "TEST.IMS_PER_BATCH"):
        batch = parse_int_opt(final_opts, batch_key)
        if batch is not None:
            if batch < world_size:
                warnings.append(f"{batch_key}={batch} is smaller than world_size={world_size}.")
            elif batch % world_size != 0:
                warnings.append(f"{batch_key}={batch} is not divisible by world_size={world_size}.")

    train_batch = parse_int_opt(final_opts, "SOLVER.IMS_PER_BATCH")
    num_instance = parse_int_opt(final_opts, "DATALOADER.NUM_INSTANCE")
    if train_batch is not None and num_instance is not None:
        per_rank = train_batch // world_size
        if per_rank < num_instance:
            warnings.append("per-rank training batch is smaller than DATALOADER.NUM_INSTANCE; identity samplers may fail.")
        elif per_rank % num_instance != 0:
            warnings.append("per-rank training batch is not divisible by DATALOADER.NUM_INSTANCE; check identity sampler behavior.")

    parts: list[str] = [args.python, str(entrypoint)]
    if repo_root is not None:
        parts.extend(["--repo-root", str(repo_root)])
    parts.append("--dry-run" if args.entrypoint_dry_run else "--confirm-run")
    parts.extend(["--config-file", args.config_file])
    if args.resume:
        parts.append("--resume")
    if args.eval_only:
        parts.append("--eval-only")
    if args.num_gpus != 1:
        parts.extend(["--num-gpus", str(args.num_gpus)])
    if args.num_machines != 1:
        parts.extend(["--num-machines", str(args.num_machines)])
    if args.machine_rank != 0:
        parts.extend(["--machine-rank", str(args.machine_rank)])
    if args.dist_url:
        parts.extend(["--dist-url", args.dist_url])
    for key, value in pairs:
        parts.extend([key, value])

    shell_command = quote_command(parts)
    requirements = [
        "FastReID package must be importable, or pass --repo-root for a local source checkout.",
        "Selected config must merge successfully before launch.",
        "Configured datasets must be present and registered before train/eval.",
    ]
    if args.eval_only:
        requirements.append("Eval-only requires the MODEL.WEIGHTS checkpoint and configured test dataset.")
        requirements.append("The command includes MODEL.BACKBONE.PRETRAIN False to avoid backbone pretrain downloads.")
    if world_size > 1:
        requirements.append("Distributed launch requires CUDA/NCCL and matching rank/dist-url settings.")

    payload = {
        "command": shell_command,
        "will_execute": False,
        "entrypoint_mode": "dry-run" if args.entrypoint_dry_run else "confirmed-run command",
        "mode": "eval-only" if args.eval_only else "train",
        "world_size": world_size,
        "repo_root_supplied": repo_root is not None,
        "requirements": requirements,
        "warnings": warnings,
    }
    if args.json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print("Command (not executed):")
        print(shell_command)
        print("\nRequirements:")
        for item in requirements:
            print(f"- {item}")
        if warnings:
            print("\nWarnings:")
            for item in warnings:
                print(f"- {item}")
        else:
            print("\nWarnings: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
