#!/usr/bin/env python3
"""Safe LatentSync inference wrapper.

This wrapper runs the repo-maintained ``scripts.inference`` module from an
explicit runtime root and performs fast preflight checks before a long denoise
run. It intentionally uses only the Python standard library so ``--help`` and
``--preflight-only`` remain lightweight.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

UNSAFE_SHELL_CHARS = set(" \t\n\r;&|`$<>\\\"'(){}[]*?!")


@dataclass
class Job:
    video: Path
    audio: Path
    output: Path
    temp_dir: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preflight and run LatentSync scripts.inference for one pair or a small batch.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        default=os.environ.get("LATENTSYNC_REPO_ROOT", "."),
        help="LatentSync runtime tree containing scripts/, latentsync/, configs/, assets/, and checkpoints/.",
    )
    parser.add_argument("--python", default=sys.executable, help="Python executable used to run scripts.inference.")
    parser.add_argument("--config", default="configs/unet/stage2_512.yaml", help="U-Net inference config path.")
    parser.add_argument("--checkpoint", default="checkpoints/latentsync_unet.pt", help="U-Net checkpoint path.")
    parser.add_argument("--video-path", default="assets/demo1_video.mp4", help="Single-pair input video path.")
    parser.add_argument("--audio-path", default="assets/demo1_audio.wav", help="Single-pair input audio path.")
    parser.add_argument("--output", default="video_out.mp4", help="Single-pair output mp4 path.")
    parser.add_argument("--pairs-file", help="Batch TSV/CSV/whitespace file: video, audio, optional output.")
    parser.add_argument("--video-list", help="Batch text file with one video path per line.")
    parser.add_argument("--audio-list", help="Batch text file with one audio path per line.")
    parser.add_argument("--output-dir", default="inference_outputs", help="Batch output directory when rows omit output.")
    parser.add_argument(
        "--pairing",
        choices=("zipped", "shuffled"),
        default="zipped",
        help="How to pair --video-list and --audio-list entries.",
    )
    parser.add_argument("--steps", type=int, default=20, help="Number of diffusion inference steps.")
    parser.add_argument("--guidance-scale", type=float, default=1.5, help="Classifier-free audio guidance scale.")
    parser.add_argument("--seed", type=int, default=1247, help="Seed passed to scripts.inference; -1 lets torch choose.")
    parser.add_argument("--temp-dir", default="temp", help="Scratch directory; the pipeline deletes/recreates it.")
    parser.add_argument("--enable-deepcache", action="store_true", help="Enable DeepCache helper in scripts.inference.")
    parser.add_argument("--ffmpeg-bin", help="Optional ffmpeg binary; its parent is prepended to PATH for the child process.")
    parser.add_argument("--skip-cuda-check", action="store_true", help="Skip torch CUDA preflight.")
    parser.add_argument("--skip-import-check", action="store_true", help="Skip Python import preflight.")
    parser.add_argument("--allow-shell-unsafe-paths", action="store_true", help="Allow paths with spaces/metacharacters despite downstream shell ffmpeg calls.")
    parser.add_argument("--preflight-only", action="store_true", help="Run validation and print planned jobs without executing inference.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing inference.")
    parser.add_argument("--continue-on-error", action="store_true", help="In batch mode, continue after a failed inference subprocess.")
    return parser.parse_args()


def resolve_under(root: Path, value: str | os.PathLike[str]) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def repo_relative(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        fail(f"{label} not found: {path}")
    if not path.is_file():
        fail(f"{label} is not a file: {path}")
    if not os.access(path, os.R_OK):
        fail(f"{label} is not readable: {path}")


def require_dir(path: Path, label: str) -> None:
    if not path.exists():
        fail(f"{label} not found: {path}")
    if not path.is_dir():
        fail(f"{label} is not a directory: {path}")


def validate_output_parent(path: Path, label: str) -> None:
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    if not os.access(parent, os.W_OK):
        fail(f"{label} parent is not writable: {parent}")


def reject_unsafe_path(path: Path, label: str, allow: bool) -> None:
    if allow:
        return
    text = path.as_posix()
    bad = sorted(ch for ch in set(text) if ch in UNSAFE_SHELL_CHARS)
    if bad:
        chars = "".join(bad)
        fail(
            f"{label} contains shell-sensitive character(s) {chars!r}: {path}. "
            "Move/copy the file to a simple path or pass --allow-shell-unsafe-paths after reviewing downstream shell usage."
        )


def read_text_paths(path: Path) -> list[str]:
    require_file(path, "list file")
    values: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            values.append(stripped)
    return values


def parse_pairs(path: Path) -> list[tuple[str, str, str | None]]:
    require_file(path, "pairs file")
    pairs: list[tuple[str, str, str | None]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "\t" in line:
            parts = next(csv.reader([line], delimiter="\t"))
        elif "," in line:
            parts = next(csv.reader([line]))
        else:
            parts = line.split()
        parts = [part.strip() for part in parts if part.strip()]
        if len(parts) not in (2, 3):
            fail(f"pairs file line {line_no} must have 2 or 3 fields, got {len(parts)}: {raw!r}")
        output = parts[2] if len(parts) == 3 else None
        pairs.append((parts[0], parts[1], output))
    if not pairs:
        fail(f"pairs file has no usable rows: {path}")
    return pairs


def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return value or "sample"


def default_batch_output(output_dir: Path, video: Path, audio: Path) -> Path:
    return output_dir / f"{slugify(video.stem)}__{slugify(audio.stem)}.mp4"


def build_jobs(args: argparse.Namespace, root: Path) -> list[Job]:
    base_temp = resolve_under(root, args.temp_dir)
    output_dir = resolve_under(root, args.output_dir)

    if args.pairs_file:
        if args.video_list or args.audio_list:
            fail("Use either --pairs-file or --video-list/--audio-list, not both.")
        pairs = parse_pairs(resolve_under(root, args.pairs_file))
        jobs: list[Job] = []
        for index, (video_s, audio_s, output_s) in enumerate(pairs, start=1):
            video = resolve_under(root, video_s)
            audio = resolve_under(root, audio_s)
            output = resolve_under(root, output_s) if output_s else default_batch_output(output_dir, video, audio)
            jobs.append(Job(video=video, audio=audio, output=output, temp_dir=base_temp / f"job_{index:04d}_{slugify(output.stem)}"))
        return jobs

    if args.video_list or args.audio_list:
        if not (args.video_list and args.audio_list):
            fail("--video-list and --audio-list must be provided together.")
        videos = read_text_paths(resolve_under(root, args.video_list))
        audios = read_text_paths(resolve_under(root, args.audio_list))
        if not videos or not audios:
            fail("video and audio lists must both contain at least one item.")
        if args.pairing == "shuffled":
            random.seed(args.seed)
            random.shuffle(videos)
            random.shuffle(audios)
        count = min(len(videos), len(audios))
        jobs = []
        for index, (video_s, audio_s) in enumerate(zip(videos[:count], audios[:count]), start=1):
            video = resolve_under(root, video_s)
            audio = resolve_under(root, audio_s)
            output = default_batch_output(output_dir, video, audio)
            jobs.append(Job(video=video, audio=audio, output=output, temp_dir=base_temp / f"job_{index:04d}_{slugify(output.stem)}"))
        return jobs

    return [
        Job(
            video=resolve_under(root, args.video_path),
            audio=resolve_under(root, args.audio_path),
            output=resolve_under(root, args.output),
            temp_dir=base_temp,
        )
    ]


def parse_config_value(config_path: Path, dotted_key: str) -> str | None:
    """Small YAML subset reader sufficient for LatentSync config preflight."""
    wanted = dotted_key.split(".")
    stack: list[tuple[int, str]] = []
    for raw in config_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.split("#", 1)[0].strip().strip('"\'')
        while stack and stack[-1][0] >= indent:
            stack.pop()
        current = [k for _, k in stack] + [key]
        if current == wanted:
            return value or None
        if value == "":
            stack.append((indent, key))
    return None


def required_whisper_checkpoint(config_path: Path, root: Path) -> Path | None:
    dim = parse_config_value(config_path, "model.cross_attention_dim")
    if dim == "384":
        return root / "checkpoints/whisper/tiny.pt"
    if dim == "768":
        return root / "checkpoints/whisper/small.pt"
    return None


def configured_mask_path(config_path: Path, root: Path) -> Path | None:
    value = parse_config_value(config_path, "data.mask_image_path")
    return resolve_under(root, value) if value else None


def run_child_probe(python: str, root: Path, env: dict[str, str], cuda: bool, imports: bool) -> None:
    statements: list[str] = []
    if imports:
        statements.append(
            "import torch, torchvision, diffusers, transformers, decord, mediapipe, gradio, onnxruntime, DeepCache; "
            "from latentsync.models.unet import UNet3DConditionModel; "
            "from latentsync.pipelines.lipsync_pipeline import LipsyncPipeline"
        )
    if cuda:
        statements.append(
            "import torch; "
            "assert torch.cuda.is_available(), 'torch.cuda.is_available() is False'; "
            "x=torch.tensor([1.0], device='cuda:0'); "
            "assert float(x.item()) == 1.0"
        )
    if not statements:
        return
    proc = subprocess.run(
        [python, "-c", "; ".join(statements)],
        cwd=root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        details = (proc.stderr or proc.stdout).strip()
        fail(f"Python runtime preflight failed with {python!r}: {details}")


def build_env(args: argparse.Namespace) -> dict[str, str]:
    env = os.environ.copy()
    if args.ffmpeg_bin:
        ffmpeg = Path(args.ffmpeg_bin).expanduser().resolve()
        require_file(ffmpeg, "ffmpeg binary")
        env["PATH"] = f"{ffmpeg.parent}{os.pathsep}" + env.get("PATH", "")
    return env


def preflight(args: argparse.Namespace, root: Path, config: Path, checkpoint: Path, jobs: Iterable[Job], env: dict[str, str]) -> None:
    require_dir(root, "repo root")
    require_file(root / "scripts" / "inference.py", "repo inference module")
    require_dir(root / "latentsync", "latentsync package directory")
    require_file(config, "U-Net config")
    require_file(checkpoint, "U-Net checkpoint")
    require_file(root / "configs" / "scheduler_config.json", "scheduler config")

    whisper = required_whisper_checkpoint(config, root)
    if whisper is None:
        fail(f"Unsupported or missing model.cross_attention_dim in config: {config}")
    require_file(whisper, "Whisper checkpoint selected by config")

    mask = configured_mask_path(config, root)
    if mask is not None:
        require_file(mask, "mask image selected by config")

    ffmpeg_cmd = args.ffmpeg_bin or "ffmpeg"
    if args.ffmpeg_bin:
        require_file(Path(args.ffmpeg_bin).expanduser().resolve(), "ffmpeg binary")
    elif shutil.which(ffmpeg_cmd, path=env.get("PATH")) is None:
        fail("ffmpeg not found on PATH")

    reject_unsafe_path(root, "repo root", args.allow_shell_unsafe_paths)
    reject_unsafe_path(config, "config path", args.allow_shell_unsafe_paths)
    reject_unsafe_path(checkpoint, "checkpoint path", args.allow_shell_unsafe_paths)
    reject_unsafe_path(whisper, "Whisper checkpoint path", args.allow_shell_unsafe_paths)
    if mask is not None:
        reject_unsafe_path(mask, "mask image path", args.allow_shell_unsafe_paths)

    materialized = list(jobs)
    for index, job in enumerate(materialized, start=1):
        require_file(job.video, f"job {index} input video")
        require_file(job.audio, f"job {index} input audio")
        validate_output_parent(job.output, f"job {index} output")
        validate_output_parent(job.temp_dir / "probe", f"job {index} temp dir")
        for label, value in (
            ("input video", job.video),
            ("input audio", job.audio),
            ("output path", job.output),
            ("temp dir", job.temp_dir),
        ):
            reject_unsafe_path(value, f"job {index} {label}", args.allow_shell_unsafe_paths)

    run_child_probe(
        args.python,
        root,
        env,
        cuda=not args.skip_cuda_check,
        imports=not args.skip_import_check,
    )


def command_for_job(args: argparse.Namespace, root: Path, config: Path, checkpoint: Path, job: Job) -> list[str]:
    cmd = [
        args.python,
        "-m",
        "scripts.inference",
        "--unet_config_path",
        repo_relative(root, config),
        "--inference_ckpt_path",
        repo_relative(root, checkpoint),
        "--video_path",
        repo_relative(root, job.video),
        "--audio_path",
        repo_relative(root, job.audio),
        "--video_out_path",
        repo_relative(root, job.output),
        "--inference_steps",
        str(args.steps),
        "--guidance_scale",
        str(args.guidance_scale),
        "--temp_dir",
        repo_relative(root, job.temp_dir),
        "--seed",
        str(args.seed),
    ]
    if args.enable_deepcache:
        cmd.append("--enable_deepcache")
    return cmd


def main() -> int:
    args = parse_args()
    root = Path(args.repo_root).expanduser().resolve()
    config = resolve_under(root, args.config)
    checkpoint = resolve_under(root, args.checkpoint)
    jobs = build_jobs(args, root)
    env = build_env(args)

    preflight(args, root, config, checkpoint, jobs, env)

    print(f"Preflight OK: {len(jobs)} job(s) planned")
    for index, job in enumerate(jobs, start=1):
        print(f"[{index}] video={repo_relative(root, job.video)} audio={repo_relative(root, job.audio)} output={repo_relative(root, job.output)}")

    if args.preflight_only:
        return 0

    failures = 0
    for index, job in enumerate(jobs, start=1):
        cmd = command_for_job(args, root, config, checkpoint, job)
        print(f"[{index}] {shlex.join(cmd)}")
        if args.dry_run:
            continue
        proc = subprocess.run(cmd, cwd=root, env=env)
        if proc.returncode != 0:
            failures += 1
            print(f"ERROR: job {index} failed with exit code {proc.returncode}", file=sys.stderr)
            if not args.continue_on_error:
                return proc.returncode
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
