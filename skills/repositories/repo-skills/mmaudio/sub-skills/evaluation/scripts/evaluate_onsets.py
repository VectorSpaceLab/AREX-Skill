#!/usr/bin/env python3
"""Score MMAudio onset predictions against text annotations on CPU.

The helper is deterministic and safe by default:
- it only reads prediction audio and ground-truth text files;
- it does not launch CUDA work;
- it does not write results unless explicitly requested.

The implementation preserves the source repo's 8-second onset metric structure
while adding safer file handling, configurable naming, and optional result
writing.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

AUDIO_SUFFIXES = {".flac", ".wav"}
DEFAULT_SAMPLE_RATE = 22050
DEFAULT_DURATION = 8.0
DEFAULT_DELTA = 0.3
DEFAULT_STRIP_PRED_SUFFIX = "_denoised"
DEFAULT_GT_SUFFIX = "_times"
DEFAULT_RESULTS_FILE = "eval_results.txt"
WINDOW_SECONDS = 0.05


@dataclass(frozen=True)
class FileMetrics:
    prediction: Path
    ground_truth: Path
    accuracy: float
    average_precision: float
    f1: float
    hits: int
    num_gt: int
    num_pred: int


def _fail(message: str) -> None:
    raise ValueError(message)


def _expand_path(value: str | None, field: str) -> Path:
    if value is None:
        _fail(f"{field} is required")
    value = value.strip()
    if not value:
        _fail(f"{field} must be non-empty")
    if any(ch in value for ch in ("\x00", "\n", "\r")):
        _fail(f"{field} must not contain control characters")
    return Path(value).expanduser()


def _validate_positive_float(value: float, field: str) -> float:
    if value <= 0:
        _fail(f"{field} must be > 0")
    return value


def _validate_positive_int(value: int, field: str) -> int:
    if value <= 0:
        _fail(f"{field} must be a positive integer")
    return value


def _import_numeric_dependencies():
    try:
        import numpy as np
        import librosa
        from sklearn.metrics import average_precision_score, f1_score
    except Exception as exc:  # pragma: no cover - import failure path depends on env
        raise RuntimeError(
            "librosa, numpy, and scikit-learn are required for onset scoring. "
            "Install the CPU metric dependencies or run inside the prepared MMAudio environment."
        ) from exc
    return np, librosa, average_precision_score, f1_score


def _window_max(np, waveform, onset_sample: int, radius: int) -> float:
    if waveform.size == 0:
        return 0.0
    start = max(0, onset_sample - radius)
    stop = min(int(waveform.shape[0]), onset_sample + radius)
    if start >= stop:
        return 0.0
    return float(np.max(waveform[start:stop]))


def _onset_nms(np, onsets, waveform, sample_rate: int, *, window_seconds: float = WINDOW_SECONDS):
    onsets = np.asarray(onsets, dtype=int)
    if onsets.size == 0:
        return onsets

    radius = max(1, int(window_seconds * sample_rate))
    confidence = np.array([_window_max(np, waveform, int(onset), radius) for onset in onsets], dtype=float)
    order = np.argsort(confidence)[::-1]
    kept: list[int] = []
    remaining = np.ones(onsets.shape[0], dtype=bool)

    for idx in order:
        if not remaining[idx]:
            continue
        current = int(onsets[idx])
        kept.append(current)
        for j, onset in enumerate(onsets):
            if remaining[j] and abs(int(onset) - current) < radius:
                remaining[j] = False

    return np.array(sorted(kept), dtype=int)


def _load_prediction(np, librosa, audio_path: Path, *, sample_rate: int, duration: float, delta: float):
    waveform, _ = librosa.load(audio_path, sr=sample_rate)
    waveform = waveform[: int(duration * sample_rate)]
    if waveform.size == 0:
        return np.array([], dtype=int), np.array([], dtype=float)

    onsets = librosa.onset.onset_detect(y=waveform, sr=sample_rate, units="samples", delta=delta)
    if onsets is None:
        onsets = np.array([], dtype=int)
    else:
        onsets = np.asarray(onsets, dtype=int)

    waveform_min = float(waveform.min())
    waveform_max = float(waveform.max())
    waveform_norm = (waveform - waveform_min) / (waveform_max - waveform_min + 1e-6)
    return onsets, waveform_norm


def _read_ground_truth(gt_file: Path, *, duration: float):
    times: list[float] = []
    with gt_file.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            token = stripped.split()[0]
            try:
                onset_time = float(token)
            except ValueError as exc:
                raise ValueError(f"Invalid onset time in {gt_file} line {line_no}: {token}") from exc
            if onset_time < 0:
                raise ValueError(f"Negative onset time in {gt_file} line {line_no}: {onset_time}")
            if onset_time >= duration:
                break
            times.append(onset_time)
    return times


def _safe_metrics(np, average_precision_score, f1_score, y_true: list[int], y_scores: list[float]):
    if not y_true:
        return 0.0, 0.0

    y_true_arr = np.asarray(y_true, dtype=int)
    y_scores_arr = np.asarray(y_scores, dtype=float)
    positives = int(y_true_arr.sum())
    negatives = int(y_true_arr.size - positives)

    if positives == 0 or negatives == 0:
        average_precision = 0.0
    else:
        try:
            average_precision = float(average_precision_score(y_true_arr, y_scores_arr))
        except Exception:
            average_precision = 0.0
    if math.isnan(average_precision) or math.isinf(average_precision):
        average_precision = 0.0

    try:
        f1 = float(f1_score(y_true_arr, (y_scores_arr > 0).astype(int), zero_division=0))
    except Exception:
        f1 = 0.0
    if math.isnan(f1) or math.isinf(f1):
        f1 = 0.0

    return average_precision, f1


def _score_file(
    np,
    librosa,
    average_precision_score,
    f1_score,
    audio_path: Path,
    gt_path: Path,
    *,
    sample_rate: int,
    duration: float,
    delta: float,
    strip_pred_suffix: str,
) -> FileMetrics:
    if not audio_path.exists():
        raise FileNotFoundError(f"Prediction audio file does not exist: {audio_path}")
    if not gt_path.exists():
        raise FileNotFoundError(f"Ground-truth file does not exist: {gt_path}")

    try:
        onsets, waveform_norm = _load_prediction(
            np,
            librosa,
            audio_path,
            sample_rate=sample_rate,
            duration=duration,
            delta=delta,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to load prediction audio {audio_path}: {exc}") from exc

    onsets = _onset_nms(np, onsets, waveform_norm, sample_rate)
    remaining_onsets = onsets.tolist()
    gt_times = _read_ground_truth(gt_path, duration=duration)

    y_true: list[int] = []
    y_scores: list[float] = []
    hits = 0
    tolerance = delta * sample_rate
    radius = max(1, int(WINDOW_SECONDS * sample_rate))

    for gt_time in gt_times:
        if not remaining_onsets:
            break

        gt_sample = int(gt_time * sample_rate)
        differences = [abs(pred - gt_sample) for pred in remaining_onsets]
        candidates = [idx for idx, diff in enumerate(differences) if diff < tolerance]
        if not candidates:
            y_true.append(1)
            y_scores.append(0.0)
            continue

        confidences = [
            _window_max(np, waveform_norm, remaining_onsets[idx], radius)
            for idx in candidates
        ]
        best_candidate = candidates[int(np.argmax(confidences))]
        matched_onset = remaining_onsets[best_candidate]
        score = _window_max(np, waveform_norm, matched_onset, radius)
        hits += 1
        y_true.append(1)
        y_scores.append(score)
        remaining_onsets.pop(best_candidate)
        if not remaining_onsets:
            break

    for onset_sample in remaining_onsets:
        y_true.append(0)
        y_scores.append(_window_max(np, waveform_norm, onset_sample, radius))

    accuracy = hits / len(gt_times) if gt_times else 0.0
    average_precision, f1 = _safe_metrics(np, average_precision_score, f1_score, y_true, y_scores)
    return FileMetrics(
        prediction=audio_path,
        ground_truth=gt_path,
        accuracy=accuracy,
        average_precision=average_precision,
        f1=f1,
        hits=hits,
        num_gt=len(gt_times),
        num_pred=len(onsets),
    )


def _score_files(
    input_dir: Path,
    gt_dir: Path,
    *,
    sample_rate: int,
    duration: float,
    delta: float,
    strip_pred_suffix: str,
    gt_suffix: str,
) -> list[FileMetrics]:
    np, librosa, average_precision_score, f1_score = _import_numeric_dependencies()

    audio_files = [
        path for path in sorted(input_dir.iterdir())
        if path.is_file() and path.suffix.lower() in AUDIO_SUFFIXES
    ]
    if not audio_files:
        raise FileNotFoundError(f"No .flac or .wav files found in input directory: {input_dir}")

    metrics: list[FileMetrics] = []
    for audio_path in audio_files:
        stem = audio_path.stem
        if strip_pred_suffix and stem.endswith(strip_pred_suffix):
            stem = stem[: -len(strip_pred_suffix)]
        gt_path = gt_dir / f"{stem}{gt_suffix}.txt"
        metrics.append(
            _score_file(
                np,
                librosa,
                average_precision_score,
                f1_score,
                audio_path,
                gt_path,
                sample_rate=sample_rate,
                duration=duration,
                delta=delta,
                strip_pred_suffix=strip_pred_suffix,
            )
        )
    return metrics


def _format_summary(metrics: list[FileMetrics], *, per_file: bool) -> list[str]:
    if not metrics:
        return ["No files were scored."]

    lines = [f"Scored files: {len(metrics)}"]
    lines.append(f"Overall accuracy: {sum(item.accuracy for item in metrics) / len(metrics):.4f}")
    lines.append(f"Overall AP: {sum(item.average_precision for item in metrics) / len(metrics):.4f}")
    lines.append(f"Overall F1: {sum(item.f1 for item in metrics) / len(metrics):.4f}")

    if per_file:
        lines.append("")
        lines.append("Per-file metrics:")
        for item in metrics:
            lines.append(
                f"{item.prediction.name}\tgt={item.ground_truth.name}\t"
                f"acc={item.accuracy:.4f}\tap={item.average_precision:.4f}\tf1={item.f1:.4f}\t"
                f"hits={item.hits}/{item.num_gt}\tpred={item.num_pred}"
            )
    return lines


def _write_summary(output_file: Path, lines: list[str]) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score MMAudio onset predictions on CPU.")
    parser.add_argument("--input-dir", "--input_dir", dest="input_dir", required=True, help="Directory with .flac or .wav predictions")
    parser.add_argument("--gt-dir", "--gt_dir", dest="gt_dir", required=True, help="Directory with onset text files")
    parser.add_argument("--delta", type=float, default=DEFAULT_DELTA, help="Onset detection threshold and matching tolerance factor")
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_SAMPLE_RATE, help="Analysis sample rate used for loading and matching")
    parser.add_argument("--duration", type=float, default=DEFAULT_DURATION, help="Analysis duration in seconds")
    parser.add_argument("--strip-pred-suffix", "--strip_pred_suffix", dest="strip_pred_suffix", default=DEFAULT_STRIP_PRED_SUFFIX, help="Suffix to remove from prediction stems before appending GT suffix")
    parser.add_argument("--gt-suffix", "--gt_suffix", dest="gt_suffix", default=DEFAULT_GT_SUFFIX, help="Stem suffix appended before .txt when locating GT files")
    parser.add_argument("--per-file", "--per_file", action="store_true", help="Print per-file metrics")
    parser.add_argument("--write-results", "--write_results", action="store_true", help="Write eval_results.txt under the prediction directory")
    parser.add_argument("--output-file", "--output_file", dest="output_file", default=None, help="Write the summary to this path instead of the default prediction-dir file")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        input_dir = _expand_path(args.input_dir, "--input-dir")
        gt_dir = _expand_path(args.gt_dir, "--gt-dir")
        if not input_dir.exists():
            _fail(f"input directory does not exist: {input_dir}")
        if not input_dir.is_dir():
            _fail(f"input directory must be a directory: {input_dir}")
        if not gt_dir.exists():
            _fail(f"ground-truth directory does not exist: {gt_dir}")
        if not gt_dir.is_dir():
            _fail(f"ground-truth directory must be a directory: {gt_dir}")

        sample_rate = _validate_positive_int(args.sample_rate, "sample-rate")
        duration = _validate_positive_float(args.duration, "duration")
        delta = _validate_positive_float(args.delta, "delta")
        strip_pred_suffix = (args.strip_pred_suffix or "").strip()
        gt_suffix = (args.gt_suffix or "").strip()
        output_file = _expand_path(args.output_file, "--output-file") if args.output_file else None
        if output_file is None and args.write_results:
            output_file = input_dir / DEFAULT_RESULTS_FILE
        if output_file is not None and args.write_results and args.output_file:
            # Explicit output path wins; the flag combination is still allowed.
            pass

        metrics = _score_files(
            input_dir,
            gt_dir,
            sample_rate=sample_rate,
            duration=duration,
            delta=delta,
            strip_pred_suffix=strip_pred_suffix,
            gt_suffix=gt_suffix,
        )
        lines = _format_summary(metrics, per_file=bool(args.per_file))
        for line in lines:
            print(line)
        if output_file is not None:
            _write_summary(output_file, lines)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
