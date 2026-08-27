#!/usr/bin/env python3
"""Plot one trial from an rPPG test-output pickle without an interactive UI.

The input is the local pickle schema documented by this sub-skill. Pickle can
execute code while loading, so only open files from a trusted local run.
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


REQUIRED_KEYS = ("predictions", "labels", "label_type", "fs")


def _as_vector(value: Any) -> np.ndarray:
    """Convert a tensor-like chunk to a finite-dimensional float vector."""
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    array = np.asarray(value)
    if array.ndim == 0:
        array = array.reshape(1)
    if not np.issubdtype(array.dtype, np.number):
        raise ValueError(f"chunk has non-numeric dtype {array.dtype}")
    return np.asarray(array, dtype=float).reshape(-1)


def _trial_vector(trial: Any, name: str) -> np.ndarray:
    """Concatenate a direct vector or sorted chunk mapping."""
    if isinstance(trial, dict):
        if not trial:
            raise ValueError(f"{name} trial has no chunks")
        chunks: Iterable[Any] = (value for _, value in sorted(trial.items(), key=lambda item: str(item[0])))
    else:
        chunks = (trial,)
    vectors = [_as_vector(chunk) for chunk in chunks]
    if not vectors or sum(vector.size for vector in vectors) == 0:
        raise ValueError(f"{name} trial is empty")
    return np.concatenate(vectors)


def _smooth_detrend(signal: np.ndarray, lambda_value: float = 100.0) -> np.ndarray:
    """Match the toolbox's second-difference smooth detrending operation."""
    from scipy.sparse import spdiags

    length = signal.size
    if length < 3:
        raise ValueError("at least 3 samples are needed for detrending")
    identity = np.identity(length)
    data = np.array([np.ones(length), -2 * np.ones(length), np.ones(length)])
    difference = spdiags(data, np.array([0, 1, 2]), length - 2, length).toarray()
    return np.dot(
        identity - np.linalg.inv(identity + (lambda_value**2) * np.dot(difference.T, difference)),
        signal,
    )


def _process(signal: np.ndarray, label_type: str, fs: float, low: float, high: float) -> np.ndarray:
    """Apply the documented derivative recovery, detrend, and bandpass."""
    from scipy.signal import butter, filtfilt

    transformed = np.cumsum(signal) if label_type == "DiffNormalized" else signal
    detrended = _smooth_detrend(transformed)
    if not 0 < low < high < fs / 2:
        raise ValueError(f"band must satisfy 0 < low < high < Nyquist ({fs / 2:g} Hz)")
    b, a = butter(1, [low / fs * 2, high / fs * 2], btype="bandpass")
    return filtfilt(b, a, np.asarray(detrended, dtype=float))


def _safe_output(path_text: str | None, force: bool, parser: argparse.ArgumentParser) -> Path:
    """Validate an explicit non-destructive output path."""
    if not path_text:
        parser.error("--output is required unless --list-trials is used")
    path = Path(path_text).expanduser()
    if not path.suffix.lower() in {".png", ".pdf", ".svg"}:
        parser.error("--output must end in .png, .pdf, or .svg")
    if path.exists() and not force:
        parser.error(f"refusing to overwrite existing output: {path} (use --force)")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="trusted prediction pickle")
    parser.add_argument("--output", help="PNG, PDF, or SVG output path")
    parser.add_argument("--trial", default="0", help="zero-based trial index or exact trial key (default: 0)")
    parser.add_argument("--chunk-size", type=int, default=-1, help="samples to plot; -1 means the full trial (default: -1)")
    parser.add_argument("--chunk", type=int, default=0, help="zero-based chunk number when --chunk-size is positive")
    parser.add_argument("--raw", action="store_true", help="plot stored values without detrending or bandpass")
    parser.add_argument("--band-low", type=float, default=0.75, help="processed plot lower band in Hz (default: 0.75)")
    parser.add_argument("--band-high", type=float, default=2.5, help="processed plot upper band in Hz (default: 2.5)")
    parser.add_argument("--list-trials", action="store_true", help="list trial ids and exit without writing")
    parser.add_argument("--force", action="store_true", help="allow replacing an existing output file")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Load, validate, optionally process, and plot a saved trial."""
    parser = _parser()
    args = parser.parse_args(argv)
    input_path = Path(args.input).expanduser()
    if not input_path.is_file():
        parser.error(f"input pickle does not exist: {input_path}")
    try:
        with input_path.open("rb") as handle:
            data = pickle.load(handle)
        missing = [key for key in REQUIRED_KEYS if key not in data]
        if missing:
            raise ValueError(f"missing required key(s): {', '.join(missing)}")
        predictions = data["predictions"]
        labels = data["labels"]
        if not isinstance(predictions, dict) or not isinstance(labels, dict):
            raise ValueError("predictions and labels must be trial mappings")
        trial_ids = sorted(predictions.keys(), key=str)
        if args.list_trials:
            for index, trial_id in enumerate(trial_ids):
                print(f"{index}: {trial_id}")
            return 0
        if not trial_ids:
            raise ValueError("predictions contains no trials")
        trial_id: Any = None
        exact = [candidate for candidate in trial_ids if str(candidate) == args.trial]
        if exact:
            trial_id = exact[0]
        elif args.trial.isdigit():
            index = int(args.trial)
            if index < len(trial_ids):
                trial_id = trial_ids[index]
        if trial_id is None:
            raise ValueError(f"unknown trial {args.trial!r}; use --list-trials")
        if trial_id not in labels:
            raise ValueError(f"trial {trial_id!r} is missing from labels")
        prediction = _trial_vector(predictions[trial_id], "prediction")
        label = _trial_vector(labels[trial_id], "label")
        if prediction.size != label.size:
            raise ValueError(f"prediction/label lengths differ: {prediction.size} vs {label.size}")
        fs = float(data["fs"])
        if not np.isfinite(fs) or fs <= 0:
            raise ValueError(f"fs must be positive, got {data['fs']!r}")
        label_type = str(data["label_type"])
        if label_type not in {"DiffNormalized", "Raw", "Standardized"}:
            raise ValueError(f"unsupported label_type {label_type!r}")
        if args.chunk_size == 0 or args.chunk_size < -1 or args.chunk < 0:
            raise ValueError("chunk-size must be -1 or positive and chunk must be nonnegative")
        if args.chunk_size == -1:
            start, stop = 0, prediction.size
        else:
            start = args.chunk * args.chunk_size
            stop = min(start + args.chunk_size, prediction.size)
            if start >= prediction.size:
                raise ValueError("requested chunk starts beyond the trial")
        prediction = prediction[start:stop]
        label = label[start:stop]
        if prediction.size == 0:
            raise ValueError("selected signal range is empty")
        if not args.raw:
            if prediction.size < 9:
                raise ValueError("processed plotting needs at least 9 samples; retry with --raw")
            prediction = _process(prediction, label_type, fs, args.band_low, args.band_high)
            label = _process(label, label_type, fs, args.band_low, args.band_high)
        if np.ptp(prediction) == 0 or np.ptp(label) == 0:
            print("warning: at least one plotted signal is constant", file=sys.stderr)
        output = _safe_output(args.output, args.force, parser)
        time = np.arange(prediction.size, dtype=float) / fs
        figure, axis = plt.subplots(figsize=(10, 5))
        axis.plot(time, prediction, color="red", label="Predictions")
        axis.plot(time, label, color="black", label="Labels")
        axis.set_title(f"Trial {trial_id} | {label_type} | fs={fs:g} Hz")
        axis.set_xlabel("Time (s)")
        axis.set_ylabel("Signal")
        axis.grid(True, alpha=0.25)
        axis.legend()
        figure.tight_layout()
        figure.savefig(output, dpi=150)
        plt.close(figure)
        print(f"saved plot: {output}")
        return 0
    except (OSError, EOFError, ImportError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
