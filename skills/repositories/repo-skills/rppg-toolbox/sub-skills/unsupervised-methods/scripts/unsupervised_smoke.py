#!/usr/bin/env python3
"""Deterministic, source-independent smoke checks for traditional rPPG methods.

The script generates a small RGB video in memory, exercises the seven public
method contracts, and reports each method separately. It never reads a dataset,
imports the repository, downloads data, or writes files. This is a numerical
boundary check, not a scientific accuracy or implementation-parity test.
"""

from __future__ import annotations

import argparse
import math
import sys
from typing import Callable, Dict

import numpy as np

try:
    from scipy import signal
except ImportError as exc:  # pragma: no cover - environment diagnostic
    raise SystemExit(f"scipy is required for this smoke check: {exc}") from exc


METHOD_NAMES = ("POS", "CHROM", "ICA", "GREEN", "LGI", "PBV", "OMIT")


def make_frames(frames: int, height: int, width: int, fs: float, seed: int) -> np.ndarray:
    """Return finite, positive synthetic RGB frames with varied pulse content."""
    rng = np.random.default_rng(seed)
    time = np.arange(frames, dtype=np.float64) / fs
    pulse = np.sin(2.0 * np.pi * 1.2 * time)
    secondary = np.sin(2.0 * np.pi * 1.7 * time + 0.35)
    # Distinct channel mixtures avoid creating an artificially singular RGB
    # covariance while keeping the generated signal reproducible.
    channels = np.stack(
        (
            100.0 + 2.1 * pulse + 0.35 * secondary,
            115.0 + 3.0 * pulse + 0.60 * secondary,
            90.0 + 1.4 * pulse - 0.45 * secondary,
        ),
        axis=1,
    )
    spatial = rng.normal(0.0, 0.03, size=(frames, height, width, 3))
    frames_rgb = channels[:, None, None, :] * (1.0 + spatial)
    return np.asarray(frames_rgb, dtype=np.float64)


def average_rgb(frames: np.ndarray) -> np.ndarray:
    """Reduce `(T,H,W,3)` frames to a `(T,3)` RGB trajectory."""
    if frames.ndim != 4 or frames.shape[-1] < 3:
        raise ValueError(f"expected (T,H,W,>=3), got {frames.shape}")
    rgb = np.mean(frames[..., :3], axis=(1, 2))
    if rgb.shape[0] == 0 or not np.all(np.isfinite(rgb)):
        raise ValueError("RGB trajectory is empty or non-finite")
    return rgb


def method_green(frames: np.ndarray, fs: float) -> np.ndarray:
    del fs
    return average_rgb(frames)[:, 1]


def method_pos(frames: np.ndarray, fs: float) -> np.ndarray:
    """Numerically equivalent POS-shaped projection without source imports."""
    rgb = average_rgb(frames)
    n_frames = rgb.shape[0]
    win = math.ceil(1.6 * fs)
    if win < 2 or n_frames <= win:
        raise ValueError(f"POS needs more than one {win}-frame window; got {n_frames}")
    accumulated = np.zeros(n_frames, dtype=np.float64)
    for end in range(win, n_frames + 1):
        start = end - win
        baseline = np.mean(rgb[start:end], axis=0)
        if np.any(np.isclose(baseline, 0.0)):
            raise ValueError("POS encountered a zero RGB baseline")
        normalized = (rgb[start:end] / baseline).T
        projected = np.array([[0.0, 1.0, -1.0], [-2.0, 1.0, 1.0]]) @ normalized
        spread = np.std(projected[1])
        if not np.isfinite(spread) or np.isclose(spread, 0.0):
            raise ValueError("POS encountered a zero projected-channel variance")
        h = projected[0] + (np.std(projected[0]) / spread) * projected[1]
        accumulated[start:end] += h - np.mean(h)
    b, a = signal.butter(1, [0.75 / fs * 2.0, 3.0 / fs * 2.0], btype="bandpass")
    return signal.filtfilt(b, a, accumulated.astype(np.float64))


def method_chrom(frames: np.ndarray, fs: float) -> np.ndarray:
    """Exercise the CHROM window/filter/overlap-add numerical contract."""
    rgb = average_rgb(frames)
    n_frames = rgb.shape[0]
    nyquist = fs / 2.0
    b, a = signal.butter(3, [0.7 / nyquist, 2.5 / nyquist], btype="bandpass")
    win = math.ceil(1.6 * fs)
    if win % 2:
        win += 1
    half = win // 2
    n_windows = math.floor((n_frames - half) / half)
    if n_windows <= 0:
        raise ValueError(f"CHROM needs at least one {win}-frame window; got {n_frames}")
    output = np.zeros(half * (n_windows + 1), dtype=np.float64)
    start = 0
    middle = half
    end = win
    for _ in range(n_windows):
        baseline = np.mean(rgb[start:end], axis=0)
        if np.any(np.isclose(baseline, 0.0)):
            raise ValueError("CHROM encountered a zero RGB baseline")
        normalized = rgb[start:end] / baseline
        x = 3.0 * normalized[:, 0] - 2.0 * normalized[:, 1]
        y = 1.5 * normalized[:, 0] + normalized[:, 1] - 1.5 * normalized[:, 2]
        xf = signal.filtfilt(b, a, x)
        yf = signal.filtfilt(b, a, y)
        y_std = np.std(yf)
        if not np.isfinite(y_std) or np.isclose(y_std, 0.0):
            raise ValueError("CHROM encountered a zero chrominance variance")
        windowed = (xf - (np.std(xf) / y_std) * yf) * signal.windows.hann(win)
        output[start:middle] += windowed[:half]
        output[middle:end] = windowed[half:]
        start = middle
        middle = start + half
        end = start + win
    return output


def method_ica(frames: np.ndarray, fs: float) -> np.ndarray:
    """Check ICA's finite RGB/conditioning/filter contract with SVD separation.

    The repository's ICA implementation uses a JADE-style separator. This
    source-independent smoke uses deterministic SVD decorrelation instead: the
    important smoke guarantee is valid RGB rank, temporal length, frequency,
    and finite one-dimensional output without importing the source checkout.
    """
    rgb = average_rgb(frames)
    if rgb.shape[0] < 16:
        raise ValueError("ICA needs a temporally resolved RGB trajectory")
    centered = signal.detrend(rgb, axis=0, type="linear")
    scale = np.std(centered, axis=0)
    if np.any(~np.isfinite(scale)) or np.any(np.isclose(scale, 0.0)):
        raise ValueError("ICA requires non-zero variance in every RGB channel")
    normalized = centered / scale
    if np.linalg.matrix_rank(normalized) < 2:
        raise ValueError("ICA requires non-degenerate RGB rank")
    u, singular, _ = np.linalg.svd(normalized, full_matrices=False)
    components = u * singular
    frequencies = np.fft.rfftfreq(rgb.shape[0], d=1.0 / fs)
    spectra = np.abs(np.fft.rfft(components, axis=0))
    band = (frequencies >= 0.7) & (frequencies <= 2.5)
    if not np.any(band):
        raise ValueError("ICA has no frequency bins in its pass band")
    selected = int(np.argmax(np.max(spectra[band], axis=0)))
    b, a = signal.butter(3, [0.7 / (fs / 2.0), 2.5 / (fs / 2.0)], btype="bandpass")
    return signal.filtfilt(b, a, components[:, selected].astype(np.float64))


def method_lgi(frames: np.ndarray, fs: float) -> np.ndarray:
    del fs
    rgb = average_rgb(frames).T[None, :, :]
    u, _, _ = np.linalg.svd(rgb)
    dominant = u[:, :, 0][:, :, None]
    projection = np.eye(3)[None, :, :] - np.matmul(dominant, np.swapaxes(dominant, 1, 2))
    projected = np.matmul(projection, rgb)
    return projected[0, 1, :].reshape(-1)


def method_pbv(frames: np.ndarray, fs: float) -> np.ndarray:
    del fs
    rgb = average_rgb(frames).T[None, :, :]
    channel_mean = np.mean(rgb, axis=2)
    if np.any(np.isclose(channel_mean, 0.0)):
        raise ValueError("PBV encountered a zero channel mean")
    normalized = rgb / channel_mean[:, :, None]
    signature_n = np.std(normalized, axis=2)
    signature_d = np.sqrt(np.sum(np.var(normalized, axis=2), axis=1, keepdims=True))
    if np.any(np.isclose(signature_d, 0.0)):
        raise ValueError("PBV encountered zero RGB variance")
    signature = signature_n / signature_d
    c = normalized
    ct = np.swapaxes(c, 1, 2)
    q = np.matmul(c, ct)
    try:
        weights = np.linalg.solve(q, signature[..., None])
    except np.linalg.LinAlgError as exc:
        raise ValueError(f"PBV covariance is singular: {exc}") from exc
    numerator = np.matmul(ct, weights)
    denominator = np.matmul(signature[:, None, :], weights)
    if np.any(np.isclose(denominator, 0.0)):
        raise ValueError("PBV encountered a zero projection denominator")
    return (numerator / denominator).squeeze().reshape(-1)


def method_omit(frames: np.ndarray, fs: float) -> np.ndarray:
    del fs
    rgb = average_rgb(frames).T
    if rgb.shape[1] < 3:
        raise ValueError("OMIT requires at least three RGB observations")
    q, _ = np.linalg.qr(rgb)
    basis = q[:, 0].reshape(1, -1)
    projection = np.eye(3) - np.matmul(basis.T, basis)
    return np.matmul(projection, rgb)[1, :].reshape(-1)


def build_methods() -> Dict[str, Callable[[np.ndarray, float], np.ndarray]]:
    """Return all method probes in dispatch order."""
    return {
        "POS": method_pos,
        "CHROM": method_chrom,
        "ICA": method_ica,
        "GREEN": method_green,
        "LGI": method_lgi,
        "PBV": method_pbv,
        "OMIT": method_omit,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse safe, in-memory smoke options."""
    parser = argparse.ArgumentParser(
        description="Run deterministic in-memory smoke checks for all traditional rPPG methods."
    )
    parser.add_argument("--frames", type=int, default=180, help="Synthetic frame count (default: 180).")
    parser.add_argument("--height", type=int, default=8, help="Synthetic frame height (default: 8).")
    parser.add_argument("--width", type=int, default=8, help="Synthetic frame width (default: 8).")
    parser.add_argument("--fs", type=float, default=30.0, help="Sampling rate in Hz (default: 30).")
    parser.add_argument("--seed", type=int, default=17, help="Synthetic RNG seed (default: 17).")
    parser.add_argument(
        "--allow-failures",
        action="store_true",
        help="Report method failures but exit successfully (useful for short-window probes).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Generate frames, run each probe, and return a diagnostic exit code."""
    args = parse_args(argv)
    if args.frames <= 0 or args.height <= 0 or args.width <= 0 or args.fs <= 0:
        print("CONFIG ERROR: frames, height, width, and fs must be positive", file=sys.stderr)
        return 2
    if args.fs <= 6.0:
        print("CONFIG ERROR: fs must exceed 6 Hz for the 3 Hz POS passband", file=sys.stderr)
        return 2

    frames = make_frames(args.frames, args.height, args.width, args.fs, args.seed)
    print(f"synthetic input: shape={frames.shape}, fs={args.fs:g}, seed={args.seed}")
    failures = 0
    for name in METHOD_NAMES:
        try:
            output = np.asarray(build_methods()[name](frames, args.fs))
            if output.ndim != 1 or output.size == 0:
                raise ValueError(f"output contract is 1-D/non-empty, got shape={output.shape}")
            if not np.all(np.isfinite(output)):
                raise ValueError("output contains NaN or Inf")
            spread = float(np.std(output))
            print(f"PASS {name:5s}: bvp_shape={output.shape}, std={spread:.6g}")
        except Exception as exc:  # report each method independently
            failures += 1
            print(f"FAIL {name:5s}: {type(exc).__name__}: {exc}")

    if failures and not args.allow_failures:
        print(f"RESULT: {failures}/{len(METHOD_NAMES)} method checks failed", file=sys.stderr)
        return 1
    print(f"RESULT: {len(METHOD_NAMES) - failures}/{len(METHOD_NAMES)} method checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
