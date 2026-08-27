#!/usr/bin/env python3
"""Run a short self-contained HiFi-GAN training smoke.

This helper is destructive only inside its work directory. It creates a
miniature LJSpeech-style fixture and a small config, then executes the bundled
`train_hifigan.py` wrapper from this skill. It does not require an external
HiFi-GAN repository checkout.

Examples:
    python smoke_train_tiny.py --dry-run
    python smoke_train_tiny.py
    python smoke_train_tiny.py --fine-tuning
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[3]
TRAIN_ENTRYPOINT = Path(__file__).with_name("train_hifigan.py")

TINY_CONFIG = {
    "resblock": "1",
    "num_gpus": 0,
    "batch_size": 1,
    "learning_rate": 0.0002,
    "adam_b1": 0.8,
    "adam_b2": 0.99,
    "lr_decay": 0.999,
    "seed": 1234,
    "upsample_rates": [4, 4, 4],
    "upsample_kernel_sizes": [8, 8, 8],
    "upsample_initial_channel": 64,
    "resblock_kernel_sizes": [3],
    "resblock_dilation_sizes": [[1, 3, 5]],
    "segment_size": 1024,
    "num_mels": 80,
    "num_freq": 129,
    "n_fft": 256,
    "hop_size": 64,
    "win_size": 256,
    "sampling_rate": 22050,
    "fmin": 0,
    "fmax": 8000,
    "fmax_for_loss": None,
    "num_workers": 0,
    "dist_config": {
        "dist_backend": "nccl",
        "dist_url": "tcp://localhost:54321",
        "world_size": 1,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny CUDA HiFi-GAN training smoke using bundled runtime source.")
    parser.add_argument("--work-dir", help="Directory for generated fixture/config/checkpoints. Defaults to a temp dir.")
    parser.add_argument("--overwrite", action="store_true", help="Allow reusing an existing work-dir by overwriting fixture files.")
    parser.add_argument("--fine-tuning", action="store_true", help="Run the smoke in --fine_tuning True mode with generated mel .npy files.")
    parser.add_argument("--dry-run", action="store_true", help="Create fixture/config and check imports, but do not execute bundled training.")
    parser.add_argument(
        "--cuda-visible-devices",
        default="0",
        help="Value to set for CUDA_VISIBLE_DEVICES before importing torch. Use '' to leave unchanged.",
    )
    parser.add_argument("--duration-sec", type=float, default=0.25, help="Synthetic wav duration.")
    parser.add_argument("--fixture-script", help="Optional explicit path to make_ljspeech_fixture.py.")
    return parser.parse_args()


def prepare_work_dir(path_arg: str | None) -> Path:
    if path_arg:
        work_dir = Path(path_arg).expanduser().resolve()
        work_dir.mkdir(parents=True, exist_ok=True)
    else:
        work_dir = Path(tempfile.mkdtemp(prefix="hifigan_train_smoke_"))
    return work_dir


def run_fixture_generator(
    fixture_script: Path,
    fixture_dir: Path,
    fine_tuning: bool,
    duration_sec: float,
    overwrite: bool,
) -> dict:
    cmd = [
        sys.executable,
        str(fixture_script),
        "--out-dir",
        str(fixture_dir),
        "--train-count",
        "2",
        "--val-count",
        "1",
        "--sample-rate",
        str(TINY_CONFIG["sampling_rate"]),
        "--duration-sec",
        str(duration_sec),
        "--hop-size",
        str(TINY_CONFIG["hop_size"]),
    ]
    if fine_tuning:
        cmd.append("--with-mels")
    if overwrite:
        cmd.append("--overwrite")
    result = subprocess.run(cmd, check=True, text=True, stdout=subprocess.PIPE)
    return json.loads(result.stdout)


def write_config(path: Path) -> None:
    path.write_text(json.dumps(TINY_CONFIG, indent=2) + "\n", encoding="utf-8")


def check_environment(dry_run: bool) -> None:
    try:
        import torch
        from torch.utils.tensorboard import SummaryWriter as _SummaryWriter  # noqa: F401
        from librosa.util import normalize as _normalize  # noqa: F401
    except Exception as exc:  # pragma: no cover - diagnostic helper
        raise SystemExit(f"Environment import check failed: {exc}") from exc

    print(f"torch: {torch.__version__}")
    print(f"cuda_available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"cuda_device_0: {torch.cuda.get_device_name(0)}")
    elif not dry_run:
        raise SystemExit("CUDA is not available. Upstream HiFi-GAN training is GPU-only; use CUDA for this smoke.")


def format_path(path: Path, work_dir: Path) -> str:
    try:
        return "<work-dir>/" + str(path.relative_to(work_dir))
    except ValueError:
        try:
            return str(path.relative_to(SKILL_ROOT))
        except ValueError:
            return path.name


def run_training(manifest: dict, config_path: Path, checkpoint_path: Path, fine_tuning: bool, work_dir: Path) -> None:
    argv = [
        sys.executable,
        str(TRAIN_ENTRYPOINT),
        "--config",
        str(config_path),
        "--input_wavs_dir",
        manifest["wavs_dir"],
        "--input_training_file",
        manifest["training_file"],
        "--input_validation_file",
        manifest["validation_file"],
        "--checkpoint_path",
        str(checkpoint_path),
        "--training_epochs",
        "1",
        "--stdout_interval",
        "1",
        "--checkpoint_interval",
        "1",
        "--summary_interval",
        "1",
        "--validation_interval",
        "1",
    ]
    if fine_tuning:
        argv.extend(["--fine_tuning", "True", "--input_mels_dir", manifest["mels_dir"]])

    pretty = ["python" if p == sys.executable else p for p in argv]
    pretty = [format_path(Path(p), work_dir) if p.startswith("/") else p for p in pretty]
    print("+", " ".join(pretty))
    env = os.environ.copy()
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    subprocess.run(argv, cwd=str(work_dir), env=env, check=True)


def summarize_outputs(work_dir: Path, checkpoint_path: Path, dry_run: bool) -> dict:
    return {
        "work_dir": str(work_dir),
        "checkpoint_path": str(checkpoint_path),
        "config_copy_exists": (checkpoint_path / "config.json").is_file(),
        "logs_dir_exists": (checkpoint_path / "logs").is_dir(),
        "generator_checkpoints": sorted(p.name for p in checkpoint_path.glob("g_????????")),
        "discriminator_checkpoints": sorted(p.name for p in checkpoint_path.glob("do_????????")),
        "dry_run": dry_run,
    }


def main() -> int:
    args = parse_args()
    if args.cuda_visible_devices != "":
        os.environ["CUDA_VISIBLE_DEVICES"] = args.cuda_visible_devices

    if not TRAIN_ENTRYPOINT.is_file():
        raise SystemExit(f"Bundled training entrypoint not found: {TRAIN_ENTRYPOINT}")

    work_dir = prepare_work_dir(args.work_dir)
    fixture_dir = work_dir / "fixture"
    config_path = work_dir / "tiny_config.json"
    checkpoint_path = work_dir / "cp_smoke"

    fixture_script = Path(args.fixture_script).expanduser().resolve() if args.fixture_script else Path(__file__).with_name("make_ljspeech_fixture.py")
    if not fixture_script.is_file():
        raise SystemExit(f"Fixture generator not found: {fixture_script}")

    manifest = run_fixture_generator(fixture_script, fixture_dir, args.fine_tuning, args.duration_sec, args.overwrite)
    write_config(config_path)
    check_environment(dry_run=args.dry_run)

    print(f"work_dir: {work_dir}")
    print(f"fixture_dir: {fixture_dir}")
    print(f"tiny_config: {config_path}")

    if not args.dry_run:
        run_training(manifest, config_path, checkpoint_path, args.fine_tuning, work_dir)

    summary = summarize_outputs(work_dir, checkpoint_path, dry_run=args.dry_run)
    print(json.dumps(summary, indent=2))

    if not args.dry_run:
        missing = []
        if not summary["config_copy_exists"]:
            missing.append("checkpoint config.json")
        if not summary["logs_dir_exists"]:
            missing.append("TensorBoard logs directory")
        if not summary["generator_checkpoints"]:
            missing.append("generator checkpoint")
        if not summary["discriminator_checkpoints"]:
            missing.append("discriminator/optimizer checkpoint")
        if missing:
            raise SystemExit("Smoke completed but expected outputs are missing: " + ", ".join(missing))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
