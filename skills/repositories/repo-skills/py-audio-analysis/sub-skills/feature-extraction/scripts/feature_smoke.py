#!/usr/bin/env python3
"""Smoke-check pyAudioAnalysis feature extraction.

This helper synthesizes a tone or reads a WAV file, runs pyAudioAnalysis
short-term and mid-term feature extraction, validates feature-name row counts,
and optionally writes NPY/CSV matrices. It keeps package imports after argparse
so `--help` works even before dependencies are installed.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import types
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-check pyAudioAnalysis short/mid/spectral/chroma feature "
            "extraction using a synthetic tone or a WAV file."
        )
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--input-wav",
        type=Path,
        help="Optional WAV file to read with audioBasicIO.read_audio_file.",
    )
    source.add_argument(
        "--duration",
        type=float,
        default=2.0,
        help="Synthetic tone duration in seconds when --input-wav is omitted (default: 2.0).",
    )
    parser.add_argument(
        "--sampling-rate",
        type=int,
        default=16000,
        help="Synthetic tone sampling rate in Hz (default: 16000).",
    )
    parser.add_argument(
        "--frequency",
        type=float,
        default=440.0,
        help="Synthetic tone frequency in Hz (default: 440.0).",
    )
    parser.add_argument(
        "--amplitude",
        type=float,
        default=0.5,
        help="Synthetic tone amplitude in [0, 1] before int16 scaling (default: 0.5).",
    )
    parser.add_argument(
        "--short-window",
        type=float,
        default=0.050,
        help="Short-term window in seconds (default: 0.050).",
    )
    parser.add_argument(
        "--short-step",
        type=float,
        default=0.050,
        help="Short-term step in seconds (default: 0.050).",
    )
    parser.add_argument(
        "--mid-window",
        type=float,
        default=1.0,
        help="Mid-term window in seconds (default: 1.0).",
    )
    parser.add_argument(
        "--mid-step",
        type=float,
        default=1.0,
        help="Mid-term step in seconds (default: 1.0).",
    )
    parser.add_argument(
        "--no-deltas",
        action="store_true",
        help="Disable delta rows for the direct short-term extraction call.",
    )
    parser.add_argument(
        "--compute-beat",
        action="store_true",
        help="Also run MidTermFeatures.beat_extraction on the short-term matrix.",
    )
    parser.add_argument(
        "--strict-imports",
        action="store_true",
        help=(
            "Do not install WAV-only import shims for missing AIFF/MP3 decoder "
            "modules; use this when verifying full dependency installation."
        ),
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        help=(
            "Optional output prefix. Writes *_short.npy, *_mid.npy, "
            "*_spectrogram.npy, and *_chromagram.npy."
        ),
    )
    parser.add_argument(
        "--store-csv",
        action="store_true",
        help="With --output-prefix, also write CSV files with time windows as rows.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include captured legacy stdout from spectrogram() in the JSON report.",
    )
    return parser


def install_wav_only_import_shims() -> list[str]:
    """Install narrow shims for optional media modules imported unconditionally.

    pyAudioAnalysis 0.3.14 imports AIFF/MP3 helper modules while importing
    audioBasicIO/MidTermFeatures, even when a smoke check only uses synthetic
    data or WAV files. The shims raise if non-WAV decoding paths are exercised.
    """
    installed: list[str] = []

    try:
        import aifc as _aifc  # noqa: F401
    except Exception:
        module = types.ModuleType("aifc")

        def _missing_aifc(*_args: Any, **_kwargs: Any) -> Any:
            raise RuntimeError("AIFF decoding is unavailable in this environment")

        module.open = _missing_aifc  # type: ignore[attr-defined]
        sys.modules.setdefault("aifc", module)
        installed.append("aifc")

    try:
        import eyed3 as _eyed3  # noqa: F401
    except Exception:
        module = types.ModuleType("eyed3")

        def _missing_eyed3(*_args: Any, **_kwargs: Any) -> Any:
            raise RuntimeError("MP3 tag reading is unavailable in this environment")

        module.load = _missing_eyed3  # type: ignore[attr-defined]
        sys.modules.setdefault("eyed3", module)
        installed.append("eyed3")

    try:
        import pydub as _pydub  # noqa: F401
    except Exception:
        module = types.ModuleType("pydub")

        class _AudioSegment:
            @staticmethod
            def from_file(*_args: Any, **_kwargs: Any) -> Any:
                raise RuntimeError("Generic media decoding is unavailable in this environment")

        module.AudioSegment = _AudioSegment  # type: ignore[attr-defined]
        sys.modules.setdefault("pydub", module)
        installed.append("pydub")

    return installed


def seconds_to_samples(value: float, sampling_rate: int, name: str) -> int:
    if value <= 0:
        raise ValueError(f"{name} must be positive seconds")
    samples = int(round(value * sampling_rate))
    if samples <= 0:
        raise ValueError(f"{name} rounds to zero samples")
    return samples


def shape_list(array: Any) -> list[int]:
    return [int(dim) for dim in getattr(array, "shape", [])]


def write_outputs(prefix: Path, store_csv: bool, np: Any, matrices: dict[str, Any]) -> list[str]:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name, matrix in matrices.items():
        npy_path = prefix.with_name(prefix.name + f"_{name}.npy")
        np.save(npy_path, matrix)
        written.append(str(npy_path))
        if store_csv:
            csv_path = prefix.with_name(prefix.name + f"_{name}.csv")
            csv_matrix = matrix.T if name in {"short", "mid"} else matrix
            np.savetxt(csv_path, csv_matrix, delimiter=",")
            written.append(str(csv_path))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.input_wav is not None and args.input_wav.suffix.lower() != ".wav":
        parser.error("--input-wav intentionally accepts only .wav files; convert other media first")

    if not args.strict_imports:
        import_shims = install_wav_only_import_shims()
    else:
        import_shims = []

    try:
        import numpy as np
        from pyAudioAnalysis import MidTermFeatures, ShortTermFeatures, audioBasicIO
    except Exception as exc:  # pragma: no cover - intentionally broad for smoke diagnostics
        raise SystemExit(
            "Could not import pyAudioAnalysis feature modules. Install pyAudioAnalysis "
            "and its feature extraction dependencies, or rerun without --strict-imports "
            "for synthetic/WAV-only smoke checks. Original error: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    # Compatibility for pyAudioAnalysis 0.3.14 helper code under NumPy >= 2.
    if not hasattr(np, "Inf"):
        np.Inf = np.inf  # type: ignore[attr-defined]
    if not hasattr(np, "NaN"):
        np.NaN = np.nan  # type: ignore[attr-defined]

    if args.input_wav is not None:
        if not args.input_wav.is_file():
            raise SystemExit(f"Input WAV does not exist: {args.input_wav}")
        sampling_rate, signal = audioBasicIO.read_audio_file(str(args.input_wav))
        source = {"kind": "input-wav", "path": str(args.input_wav)}
        if sampling_rate <= 0 or getattr(signal, "size", 0) == 0:
            raise SystemExit("audioBasicIO.read_audio_file failed or returned empty audio")
        signal = audioBasicIO.stereo_to_mono(signal)
    else:
        if args.duration <= 0:
            parser.error("--duration must be positive")
        if args.sampling_rate <= 0:
            parser.error("--sampling-rate must be positive")
        if not (0 < args.amplitude <= 1.0):
            parser.error("--amplitude must be in (0, 1]")
        sampling_rate = int(args.sampling_rate)
        t = np.arange(int(round(args.duration * sampling_rate))) / float(sampling_rate)
        signal = (args.amplitude * np.sin(2 * np.pi * args.frequency * t) * 32767).astype(np.int16)
        source = {
            "kind": "synthetic-tone",
            "duration_seconds": float(args.duration),
            "frequency_hz": float(args.frequency),
            "amplitude": float(args.amplitude),
        }

    signal = np.asarray(signal)
    if signal.ndim != 1:
        raise SystemExit(
            f"Expected mono audio after stereo_to_mono; got shape {shape_list(signal)}. "
            "Downmix multichannel input explicitly."
        )

    short_window = seconds_to_samples(args.short_window, sampling_rate, "short_window")
    short_step = seconds_to_samples(args.short_step, sampling_rate, "short_step")
    mid_window = seconds_to_samples(args.mid_window, sampling_rate, "mid_window")
    mid_step = seconds_to_samples(args.mid_step, sampling_rate, "mid_step")

    if len(signal) < short_window:
        raise SystemExit("Audio is too short for one short-term window")
    if int(round(mid_step / short_step)) < 1:
        raise SystemExit("mid_step must be at least about one short_step")
    if round((mid_window - (short_window - short_step)) / short_step) < 1:
        raise SystemExit("mid_window is too small relative to short_window/short_step")
    if len(signal) < short_window + short_step:
        raise SystemExit("Audio is too short for stable spectral/chroma representation smoke checks")

    short_features, short_names = ShortTermFeatures.feature_extraction(
        signal,
        sampling_rate,
        short_window,
        short_step,
        deltas=not args.no_deltas,
    )
    if short_features.shape[0] != len(short_names):
        raise SystemExit("Short-term feature rows do not match feature names")
    if short_features.shape[1] <= 0:
        raise SystemExit("Short-term extraction produced zero windows")
    if not np.isfinite(short_features).all():
        raise SystemExit("Short-term extraction produced non-finite values")

    mid_features, short_from_mid, mid_names = MidTermFeatures.mid_feature_extraction(
        signal,
        sampling_rate,
        mid_window,
        mid_step,
        short_window,
        short_step,
    )
    if mid_features.shape[0] != len(mid_names):
        raise SystemExit("Mid-term feature rows do not match feature names")
    if mid_features.shape[1] <= 0:
        raise SystemExit("Mid-term extraction produced zero windows")
    if not np.isfinite(mid_features).all():
        raise SystemExit("Mid-term extraction produced non-finite values")

    legacy_stdout = io.StringIO()
    with contextlib.redirect_stdout(legacy_stdout):
        spectrogram, spec_time, spec_freq = ShortTermFeatures.spectrogram(
            signal,
            sampling_rate,
            short_window,
            short_step,
            plot=False,
            show_progress=False,
        )
    chromagram, chroma_time, chroma_labels = ShortTermFeatures.chromagram(
        signal,
        sampling_rate,
        short_window,
        short_step,
        plot=False,
        show_progress=False,
    )

    if spectrogram.shape[0] != len(spec_time) or spectrogram.shape[1] != len(spec_freq):
        raise SystemExit("Spectrogram shape does not match returned axes")
    if chromagram.shape[0] != len(chroma_time) or chromagram.shape[1] != len(chroma_labels):
        raise SystemExit("Chromagram shape does not match returned axes")

    beat_report: dict[str, Any] | None = None
    if args.compute_beat:
        try:
            bpm, ratio = MidTermFeatures.beat_extraction(short_features, args.short_step, plot=False)
            beat_report = {"bpm": float(bpm), "ratio": float(ratio)}
        except Exception as exc:  # pragma: no cover - data-dependent diagnostic path
            beat_report = {"error": f"{type(exc).__name__}: {exc}"}

    matrices = {
        "short": short_features,
        "mid": mid_features,
        "spectrogram": spectrogram,
        "chromagram": chromagram,
    }
    written_files: list[str] = []
    if args.output_prefix is not None:
        written_files = write_outputs(args.output_prefix, args.store_csv, np, matrices)

    report: dict[str, Any] = {
        "source": source,
        "sampling_rate": int(sampling_rate),
        "samples": int(len(signal)),
        "duration_seconds": float(len(signal) / float(sampling_rate)),
        "io_import_shims": import_shims,
        "windows_seconds": {
            "short_window": float(args.short_window),
            "short_step": float(args.short_step),
            "mid_window": float(args.mid_window),
            "mid_step": float(args.mid_step),
        },
        "windows_samples": {
            "short_window": int(short_window),
            "short_step": int(short_step),
            "mid_window": int(mid_window),
            "mid_step": int(mid_step),
        },
        "short_features": {
            "shape": shape_list(short_features),
            "name_count": int(len(short_names)),
            "finite": bool(np.isfinite(short_features).all()),
            "first_names": list(short_names[:8]),
        },
        "mid_features": {
            "shape": shape_list(mid_features),
            "name_count": int(len(mid_names)),
            "finite": bool(np.isfinite(mid_features).all()),
            "first_names": list(mid_names[:8]),
            "short_from_mid_shape": shape_list(short_from_mid),
        },
        "spectrogram": {
            "shape": shape_list(spectrogram),
            "time_axis_length": int(len(spec_time)),
            "freq_axis_length": int(len(spec_freq)),
            "finite": bool(np.isfinite(spectrogram).all()),
        },
        "chromagram": {
            "shape": shape_list(chromagram),
            "time_axis_length": int(len(chroma_time)),
            "labels": list(chroma_labels),
            "finite": bool(np.isfinite(chromagram).all()),
        },
        "beat": beat_report,
        "written_files": written_files,
    }
    if args.verbose:
        report["captured_legacy_stdout"] = legacy_stdout.getvalue().splitlines()

    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
