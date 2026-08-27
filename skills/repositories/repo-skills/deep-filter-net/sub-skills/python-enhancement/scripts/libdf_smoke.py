#!/usr/bin/env python3
"""No-network smoke test for libdf STFT/ISTFT/ERB primitives."""

from __future__ import annotations

import argparse
import json
import math
from typing import Optional

import numpy as np


def positive_int(value: str) -> int:
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return ivalue


def positive_float(value: str) -> float:
    fvalue = float(value)
    if fvalue <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return fvalue


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Construct libdf.DF and run STFT, synthesis, ERB, erb_norm, and unit_norm "
            "shape/finite checks without loading models, audio files, or network resources."
        )
    )
    parser.add_argument("--sr", type=positive_int, default=48000, help="Sampling rate. Default: 48000")
    parser.add_argument("--fft", type=positive_int, default=960, help="FFT/window size. Default: 960")
    parser.add_argument("--hop", type=positive_int, default=480, help="Hop size. Default: 480")
    parser.add_argument(
        "--duration", type=positive_float, default=0.1, help="Signal duration in seconds. Default: 0.1"
    )
    parser.add_argument("--channels", type=positive_int, default=1, help="Channel count. Default: 1")
    parser.add_argument("--nb-bands", type=positive_int, default=32, help="ERB band count. Default: 32")
    parser.add_argument(
        "--min-nb-erb-freqs",
        type=positive_int,
        default=1,
        help="Minimum FFT bins per ERB band. Default: 1",
    )
    parser.add_argument("--alpha", type=float, default=0.99, help="Normalization alpha. Default: 0.99")
    parser.add_argument("--silence", action="store_true", help="Use zeros instead of deterministic sine waves.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    return parser


def make_signal(sr: int, hop: int, duration: float, channels: int, silence: bool) -> np.ndarray:
    # Use a hop-aligned length so synthesis shape expectations are stable.
    requested = max(1, int(round(sr * duration)))
    frames = max(1, int(math.ceil(requested / hop)))
    n_samples = frames * hop
    if silence:
        return np.zeros((channels, n_samples), dtype=np.float32)

    t = np.arange(n_samples, dtype=np.float32) / float(sr)
    data = []
    for ch in range(channels):
        freq = 220.0 * (ch + 1)
        sig = 0.05 * np.sin(2.0 * np.pi * freq * t) + 0.025 * np.sin(
            2.0 * np.pi * (freq * 2.0 + 30.0) * t
        )
        data.append(sig.astype(np.float32))
    return np.stack(data, axis=0)


def assert_finite(name: str, array: np.ndarray) -> None:
    if not np.all(np.isfinite(array)):
        raise AssertionError(f"{name} contains non-finite values")


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.hop > args.fft:
        raise SystemExit("--hop must be <= --fft")
    if not (0.0 < args.alpha < 1.0):
        raise SystemExit("--alpha should be in the open interval (0, 1)")

    try:
        import libdf
        from libdf import DF
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing libdf. Install DeepFilterLib/deepfilterlib in the active environment before retrying."
        ) from exc

    signal = make_signal(args.sr, args.hop, args.duration, args.channels, args.silence)
    df_state = DF(
        sr=args.sr,
        fft_size=args.fft,
        hop_size=args.hop,
        nb_bands=args.nb_bands,
        min_nb_erb_freqs=args.min_nb_erb_freqs,
    )

    spec = df_state.analysis(signal)
    if spec.ndim != 3:
        raise AssertionError(f"analysis output must be 3-D [C, frames, bins], got {spec.shape}")
    if spec.shape[0] != args.channels:
        raise AssertionError(f"analysis channel count mismatch: got {spec.shape[0]}, expected {args.channels}")
    expected_bins = args.fft // 2 + 1
    if spec.shape[2] != expected_bins:
        raise AssertionError(f"analysis fft bins mismatch: got {spec.shape[2]}, expected {expected_bins}")
    if not np.iscomplexobj(spec):
        raise AssertionError(f"analysis output should be complex, got dtype {spec.dtype}")
    assert_finite("analysis", spec)

    synth = df_state.synthesis(np.array(spec, copy=True))
    if synth.ndim != 2 or synth.shape[0] != args.channels:
        raise AssertionError(f"synthesis output should be [C, samples], got {synth.shape}")
    assert_finite("synthesis", synth)

    erb_fb = df_state.erb_widths()
    erb_spec = libdf.erb(spec, erb_fb)
    if erb_spec.shape[:2] != spec.shape[:2] or erb_spec.shape[-1] != args.nb_bands:
        raise AssertionError(
            f"ERB shape mismatch: got {erb_spec.shape}, expected [C, frames, {args.nb_bands}]"
        )
    assert_finite("erb", erb_spec)

    erb_norm = libdf.erb_norm(erb_spec, args.alpha)
    if erb_norm.shape != erb_spec.shape:
        raise AssertionError(f"erb_norm shape mismatch: got {erb_norm.shape}, expected {erb_spec.shape}")
    assert_finite("erb_norm", erb_norm)

    unit_norm = libdf.unit_norm(spec, args.alpha)
    if unit_norm.shape != spec.shape:
        raise AssertionError(f"unit_norm shape mismatch: got {unit_norm.shape}, expected {spec.shape}")
    assert_finite("unit_norm", unit_norm)

    report = {
        "ok": True,
        "sr": args.sr,
        "fft": args.fft,
        "hop": args.hop,
        "channels": args.channels,
        "nb_bands": args.nb_bands,
        "input_shape": list(signal.shape),
        "analysis_shape": list(spec.shape),
        "analysis_dtype": str(spec.dtype),
        "synthesis_shape": list(synth.shape),
        "synthesis_dtype": str(synth.dtype),
        "erb_widths_shape": list(np.asarray(erb_fb).shape),
        "erb_shape": list(erb_spec.shape),
        "erb_norm_shape": list(erb_norm.shape),
        "unit_norm_shape": list(unit_norm.shape),
        "state": {
            "sr": int(df_state.sr()),
            "fft_size": int(df_state.fft_size()),
            "hop_size": int(df_state.hop_size()),
            "nb_erb": int(df_state.nb_erb()),
        },
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("libdf smoke passed")
        for key in (
            "input_shape",
            "analysis_shape",
            "synthesis_shape",
            "erb_widths_shape",
            "erb_shape",
            "erb_norm_shape",
            "unit_norm_shape",
        ):
            print(f"  {key}: {report[key]}")
        print(
            "  state: "
            f"sr={report['state']['sr']} fft={report['state']['fft_size']} "
            f"hop={report['state']['hop_size']} nb_erb={report['state']['nb_erb']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
