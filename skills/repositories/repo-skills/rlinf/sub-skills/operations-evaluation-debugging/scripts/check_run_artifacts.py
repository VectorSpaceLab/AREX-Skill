#!/usr/bin/env python3
"""Read-only RLinf run artifact checker.

The checker summarizes likely logs, checkpoints, metric fragments, backend logger
folders, videos, profiling/tracing outputs, and common failure fragments. It never
writes to the inspected run directory.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

LOG_NAMES = {
    "run_embodiment.log",
    "eval_embodiment.log",
    "run_ppo.log",
    "metrics.log",
}
LOG_SUFFIXES = {".log", ".out", ".err", ".txt"}
VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".gif"}
CONFIG_SUFFIXES = {".yaml", ".yml", ".json", ".toml"}
BACKEND_DIR_NAMES = {
    "tensorboard",
    "wandb",
    "swanlab",
    "worker_logs",
    "profiling",
    "trace",
    "checkpoints",
    "converted_ckpts",
    "video",
}
ERROR_PATTERNS = [
    r"Traceback\s*\(most recent call last\)",
    r"CUDA out of memory",
    r"\bOOM\b",
    r"\bKilled\b",
    r"RuntimeError",
    r"AssertionError",
    r"Segmentation fault",
    r"Aborted",
    r"Cannot connect to GCS",
    r"Gloo.*timeout|unbound_buffer\.cc|Global rank .* not part of group",
    r"NCCL.*cuda invalid argument",
    r"CUresult error.*torch_memory_saver",
    r"MUJOCO_EGL_DEVICE_ID",
    r"Vulkan.*driver|Incompatible GPU driver",
    r"No such file or directory",
    r"FileNotFoundError",
    r"ModuleNotFoundError",
    r"ValueError",
]
ERROR_RE = re.compile("|".join(f"(?:{p})" for p in ERROR_PATTERNS), re.IGNORECASE)
GLOBAL_STEP_RE = re.compile(r"Global Step:\s*(\d+)\s*/\s*(\d+)")
SUCCESS_RE = re.compile(r"(?:(?:eval|env)/)?success_once[\w/]*\s*[=:]\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)")
RETURN_RE = re.compile(r"(?:(?:eval|env)/)?return[\w/]*\s*[=:]\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)")
GLOBAL_STEP_DIR_RE = re.compile(r"global_step_(\d+)$")


@dataclass
class LogSummary:
    path: str
    size_bytes: int
    last_global_step: dict[str, int] | None = None
    last_success_once: float | None = None
    last_return: float | None = None
    error_fragments: list[str] = field(default_factory=list)


@dataclass
class CheckpointSummary:
    path: str
    step: int
    has_actor: bool
    has_critic: bool
    has_data_pt: bool
    has_distcp: bool
    has_full_weights: bool
    has_megatron_rank: bool
    has_latest_iteration: bool
    likely_format: str


@dataclass
class ArtifactSummary:
    root: str
    exists: bool
    log_files: list[LogSummary] = field(default_factory=list)
    checkpoint_dirs: list[CheckpointSummary] = field(default_factory=list)
    backend_dirs: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    video_files: list[str] = field(default_factory=list)
    profiling_files: list[str] = field(default_factory=list)
    trace_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def iter_files(root: Path, max_depth: int, max_files: int) -> Iterable[Path]:
    count = 0
    root_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        depth = len(current.parts) - root_depth
        if depth >= max_depth:
            dirnames[:] = []
        for filename in filenames:
            count += 1
            if count > max_files:
                return
            yield current / filename


def iter_dirs(root: Path, max_depth: int, max_dirs: int) -> Iterable[Path]:
    count = 0
    root_depth = len(root.parts)
    for dirpath, dirnames, _filenames in os.walk(root):
        current = Path(dirpath)
        depth = len(current.parts) - root_depth
        if depth > 0:
            count += 1
            if count > max_dirs:
                return
            yield current
        if depth >= max_depth:
            dirnames[:] = []


def read_tail(path: Path, max_bytes: int) -> str:
    try:
        size = path.stat().st_size
        with path.open("rb") as file_obj:
            if size > max_bytes:
                file_obj.seek(max(0, size - max_bytes))
            raw = file_obj.read(max_bytes)
        return raw.decode("utf-8", errors="replace")
    except OSError as exc:
        return f"<could not read log: {exc}>"


def summarize_log(path: Path, root: Path, max_log_bytes: int, max_errors: int) -> LogSummary:
    text = read_tail(path, max_log_bytes)
    steps = [(int(a), int(b)) for a, b in GLOBAL_STEP_RE.findall(text)]
    successes = [float(x) for x in SUCCESS_RE.findall(text)]
    returns = [float(x) for x in RETURN_RE.findall(text)]

    fragments: list[str] = []
    for line in text.splitlines():
        if ERROR_RE.search(line):
            compact = " ".join(line.strip().split())
            if compact and compact not in fragments:
                fragments.append(compact[:300])
            if len(fragments) >= max_errors:
                break

    return LogSummary(
        path=rel(path, root),
        size_bytes=path.stat().st_size,
        last_global_step={"current": steps[-1][0], "total": steps[-1][1]} if steps else None,
        last_success_once=successes[-1] if successes else None,
        last_return=returns[-1] if returns else None,
        error_fragments=fragments,
    )


def classify_checkpoint(path: Path, root: Path) -> CheckpointSummary:
    match = GLOBAL_STEP_DIR_RE.search(path.name)
    step = int(match.group(1)) if match else -1
    actor = path / "actor"
    critic = path / "critic"
    data_pt = path / "data" / "data.pt"

    has_distcp = any(actor.glob("**/*.distcp")) if actor.exists() else False
    has_full_weights = any(actor.glob("**/full_weights.pt")) or any(
        actor.glob("**/full_weigths.pt")
    )
    has_megatron_rank = any(actor.glob("**/mp_rank_*")) if actor.exists() else False
    has_latest_iteration = (actor / "latest_checkpointed_iteration.txt").exists()

    if has_megatron_rank or has_latest_iteration:
        likely_format = "megatron-sharded"
    elif has_distcp:
        likely_format = "fsdp-dcp"
    elif has_full_weights:
        likely_format = "consolidated-pt"
    elif actor.exists():
        likely_format = "actor-present-unknown"
    else:
        likely_format = "incomplete-or-not-a-checkpoint"

    return CheckpointSummary(
        path=rel(path, root),
        step=step,
        has_actor=actor.exists(),
        has_critic=critic.exists(),
        has_data_pt=data_pt.exists(),
        has_distcp=has_distcp,
        has_full_weights=has_full_weights,
        has_megatron_rank=has_megatron_rank,
        has_latest_iteration=has_latest_iteration,
        likely_format=likely_format,
    )


def asdict_dataclass(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return {k: asdict_dataclass(getattr(obj, k)) for k in obj.__dataclass_fields__}
    if isinstance(obj, list):
        return [asdict_dataclass(x) for x in obj]
    return obj


def inspect_root(path: Path, args: argparse.Namespace) -> ArtifactSummary:
    root = path.expanduser().resolve()
    summary = ArtifactSummary(root=str(root), exists=root.exists())
    if not root.exists():
        summary.warnings.append("root does not exist")
        return summary
    if not root.is_dir():
        summary.warnings.append("root is not a directory")
        return summary

    files = list(iter_files(root, args.max_depth, args.max_files))
    dirs = list(iter_dirs(root, args.max_depth, args.max_dirs))

    for directory in dirs:
        if directory.name in BACKEND_DIR_NAMES:
            summary.backend_dirs.append(rel(directory, root))
        if GLOBAL_STEP_DIR_RE.search(directory.name):
            summary.checkpoint_dirs.append(classify_checkpoint(directory, root))

    for file_path in files:
        name = file_path.name
        suffix = file_path.suffix.lower()
        relative = rel(file_path, root)
        parts = {p.lower() for p in file_path.parts}

        if name in LOG_NAMES or suffix in LOG_SUFFIXES:
            # Avoid treating every metadata text file as a log unless it is small enough and likely relevant.
            if name in LOG_NAMES or suffix == ".log" or "log" in parts or file_path.stat().st_size <= args.max_text_log_bytes:
                summary.log_files.append(
                    summarize_log(file_path, root, args.max_log_bytes, args.max_errors)
                )
        if suffix in VIDEO_SUFFIXES:
            summary.video_files.append(relative)
        if suffix in CONFIG_SUFFIXES and (
            name == "config.yaml" or "tensorboard" in parts or "hydra" in parts or "config" in parts
        ):
            summary.config_files.append(relative)
        if "profiling" in parts or suffix in {".qdrep", ".nsys-rep", ".sqlite"}:
            summary.profiling_files.append(relative)
        if "trace" in parts or name.startswith("trace_events"):
            summary.trace_files.append(relative)

    summary.log_files.sort(key=lambda item: item.path)
    summary.checkpoint_dirs.sort(key=lambda item: item.step)
    summary.backend_dirs = sorted(set(summary.backend_dirs))[: args.max_list]
    summary.config_files = sorted(set(summary.config_files))[: args.max_list]
    summary.video_files = sorted(set(summary.video_files))[: args.max_list]
    summary.profiling_files = sorted(set(summary.profiling_files))[: args.max_list]
    summary.trace_files = sorted(set(summary.trace_files))[: args.max_list]

    if not summary.log_files:
        summary.warnings.append("no obvious log files found")
    if not summary.checkpoint_dirs:
        summary.warnings.append("no global_step_<N> checkpoint directories found")
    if not summary.video_files:
        summary.warnings.append("no video files found")
    if len(files) >= args.max_files:
        summary.warnings.append(f"file scan stopped at max_files={args.max_files}")
    if len(dirs) >= args.max_dirs:
        summary.warnings.append(f"directory scan stopped at max_dirs={args.max_dirs}")
    return summary


def print_text(summary: ArtifactSummary) -> None:
    print(f"\n== {summary.root} ==")
    if not summary.exists:
        print("missing root")
        return

    if summary.warnings:
        print("Warnings:")
        for warning in summary.warnings:
            print(f"  - {warning}")

    print("Backend/artifact dirs:")
    for item in summary.backend_dirs or ["<none>"]:
        print(f"  - {item}")

    print("Logs:")
    for log in summary.log_files or []:
        step = log.last_global_step or {}
        step_text = f" step={step.get('current')}/{step.get('total')}" if step else ""
        success_text = f" success_once={log.last_success_once}" if log.last_success_once is not None else ""
        return_text = f" return={log.last_return}" if log.last_return is not None else ""
        print(f"  - {log.path} ({log.size_bytes} bytes){step_text}{success_text}{return_text}")
        for fragment in log.error_fragments:
            print(f"      ! {fragment}")
    if not summary.log_files:
        print("  - <none>")

    print("Checkpoints:")
    for ckpt in summary.checkpoint_dirs or []:
        flags = []
        for name in ["actor", "critic", "data_pt", "distcp", "full_weights", "megatron_rank", "latest_iteration"]:
            attr = f"has_{name}" if name not in {"actor", "critic"} else f"has_{name}"
            if getattr(ckpt, attr):
                flags.append(name)
        print(f"  - {ckpt.path} step={ckpt.step} format={ckpt.likely_format} flags={','.join(flags) or 'none'}")
    if not summary.checkpoint_dirs:
        print("  - <none>")

    print("Configs:")
    for item in summary.config_files or ["<none>"]:
        print(f"  - {item}")
    print("Videos:")
    for item in summary.video_files or ["<none>"]:
        print(f"  - {item}")
    print("Profiling files:")
    for item in summary.profiling_files or ["<none>"]:
        print(f"  - {item}")
    print("Trace files:")
    for item in summary.trace_files or ["<none>"]:
        print(f"  - {item}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only checker for RLinf log/checkpoint/video/profiling artifact layouts."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Run output directory or experiment directory to inspect.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--max-depth", type=int, default=8, help="Maximum directory depth to scan (default: 8).")
    parser.add_argument("--max-files", type=int, default=5000, help="Maximum files to inspect per root (default: 5000).")
    parser.add_argument("--max-dirs", type=int, default=2000, help="Maximum directories to inspect per root (default: 2000).")
    parser.add_argument("--max-list", type=int, default=200, help="Maximum files listed per artifact category (default: 200).")
    parser.add_argument("--max-log-bytes", type=int, default=512_000, help="Tail bytes read from each log-like file (default: 512000).")
    parser.add_argument("--max-text-log-bytes", type=int, default=64_000, help="Non-.log text files larger than this are not scanned as logs (default: 64000).")
    parser.add_argument("--max-errors", type=int, default=5, help="Maximum error fragments per log (default: 5).")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    summaries = [inspect_root(Path(path), args) for path in args.paths]
    if args.json:
        json.dump([asdict_dataclass(summary) for summary in summaries], sys.stdout, indent=2)
        print()
    else:
        for summary in summaries:
            print_text(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
