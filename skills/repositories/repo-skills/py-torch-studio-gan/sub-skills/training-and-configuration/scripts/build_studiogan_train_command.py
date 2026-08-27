#!/usr/bin/env python3
"""Build a safe StudioGAN training command without executing it."""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

VALID_METRICS = {"is", "fid", "prdc", "none"}
VALID_PRE_RESIZERS = {"wo_resize", "nearest", "bilinear", "bicubic", "lanczos"}
VALID_POST_RESIZERS = {"legacy", "clean", "friendly"}
VALID_BACKBONES = {
    "InceptionV3_tf",
    "InceptionV3_torch",
    "ResNet50_torch",
    "SwAV_torch",
    "DINO_torch",
    "Swin-T_torch",
}


class CommandError(RuntimeError):
    """Raised for user-correctable command construction failures."""


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def normalize_path(value: str, *, base: Optional[Path] = None) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute() and base is not None:
        path = base / path
    return path.resolve(strict=False)


def visible_gpu_count(value: str) -> int:
    text = value.strip()
    if not text:
        return 1
    return max(1, len([item for item in text.split(",") if item.strip()]))


def normalize_metrics(metrics: List[str]) -> List[str]:
    normalized = [item.lower() for item in metrics]
    invalid = sorted(set(normalized) - VALID_METRICS)
    if invalid:
        raise CommandError("unsupported metrics: " + ", ".join(invalid) + " (expected is, fid, prdc, or none)")
    if "none" in normalized and len(normalized) > 1:
        raise CommandError("use -metrics none by itself; do not combine none with metric names")
    return normalized


def load_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception:
        warn("PyYAML is not importable; skipping YAML-derived batch-size checks.")
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
    except Exception as exc:  # noqa: BLE001 - concise user-facing parse error.
        raise CommandError(f"could not read YAML config {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise CommandError(f"YAML config {path} did not parse to a mapping")
    return loaded


def nested_get(mapping: Dict[str, Any], section: str, key: str, default: Any) -> Any:
    section_data = mapping.get(section, {})
    if isinstance(section_data, dict) and key in section_data:
        return section_data[key]
    return default


def append_if(command: List[str], condition: bool, *parts: str) -> None:
    if condition:
        command.extend(parts)


def quote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build and print a StudioGAN src/main.py training command. "
            "The command is not executed, no data is downloaded, and no output directories are written."
        )
    )
    parser.add_argument("--repo-root", required=True, help="Path to a StudioGAN checkout containing src/main.py.")
    parser.add_argument("--cfg", required=True, help="StudioGAN YAML config path; relative paths resolve under --repo-root.")
    parser.add_argument("--data-dir", required=True, help="Dataset root passed to native -data.")
    parser.add_argument("--save-dir", required=True, help="Output root passed to native -save.")
    parser.add_argument("--gpus", default="0", help="CUDA_VISIBLE_DEVICES value for the printed command. Default: 0.")
    parser.add_argument("--python", default="python", help="Python executable token to print. Default: python.")
    parser.add_argument("--metrics", nargs="+", default=["fid"], help="Native -metrics values: is fid prdc none. Default: fid.")
    parser.add_argument("--dry-run-no-path-check", action="store_true", help="Skip repo/config existence checks for command drafting.")

    parser.add_argument("--ddp", action="store_true", help="Add native -DDP. Set MASTER_ADDR/MASTER_PORT before running.")
    parser.add_argument("--backend", default="nccl", help="Add native --backend value when DDP is selected. Default: nccl.")
    parser.add_argument("--total-nodes", type=int, default=1, help="Add native -tn when greater than 1. Default: 1.")
    parser.add_argument("--current-node", type=int, default=0, help="Add native -cn when nonzero. Default: 0.")
    parser.add_argument("--sync-bn", action="store_true", help="Add native -sync_bn.")
    parser.add_argument("--mixed-precision", action="store_true", help="Add native -mpc.")
    parser.add_argument("--hdf5", action="store_true", help="Add native -hdf5.")
    parser.add_argument("--load-in-memory", action="store_true", help="Add native -l; requires --hdf5.")
    parser.add_argument("--checkpoint", help="Add native -ckpt for resume or FreezeD transfer.")
    parser.add_argument("--load-best", action="store_true", help="Add native -best with --checkpoint.")
    parser.add_argument("--freeze-d", type=int, help="Add native --freezeD N; requires --checkpoint.")
    parser.add_argument("--pre-resizer", default="wo_resize", choices=sorted(VALID_PRE_RESIZERS), help="Add native --pre_resizer. Default: wo_resize.")
    parser.add_argument("--post-resizer", default="legacy", choices=sorted(VALID_POST_RESIZERS), help="Add native --post_resizer. Default: legacy.")
    parser.add_argument("--eval-backbone", default="InceptionV3_tf", choices=sorted(VALID_BACKBONES), help="Add native --eval_backbone. Default: InceptionV3_tf.")
    parser.add_argument("--ref", default="train", help="Add native -ref/--ref_dataset. Common values: train, valid, test. Default: train.")
    parser.add_argument("--print-freq", type=int, default=100, help="Add native --print_freq. Default: 100.")
    parser.add_argument("--save-freq", type=int, default=2000, help="Add native --save_freq. Default: 2000.")
    parser.add_argument("--num-workers", type=int, help="Add native --num_workers.")
    parser.add_argument("--seed", type=int, help="Add native --seed.")
    return parser


def validate_args(args: argparse.Namespace, cfg_path: Path, gpu_count: int, metrics: List[str]) -> None:
    if args.total_nodes <= 0:
        raise CommandError("--total-nodes must be positive")
    if args.current_node < 0:
        raise CommandError("--current-node must be non-negative")
    if args.print_freq <= 0 or args.save_freq <= 0:
        raise CommandError("--print-freq and --save-freq must be positive")
    if args.save_freq % args.print_freq != 0:
        raise CommandError("native RUN.save_freq must be divisible by RUN.print_freq")
    if args.load_in_memory and not args.hdf5:
        raise CommandError("--load-in-memory maps to native -l and requires --hdf5")
    if args.load_best and args.checkpoint is None:
        raise CommandError("--load-best maps to native -best and should be used with --checkpoint")
    if args.freeze_d is not None:
        if args.freeze_d < 0:
            raise CommandError("--freeze-d must be non-negative when supplied")
        if args.checkpoint is None:
            raise CommandError("--freeze-d maps to native --freezeD and requires --checkpoint")
    if args.ddp and gpu_count <= 1:
        raise CommandError("--ddp requires more than one visible GPU in --gpus")

    if cfg_path.exists() and cfg_path.is_file():
        cfg = load_yaml(cfg_path)
        batch_size_raw = nested_get(cfg, "OPTIMIZATION", "batch_size", 64)
        try:
            batch_size = int(batch_size_raw)
        except Exception:
            warn(f"could not interpret OPTIMIZATION.batch_size={batch_size_raw!r}; skipping divisibility check.")
        else:
            world_size = gpu_count * args.total_nodes
            if batch_size % world_size != 0:
                raise CommandError(f"OPTIMIZATION.batch_size={batch_size} is not divisible by world size {world_size}")

    if "none" in metrics:
        warn("-metrics none skips StudioGAN metric evaluation during training; this is useful for infrastructure smoke runs.")
    if args.ddp:
        warn("DDP commands require MASTER_ADDR and MASTER_PORT in the shell before execution.")


def build_command(args: argparse.Namespace, repo_root: Path, cfg_path: Path, data_dir: Path, save_dir: Path,
                  checkpoint: Optional[Path], metrics: List[str]) -> List[str]:
    main_py = repo_root / "src" / "main.py"
    command: List[str] = []
    if args.gpus:
        command.append(f"CUDA_VISIBLE_DEVICES={args.gpus}")
    command.extend([
        args.python,
        str(main_py),
        "-t",
        "-cfg",
        str(cfg_path),
        "-data",
        str(data_dir),
        "-save",
        str(save_dir),
        "-metrics",
        *metrics,
    ])
    if args.ddp:
        command.append("-DDP")
        command.extend(["--backend", args.backend])
    if args.total_nodes != 1:
        command.extend(["-tn", str(args.total_nodes)])
    if args.current_node != 0:
        command.extend(["-cn", str(args.current_node)])
    append_if(command, args.sync_bn, "-sync_bn")
    append_if(command, args.mixed_precision, "-mpc")
    append_if(command, args.hdf5, "-hdf5")
    append_if(command, args.load_in_memory, "-l")
    if checkpoint is not None:
        command.extend(["-ckpt", str(checkpoint)])
    append_if(command, args.load_best, "-best")
    if args.freeze_d is not None:
        command.extend(["--freezeD", str(args.freeze_d)])
    if args.pre_resizer != "wo_resize":
        command.extend(["--pre_resizer", args.pre_resizer])
    if args.post_resizer != "legacy":
        command.extend(["--post_resizer", args.post_resizer])
    if args.eval_backbone != "InceptionV3_tf":
        command.extend(["--eval_backbone", args.eval_backbone])
    if args.ref != "train":
        command.extend(["-ref", args.ref])
    if args.print_freq != 100:
        command.extend(["--print_freq", str(args.print_freq)])
    if args.save_freq != 2000:
        command.extend(["--save_freq", str(args.save_freq)])
    if args.num_workers is not None:
        command.extend(["--num_workers", str(args.num_workers)])
    if args.seed is not None:
        command.extend(["--seed", str(args.seed)])
    return command


def main(argv: Optional[List[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    try:
        metrics = normalize_metrics(args.metrics)
        repo_root = normalize_path(args.repo_root)
        cfg_path = normalize_path(args.cfg, base=repo_root)
        data_dir = normalize_path(args.data_dir)
        save_dir = normalize_path(args.save_dir)
        checkpoint = normalize_path(args.checkpoint) if args.checkpoint is not None else None

        if not args.dry_run_no_path_check:
            if not repo_root.exists() or not repo_root.is_dir():
                raise CommandError(f"--repo-root is not a directory: {repo_root}")
            if not (repo_root / "src" / "main.py").is_file():
                raise CommandError(f"--repo-root does not contain src/main.py: {repo_root}")
            if not cfg_path.is_file():
                raise CommandError(f"--cfg is not a file: {cfg_path}")
            if checkpoint is not None and not checkpoint.exists():
                warn(f"checkpoint path does not exist yet: {checkpoint}")
            if not data_dir.exists():
                warn(f"data directory does not exist yet: {data_dir}")

        gpu_count = visible_gpu_count(args.gpus)
        validate_args(args, cfg_path, gpu_count, metrics)
        command = build_command(args, repo_root, cfg_path, data_dir, save_dir, checkpoint, metrics)
        print(quote_command(command))
        return 0
    except CommandError as exc:
        parser.exit(status=2, message=f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
