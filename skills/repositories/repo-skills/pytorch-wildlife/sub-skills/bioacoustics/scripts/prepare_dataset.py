#!/usr/bin/env python3
"""Safe, installed-package-facing bioacoustics preparation helper.

This helper preserves the public companion CLI's ``--config`` and ``--steps``
contract, but validates geometry and uses the core spectrogram naming function
consistently. It never downloads weights, launches a service, or trains.

Examples:
  python prepare_dataset.py --config domain.yaml --validate-only
  python prepare_dataset.py --config domain.yaml --steps stats windows
  python prepare_dataset.py --config domain.yaml --steps spectrograms splits
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Iterable, Optional


STEPS = ("stats", "windows", "spectrograms", "splits")


def _load_config(path: str):
    from PytorchWildlife.data.bioacoustics.bioacoustics_configs import load_config

    return load_config(path)


def _window_path(config) -> Path:
    value = config.paths.windows_json or "windows_annotations.json"
    path = Path(value).expanduser()
    return path if path.is_absolute() else Path(config.paths.output_root).expanduser() / path


def _resolve_audio_path(config, value: str) -> str:
    path = Path(value).expanduser()
    if path.is_absolute():
        return str(path)
    return str(Path(config.paths.data_root).expanduser() / path)


def validate_config(config, *, check_files: bool = False) -> list[str]:
    """Return actionable validation errors without creating directories."""
    errors: list[str] = []
    audio = config.audio
    spec = config.spectrogram
    train = config.training
    paths = config.paths

    if not paths.data_root:
        errors.append("paths.data_root must be nonempty")
    if not paths.output_root:
        errors.append("paths.output_root must be nonempty")
    if not paths.spectrograms_dir:
        errors.append("paths.spectrograms_dir must be nonempty")
    if audio.sample_rate <= 0:
        errors.append("audio.sample_rate must be > 0")
    if audio.window_size_sec <= 0:
        errors.append("audio.window_size_sec must be > 0")
    if audio.overlap_sec < 0 or audio.overlap_sec >= audio.window_size_sec:
        errors.append("audio.overlap_sec must satisfy 0 <= overlap_sec < window_size_sec")
    if audio.window_strategy not in {"sliding", "balanced", "customized"}:
        errors.append("audio.window_strategy must be sliding, balanced, or customized")
    if not 0 <= audio.negative_proportion < 1:
        errors.append("audio.negative_proportion must be in [0, 1)")
    if audio.min_overlap_sec < 0:
        errors.append("audio.min_overlap_sec must be >= 0")
    for name in ("n_fft", "hop_length", "n_mels"):
        if getattr(spec, name) <= 0:
            errors.append(f"spectrogram.{name} must be > 0")
    if spec.mono_channel not in {"left", "right", "mean"}:
        errors.append("spectrogram.mono_channel must be left, right, or mean")
    if spec.storage_dtype not in {"float16", "float32"}:
        errors.append("spectrogram.storage_dtype must be float16 or float32")
    if train.num_classes < 2:
        errors.append("training.num_classes must be 2 or greater")
    if train.backbone not in {"resnet18", "resnet34", "resnet50"}:
        errors.append("training.backbone must be resnet18, resnet34, or resnet50")
    if train.x_col == "":
        errors.append("training.x_col must be nonempty")
    if train.y_col == "":
        errors.append("training.y_col must be nonempty")

    # Output locations may not exist yet, so check the nearest existing parent.
    for label, raw in (("output_root", paths.output_root),
                       ("spectrograms_dir", paths.spectrograms_dir)):
        path = Path(raw).expanduser()
        probe = path
        while not probe.exists() and probe != probe.parent:
            probe = probe.parent
        if probe.exists() and not os.access(probe, os.W_OK | os.X_OK):
            errors.append(f"{label} is not writable: {path}")
    if check_files and not errors:
        annotation = Path(paths.data_root).expanduser() / paths.annotations_file
        if not annotation.is_file():
            errors.append(f"annotation file does not exist: {annotation}")
        data_root = Path(paths.data_root).expanduser()
        if data_root.exists() and not os.access(data_root, os.R_OK | os.X_OK):
            errors.append(f"data_root is not readable: {data_root}")
    return errors


def _require_valid(config, *, check_files: bool = False) -> None:
    errors = validate_config(config, check_files=check_files)
    if errors:
        raise ValueError("Invalid bioacoustics configuration:\n- " + "\n- ".join(errors))


def _ensure_output(config) -> None:
    Path(config.paths.output_root).expanduser().mkdir(parents=True, exist_ok=True)
    Path(config.paths.spectrograms_dir).expanduser().mkdir(parents=True, exist_ok=True)


def run_stats(config) -> None:
    annotation_path = Path(config.paths.data_root).expanduser() / config.paths.annotations_file
    print(f"Loading annotations from: {annotation_path}")
    with annotation_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    sounds = data.get("sounds", [])
    annotations = data.get("annotations", [])
    durations = [float(sound.get("duration", 0)) for sound in sounds]
    categories: dict[Any, int] = {}
    for annotation in annotations:
        key = annotation.get("category_id", 0)
        categories[key] = categories.get(key, 0) + 1
    print(f"Sounds: {len(sounds)}")
    if durations:
        print(f"Total duration: {sum(durations):.1f}s ({sum(durations) / 3600:.2f}h)")
        print(f"Mean/min/max duration: {sum(durations) / len(durations):.1f}/"
              f"{min(durations):.1f}/{max(durations):.1f}s")
    print(f"Annotations: {len(annotations)}")
    print(f"Annotations by category: {categories}")


def run_windows(config) -> list[dict]:
    from PytorchWildlife.data.bioacoustics.bioacoustics_windows import build_windows

    annotation_path = str(Path(config.paths.data_root).expanduser() / config.paths.annotations_file)
    print(f"Building {config.audio.window_strategy} windows")
    windows = build_windows(
        annotation_file=annotation_path,
        window_size_sec=config.audio.window_size_sec,
        overlap_sec=config.audio.overlap_sec,
        sample_rate=config.audio.sample_rate,
        datasets_names=config.datasets,
        strategy=config.audio.window_strategy,
        negative_proportion=config.audio.negative_proportion,
        multiclass=config.audio.multiclass,
        min_overlap_sec=config.audio.min_overlap_sec,
    )
    destination = _window_path(config)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(windows, indent=2), encoding="utf-8")
    counts: dict[Any, int] = {}
    for window in windows:
        label = window.get("label", 0)
        counts[label] = counts.get(label, 0) + 1
    print(f"Saved {len(windows)} windows to {destination}")
    print(f"Label distribution: {counts}")
    return windows


def _windows_with_sound_paths(config, windows: Iterable[dict]) -> list[dict]:
    annotation_path = Path(config.paths.data_root).expanduser() / config.paths.annotations_file
    data = json.loads(annotation_path.read_text(encoding="utf-8"))
    sounds = {sound["id"]: sound for sound in data.get("sounds", [])}
    result: list[dict] = []
    for window in windows:
        sound = sounds.get(window.get("sound_id"))
        if sound is None:
            raise ValueError(f"window references unknown sound_id={window.get('sound_id')}")
        item = dict(window)
        item["sound_path"] = _resolve_audio_path(config, sound["file_name_path"])
        result.append(item)
    return result


def run_spectrograms(config, windows: list[dict]) -> None:
    from PytorchWildlife.data.bioacoustics.bioacoustics_spectrograms import (
        compute_mel_spectrograms_gpu,
    )

    items = _windows_with_sound_paths(config, windows)
    _ensure_output(config)
    print(f"Computing missing spectrograms in {config.paths.spectrograms_dir}")
    compute_mel_spectrograms_gpu(
        windows=items,
        sample_rate=config.audio.sample_rate,
        n_fft=config.spectrogram.n_fft,
        hop_length=config.spectrogram.hop_length,
        n_mels=config.spectrogram.n_mels,
        top_db=config.spectrogram.top_db,
        spectrograms_path=str(Path(config.paths.spectrograms_dir).expanduser()),
        save_npy=True,
        f_min=config.spectrogram.f_min,
        mono_channel=config.spectrogram.mono_channel,
        fill_highfreq=config.spectrogram.fill_highfreq,
        fill_mean_below_sr=config.spectrogram.fill_mean_below_sr,
        noise_db_std=config.spectrogram.noise_db_std,
        storage_dtype=config.spectrogram.storage_dtype,
    )


def run_splits(config, windows: list[dict]) -> None:
    import pandas as pd
    from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold
    from PytorchWildlife.data.bioacoustics.bioacoustics_spectrograms import default_spectrogram_path

    _ensure_output(config)
    with_sound = _windows_with_sound_paths(config, windows)
    rows = []
    for window in with_sound:
        row = dict(window)
        row["spec_name"] = Path(default_spectrogram_path(
            window, str(Path(config.paths.spectrograms_dir).expanduser())
        )).name
        if config.training.x_col != "spec_name":
            row[config.training.x_col] = row["spec_name"]
        if config.training.y_col != "label":
            row[config.training.y_col] = row["label"]
        row["spec_exists"] = Path(config.paths.spectrograms_dir).expanduser().joinpath(row["spec_name"]).is_file()
        rows.append(row)
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError("no windows available for splitting")
    frame = frame[frame["spec_exists"]].drop(columns=["spec_exists"])
    if frame.empty:
        raise FileNotFoundError("no spectrogram cache files match the generated windows")
    if config.training.y_col not in frame.columns:
        raise ValueError(f"generated windows do not contain label column {config.training.y_col!r}")

    # Group by recording so overlapping windows cannot cross a split boundary.
    gss = GroupShuffleSplit(n_splits=1, test_size=config.splits.test_size,
                            random_state=config.splits.random_state)
    trainval_idx, test_idx = next(gss.split(frame, frame[config.training.y_col], groups=frame["sound_id"]))
    trainval = frame.iloc[trainval_idx].copy()
    test = frame.iloc[test_idx].copy()
    sgkf = StratifiedGroupKFold(n_splits=config.splits.n_splits, shuffle=True,
                                random_state=config.splits.random_state)
    train_idx, val_idx = next(sgkf.split(trainval, trainval[config.training.y_col], trainval["sound_id"]))
    train = trainval.iloc[train_idx].copy()
    val = trainval.iloc[val_idx].copy()
    for name, split in (("train_split.csv", train), ("val_split.csv", val), ("test_split.csv", test)):
        split.drop(columns=["sound_path"], errors="ignore").to_csv(
            Path(config.paths.output_root).expanduser() / name, index=False
        )
    print(f"Saved splits: train={len(train)}, val={len(val)}, test={len(test)}")


def load_windows(config) -> Optional[list[dict]]:
    path = _window_path(config)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare dataset for bioacoustic training")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config file")
    parser.add_argument("--steps", type=str, nargs="+", default=list(STEPS), choices=STEPS,
                        help="Steps to run (default: stats windows spectrograms splits)")
    parser.add_argument("--validate-only", action="store_true",
                        help="Validate YAML and paths without reading audio or writing outputs")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    config = _load_config(args.config)
    _require_valid(config, check_files=not args.validate_only)
    print(f"Domain: {config.name or '<unnamed>'}")
    print(f"Window hop: {config.audio.hop_size_sec:g}s")
    if args.validate_only:
        print("Configuration is valid; no files were read or written.")
        return 0

    windows: Optional[list[dict]] = None
    if "stats" in args.steps:
        run_stats(config)
    if "windows" in args.steps:
        windows = run_windows(config)
    elif any(step in args.steps for step in ("spectrograms", "splits")):
        windows = load_windows(config)
        if windows is None:
            raise FileNotFoundError("windows file not found; run the windows step first")
    if "spectrograms" in args.steps:
        assert windows is not None
        run_spectrograms(config, windows)
    if "splits" in args.steps:
        assert windows is not None
        run_splits(config, windows)
    print("Dataset preparation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
