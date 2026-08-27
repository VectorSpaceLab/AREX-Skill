#!/usr/bin/env python3
"""Installed-package-facing bioacoustics inference helper.

The CLI mirrors the public companion inference arguments while adding
``--dry-run`` and ``--output_dir``. Full inference reads a user-supplied
checkpoint and audio/cache; it never downloads data intentionally, but model
construction can require cached torchvision backbone weights.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Optional

import numpy as np


def _load_config(path: str):
    from PytorchWildlife.data.bioacoustics.bioacoustics_configs import load_config

    return load_config(path)


def validate_inference_args(args) -> list[str]:
    errors: list[str] = []
    if args.num_classes < 2:
        errors.append("--num_classes must be 2 or greater")
    if args.window_size_sec <= 0:
        errors.append("--window_size_sec must be > 0")
    if args.overlap_sec < 0 or args.overlap_sec >= args.window_size_sec:
        errors.append("--overlap_sec must satisfy 0 <= overlap_sec < window_size_sec")
    if args.sample_rate <= 0:
        errors.append("--sample_rate must be > 0")
    if args.n_fft <= 0 or args.hop_length <= 0 or args.n_mels <= 0:
        errors.append("--n_fft, --hop_length, and --n_mels must be > 0")
    if args.temperature <= 0:
        errors.append("--temperature must be > 0")
    if args.batch_size <= 0 or args.num_workers < 0:
        errors.append("--batch_size must be > 0 and --num_workers must be >= 0")
    if args.class_names is not None and len(args.class_names) != args.num_classes:
        errors.append("--class_names must contain exactly --num_classes names")
    if not args.dataset:
        errors.append("--dataset is required for an output directory")
    if not args.dry_run and not args.audios_source:
        errors.append("--audios_source is required unless --dry-run is used")
    if not args.dry_run and not args.checkpoint:
        errors.append("--checkpoint is required unless --dry-run is used")
    return errors


def _parse_audio_times(path: str, sample_rate: int) -> tuple[str, float, float]:
    """Recover audio id and seconds from common cache names."""
    name = Path(path).stem
    match = re.search(r"sid(\d+).*?start(\d+).*?end(\d+)", name)
    if match:
        return (f"sound_{match.group(1)}",
                int(match.group(2)) / sample_rate,
                int(match.group(3)) / sample_rate)
    numbers = re.search(r"(?:^|_)(\d+)_(\d+)$", name)
    if numbers:
        return (name[:numbers.start()].rstrip("_"),
                int(numbers.group(1)) / sample_rate,
                int(numbers.group(2)) / sample_rate)
    return name, 0.0, 0.0


def run_inference_batch(
    model,
    dataloader,
    sample_rate: int,
    num_classes: int = 2,
    annotations_json: Optional[str] = None,
    device: str = "cuda",
    temperature: float = 1.0,
) -> dict[str, Any]:
    """Run a checkpoint on `(tensor, path)` batches and return NumPy results.

    The optional annotation file maps ``sid<N>`` cache names back to the
    original ``sounds[].file_name_path`` value, matching the companion API.
    """
    import torch
    import torch.nn.functional as F

    audio_by_id: dict[int, str] = {}
    if annotations_json is not None:
        data = json.loads(Path(annotations_json).read_text(encoding="utf-8"))
        audio_by_id = {
            int(sound["id"]): str(sound["file_name_path"])
            for sound in data.get("sounds", [])
            if "id" in sound and "file_name_path" in sound
        }

    model.eval()
    paths: list[str] = []
    logits_batches: list[np.ndarray] = []
    with torch.no_grad():
        for x, batch_paths in dataloader:
            x = x.to(device)
            logits = model(x)
            if num_classes == 2:
                logits = logits.squeeze(1)
            logits_batches.append(logits.detach().cpu().numpy())
            paths.extend(str(path) for path in batch_paths)
    if not logits_batches:
        raise ValueError("inference dataset is empty")

    logits_np = np.concatenate(logits_batches)
    if num_classes == 2:
        probabilities = 1.0 / (1.0 + np.exp(-(logits_np / temperature)))
        predictions = (probabilities > 0.5).astype(int)
    else:
        probabilities = F.softmax(torch.from_numpy(logits_np) / temperature, dim=1).numpy()
        predictions = probabilities.argmax(axis=1)

    audios: list[str] = []
    starts: list[float] = []
    ends: list[float] = []
    for path in paths:
        audio, start, end = _parse_audio_times(path, sample_rate)
        sid = re.search(r"sid(\\d+)", Path(path).stem)
        if sid and int(sid.group(1)) in audio_by_id:
            audio = audio_by_id[int(sid.group(1))]
        audios.append(audio)
        starts.append(start)
        ends.append(end)
    return {
        "paths": paths,
        "audios": audios,
        "starts": starts,
        "ends": ends,
        "predictions": predictions,
        "probabilities": probabilities,
    }


def save_inference_results(results: dict[str, Any], output_path: str, num_classes: int,
                           class_names: Optional[list[str]] = None):
    """Write the companion binary or multiclass CSV schema."""
    import pandas as pd

    if num_classes == 2:
        frame = pd.DataFrame({
            "audio": results["audios"],
            "start(s)": results["starts"],
            "end(s)": results["ends"],
            "prediction": results["predictions"],
            "probability": results["probabilities"],
            "confidence": np.abs(results["probabilities"] - 0.5) * 2,
        }).sort_values("confidence", ascending=False)
    else:
        names = class_names or [f"class_{i}" for i in range(num_classes)]
        data: dict[str, Any] = {
            "file_path": results["paths"],
            "audio": results["audios"],
            "start(s)": results["starts"],
            "end(s)": results["ends"],
            "prediction": results["predictions"],
        }
        for index, name in enumerate(names):
            data[name.replace(" ", "_") + "_prob"] = results["probabilities"][:, index]
        frame = pd.DataFrame(data)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    print(f"Results saved to: {output_path}")
    return frame


def process_inference_results_per_second(csv_path: str):
    """Aggregate binary window results by overlap-weighted recording second."""
    import pandas as pd

    frame = pd.read_csv(csv_path)
    required = {"audio", "start(s)", "end(s)", "prediction", "probability", "confidence"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError("per-second aggregation is binary-only; missing " + ", ".join(sorted(missing)))
    rows: list[dict[str, Any]] = []
    for audio, audio_frame in frame.groupby("audio", sort=False):
        for second in range(int(math.floor(audio_frame["start(s)"].min())),
                           int(math.ceil(audio_frame["end(s)"].max()))):
            overlap = audio_frame[
                (audio_frame["start(s)"] < second + 1) &
                (audio_frame["end(s)"] > second)
            ].copy()
            if overlap.empty:
                continue
            weights = np.maximum(
                0.0,
                np.minimum(overlap["end(s)"].to_numpy(), second + 1) -
                np.maximum(overlap["start(s)"].to_numpy(), second),
            )
            if weights.sum() <= 0:
                continue
            weights = weights / weights.sum()
            avg_prediction = float(np.average(overlap["prediction"], weights=weights))
            rows.append({
                "audio": audio,
                "second": second,
                "count_overlaps": len(overlap),
                "prediction": int(avg_prediction >= 0.5),
                "avg_prediction": avg_prediction,
                "avg_probability": float(np.average(overlap["probability"], weights=weights)),
                "avg_confidence": float(np.average(overlap["confidence"], weights=weights)),
            })
    result = pd.DataFrame(rows, columns=[
        "audio", "second", "count_overlaps", "prediction", "avg_prediction",
        "avg_probability", "avg_confidence",
    ]).sort_values(["audio", "second"]).reset_index(drop=True)
    output = Path(csv_path).with_name("per_second_results.csv")
    result.to_csv(output, index=False)
    print(f"Per-second results saved to: {output}")
    return result


def _windows_dataframe(args, output_dir: Path):
    import pandas as pd
    from PytorchWildlife.data.bioacoustics.bioacoustics_windows import build_inference_windows

    source = str(args.audios_source)
    if source.lower().endswith(".json"):
        windows = json.loads(Path(source).read_text(encoding="utf-8"))
    elif source.lower().endswith(".csv"):
        windows = pd.read_csv(source).to_dict("records")
    else:
        windows = build_inference_windows(source, args.window_size_sec, args.overlap_sec, args.sample_rate)
    frame = pd.DataFrame(windows)
    if frame.empty:
        raise ValueError("no complete audio windows were produced")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{args.dataset}_windows.json").write_text(
        json.dumps(windows, indent=2), encoding="utf-8"
    )
    return frame, windows


def _prepare_spectrogram_column(frame, windows, args, spectrogram_dir: Path):
    from PytorchWildlife.data.bioacoustics.bioacoustics_spectrograms import default_spectrogram_path

    if "file_path" in frame.columns:
        return "file_path"
    if "spec_name" in frame.columns:
        return "spec_name"
    if "sound_path" not in frame.columns:
        raise ValueError("windows input needs spec_name, file_path, or sound_path")
    names = []
    for window in windows:
        names.append(Path(default_spectrogram_path(window, str(spectrogram_dir))).name)
    frame["spec_name"] = [str(spectrogram_dir / name) for name in names]
    return "spec_name"


def _compute_missing_spectrograms(frame, windows, args, spectrogram_dir: Path) -> None:
    from PytorchWildlife.data.bioacoustics.bioacoustics_spectrograms import compute_mel_spectrograms_gpu

    if "sound_path" not in frame.columns:
        return
    spectrogram_dir.mkdir(parents=True, exist_ok=True)
    compute_mel_spectrograms_gpu(
        windows=windows,
        sample_rate=args.sample_rate,
        n_fft=args.n_fft,
        hop_length=args.hop_length,
        n_mels=args.n_mels,
        top_db=args.top_db,
        spectrograms_path=str(spectrogram_dir),
        save_npy=True,
    )


def run_pipeline(args, cfg=None) -> Path:
    import torch
    from torch.utils.data import DataLoader
    from PytorchWildlife.data.bioacoustics.bioacoustics_datasets import BioacousticsInferenceDataset
    from PytorchWildlife.models.bioacoustics.resnet_classifier import load_model_from_checkpoint

    output_dir = Path(args.output_dir).expanduser() if args.output_dir else Path("inference") / args.dataset
    frame, windows = _windows_dataframe(args, output_dir)
    spectrogram_dir = Path(args.spectrograms_path).expanduser() if args.spectrograms_path else output_dir / "spectrograms"
    x_col = _prepare_spectrogram_column(frame, windows, args, spectrogram_dir)
    _compute_missing_spectrograms(frame, windows, args, spectrogram_dir)
    if x_col == "spec_name":
        frame[x_col] = frame[x_col].map(lambda value: str(value) if Path(str(value)).is_absolute()
                                        else str(spectrogram_dir / str(value)))
    missing = [str(path) for path in frame[x_col] if not Path(str(path)).is_file()]
    if missing:
        raise FileNotFoundError(f"{len(missing)} spectrogram files are missing; first: {missing[0]}")

    n_frames = int(np.ceil((args.window_size_sec * args.sample_rate - args.n_fft) / args.hop_length)) + 1
    dataset = BioacousticsInferenceDataset(
        dataframe=frame, x_col=x_col,
        target_size=[args.n_mels, n_frames], normalize=args.normalize,
    )
    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA is not available; using CPU.")
        args.device = "cpu"
    loader = DataLoader(
        dataset, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers,
        pin_memory=args.device == "cuda",
    )
    model = load_model_from_checkpoint(args.checkpoint, args.device)
    results = run_inference_batch(
        model=model,
        dataloader=loader,
        sample_rate=args.sample_rate,
        num_classes=args.num_classes,
        annotations_json=args.annotations_json,
        device=args.device,
        temperature=args.temperature,
    )
    suffix = "binary" if args.num_classes == 2 else "multiclass"
    result_path = output_dir / f"{suffix}_inference_results.csv"
    save_inference_results(results, str(result_path), args.num_classes, args.class_names)
    if args.per_second:
        if args.num_classes != 2:
            raise ValueError("--per-second is only defined for binary output")
        process_inference_results_per_second(str(result_path))
    return result_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run inference on bioacoustic sounds")
    parser.add_argument("--config", type=str, default=None, help="Path to YAML config file")
    parser.add_argument("--audios_source", type=str, default=None,
                        help="Audio folder, JSON windows, or CSV windows")
    parser.add_argument("--num_classes", type=int, default=2, help="2=binary, >2=multiclass")
    parser.add_argument("--class_names", type=str, nargs="+", default=None)
    parser.add_argument("--window_size_sec", type=float, default=5.0)
    parser.add_argument("--overlap_sec", type=float, default=4.0)
    parser.add_argument("--sample_rate", type=int, default=48000)
    parser.add_argument("--n_fft", type=int, default=2048)
    parser.add_argument("--hop_length", type=int, default=512)
    parser.add_argument("--n_mels", type=int, default=224)
    parser.add_argument("--top_db", type=float, default=80.0)
    parser.add_argument("--checkpoint", type=str, default=None)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--num_workers", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--dataset", type=str, default=None)
    parser.add_argument("--normalize", action="store_true")
    parser.add_argument("--spectrograms_path", type=str, default=None)
    parser.add_argument("--annotations_json", type=str, default=None,
                        help="Retained for companion compatibility; IDs must be encoded in paths")
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--per-second", action="store_true",
                        help="Also write weighted binary per-second results")
    parser.add_argument("--dry-run", action="store_true",
                        help="Resolve config and validate flags without audio/model/output work")
    return parser


def _apply_config(args, cfg) -> None:
    if args.num_classes == 2 and cfg.training.num_classes != 2:
        args.num_classes = cfg.training.num_classes
    if args.class_names is None and cfg.class_names:
        args.class_names = [str(value) for value in cfg.class_names.values()]
    if args.window_size_sec == 5.0:
        args.window_size_sec = cfg.audio.window_size_sec
    if args.overlap_sec == 4.0:
        args.overlap_sec = cfg.audio.overlap_sec
    if args.sample_rate == 48000:
        args.sample_rate = cfg.audio.sample_rate
    if args.n_fft == 2048:
        args.n_fft = cfg.spectrogram.n_fft
    if args.hop_length == 512:
        args.hop_length = cfg.spectrogram.hop_length
    if args.n_mels == 224:
        args.n_mels = cfg.spectrogram.n_mels
    if args.top_db == 80.0:
        args.top_db = cfg.spectrogram.top_db
    if args.dataset is None:
        args.dataset = cfg.name


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = _load_config(args.config) if args.config else None
    if cfg is not None:
        _apply_config(args, cfg)
    errors = validate_inference_args(args)
    if errors:
        raise ValueError("Invalid inference arguments:\n- " + "\n- ".join(errors))
    if args.dry_run:
        print(f"Valid {('binary' if args.num_classes == 2 else 'multiclass')} inference configuration")
        print(f"Window hop: {args.window_size_sec - args.overlap_sec:g}s; device request: {args.device}")
        print("Dry run complete; no audio, checkpoint, or output was touched.")
        return 0
    run_pipeline(args, cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
