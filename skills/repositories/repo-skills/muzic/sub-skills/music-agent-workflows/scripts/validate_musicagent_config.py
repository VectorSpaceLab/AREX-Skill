#!/usr/bin/env python3
"""Validate MusicAgent configuration files without importing repo modules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

KNOWN_PIPE_KEYS = {
    "muzic/roc",
    "cvssp/audioldm-m-full",
    "DiffSinger",
    "dima806/music_genres_classification",
    "lewtun/distilhubert-finetuned_music-genres",
}

# Backward-compatible aliases for the current wrapper keys.
KNOWN_PIPE_KEYS.update(
    {
        "lewtun/distilhubert-finetuned-music-genres",
        "spotify",
        "ddsp",
        "demucs",
        "basic-merge",
        "basic-crop",
        "basic-splice",
        "basic-pitch",
        "google-search",
        "jonatasgrosman/whisper-large-zh-cv11",
        "sander-wood/text-to-music",
        "getmusic",
        "muzic/telemelody",
    }
)

REQUIRED_KEYS = (
    "debug",
    "use_azure_openai",
    "model",
    "device",
    "local_fold",
    "log_file",
    "src_fold",
    "disabled_tools",
    "history_len",
    "candidate_tools",
)

OPTIONAL_MAPPINGS = ("huggingface", "spotify", "google")


class ValidationError(Exception):
    """Raised when the configuration is structurally invalid."""


def load_config(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"config file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ValidationError(f"YAML parse error: {exc}") from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValidationError("top-level config must be a mapping")
    return data


def normalize_disabled_tools(value: Any) -> list[str]:
    if value in (None, "", []):
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raise ValidationError("disabled_tools must be a string, list, or null")


def ensure_type(name: str, value: Any, expected: tuple[type, ...]) -> None:
    if not isinstance(value, expected):
        expected_names = ", ".join(t.__name__ for t in expected)
        raise ValidationError(f"{name} must be one of: {expected_names}")


def resolve_path(base_dir: Path, raw: Any) -> Path:
    if not isinstance(raw, str) or not raw:
        raise ValidationError("path fields must be non-empty strings")
    path = Path(raw)
    return path if path.is_absolute() else base_dir / path


def relative_display(base_dir: Path, path: Path) -> str:
    try:
        return str(path.relative_to(base_dir))
    except ValueError:
        return str(path)


def validate_config(config: dict[str, Any], base_dir: Path, check_optional_assets: bool) -> tuple[dict[str, Any], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    for key in REQUIRED_KEYS:
        if key not in config:
            errors.append(f"missing required key: {key}")

    for key in OPTIONAL_MAPPINGS:
        if key in config and not isinstance(config[key], dict):
            errors.append(f"{key} must be a mapping when present")

    if errors:
        return {}, warnings, errors

    ensure_type("debug", config["debug"], (bool,))
    ensure_type("use_azure_openai", config["use_azure_openai"], (bool,))
    ensure_type("model", config["model"], (str,))
    ensure_type("device", config["device"], (str,))
    ensure_type("history_len", config["history_len"], (int,))
    ensure_type("candidate_tools", config["candidate_tools"], (int,))

    if not config["model"].strip():
        errors.append("model must not be empty")
    if not config["device"].strip():
        errors.append("device must not be empty")
    if config["history_len"] <= 0:
        errors.append("history_len must be positive")
    if config["candidate_tools"] <= 0:
        errors.append("candidate_tools must be positive")

    disabled_tools = normalize_disabled_tools(config["disabled_tools"])
    unknown_disabled = [tool for tool in disabled_tools if tool not in KNOWN_PIPE_KEYS]
    if unknown_disabled:
        warnings.append(
            "unknown disabled_tools pipe key(s): " + ", ".join(sorted(unknown_disabled))
        )

    local_fold = resolve_path(base_dir, config["local_fold"])
    if not local_fold.exists():
        warnings.append(
            f"local_fold is missing: {relative_display(base_dir, local_fold)}"
        )

    log_file = resolve_path(base_dir, config["log_file"])
    if log_file.parent.name != "logs" and not log_file.parent.exists():
        warnings.append(
            f"log_file parent does not exist: {relative_display(base_dir, log_file.parent)}"
        )

    summary = {
        "base_dir": str(base_dir),
        "model": config["model"],
        "device": config["device"],
        "local_fold": config["local_fold"],
        "log_file": config["log_file"],
        "src_fold": config["src_fold"],
        "disabled_tools": disabled_tools,
        "history_len": config["history_len"],
        "candidate_tools": config["candidate_tools"],
        "use_azure_openai": config["use_azure_openai"],
    }

    if check_optional_assets:
        optional_assets = {
            "muzic/roc": ["muzic/roc/main.py", "muzic/roc/midi2dict.py", "muzic/roc/utils/lyrics_match.py"],
            "cvssp/audioldm-m-full": ["cvssp/audioldm-m-full"],
            "DiffSinger": ["DiffSinger"],
            "lewtun/distilhubert-finetuned-music-genres": ["lewtun/distilhubert-finetuned-music-genres"],
            "dima806/music_genres_classification": ["dima806/music_genres_classification"],
            "jonatasgrosman/whisper-large-zh-cv11": ["jonatasgrosman/whisper-large-zh-cv11"],
            "sander-wood/text-to-music": ["sander-wood/text-to-music"],
            "ddsp": ["ddsp/violin", "ddsp/flute"],
        }
        for tool_key, rel_paths in optional_assets.items():
            if tool_key in disabled_tools:
                continue
            for rel_path in rel_paths:
                candidate = local_fold / rel_path
                if not candidate.exists():
                    warnings.append(
                        f"missing optional asset for {tool_key}: {relative_display(base_dir, candidate)}"
                    )
                    break

    return summary, warnings, errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a MusicAgent YAML config without importing source-repo modules."
    )
    parser.add_argument("--config", required=True, help="Path to config.yaml")
    parser.add_argument(
        "--base-dir",
        help="Base directory for relative paths; defaults to the config file directory.",
    )
    parser.add_argument(
        "--check-optional-assets",
        action="store_true",
        help="Check common MusicAgent model/cache directories under local_fold.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when warnings are emitted.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary instead of human-readable text.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config_path = Path(args.config).expanduser()
    base_dir = Path(args.base_dir).expanduser() if args.base_dir else config_path.resolve().parent

    try:
        config = load_config(config_path)
        summary, warnings, errors = validate_config(config, base_dir, args.check_optional_assets)
    except ValidationError as exc:
        parser.error(str(exc))
        return 2

    ok = not errors and (not warnings or not args.strict)

    if args.json:
        print(
            json.dumps(
                {
                    "ok": ok,
                    "summary": summary,
                    "warnings": warnings,
                    "errors": errors,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print("MusicAgent config validation: OK" if ok else "MusicAgent config validation: issues found")
        for key, value in summary.items():
            print(f"{key}: {value}")
        if warnings:
            print("warnings:")
            for item in warnings:
                print(f"- {item}")
        if errors:
            print("errors:")
            for item in errors:
                print(f"- {item}")

    if errors:
        return 2
    if warnings and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
