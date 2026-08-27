#!/usr/bin/env python3
"""Validate a Coqui TTS config and dataset paths without starting training."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SUPPORTED_PYTHON = ((3, 9), (3, 12))


def _as_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        try:
            return obj.to_dict()
        except Exception:
            pass
    result = {}
    for key in (
        "formatter",
        "dataset_name",
        "path",
        "meta_file_train",
        "ignored_speakers",
        "language",
        "phonemizer",
        "meta_file_val",
        "meta_file_attn_mask",
    ):
        if hasattr(obj, key):
            result[key] = getattr(obj, key)
    if not result and hasattr(obj, "__dict__"):
        result.update(vars(obj))
    return result


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    try:
        return obj[key]
    except Exception:
        return getattr(obj, key, default)


def _rel_join(root: Path, maybe_path: str | None) -> Path | None:
    if not maybe_path:
        return None
    path = Path(os.path.expanduser(str(maybe_path)))
    if not path.is_absolute():
        path = root / path
    return path


def _sample_lines(path: Path, limit: int) -> List[str]:
    lines: List[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for idx, line in enumerate(handle):
            if idx >= limit:
                break
            lines.append(line.rstrip("\n"))
    return lines


def _check_ljspeech(root: Path, meta: Path, limit: int) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    wavs_dir = root / "wavs"
    if not wavs_dir.is_dir():
        errors.append(f"ljspeech formatter expects a wavs/ directory under dataset path: {wavs_dir}")
    if meta.is_file():
        for line_no, line in enumerate(_sample_lines(meta, limit), start=1):
            if not line.strip():
                warnings.append(f"metadata line {line_no} is blank")
                continue
            cols = line.split("|")
            if len(cols) < 3:
                errors.append(f"metadata line {line_no} has {len(cols)} columns; ljspeech expects basename|raw|normalized")
                continue
            wav_path = wavs_dir / f"{cols[0]}.wav"
            if not wav_path.is_file():
                errors.append(f"metadata line {line_no} references missing wav: {wav_path}")
    return errors, warnings


def _check_common_voice(root: Path, meta: Path, limit: int) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    clips_dir = root / "clips"
    if not clips_dir.is_dir():
        errors.append(f"common_voice formatter expects a clips/ directory under dataset path: {clips_dir}")
    if meta.is_file():
        lines = _sample_lines(meta, max(limit + 1, 2))
        if not lines:
            errors.append("metadata file is empty")
            return errors, warnings
        header = lines[0].split("\t")
        if not header or header[0] != "client_id":
            warnings.append("common_voice metadata usually starts with a tab-separated client_id header")
        for line_no, line in enumerate(lines[1:] if header and header[0] == "client_id" else lines, start=2):
            if not line.strip():
                continue
            cols = line.split("\t")
            if len(cols) < 3:
                errors.append(f"metadata line {line_no} has {len(cols)} tab-separated columns; expected at least client_id, path, sentence")
                continue
            wav_name = cols[1].replace(".mp3", ".wav")
            wav_path = clips_dir / wav_name
            if not wav_path.is_file():
                errors.append(f"metadata line {line_no} references missing converted wav: {wav_path}")
    return errors, warnings


def _check_coqui(root: Path, meta: Path, limit: int) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if meta.is_file():
        lines = _sample_lines(meta, max(limit + 1, 2))
        if not lines:
            errors.append("metadata file is empty")
            return errors, warnings
        header = lines[0].split("|")
        if "audio_file" not in header or "text" not in header:
            errors.append("coqui formatter expects a pipe-separated header containing audio_file and text")
            return errors, warnings
        audio_idx = header.index("audio_file")
        for line_no, line in enumerate(lines[1:], start=2):
            if not line.strip():
                continue
            cols = line.split("|")
            if len(cols) <= audio_idx:
                errors.append(f"metadata line {line_no} is missing audio_file column")
                continue
            audio_path = root / cols[audio_idx]
            if not audio_path.is_file():
                errors.append(f"metadata line {line_no} references missing audio file: {audio_path}")
    return errors, warnings


def _dataset_checks(dataset: Any, idx: int, sample_preview: int) -> Tuple[List[str], List[str], Dict[str, Any]]:
    errors: List[str] = []
    warnings: List[str] = []
    info = _as_dict(dataset)

    formatter = str(info.get("formatter") or "").strip()
    dataset_name = str(info.get("dataset_name") or "").strip()
    root_raw = str(info.get("path") or "").strip()
    meta_train = str(info.get("meta_file_train") or "").strip()
    meta_val = str(info.get("meta_file_val") or "").strip()
    attn_mask = str(info.get("meta_file_attn_mask") or "").strip()

    label = f"dataset[{idx}]"
    if not formatter:
        errors.append(f"{label}: missing formatter")
    if not dataset_name:
        warnings.append(f"{label}: dataset_name is empty; audio_unique_name keys will be less stable")
    if not root_raw:
        errors.append(f"{label}: missing dataset path")
        return errors, warnings, info

    root = Path(os.path.expanduser(root_raw))
    if not root.exists():
        errors.append(f"{label}: dataset path does not exist: {root}")
        return errors, warnings, info
    if not root.is_dir():
        errors.append(f"{label}: dataset path is not a directory: {root}")
        return errors, warnings, info

    if not meta_train:
        errors.append(f"{label}: missing meta_file_train")
        meta_path = None
    else:
        meta_path = _rel_join(root, meta_train)
        if meta_path is None or not meta_path.is_file():
            errors.append(f"{label}: training metadata file does not exist: {meta_path}")

    if meta_val:
        meta_val_path = _rel_join(root, meta_val)
        if meta_val_path is None or not meta_val_path.is_file():
            errors.append(f"{label}: validation metadata file does not exist: {meta_val_path}")

    if attn_mask:
        attn_path = _rel_join(root, attn_mask)
        if attn_path is None or not attn_path.is_file():
            errors.append(f"{label}: attention-mask metadata file does not exist: {attn_path}")

    # Check whether built-in formatter exists when possible.
    if formatter:
        try:
            import TTS.tts.datasets.formatters as formatters

            if not hasattr(formatters, formatter.lower()):
                warnings.append(f"{label}: formatter '{formatter}' was not found among installed built-in formatters; use a custom formatter in Python training code")
        except Exception as exc:
            warnings.append(f"{label}: could not inspect built-in formatters: {exc}")

    if meta_path is not None and meta_path.is_file():
        fmt = formatter.lower()
        if fmt == "ljspeech":
            e, w = _check_ljspeech(root, meta_path, sample_preview)
            errors.extend(f"{label}: {msg}" for msg in e)
            warnings.extend(f"{label}: {msg}" for msg in w)
        elif fmt == "common_voice":
            e, w = _check_common_voice(root, meta_path, sample_preview)
            errors.extend(f"{label}: {msg}" for msg in e)
            warnings.extend(f"{label}: {msg}" for msg in w)
        elif fmt == "coqui":
            e, w = _check_coqui(root, meta_path, sample_preview)
            errors.extend(f"{label}: {msg}" for msg in e)
            warnings.extend(f"{label}: {msg}" for msg in w)
        else:
            warnings.append(f"{label}: generic validation checked existence only for formatter '{formatter}'")

    return errors, warnings, info


def _load_config(config_path: str) -> Any:
    try:
        from TTS.config import load_config
    except Exception as exc:  # pragma: no cover - environment-specific
        raise RuntimeError(f"Could not import TTS.config.load_config. Check that Coqui TTS is installed: {exc}") from exc
    return load_config(config_path)


def _load_samples(config: Any, eval_split: bool) -> Tuple[int, int | None]:
    from TTS.tts.datasets import load_tts_samples

    train, eval_items = load_tts_samples(
        _get(config, "datasets"),
        eval_split=eval_split,
        eval_split_max_size=_get(config, "eval_split_max_size"),
        eval_split_size=_get(config, "eval_split_size", 0.01),
    )
    return len(train), None if eval_items is None else len(eval_items)


def _python_warning() -> str | None:
    low, high = SUPPORTED_PYTHON
    version = sys.version_info[:2]
    if not (low <= version < high):
        return f"Python {sys.version.split()[0]} is outside Coqui TTS supported range >=3.9,<3.12"
    return None


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-path", required=True, help="Path to a Coqui TTS JSON/YAML config.")
    parser.add_argument("--load-samples", action="store_true", help="Call load_tts_samples() to count train/eval samples. This can scan metadata but never trains.")
    parser.add_argument("--no-eval-split", action="store_true", help="Use eval_split=False when --load-samples is set; useful for tiny datasets.")
    parser.add_argument("--sample-preview", type=int, default=5, help="Rows to inspect per metadata file for formatter-specific path checks.")
    parser.add_argument("--allow-warnings", action="store_true", help="Exit 0 when only warnings are present.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON report.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    errors: List[str] = []
    warnings: List[str] = []
    report: Dict[str, Any] = {"config_path": args.config_path, "errors": errors, "warnings": warnings, "datasets": []}

    py_warning = _python_warning()
    if py_warning:
        warnings.append(py_warning)

    config_file = Path(os.path.expanduser(args.config_path))
    if not config_file.is_file():
        errors.append(f"Config file does not exist: {config_file}")
        config = None
    else:
        try:
            config = _load_config(str(config_file))
            report["model"] = _get(config, "model")
            report["output_path"] = _get(config, "output_path")
        except Exception as exc:
            errors.append(f"Could not load/register config: {type(exc).__name__}: {exc}")
            config = None

    if config is not None:
        if hasattr(config, "check_values"):
            try:
                config.check_values()
            except Exception as exc:
                errors.append(f"config.check_values() failed: {type(exc).__name__}: {exc}")

        datasets = _get(config, "datasets")
        if not datasets:
            errors.append("Config has no datasets")
        else:
            if not isinstance(datasets, list):
                datasets = [datasets]
            for idx, dataset in enumerate(datasets):
                e, w, info = _dataset_checks(dataset, idx, max(args.sample_preview, 0))
                errors.extend(e)
                warnings.extend(w)
                report["datasets"].append(info)

        audio = _get(config, "audio")
        if audio:
            audio_info = _as_dict(audio)
            report["audio"] = audio_info
            stats_path = audio_info.get("stats_path")
            if stats_path and not Path(os.path.expanduser(str(stats_path))).exists():
                warnings.append(f"audio.stats_path is set but does not exist: {stats_path}")
            sample_rate = audio_info.get("sample_rate")
            if sample_rate and int(sample_rate) < 8000:
                warnings.append(f"audio.sample_rate={sample_rate} is unusually low for TTS")
        else:
            warnings.append("Config has no audio section; model defaults may apply")

        if args.load_samples and not errors:
            try:
                train_count, eval_count = _load_samples(config, eval_split=not args.no_eval_split)
                report["sample_counts"] = {"train": train_count, "eval": eval_count}
            except Exception as exc:
                errors.append(f"load_tts_samples() failed: {type(exc).__name__}: {exc}")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print("Coqui TTS config validation report")
        print(f"config: {args.config_path}")
        if report.get("model"):
            print(f"model: {report['model']}")
        if "sample_counts" in report:
            counts = report["sample_counts"]
            print(f"samples: train={counts['train']} eval={counts['eval']}")
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  - {warning}")
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"  - {error}")
        if not errors:
            print("\nOK: config loaded and no blocking validation errors were found. No training was started.")

    if errors:
        return 2
    if warnings and not args.allow_warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
