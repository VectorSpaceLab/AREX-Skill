#!/usr/bin/env python3
"""Safe smoke checks for segmentation, diarization, and silence removal.

The script synthesizes a tiny WAV by default, runs silence removal, and only
runs HMM segmentation or speaker diarization when the caller supplies the
needed sample/model paths.
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

import numpy as np
from scipy.io import wavfile

from pyAudioAnalysis import audioBasicIO as aIO
from pyAudioAnalysis import audioSegmentation as aS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke test pyAudioAnalysis segmentation workflows.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--sample-wav",
        type=Path,
        help=(
            "Optional WAV to reuse for HMM segmentation and diarization. "
            "If omitted, a synthetic WAV is generated and only silence removal "
            "is exercised."
        ),
    )
    parser.add_argument(
        "--hmm-model",
        type=Path,
        help="Optional HMM model file to test on the sample WAV.",
    )
    parser.add_argument(
        "--hmm-gt",
        type=Path,
        help="Optional .segments file to score the HMM result.",
    )
    parser.add_argument(
        "--n-speakers",
        type=int,
        help="Optional speaker count for diarization; omit to skip diarization.",
    )
    parser.add_argument(
        "--mid-window",
        type=float,
        default=1.0,
        help="Mid-term window size in seconds for diarization.",
    )
    parser.add_argument(
        "--mid-step",
        type=float,
        default=0.1,
        help="Mid-term step in seconds for diarization.",
    )
    parser.add_argument(
        "--short-window",
        type=float,
        default=0.1,
        help="Short-term window in seconds for diarization.",
    )
    parser.add_argument(
        "--lda-dim",
        type=int,
        default=0,
        help="LDA dimension for diarization (0 disables LDA).",
    )
    parser.add_argument(
        "--silence-window",
        type=float,
        default=0.05,
        help="Short-term window in seconds for silence removal.",
    )
    parser.add_argument(
        "--silence-step",
        type=float,
        default=0.05,
        help="Short-term step in seconds for silence removal.",
    )
    parser.add_argument(
        "--smooth-window",
        type=float,
        default=0.5,
        help="Smoothing window in seconds for silence removal.",
    )
    parser.add_argument(
        "--weight",
        type=float,
        default=0.5,
        help="Weight factor used by silence removal.",
    )
    parser.add_argument(
        "--synth-rate",
        type=int,
        default=16000,
        help="Sample rate for the synthetic WAV.",
    )
    parser.add_argument(
        "--synth-duration",
        type=float,
        default=3.0,
        help="Duration in seconds for the synthetic WAV.",
    )
    return parser


def synthesize_wav(path: Path, sample_rate: int, duration: float) -> Path:
    n_samples = max(1, int(round(sample_rate * duration)))
    time = np.arange(n_samples, dtype=np.float32) / float(sample_rate)
    signal = np.zeros(n_samples, dtype=np.float32)

    tone_windows = [
        (0.30, 0.90, 440.0, 0.85),
        (1.20, 1.80, 660.0, 0.75),
        (2.10, min(duration, 2.70), 330.0, 0.80),
    ]
    for start, stop, freq, amplitude in tone_windows:
        if start >= duration:
            continue
        mask = (time >= start) & (time < stop)
        if not np.any(mask):
            continue
        local_time = time[mask] - start
        signal[mask] += amplitude * np.sin(2.0 * np.pi * freq * local_time)

    peak = float(np.max(np.abs(signal))) or 1.0
    signal = np.clip(signal / peak * 0.95 * np.iinfo(np.int16).max,
                     -32768, 32767).astype(np.int16)
    wavfile.write(path, sample_rate, signal)
    return path


def summarize_segments(prefix: str, segments: list[list[float]]) -> None:
    print(f"{prefix}_count={len(segments)}")
    for index, (start, end) in enumerate(segments):
        print(f"{prefix}[{index}]={start:.3f}\t{end:.3f}")


def resolve_sample_path(args: argparse.Namespace, temp_dir: Path) -> Path:
    if args.sample_wav is not None:
        sample_path = args.sample_wav.expanduser().resolve()
        if not sample_path.is_file():
            raise FileNotFoundError(f"sample WAV not found: {sample_path}")
        return sample_path

    sample_path = temp_dir / "synthetic_segmentation_smoke.wav"
    synthesize_wav(sample_path, args.synth_rate, args.synth_duration)
    return sample_path


def run_silence_removal(sample_path: Path, args: argparse.Namespace) -> None:
    sample_rate, signal = aIO.read_audio_file(str(sample_path))
    if sample_rate <= 0 or signal.size == 0:
        raise RuntimeError(f"failed to read audio: {sample_path}")
    segments = aS.silence_removal(
        signal,
        sample_rate,
        args.silence_window,
        args.silence_step,
        smooth_window=args.smooth_window,
        weight=args.weight,
        plot=False,
    )
    summarize_segments("silence_removal", segments)


def run_hmm(sample_path: Path, args: argparse.Namespace) -> None:
    if args.hmm_model is None:
        return
    if args.sample_wav is None:
        print("hmm_segmentation_skipped=missing_sample_wav")
        return

    hmm_model = args.hmm_model.expanduser().resolve()
    if not hmm_model.is_file():
        raise FileNotFoundError(f"HMM model not found: {hmm_model}")

    gt_file = None
    if args.hmm_gt is not None:
        gt_file = args.hmm_gt.expanduser().resolve()
        if not gt_file.is_file():
            raise FileNotFoundError(f"HMM ground truth not found: {gt_file}")

    labels, class_names, accuracy, cm = aS.hmm_segmentation(
        str(sample_path),
        str(hmm_model),
        plot_results=False,
        gt_file=str(gt_file) if gt_file is not None else "",
    )
    print(f"hmm_segmentation_labels={len(labels)}")
    print("hmm_segmentation_classes=" + ",".join(class_names))
    print(f"hmm_segmentation_accuracy={accuracy:.4f}")
    print(f"hmm_segmentation_cm_shape={cm.shape}")


def run_diarization(sample_path: Path, args: argparse.Namespace) -> None:
    if args.n_speakers is None:
        return
    if args.sample_wav is None:
        print("speaker_diarization_skipped=missing_sample_wav")
        return

    with tempfile.TemporaryDirectory(prefix="segmentation-diarization-") as scratch_name:
        diarization_path = Path(scratch_name) / "diarization_smoke.wav"
        shutil.copyfile(sample_path, diarization_path)
        cls, purity_cluster_m, purity_speaker_m = aS.speaker_diarization(
            str(diarization_path),
            args.n_speakers,
            mid_window=args.mid_window,
            mid_step=args.mid_step,
            short_window=args.short_window,
            lda_dim=args.lda_dim,
            plot_res=False,
        )
    print(f"speaker_diarization_labels={len(cls)}")
    print(f"speaker_diarization_cluster_purity={purity_cluster_m:.4f}")
    print(f"speaker_diarization_speaker_purity={purity_speaker_m:.4f}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="segmentation-smoke-") as tmpdir_name:
        temp_dir = Path(tmpdir_name)
        sample_path = resolve_sample_path(args, temp_dir)
        print(f"input_wav={sample_path}")
        run_silence_removal(sample_path, args)
        run_hmm(sample_path, args)
        run_diarization(sample_path, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
