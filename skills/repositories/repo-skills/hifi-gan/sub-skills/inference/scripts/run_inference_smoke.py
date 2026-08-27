#!/usr/bin/env python3
"""Run a self-contained synthetic HiFi-GAN inference smoke test.

The helper creates a dummy generator checkpoint, writes tiny wav and mel
fixtures, and runs the bundled `infer_hifigan.py` entrypoint for both wav and
mel modes. It does not require an external HiFi-GAN repository checkout.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent


def format_cmd(cmd: list[str], *, work_dir: Path) -> str:
    pretty: list[str] = []
    for part in cmd:
        if part == sys.executable:
            pretty.append("python")
            continue
        path = Path(part)
        if path.is_absolute():
            if path == SKILL_ROOT or SKILL_ROOT in path.parents:
                pretty.append(str(path.relative_to(SKILL_ROOT)))
                continue
            if path == work_dir or work_dir in path.parents:
                pretty.append("<work-dir>/" + str(path.relative_to(work_dir)))
                continue
            pretty.append(path.name)
            continue
        pretty.append(part)
    return " ".join(pretty)


def run(cmd: list[str], *, cwd: Path, work_dir: Path) -> None:
    print("+", format_cmd(cmd, work_dir=work_dir))
    subprocess.run(cmd, cwd=str(cwd), check=True)


def preflight_librosa() -> None:
    try:
        from librosa.util import normalize  # noqa: F401
    except Exception as exc:  # pragma: no cover - exercised only in missing-dependency environments
        raise SystemExit(
            "HiFi-GAN inference smoke needs librosa.util.normalize. Install the repo's audio dependencies first."
        ) from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Create synthetic inputs and run both bundled HiFi-GAN inference modes.")
    parser.add_argument("--work-dir", type=Path, default=None, help="Scratch directory to reuse. Defaults to a temp directory.")
    parser.add_argument("--config", default="v1", help="Bundled config alias or file to pair with the dummy checkpoint.")
    parser.add_argument("--stem", default="sample", help="Base filename stem for the synthetic wav and mel fixtures.")
    parser.add_argument("--sample-rate", type=int, default=22050, help="Sample rate for the synthetic wav fixture.")
    parser.add_argument("--wav-duration", type=float, default=0.05, help="Duration of the synthetic wav fixture.")
    parser.add_argument("--wav-frequency", type=float, default=440.0, help="Frequency of the synthetic wav fixture.")
    parser.add_argument("--wav-amplitude", type=float, default=0.2, help="Amplitude of the synthetic wav fixture.")
    parser.add_argument("--mel-bins", type=int, default=80, help="Number of mel bins to use for the synthetic mel fixture.")
    parser.add_argument("--mel-frames", type=int, default=8, help="Number of mel frames to use for the synthetic mel fixture.")
    parser.add_argument(
        "--mel-rank",
        type=int,
        default=2,
        choices=(1, 2, 3),
        help="Mel rank for the synthetic fixture. Use 2 for the standard smoke path.",
    )
    parser.add_argument("--seed", type=int, default=1234, help="Random seed for the dummy checkpoint and mel fixture.")
    args = parser.parse_args()

    if args.work_dir is None:
        work_dir = Path(tempfile.mkdtemp(prefix="hifigan-inference-smoke-"))
    else:
        work_dir = args.work_dir.expanduser().resolve()
        work_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_dir = work_dir / "checkpoint"
    fixtures_dir = work_dir / "fixtures"
    wav_output_dir = work_dir / "generated_files"
    mel_output_dir = work_dir / "generated_files_from_mel"

    dummy_checkpoint = SCRIPT_DIR / "make_dummy_checkpoint.py"
    fixture_maker = SCRIPT_DIR / "make_tiny_inference_fixtures.py"
    infer_entrypoint = SCRIPT_DIR / "infer_hifigan.py"

    run(
        [
            sys.executable,
            str(dummy_checkpoint),
            "--output-dir",
            str(checkpoint_dir),
            "--state-config",
            args.config,
            "--seed",
            str(args.seed),
        ],
        cwd=SKILL_ROOT,
        work_dir=work_dir,
    )

    run(
        [
            sys.executable,
            str(fixture_maker),
            "--output-root",
            str(fixtures_dir),
            "--stem",
            args.stem,
            "--sample-rate",
            str(args.sample_rate),
            "--wav-duration",
            str(args.wav_duration),
            "--wav-frequency",
            str(args.wav_frequency),
            "--wav-amplitude",
            str(args.wav_amplitude),
            "--mel-bins",
            str(args.mel_bins),
            "--mel-frames",
            str(args.mel_frames),
            "--mel-rank",
            str(args.mel_rank),
            "--seed",
            str(args.seed),
        ],
        cwd=SKILL_ROOT,
        work_dir=work_dir,
    )

    checkpoint_file = checkpoint_dir / "g_00000000"
    wav_input_dir = fixtures_dir / "test_files"
    mel_input_dir = fixtures_dir / "test_mel_files"

    preflight_librosa()

    run(
        [
            sys.executable,
            str(infer_entrypoint),
            "--mode",
            "wav",
            "--checkpoint_file",
            str(checkpoint_file),
            "--input_wavs_dir",
            str(wav_input_dir),
            "--output_dir",
            str(wav_output_dir),
        ],
        cwd=SKILL_ROOT,
        work_dir=work_dir,
    )

    run(
        [
            sys.executable,
            str(infer_entrypoint),
            "--mode",
            "mel",
            "--checkpoint_file",
            str(checkpoint_file),
            "--input_mels_dir",
            str(mel_input_dir),
            "--output_dir",
            str(mel_output_dir),
        ],
        cwd=SKILL_ROOT,
        work_dir=work_dir,
    )

    expected = [wav_output_dir / f"{args.stem}_generated.wav", mel_output_dir / f"{args.stem}_generated_e2e.wav"]
    missing = [str(path) for path in expected if not path.is_file()]
    if missing:
        raise SystemExit("Smoke finished but expected output files are missing: " + ", ".join(missing))

    location_label = "<work-dir>" if args.work_dir is not None else "<temp work dir>"
    print(f"Smoke artifacts are in: {location_label}")


if __name__ == "__main__":
    main()
