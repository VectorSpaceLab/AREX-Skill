#!/usr/bin/env python3
"""Self-contained HiFi-GAN inference entrypoint bundled with the repo skill.

The wrapper runs the copied HiFi-GAN inference source from the skill runtime. It
requires only a generator checkpoint directory with its matching `config.json`
and user-provided wav or mel inputs; no external HiFi-GAN checkout is needed.
"""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_DIR = SKILL_ROOT / "scripts" / "hifigan_runtime"
WAV_INFERENCE = RUNTIME_DIR / "inference.py"
MEL_INFERENCE = RUNTIME_DIR / "inference_e2e.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run bundled HiFi-GAN wav or mel inference.")
    parser.add_argument("--mode", choices=("wav", "mel"), default="wav", help="Use wav-to-wav or mel-to-wav inference.")
    parser.add_argument("--checkpoint_file", required=True, help="Generator checkpoint file containing a `generator` state dict.")
    parser.add_argument("--input_wavs_dir", default="test_files", help="Directory of input wav files for --mode wav.")
    parser.add_argument("--input_mels_dir", default="test_mel_files", help="Directory of mel .npy files for --mode mel.")
    parser.add_argument(
        "--output_dir",
        default=None,
        help="Output directory. Defaults to generated_files for wav mode or generated_files_from_mel for mel mode.",
    )
    parser.add_argument(
        "--no-compat-shims",
        action="store_true",
        help="Disable process-local modern torch/librosa compatibility shims.",
    )
    return parser.parse_args()


def run_entrypoint(script_path: Path, argv: list[str], *, compat: bool) -> None:
    if not script_path.is_file():
        raise SystemExit(f"Bundled inference script is missing: {script_path}")
    if str(RUNTIME_DIR) not in sys.path:
        sys.path.insert(0, str(RUNTIME_DIR))
    if compat:
        from compat import apply_compat_shims

        apply_compat_shims(training=False)
    sys.argv = [str(script_path), *argv]
    runpy.run_path(str(script_path), run_name="__main__")


def main() -> None:
    args = parse_args()
    if args.mode == "wav":
        output_dir = args.output_dir or "generated_files"
        run_entrypoint(
            WAV_INFERENCE,
            [
                "--checkpoint_file",
                args.checkpoint_file,
                "--input_wavs_dir",
                args.input_wavs_dir,
                "--output_dir",
                output_dir,
            ],
            compat=not args.no_compat_shims,
        )
    else:
        output_dir = args.output_dir or "generated_files_from_mel"
        run_entrypoint(
            MEL_INFERENCE,
            [
                "--checkpoint_file",
                args.checkpoint_file,
                "--input_mels_dir",
                args.input_mels_dir,
                "--output_dir",
                output_dir,
            ],
            compat=not args.no_compat_shims,
        )


if __name__ == "__main__":
    main()
