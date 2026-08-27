#!/usr/bin/env python3
"""Validate a Coqui TTS vocoder config without training.

The script loads a config with the installed TTS package, checks audio/data
fields, optionally compares a TTS config for mel compatibility, and optionally
instantiates the vocoder model. It never starts Trainer.fit().
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


MEL_COMPAT_FIELDS = (
    "sample_rate",
    "num_mels",
    "hop_length",
    "win_length",
    "fft_size",
    "mel_fmin",
    "mel_fmax",
    "do_amp_to_db_mel",
    "signal_norm",
)

KNOWN_VOCODER_MODELS = {
    "gan",
    "hifigan",
    "melgan",
    "multiband_melgan",
    "fullband_melgan",
    "parallel_wavegan",
    "univnet",
    "wavegrad",
    "wavernn",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a Coqui TTS vocoder config, data paths, audio fields, and optional TTS mel pairing without training."
    )
    parser.add_argument("config_path", help="Path to a vocoder JSON/YAML config.")
    parser.add_argument("--data-path", help="Override config.data_path for validation only.")
    parser.add_argument("--feature-path", help="Override config.feature_path for validation only.")
    parser.add_argument("--tts-config", help="Optional TTS config to compare audio/mel fields against.")
    parser.add_argument("--require-data", action="store_true", help="Fail if data_path is empty or has no wav files.")
    parser.add_argument("--check-stats", action="store_true", help="Load and validate audio.stats_path when present.")
    parser.add_argument(
        "--instantiate-model",
        action="store_true",
        help="Instantiate TTS.vocoder.models.setup_model(config) without training. May allocate a torch model.",
    )
    parser.add_argument("--max-feature-files", type=int, default=20, help="Maximum feature .npy files to inspect for shape checks.")
    parser.add_argument("--json", action="store_true", help="Print a JSON report instead of human-readable text.")
    return parser.parse_args()


def as_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return dict(obj)
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return dict(vars(obj))
    return {}


def get_field(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    try:
        if name in obj:  # Coqpit implements membership for config keys.
            return obj[name]
    except Exception:
        pass
    return getattr(obj, name, default)


def resolve_existing_path(raw: Any, config_dir: Path) -> Path | None:
    if raw in (None, ""):
        return None
    path = Path(str(raw)).expanduser()
    if path.exists():
        return path
    candidate = config_dir / path
    if candidate.exists():
        return candidate
    return path


def add(report: Dict[str, Any], level: str, message: str, **details: Any) -> None:
    report[level].append({"message": message, **details})


def count_wavs(data_path: Path) -> Tuple[int, List[str]]:
    wavs = sorted(data_path.rglob("*.wav")) if data_path.exists() else []
    return len(wavs), [str(p) for p in wavs[:5]]


def validate_audio(audio: Dict[str, Any], report: Dict[str, Any]) -> None:
    required_positive_ints = ("sample_rate", "num_mels", "hop_length", "win_length", "fft_size")
    for field in required_positive_ints:
        value = audio.get(field)
        if not isinstance(value, int) or value <= 0:
            add(report, "errors", f"audio.{field} must be a positive integer", value=value)

    sample_rate = audio.get("sample_rate")
    mel_fmax = audio.get("mel_fmax")
    if isinstance(sample_rate, int):
        if not 512 <= sample_rate <= 100000:
            add(report, "errors", "audio.sample_rate is outside the package validation range", value=sample_rate)
        if mel_fmax is not None and isinstance(mel_fmax, (int, float)) and mel_fmax > sample_rate / 2:
            add(report, "errors", "audio.mel_fmax exceeds Nyquist frequency", mel_fmax=mel_fmax, nyquist=sample_rate / 2)

    win_length = audio.get("win_length")
    fft_size = audio.get("fft_size")
    if isinstance(win_length, int) and isinstance(fft_size, int) and win_length > fft_size:
        add(report, "errors", "audio.win_length must not be larger than audio.fft_size", win_length=win_length, fft_size=fft_size)

    min_level_db = audio.get("min_level_db")
    if min_level_db == 0 or min_level_db == 0.0:
        add(report, "errors", "audio.min_level_db must not be 0 because AudioProcessor asserts on that value")

    hop_length = audio.get("hop_length")
    upsample = report.get("generator_upsample_product")
    if isinstance(hop_length, int) and isinstance(upsample, int) and hop_length != upsample:
        add(
            report,
            "warnings",
            "generator upsampling product does not match audio.hop_length",
            hop_length=hop_length,
            upsample_product=upsample,
        )


def validate_data_paths(config: Any, args: argparse.Namespace, config_dir: Path, report: Dict[str, Any]) -> None:
    raw_data_path = args.data_path if args.data_path is not None else get_field(config, "data_path", "")
    raw_feature_path = args.feature_path if args.feature_path is not None else get_field(config, "feature_path", None)
    data_path = resolve_existing_path(raw_data_path, config_dir)
    feature_path = resolve_existing_path(raw_feature_path, config_dir)

    report["data_path"] = str(raw_data_path) if raw_data_path not in (None, "") else ""
    report["feature_path"] = str(raw_feature_path) if raw_feature_path not in (None, "") else ""

    if data_path is None:
        if args.require_data:
            add(report, "errors", "config.data_path is empty and --require-data was set")
        else:
            add(report, "warnings", "config.data_path is empty; valid for structure checks but not for training")
    elif not data_path.exists():
        level = "errors" if args.require_data else "warnings"
        add(report, level, "data_path does not exist", path=str(data_path))
    elif not data_path.is_dir():
        add(report, "errors", "data_path must be a directory", path=str(data_path))
    else:
        wav_count, examples = count_wavs(data_path)
        report["wav_count"] = wav_count
        report["wav_examples"] = examples
        if wav_count == 0:
            level = "errors" if args.require_data else "warnings"
            add(report, level, "data_path contains no .wav files", path=str(data_path))

    if feature_path is not None:
        if not feature_path.exists():
            add(report, "errors", "feature_path does not exist", path=str(feature_path))
        elif not feature_path.is_dir():
            add(report, "errors", "feature_path must be a directory", path=str(feature_path))
        else:
            features = sorted(feature_path.rglob("*.npy"))
            report["feature_count"] = len(features)
            if not features:
                add(report, "errors", "feature_path contains no .npy files", path=str(feature_path))
            inspect_feature_shapes(features[: max(0, args.max_feature_files)], report)


def inspect_feature_shapes(features: Iterable[Path], report: Dict[str, Any]) -> None:
    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover - environment dependent
        add(report, "warnings", "numpy import failed; feature shape checks skipped", error=repr(exc))
        return

    audio = report.get("audio", {})
    expected_mels = audio.get("num_mels")
    checked = []
    for path in features:
        try:
            arr = np.load(path, allow_pickle=False)
            shape = tuple(int(x) for x in arr.shape)
            checked.append({"path": str(path), "shape": shape})
            if expected_mels and shape and shape[0] != expected_mels:
                add(report, "errors", "feature first dimension does not match audio.num_mels", path=str(path), shape=shape, num_mels=expected_mels)
        except Exception as exc:
            add(report, "errors", "failed to load feature .npy file", path=str(path), error=repr(exc))
    report["feature_shapes_checked"] = checked


def validate_stats(audio: Dict[str, Any], config_dir: Path, report: Dict[str, Any]) -> None:
    stats_raw = audio.get("stats_path")
    if not stats_raw:
        return
    stats_path = resolve_existing_path(stats_raw, config_dir)
    if stats_path is None or not stats_path.exists():
        add(report, "errors", "audio.stats_path does not exist", path=str(stats_path or stats_raw))
        return
    try:
        import numpy as np

        stats = np.load(stats_path, allow_pickle=True).item()
    except Exception as exc:
        add(report, "errors", "failed to load stats_path as a Coqui stats .npy dictionary", path=str(stats_path), error=repr(exc))
        return

    required = ("mel_mean", "mel_std", "linear_mean", "linear_std", "audio_config")
    missing = [key for key in required if key not in stats]
    if missing:
        add(report, "errors", "stats file is missing required keys", path=str(stats_path), missing=missing)
        return

    expected_mels = audio.get("num_mels")
    mel_len = len(stats["mel_mean"])
    if expected_mels and mel_len != expected_mels:
        add(report, "errors", "stats mel dimension does not match audio.num_mels", stats_mel_len=mel_len, num_mels=expected_mels)

    stats_audio = as_dict(stats.get("audio_config"))
    mismatches = {}
    for key in ("num_mels", "hop_length", "win_length", "fft_size", "mel_fmin", "mel_fmax", "do_amp_to_db_mel"):
        if key in stats_audio and key in audio and stats_audio[key] != audio[key]:
            mismatches[key] = {"stats": stats_audio[key], "config": audio[key]}
    if mismatches:
        add(report, "errors", "stats audio_config differs from current audio config", mismatches=mismatches)


def compare_tts_config(tts_config_path: str, vocoder_audio: Dict[str, Any], load_config: Any, report: Dict[str, Any]) -> None:
    try:
        tts_config = load_config(tts_config_path)
    except Exception as exc:
        add(report, "errors", "failed to load --tts-config", path=tts_config_path, error=repr(exc))
        return
    tts_audio = as_dict(get_field(tts_config, "audio", {}))
    report["tts_audio"] = {k: tts_audio.get(k) for k in MEL_COMPAT_FIELDS if k in tts_audio}
    mismatches = {}
    for field in MEL_COMPAT_FIELDS:
        if field in vocoder_audio and field in tts_audio:
            left = vocoder_audio[field]
            right = tts_audio[field]
            if left != right:
                if isinstance(left, float) and isinstance(right, float) and math.isclose(left, right):
                    continue
                mismatches[field] = {"vocoder": left, "tts": right}
    if mismatches:
        add(report, "errors", "TTS and vocoder audio/mel fields differ", mismatches=mismatches)


def maybe_instantiate_model(config: Any, report: Dict[str, Any]) -> None:
    try:
        from TTS.vocoder.models import setup_model

        model = setup_model(config)
        report["model_class"] = model.__class__.__name__
        add(report, "warnings", "model was instantiated for validation only; no training or checkpoint load was run")
    except Exception as exc:
        add(report, "errors", "failed to instantiate vocoder model with setup_model(config)", error=repr(exc))


def infer_upsample_product(config: Any) -> int | None:
    params = get_field(config, "generator_model_params", {})
    if not isinstance(params, dict):
        params = as_dict(params)
    factors = params.get("upsample_factors")
    if not factors:
        return None
    product = 1
    try:
        for value in factors:
            product *= int(value)
        return product
    except Exception:
        return None


def main() -> int:
    args = parse_args()
    report: Dict[str, Any] = {
        "ok": False,
        "config_path": args.config_path,
        "warnings": [],
        "errors": [],
    }

    try:
        from TTS.config import load_config
    except Exception as exc:
        add(report, "errors", "failed to import TTS.config.load_config from the installed package", error=repr(exc))
        return finish(report, args.json)

    config_path = Path(args.config_path).expanduser()
    config_dir = config_path.parent if config_path.parent != Path("") else Path.cwd()
    try:
        config = load_config(str(config_path))
    except Exception as exc:
        add(report, "errors", "failed to load vocoder config", error=repr(exc))
        return finish(report, args.json)

    model_name = str(get_field(config, "model", ""))
    report["model"] = model_name
    if model_name.lower() not in KNOWN_VOCODER_MODELS:
        add(report, "warnings", "vocoder model name is not one of the distilled common vocoder models", model=model_name)

    report["generator_model"] = get_field(config, "generator_model", None)
    report["discriminator_model"] = get_field(config, "discriminator_model", None)
    upsample = infer_upsample_product(config)
    if upsample:
        report["generator_upsample_product"] = upsample

    audio = as_dict(get_field(config, "audio", {}))
    report["audio"] = {k: audio.get(k) for k in sorted(audio.keys()) if k in set(MEL_COMPAT_FIELDS) | {"min_level_db", "stats_path", "trim_db", "resample"}}
    validate_audio(audio, report)
    validate_data_paths(config, args, config_dir, report)
    if args.check_stats or audio.get("stats_path"):
        validate_stats(audio, config_dir, report)
    if args.tts_config:
        compare_tts_config(args.tts_config, audio, load_config, report)
    if args.instantiate_model:
        maybe_instantiate_model(config, report)

    return finish(report, args.json)


def finish(report: Dict[str, Any], as_json: bool) -> int:
    report["ok"] = not report["errors"]
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "OK" if report["ok"] else "FAILED"
        print(f"vocoder config validation: {status}")
        for key in ("model", "generator_model", "discriminator_model", "generator_upsample_product", "wav_count", "feature_count"):
            if key in report and report[key] not in (None, ""):
                print(f"  {key}: {report[key]}")
        if report.get("errors"):
            print("errors:")
            for item in report["errors"]:
                print(f"  - {item['message']}")
                for k, v in item.items():
                    if k != "message":
                        print(f"      {k}: {v}")
        if report.get("warnings"):
            print("warnings:")
            for item in report["warnings"]:
                print(f"  - {item['message']}")
                for k, v in item.items():
                    if k != "message":
                        print(f"      {k}: {v}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
