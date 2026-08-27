#!/usr/bin/env python3
"""Inspect a StyleTTS2 YAML config and report the fields that matter most."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import yaml


STAGES = {"first", "second", "finetune", "inference"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect StyleTTS2 configuration files safely.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("Configs/config.yml"),
        help="Config YAML to inspect (default: Configs/config.yml).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional checkout root used to resolve relative config fields.",
    )
    parser.add_argument(
        "--stage",
        choices=sorted(STAGES),
        default=None,
        help="Optional stage hint: first, second, finetune, or inference.",
    )
    return parser


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("config root must be a mapping")
    return data


def get_in(mapping: Dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = mapping
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def as_path(value: Any, repo_root: Optional[Path]) -> Optional[Path]:
    if value in (None, ""):
        return None
    path = Path(str(value))
    if path.is_absolute():
        return path
    if repo_root is None:
        return path
    return (repo_root / path).resolve()


def emit_path(label: str, value: Any, repo_root: Optional[Path]) -> None:
    resolved = as_path(value, repo_root)
    print(f"{label}: {value!r}")
    if resolved is not None and str(resolved) != str(value):
        print(f"  resolved: {resolved}")


def emit_section(title: str) -> None:
    print(f"\n[{title}]")


def emit_warning(message: str) -> None:
    print(f"WARNING: {message}")


def inspect_config(config: Dict[str, Any], repo_root: Optional[Path], stage: Optional[str]) -> int:
    warnings = 0

    emit_section("General")
    print(f"log_dir: {config.get('log_dir')!r}")
    print(f"device: {config.get('device')!r}")
    print(f"batch_size: {config.get('batch_size')!r}")
    print(f"max_len: {config.get('max_len')!r}")
    print(f"save_freq: {config.get('save_freq')!r}")
    print(f"log_interval: {config.get('log_interval')!r}")

    emit_section("Paths and checkpoints")
    first_stage_value = config.get("first_stage_path")
    print(f"first_stage_path: {first_stage_value!r}")
    log_dir_path = as_path(config.get("log_dir"), repo_root)
    if first_stage_value not in (None, "") and log_dir_path is not None:
        first_stage_path = Path(str(first_stage_value)).expanduser()
        resolved_first_stage = first_stage_path if first_stage_path.is_absolute() else log_dir_path / first_stage_path
        print(f"  stage-2 fallback under log_dir: {resolved_first_stage}")
    emit_path("pretrained_model", config.get("pretrained_model"), repo_root)
    print(f"second_stage_load_pretrained: {config.get('second_stage_load_pretrained')!r}")
    print(f"load_only_params: {config.get('load_only_params')!r}")
    emit_path("F0_path", config.get("F0_path"), repo_root)
    emit_path("ASR_config", config.get("ASR_config"), repo_root)
    emit_path("ASR_path", config.get("ASR_path"), repo_root)
    emit_path("PLBERT_dir", config.get("PLBERT_dir"), repo_root)

    emit_section("Data and preprocessing")
    data_params = config.get("data_params", {}) or {}
    print(f"train_data: {data_params.get('train_data')!r}")
    print(f"val_data: {data_params.get('val_data')!r}")
    emit_path("root_path", data_params.get("root_path"), repo_root)
    print(f"OOD_data: {data_params.get('OOD_data')!r}")
    print(f"min_length: {data_params.get('min_length')!r}")
    preprocess_params = config.get("preprocess_params", {}) or {}
    print(f"preprocess sr: {preprocess_params.get('sr')!r}")
    print(f"spect params: {preprocess_params.get('spect_params')!r}")

    emit_section("Model and loss schedule")
    model_params = config.get("model_params", {}) or {}
    loss_params = config.get("loss_params", {}) or {}
    slmadv_params = config.get("slmadv_params", {}) or {}
    print(f"multispeaker: {model_params.get('multispeaker')!r}")
    decoder = model_params.get("decoder", {}) or {}
    print(f"decoder.type: {decoder.get('type')!r}")
    print(f"epochs_1st: {config.get('epochs_1st')!r}")
    print(f"epochs_2nd: {config.get('epochs_2nd')!r}")
    print(f"epochs: {config.get('epochs')!r}")
    print(f"TMA_epoch: {loss_params.get('TMA_epoch')!r}")
    print(f"diff_epoch: {loss_params.get('diff_epoch')!r}")
    print(f"joint_epoch: {loss_params.get('joint_epoch')!r}")
    print(f"optimizer_params: {config.get('optimizer_params')!r}")
    print(f"slmadv_params: {slmadv_params!r}")

    if decoder.get("type") not in {"istftnet", "hifigan"}:
        emit_warning(f"decoder.type should be 'istftnet' or 'hifigan', got {decoder.get('type')!r}")
        warnings += 1

    if not data_params.get("train_data"):
        emit_warning("train_data is missing")
        warnings += 1
    if not data_params.get("val_data"):
        emit_warning("val_data is missing")
        warnings += 1

    if stage in {"first", "second", "finetune"} and not data_params.get("root_path"):
        emit_warning("root_path is empty; confirm the list paths already resolve correctly")
        warnings += 1

    if stage in {"second", "finetune"}:
        if config.get("pretrained_model") and not config.get("second_stage_load_pretrained", False):
            emit_warning("pretrained_model is set but second_stage_load_pretrained is false, so the path will be ignored")
            warnings += 1
        if not config.get("pretrained_model") and not config.get("first_stage_path"):
            emit_warning("neither pretrained_model nor first_stage_path is set for a stage-2 style run")
            warnings += 1

    if stage == "finetune" and config.get("load_only_params") is False:
        emit_warning("load_only_params is false; fine-tuning usually wants weights-only loading")
        warnings += 1

    if stage == "first" and config.get("pretrained_model"):
        emit_warning("first-stage runs usually leave pretrained_model empty unless you are resuming deliberately")
        warnings += 1

    if stage == "inference" and not config.get("pretrained_model"):
        emit_warning("inference-style inspection sees no pretrained_model path; demo asset handling is usually managed by the inference sub-skill")
        warnings += 1

    # Memory hints derived from the shipped configs.
    batch_size = config.get("batch_size")
    max_len = config.get("max_len")
    batch_percentage = slmadv_params.get("batch_percentage")
    if stage in {"first", "second", "finetune"} and batch_size is not None and max_len is not None:
        print(f"\nMemory hint: batch_size={batch_size!r}, max_len={max_len!r}, slmadv batch_percentage={batch_percentage!r}")

    if stage == "finetune":
        print(f"fine-tune lr hint: ft_lr={get_in(config, 'optimizer_params.ft_lr')!r}")

    return warnings


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve() if args.repo_root is not None else None
    if args.config.is_absolute():
        config_path = args.config.resolve()
    else:
        base = repo_root if repo_root is not None else Path.cwd()
        config_path = (base / args.config).resolve()
    if not config_path.exists():
        parser.error(f"config file not found: {config_path}")

    if repo_root is None and config_path.parent.name == "Configs":
        repo_root = config_path.parent.parent.resolve()

    config = load_yaml(config_path)

    print(f"config: {config_path}")
    if repo_root is not None:
        print(f"repo_root: {repo_root}")
    if args.stage:
        print(f"stage hint: {args.stage}")

    warnings = inspect_config(config, repo_root=repo_root, stage=args.stage)
    if warnings:
        print(f"\nwarning count: {warnings}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
