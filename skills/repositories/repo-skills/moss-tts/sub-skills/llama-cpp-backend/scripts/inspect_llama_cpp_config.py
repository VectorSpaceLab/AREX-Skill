#!/usr/bin/env python3
"""Safely inspect a MOSS-TTS llama.cpp PipelineConfig YAML file.

This helper does not import moss_tts_delay, load models, initialize ONNX/TRT,
or download artifacts. It uses PyYAML when available and falls back to a small
parser for the simple top-level scalar YAML used by the backend configs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

PATH_FIELDS = [
    "backbone_gguf",
    "embedding_dir",
    "lm_head_dir",
    "tokenizer_dir",
    "audio_encoder_onnx",
    "audio_decoder_onnx",
    "audio_encoder_trt",
    "audio_decoder_trt",
]
CORE_PATH_FIELDS = ["backbone_gguf", "embedding_dir", "lm_head_dir", "tokenizer_dir"]
VALID_AUDIO_BACKENDS = {"onnx", "trt", "torch"}
VALID_HEADS_BACKENDS = {"auto", "numpy", "torch"}

DEFAULTS: dict[str, Any] = {
    "backbone_gguf": "",
    "embedding_dir": "",
    "lm_head_dir": "",
    "tokenizer_dir": "",
    "audio_backend": "onnx",
    "audio_encoder_onnx": "",
    "audio_decoder_onnx": "",
    "audio_encoder_trt": "",
    "audio_decoder_trt": "",
    "audio_model_name_or_path": "",
    "heads_backend": "auto",
    "n_ctx": 4096,
    "n_batch": 512,
    "n_threads": 4,
    "n_gpu_layers": -1,
    "max_new_tokens": 2000,
    "use_gpu_audio": True,
    "low_memory": False,
    "kv_cache_type_k": "f16",
    "kv_cache_type_v": "f16",
    "flash_attn": "auto",
    "text_temperature": 1.5,
    "text_top_p": 1.0,
    "text_top_k": 50,
    "audio_temperature": 1.7,
    "audio_top_p": 0.8,
    "audio_top_k": 25,
    "audio_repetition_penalty": 1.0,
    "profile": False,
}


def strip_inline_comment(line: str) -> str:
    """Remove comments outside single/double quotes for simple YAML fallback."""
    in_single = False
    in_double = False
    escaped = False
    out = []
    for ch in line:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\" and in_double:
            out.append(ch)
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            out.append(ch)
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            out.append(ch)
            continue
        if ch == "#" and not in_single and not in_double:
            break
        out.append(ch)
    return "".join(out).rstrip()


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    low = value.lower()
    if low in {"true", "false"}:
        return low == "true"
    if low in {"null", "none", "~"}:
        return None
    if re.fullmatch(r"[-+]?\d+", value):
        try:
            return int(value)
        except ValueError:
            return value
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][-+]?\d+)?", value) or re.fullmatch(r"[-+]?\d+[eE][-+]?\d+", value):
        try:
            return float(value)
        except ValueError:
            return value
    return value


def minimal_yaml_load(text: str) -> tuple[dict[str, Any], list[str]]:
    """Parse top-level `key: scalar` YAML and ignore nested/list constructs."""
    data: dict[str, Any] = {}
    warnings: list[str] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[:1].isspace():
            warnings.append(f"line {lineno}: ignored indented/nested content")
            continue
        line = strip_inline_comment(raw)
        if not line.strip():
            continue
        if ":" not in line:
            warnings.append(f"line {lineno}: ignored non key/value line")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            warnings.append(f"line {lineno}: ignored empty key")
            continue
        data[key] = parse_scalar(value)
    return data, warnings


def load_config(path: Path) -> tuple[dict[str, Any], str, list[str]]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        data, warnings = minimal_yaml_load(text)
        warnings.insert(0, f"PyYAML unavailable ({exc.__class__.__name__}); used simple top-level parser")
        return data, "minimal", warnings

    loaded = yaml.safe_load(text)
    if loaded is None:
        return {}, "pyyaml", []
    if not isinstance(loaded, dict):
        return {}, "pyyaml", ["YAML root is not a mapping"]
    return dict(loaded), "pyyaml", []


def find_project_root(config_path: Path) -> Path | None:
    for parent in (config_path.parent, *config_path.parent.parents):
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return None


def resolve_path(value: Any, config_path: Path, base_dir: Path | None) -> dict[str, Any]:
    if value in (None, ""):
        return {"raw": value, "resolved": None, "exists": False, "kind": "empty"}
    raw = os.fspath(value)
    expanded = Path(raw).expanduser()
    if expanded.is_absolute():
        resolved = expanded.resolve(strict=False)
        return {"raw": raw, "resolved": str(resolved), "exists": resolved.exists(), "kind": kind_of(resolved)}

    candidates: list[Path] = []
    if base_dir is not None:
        candidates.append((base_dir / expanded).resolve(strict=False))
    project_root = find_project_root(config_path)
    if project_root is not None:
        candidate = (project_root / expanded).resolve(strict=False)
        if candidate not in candidates:
            candidates.append(candidate)
    for root in (config_path.parent, Path.cwd()):
        candidate = (root / expanded).resolve(strict=False)
        if candidate not in candidates:
            candidates.append(candidate)

    existing = next((p for p in candidates if p.exists()), candidates[0] if candidates else expanded)
    return {
        "raw": raw,
        "resolved": str(existing),
        "exists": existing.exists(),
        "kind": kind_of(existing),
        "candidates": [str(p) for p in candidates],
    }


def kind_of(path: Path) -> str:
    if path.is_file():
        return "file"
    if path.is_dir():
        return "dir"
    return "missing"


def required_fields_for(audio_backend: str) -> tuple[list[str], list[str]]:
    path_fields = list(CORE_PATH_FIELDS)
    scalar_fields: list[str] = []
    if audio_backend == "onnx":
        path_fields += ["audio_encoder_onnx", "audio_decoder_onnx"]
    elif audio_backend == "trt":
        path_fields += ["audio_encoder_trt", "audio_decoder_trt"]
    elif audio_backend == "torch":
        scalar_fields.append("audio_model_name_or_path")
    return path_fields, scalar_fields


def inspect_config(config_path: Path, base_dir: Path | None) -> dict[str, Any]:
    raw, loader, load_warnings = load_config(config_path)
    known = set(DEFAULTS)
    unknown_keys = sorted(set(raw) - known)
    config = dict(DEFAULTS)
    config.update({k: v for k, v in raw.items() if k in known})

    audio_backend = str(config.get("audio_backend", "onnx"))
    heads_backend = str(config.get("heads_backend", "auto"))
    required_path_fields, required_scalar_fields = required_fields_for(audio_backend)

    path_checks = {field: resolve_path(config.get(field), config_path, base_dir) for field in PATH_FIELDS}

    errors: list[str] = []
    warnings = list(load_warnings)
    if audio_backend not in VALID_AUDIO_BACKENDS:
        errors.append(f"audio_backend must be one of {sorted(VALID_AUDIO_BACKENDS)}, got {audio_backend!r}")
    if heads_backend not in VALID_HEADS_BACKENDS:
        errors.append(f"heads_backend must be one of {sorted(VALID_HEADS_BACKENDS)}, got {heads_backend!r}")
    if bool(config.get("low_memory")) and audio_backend == "torch":
        errors.append("low_memory mode requires audio_backend 'onnx' or 'trt', not 'torch'")

    missing_required_paths = []
    for field in required_path_fields:
        check = path_checks[field]
        if not check["exists"]:
            missing_required_paths.append(field)
            errors.append(f"required path field {field!r} is missing or does not exist")

    missing_required_scalars = []
    for field in required_scalar_fields:
        if config.get(field) in (None, ""):
            missing_required_scalars.append(field)
            errors.append(f"required field {field!r} is empty")

    if audio_backend == "trt":
        warnings.append("TensorRT engines are machine-specific; existence does not prove compatibility")
    if heads_backend == "auto":
        warnings.append("heads_backend 'auto' may use Torch on one machine and NumPy on another")

    summary = {
        "config_path": str(config_path),
        "loader": loader,
        "unknown_keys": unknown_keys,
        "audio_backend": audio_backend,
        "heads_backend": heads_backend,
        "low_memory": bool(config.get("low_memory")),
        "use_gpu_audio": bool(config.get("use_gpu_audio")),
        "runtime": {
            "n_ctx": config.get("n_ctx"),
            "n_batch": config.get("n_batch"),
            "n_threads": config.get("n_threads"),
            "n_gpu_layers": config.get("n_gpu_layers"),
            "max_new_tokens": config.get("max_new_tokens"),
            "kv_cache_type_k": config.get("kv_cache_type_k"),
            "kv_cache_type_v": config.get("kv_cache_type_v"),
            "flash_attn": config.get("flash_attn"),
        },
        "sampling": {
            "text_temperature": config.get("text_temperature"),
            "text_top_p": config.get("text_top_p"),
            "text_top_k": config.get("text_top_k"),
            "audio_temperature": config.get("audio_temperature"),
            "audio_top_p": config.get("audio_top_p"),
            "audio_top_k": config.get("audio_top_k"),
            "audio_repetition_penalty": config.get("audio_repetition_penalty"),
        },
        "audio_model_name_or_path": config.get("audio_model_name_or_path"),
        "required_path_fields": required_path_fields,
        "required_scalar_fields": required_scalar_fields,
        "path_checks": path_checks,
        "missing_required_paths": missing_required_paths,
        "missing_required_scalars": missing_required_scalars,
        "warnings": warnings,
        "errors": errors,
        "valid": not errors,
    }
    return summary


def print_text(summary: dict[str, Any]) -> None:
    print(f"Config: {summary['config_path']}")
    print(f"YAML loader: {summary['loader']}")
    print(
        "Backends: "
        f"audio={summary['audio_backend']} "
        f"heads={summary['heads_backend']} "
        f"low_memory={summary['low_memory']} "
        f"use_gpu_audio={summary['use_gpu_audio']}"
    )
    rt = summary["runtime"]
    print(
        "Runtime: "
        f"n_ctx={rt['n_ctx']} n_batch={rt['n_batch']} n_threads={rt['n_threads']} "
        f"n_gpu_layers={rt['n_gpu_layers']} max_new_tokens={rt['max_new_tokens']} "
        f"kv=({rt['kv_cache_type_k']},{rt['kv_cache_type_v']}) flash_attn={rt['flash_attn']}"
    )
    sp = summary["sampling"]
    print(
        "Sampling: "
        f"text(temp={sp['text_temperature']}, top_p={sp['text_top_p']}, top_k={sp['text_top_k']}); "
        f"audio(temp={sp['audio_temperature']}, top_p={sp['audio_top_p']}, "
        f"top_k={sp['audio_top_k']}, rep_penalty={sp['audio_repetition_penalty']})"
    )
    if summary["unknown_keys"]:
        print("Unknown keys ignored by PipelineConfig:")
        for key in summary["unknown_keys"]:
            print(f"  - {key}")
    print("Path checks:")
    required = set(summary["required_path_fields"])
    for field, check in summary["path_checks"].items():
        marker = "required" if field in required else "optional"
        status = "OK" if check["exists"] else "MISSING"
        raw = check["raw"] if check["raw"] not in (None, "") else "<empty>"
        resolved = check["resolved"] or "<none>"
        print(f"  {status:7s} {field:18s} ({marker}) raw={raw} resolved={resolved}")
    if summary["required_scalar_fields"]:
        print("Required scalar fields:")
        for field in summary["required_scalar_fields"]:
            value = summary.get(field) or summary.get("audio_model_name_or_path")
            status = "OK" if value else "MISSING"
            print(f"  {status:7s} {field}: {value or '<empty>'}")
    if summary["warnings"]:
        print("Warnings:")
        for msg in summary["warnings"]:
            print(f"  - {msg}")
    if summary["errors"]:
        print("Errors:")
        for msg in summary["errors"]:
            print(f"  - {msg}")
    print(f"Validation: {'PASS' if summary['valid'] else 'FAIL'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a MOSS-TTS llama.cpp PipelineConfig YAML without loading models."
    )
    parser.add_argument("config", help="Path to a llama.cpp PipelineConfig YAML file")
    parser.add_argument(
        "--base-dir",
        help="Optional base directory for resolving relative model paths before auto-detection",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero when validation fails. Without this flag, failures are reported but exit code is 0.",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config).expanduser().resolve(strict=False)
    if not config_path.exists():
        print(f"Config file does not exist: {config_path}", file=sys.stderr)
        return 2
    base_dir = Path(args.base_dir).expanduser().resolve(strict=False) if args.base_dir else None
    summary = inspect_config(config_path, base_dir)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary)
    if args.strict and not summary["valid"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
