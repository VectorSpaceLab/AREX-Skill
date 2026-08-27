#!/usr/bin/env python3
"""Create a static inspection plot for one preprocessed input/label pair."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _detrend(signal: np.ndarray, lambda_value: float = 100.0) -> np.ndarray:
    """Apply the toolbox-style smooth second-difference detrend."""
    from scipy.sparse import spdiags

    length = signal.size
    if length < 3:
        raise ValueError("at least 3 label samples are needed for detrending")
    identity = np.identity(length)
    data = np.array([np.ones(length), -2 * np.ones(length), np.ones(length)])
    difference = spdiags(data, np.array([0, 1, 2]), length - 2, length).toarray()
    return np.dot(
        identity - np.linalg.inv(identity + (lambda_value**2) * np.dot(difference.T, difference)),
        signal,
    )


def _process_label(label: np.ndarray, fs: float, diff_flag: bool, no_filter: bool) -> np.ndarray:
    """Apply explicit label transformation and optional visualization filter."""
    from scipy.signal import butter, filtfilt

    transformed = np.cumsum(label) if diff_flag else label
    detrended = _detrend(transformed)
    if no_filter:
        return detrended
    low, high = 0.75, 2.5
    if high >= fs / 2:
        raise ValueError(f"0.75-2.5 Hz visualization band exceeds Nyquist ({fs / 2:g} Hz); use --no-filter")
    b, a = butter(1, [low / fs * 2, high / fs * 2], btype="bandpass")
    return filtfilt(b, a, np.asarray(detrended, dtype=float))


def _display_frame(frame: np.ndarray) -> np.ndarray:
    """Make an arbitrary numeric RGB frame safe and informative for imshow."""
    frame = np.asarray(frame)
    if not np.issubdtype(frame.dtype, np.number):
        raise ValueError(f"frame has non-numeric dtype {frame.dtype}")
    frame = np.asarray(frame, dtype=float)
    minimum, maximum = np.nanmin(frame), np.nanmax(frame)
    if not np.isfinite(minimum) or not np.isfinite(maximum):
        raise ValueError("selected frame contains no finite pixel values")
    if minimum < 0 or maximum > 1:
        if maximum == minimum:
            return np.zeros_like(frame)
        frame = (frame - minimum) / (maximum - minimum)
    return np.clip(frame, 0, 1)


def _safe_output(text: str | None, force: bool, parser: argparse.ArgumentParser) -> Path:
    if not text:
        parser.error("--output is required")
    path = Path(text).expanduser()
    if path.suffix.lower() not in {".png", ".pdf", ".svg"}:
        parser.error("--output must end in .png, .pdf, or .svg")
    if path.exists() and not force:
        parser.error(f"refusing to overwrite existing output: {path} (use --force)")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="frame-first input .npy with last dimension 3 or 6")
    parser.add_argument("--label", required=True, help="matching scalar label .npy")
    parser.add_argument("--output", required=True, help="PNG, PDF, or SVG output path")
    parser.add_argument("--frame", type=int, default=0, help="zero-based frame to display (default: 0)")
    parser.add_argument("--fs", type=float, default=30.0, help="label sampling rate in Hz (default: 30)")
    transform = parser.add_mutually_exclusive_group()
    transform.add_argument("--diff-flag", action="store_true", help="cumulative-sum labels before detrending")
    transform.add_argument("--no-diff-flag", action="store_true", help="treat labels as Raw/Standardized values")
    parser.add_argument("--no-filter", action="store_true", help="skip the 0.75-2.5 Hz label bandpass")
    parser.add_argument("--force", action="store_true", help="allow replacing an existing output file")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Validate arrays and write a noninteractive inspection figure."""
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        input_path, label_path = Path(args.input).expanduser(), Path(args.label).expanduser()
        if not input_path.is_file() or not label_path.is_file():
            raise ValueError("both --input and --label must be existing .npy files")
        if args.frame < 0 or not np.isfinite(args.fs) or args.fs <= 0:
            raise ValueError("frame must be nonnegative and fs must be positive")
        input_data = np.load(input_path, allow_pickle=False)
        label_data = np.load(label_path, allow_pickle=False)
        if input_data.ndim < 3 or input_data.shape[-1] not in {3, 6}:
            raise ValueError(f"input shape must be frame-first (..., 3) or (..., 6), got {input_data.shape}")
        frame_count = input_data.shape[0]
        if args.frame >= frame_count:
            raise ValueError(f"frame {args.frame} is outside input frame range 0..{frame_count - 1}")
        label = np.asarray(label_data, dtype=float).reshape(-1)
        if label.size != frame_count:
            raise ValueError(f"label length {label.size} does not match input frames {frame_count}")
        if label.size == 0:
            raise ValueError("label array is empty")
        if not np.all(np.isfinite(label)):
            raise ValueError("label array contains non-finite values")
        if args.no_filter or label.size < 9:
            if not args.no_filter and label.size < 9:
                raise ValueError("filtered plotting needs at least 9 labels; retry with --no-filter")
            plotted_label = label
        else:
            plotted_label = _process_label(label, args.fs, args.diff_flag, args.no_filter)
        if np.ptp(label) == 0:
            print("warning: label signal is constant; dominant frequency is not meaningful", file=sys.stderr)
        frame = input_data[args.frame]
        if input_data.shape[-1] == 6:
            frame = np.concatenate((frame[..., 3:], frame[..., :3]), axis=1)
        frame = _display_frame(frame)
        frequency = np.fft.rfftfreq(plotted_label.size, d=1.0 / args.fs)
        power = np.abs(np.fft.rfft(plotted_label - np.mean(plotted_label))) ** 2
        output = _safe_output(args.output, args.force, parser)
        figure, axes = plt.subplots(2, 2, figsize=(11, 7))
        axes[0, 0].imshow(frame)
        axes[0, 0].set_title(f"Frame {args.frame}")
        axes[0, 0].set_axis_off()
        axes[0, 1].plot(np.arange(plotted_label.size) / args.fs, plotted_label, color="black")
        axes[0, 1].set_title("Label waveform")
        axes[0, 1].set_xlabel("Time (s)")
        axes[0, 1].set_ylabel("Magnitude")
        axes[1, 0].plot(frequency, power, color="tab:blue")
        axes[1, 0].set_xlim(0, min(5.0, args.fs / 2))
        axes[1, 0].set_title("Label periodogram proxy")
        axes[1, 0].set_xlabel("Frequency (Hz)")
        axes[1, 0].set_ylabel("Power")
        axes[1, 1].axis("off")
        axes[1, 1].text(
            0.02,
            0.95,
            f"input: {input_path.name}\nlabel: {label_path.name}\nframes: {frame_count}\n"
            f"fs: {args.fs:g} Hz\ndiff_flag: {args.diff_flag}\nfiltered: {not args.no_filter}",
            va="top",
            family="monospace",
        )
        figure.tight_layout()
        figure.savefig(output, dpi=150)
        plt.close(figure)
        print(f"saved plot: {output}")
        return 0
    except (OSError, ValueError, TypeError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
