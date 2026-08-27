#!/usr/bin/env python3
"""Compute bounded Coqui TTS audio statistics for a wav directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute mel/linear mean-variance stats for a bounded wav directory using a Coqui TTS audio config."
    )
    parser.add_argument("config_path", help="Path to a Coqui JSON/YAML config containing an audio section.")
    parser.add_argument("out_path", help="Output .npy stats file path.")
    parser.add_argument("--wav-dir", required=True, help="Directory containing wav files to scan.")
    parser.add_argument("--file-ext", default="wav", help="Audio file extension to include. Default: wav")
    parser.add_argument("--max-files", type=int, default=128, help="Maximum files to process. Use 0 for all files.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite out_path if it already exists.")
    parser.add_argument("--skip-bad-files", action="store_true", help="Skip unreadable files instead of failing immediately.")
    parser.add_argument("--dry-run", action="store_true", help="List planned files and audio settings without computing stats.")
    return parser.parse_args()


def as_dict(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict):
        return dict(obj)
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return dict(vars(obj))
    return {}


def get_field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    try:
        if name in obj:
            return obj[name]
    except Exception:
        pass
    return getattr(obj, name, default)


def set_field(obj: Any, name: str, value: Any) -> None:
    try:
        obj[name] = value
        return
    except Exception:
        pass
    setattr(obj, name, value)


def collect_audio_files(wav_dir: Path, file_ext: str, max_files: int) -> List[Path]:
    ext = file_ext.lower().lstrip(".")
    files = sorted(p for p in wav_dir.rglob(f"*.{ext}") if p.is_file())
    if max_files > 0:
        return files[:max_files]
    return files


def make_stats_audio_config(audio_obj: Any, out_path: Path) -> Dict[str, Any]:
    audio_config = as_dict(audio_obj)
    audio_config["stats_path"] = str(out_path)
    audio_config["signal_norm"] = True
    # Match Coqui's stats file expectation: range-normalization-only fields are
    # redundant once mean-variance stats are active.
    for key in ("max_norm", "min_level_db", "symmetric_norm", "clip_norm"):
        audio_config.pop(key, None)
    return audio_config


def main() -> int:
    args = parse_args()
    config_path = Path(args.config_path).expanduser()
    out_path = Path(args.out_path).expanduser()
    wav_dir = Path(args.wav_dir).expanduser()

    if args.max_files < 0:
        print("error: --max-files must be >= 0", file=sys.stderr)
        return 2
    if not wav_dir.is_dir():
        print(f"error: --wav-dir is not a directory: {wav_dir}", file=sys.stderr)
        return 2
    if out_path.exists() and not args.overwrite and not args.dry_run:
        print(f"error: output exists; pass --overwrite to replace: {out_path}", file=sys.stderr)
        return 2

    files = collect_audio_files(wav_dir, args.file_ext, args.max_files)
    total_available = len(sorted(p for p in wav_dir.rglob(f"*.{args.file_ext.lower().lstrip('.')}") if p.is_file()))
    if not files:
        print(f"error: no .{args.file_ext.lstrip('.')} files found in {wav_dir}", file=sys.stderr)
        return 2

    try:
        from TTS.config import load_config
        from TTS.utils.audio import AudioProcessor
        import numpy as np
    except Exception as exc:
        print(f"error: failed to import installed Coqui TTS audio dependencies: {exc!r}", file=sys.stderr)
        return 1

    try:
        config = load_config(str(config_path))
    except Exception as exc:
        print(f"error: failed to load config: {exc!r}", file=sys.stderr)
        return 1

    audio_obj = get_field(config, "audio", config)
    set_field(audio_obj, "signal_norm", False)
    set_field(audio_obj, "stats_path", None)
    audio_dict = as_dict(audio_obj)

    print(f"config: {config_path}")
    print(f"wav_dir: {wav_dir}")
    print(f"files selected: {len(files)} of {total_available}")
    print(
        "audio: "
        f"sample_rate={audio_dict.get('sample_rate')} "
        f"num_mels={audio_dict.get('num_mels')} "
        f"hop_length={audio_dict.get('hop_length')} "
        f"fft_size={audio_dict.get('fft_size')}"
    )
    if args.dry_run:
        for path in files[:10]:
            print(f"  would process: {path}")
        if len(files) > 10:
            print(f"  ... {len(files) - 10} more")
        return 0

    try:
        ap = AudioProcessor(**audio_dict)
    except Exception as exc:
        print(f"error: failed to initialize AudioProcessor: {exc!r}", file=sys.stderr)
        return 1

    mel_sum = 0
    mel_square_sum = 0
    linear_sum = 0
    linear_square_sum = 0
    frame_count = 0
    processed = 0
    skipped: List[str] = []

    for path in files:
        try:
            wav = ap.load_wav(str(path))
            linear = ap.spectrogram(wav)
            mel = ap.melspectrogram(wav)
        except Exception as exc:
            if args.skip_bad_files:
                skipped.append(f"{path}: {exc!r}")
                continue
            print(f"error: failed to process {path}: {exc!r}", file=sys.stderr)
            return 1

        if mel.shape[1] == 0:
            message = f"{path}: mel spectrogram has zero frames"
            if args.skip_bad_files:
                skipped.append(message)
                continue
            print(f"error: {message}", file=sys.stderr)
            return 1

        frame_count += mel.shape[1]
        mel_sum += mel.sum(axis=1)
        linear_sum += linear.sum(axis=1)
        mel_square_sum += (mel**2).sum(axis=1)
        linear_square_sum += (linear**2).sum(axis=1)
        processed += 1

    if processed == 0 or frame_count == 0:
        print("error: no files were successfully processed", file=sys.stderr)
        return 1

    mel_mean = mel_sum / frame_count
    mel_std = np.sqrt(mel_square_sum / frame_count - mel_mean**2)
    linear_mean = linear_sum / frame_count
    linear_std = np.sqrt(linear_square_sum / frame_count - linear_mean**2)

    stats = {
        "mel_mean": mel_mean,
        "mel_std": mel_std,
        "linear_mean": linear_mean,
        "linear_std": linear_std,
        "audio_config": make_stats_audio_config(audio_obj, out_path),
        "metadata": {
            "processed_files": processed,
            "selected_files": len(files),
            "total_available_files": total_available,
            "skipped_files": skipped,
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_path, stats, allow_pickle=True)
    print(f"processed files: {processed}")
    print(f"frames: {frame_count}")
    print(f"avg mel mean: {float(mel_mean.mean())}")
    print(f"avg mel std: {float(mel_std.mean())}")
    print(f"avg linear mean: {float(linear_mean.mean())}")
    print(f"avg linear std: {float(linear_std.mean())}")
    if skipped:
        print("skipped files:")
        for item in skipped:
            print(f"  - {item}")
    print(f"stats saved: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
