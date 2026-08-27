#!/usr/bin/env python3
"""No-load MAGI config preflight.

This helper validates the JSON shape and launch-critical settings used by
MAGI-1 source-code inference. It intentionally uses only the Python standard
library and never imports MAGI, torch, T5, VAE, or DiT code.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

MODEL_FIELDS = [
    "model_name",
    "num_layers",
    "hidden_size",
    "ffn_hidden_size",
    "num_attention_heads",
    "num_query_groups",
    "kv_channels",
    "layernorm_epsilon",
    "apply_layernorm_1p",
    "x_rescale_factor",
    "half_channel_vae",
    "params_dtype",
    "patch_size",
    "t_patch_size",
    "in_channels",
    "out_channels",
    "cond_hidden_ratio",
    "caption_channels",
    "caption_max_length",
    "xattn_cond_hidden_ratio",
    "cond_gating_ratio",
    "gated_linear_unit",
]

RUNTIME_FIELDS = [
    "cfg_number",
    "cfg_t_range",
    "prev_chunk_scales",
    "text_scales",
    "noise2clean_kvrange",
    "clean_chunk_kvrange",
    "clean_t",
    "seed",
    "num_frames",
    "video_size_h",
    "video_size_w",
    "num_steps",
    "window_size",
    "fps",
    "chunk_width",
    "t5_pretrained",
    "t5_device",
    "vae_pretrained",
    "scale_factor",
    "temporal_downsample_factor",
    "load",
]

ENGINE_FIELDS = [
    "distributed_backend",
    "distributed_timeout_minutes",
    "pp_size",
    "cp_size",
    "cp_strategy",
    "ulysses_overlap_degree",
    "fp8_quant",
    "distill_nearly_clean_chunk_threshold",
    "shortcut_mode",
    "distill",
    "kv_offload",
    "enable_cuda_graph",
]

VALID_DTYPES = {"torch.bfloat16", "torch.float16", "torch.float32"}
VALID_BACKENDS = {"nccl", "gloo"}
VALID_CP_STRATEGIES = {"none", "cp_ulysses", "cp_shuffle_overlap"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a MAGI inference config JSON without importing MAGI or "
            "loading model checkpoints."
        )
    )
    parser.add_argument("config", help="Path to the MAGI config JSON to validate.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help=(
            "Source root used to resolve relative checkpoint/asset paths when "
            "--check-paths is set. Default: current directory."
        ),
    )
    parser.add_argument(
        "--world-size",
        type=int,
        default=None,
        help=(
            "Expected distributed WORLD_SIZE. If omitted, WORLD_SIZE from the "
            "environment is used when present."
        ),
    )
    parser.add_argument(
        "--check-paths",
        action="store_true",
        help="Warn if load/t5_pretrained/vae_pretrained/special-token paths are missing.",
    )
    parser.add_argument(
        "--strict-paths",
        action="store_true",
        help="Treat missing paths found by --check-paths as errors instead of warnings.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON results.")
    return parser.parse_args()


def load_config(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return None, [f"Config file not found: {path}"]
    except json.JSONDecodeError as exc:
        return None, [f"Invalid JSON: {exc}"]
    except OSError as exc:
        return None, [f"Could not read config file: {exc}"]
    if not isinstance(data, dict):
        errors.append("Top-level config must be a JSON object.")
        return None, errors
    return data, errors


def require_section(data: dict[str, Any], name: str, errors: list[str]) -> dict[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        errors.append(f"{name} must exist and be a JSON object.")
        return {}
    return value


def check_required(section_name: str, section: dict[str, Any], required: list[str], errors: list[str], warnings: list[str]) -> None:
    missing = [field for field in required if field not in section]
    if missing:
        errors.append(f"{section_name} missing required fields: {', '.join(missing)}")
    unknown = sorted(set(section) - set(required))
    if unknown:
        warnings.append(f"{section_name} has unknown fields not present in source dataclasses: {', '.join(unknown)}")


def as_positive_int(section: dict[str, Any], key: str, errors: list[str]) -> int | None:
    value = section.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{key} must be a positive integer.")
        return None
    if value <= 0:
        errors.append(f"{key} must be > 0.")
        return None
    return value


def as_bool(section: dict[str, Any], key: str, errors: list[str]) -> bool | None:
    value = section.get(key)
    if not isinstance(value, bool):
        errors.append(f"{key} must be a boolean.")
        return None
    return value


def resolve_runtime_path(repo_root: Path, raw: Any) -> Path | None:
    if not isinstance(raw, str) or not raw:
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path


def add_path_message(
    message: str,
    *,
    strict: bool,
    errors: list[str],
    warnings: list[str],
) -> None:
    if strict:
        errors.append(message)
    else:
        warnings.append(message)


def selected_weight_subdir(engine: dict[str, Any]) -> str:
    # Mirrors inference/infra/checkpoint/checkpointing.py: fp8 wins over distill.
    subdir = "inference_weight"
    if engine.get("fp8_quant") is True:
        return f"{subdir}.fp8"
    if engine.get("distill") is True:
        return f"{subdir}.distill"
    return subdir


def check_paths(
    runtime: dict[str, Any],
    engine: dict[str, Any],
    repo_root: Path,
    strict: bool,
    errors: list[str],
    warnings: list[str],
) -> None:
    for key in ("load", "t5_pretrained", "vae_pretrained"):
        path = resolve_runtime_path(repo_root, runtime.get(key))
        if path is None:
            errors.append(f"runtime_config.{key} must be a non-empty string path.")
            continue
        if not path.exists():
            add_path_message(f"runtime_config.{key} path does not exist: {path}", strict=strict, errors=errors, warnings=warnings)

    load_path = resolve_runtime_path(repo_root, runtime.get("load"))
    if load_path is not None:
        weight_dir = load_path / selected_weight_subdir(engine)
        if not weight_dir.exists():
            add_path_message(f"Selected DiT weight directory does not exist: {weight_dir}", strict=strict, errors=errors, warnings=warnings)
        elif not any(weight_dir.iterdir()):
            add_path_message(f"Selected DiT weight directory is empty: {weight_dir}", strict=strict, errors=errors, warnings=warnings)
        else:
            has_single = (weight_dir / "model.safetensors").exists()
            has_index = (weight_dir / "model.safetensors.index.json").exists()
            has_zst = any(weight_dir.glob("*.safetensors.zst"))
            if not (has_single or has_index or has_zst):
                warnings.append(
                    "Selected DiT weight directory exists but no model.safetensors, "
                    "model.safetensors.index.json, or .safetensors.zst files were detected."
                )

    special_token_raw = os.environ.get("SPECIAL_TOKEN_PATH", "example/assets/special_tokens.npz")
    special_token = resolve_runtime_path(repo_root, special_token_raw)
    if special_token is not None and not special_token.exists():
        add_path_message(f"Special-token asset path does not exist: {special_token}", strict=strict, errors=errors, warnings=warnings)


def validate(data: dict[str, Any], args: argparse.Namespace) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    summary: dict[str, Any] = {}

    expected_top = {"model_config", "runtime_config", "engine_config"}
    missing_top = sorted(expected_top - set(data))
    if missing_top:
        errors.append(f"Top-level config missing sections: {', '.join(missing_top)}")
    extra_top = sorted(set(data) - expected_top)
    if extra_top:
        warnings.append(f"Top-level config has unknown sections: {', '.join(extra_top)}")

    model = require_section(data, "model_config", errors)
    runtime = require_section(data, "runtime_config", errors)
    engine = require_section(data, "engine_config", errors)

    check_required("model_config", model, MODEL_FIELDS, errors, warnings)
    check_required("runtime_config", runtime, RUNTIME_FIELDS, errors, warnings)
    check_required("engine_config", engine, ENGINE_FIELDS, errors, warnings)

    dtype = model.get("params_dtype")
    if dtype not in VALID_DTYPES:
        errors.append(f"model_config.params_dtype must be one of {sorted(VALID_DTYPES)}.")

    for key in ("num_layers", "hidden_size", "ffn_hidden_size", "num_attention_heads", "num_query_groups", "kv_channels", "patch_size", "t_patch_size", "in_channels", "out_channels", "caption_channels", "caption_max_length"):
        if key in model:
            as_positive_int(model, key, errors)

    for key in ("cfg_number", "seed", "num_frames", "video_size_h", "video_size_w", "num_steps", "window_size", "fps", "chunk_width", "temporal_downsample_factor"):
        if key in runtime:
            as_positive_int(runtime, key, errors)

    for key in ("pp_size", "cp_size", "distributed_timeout_minutes", "ulysses_overlap_degree"):
        if key in engine:
            as_positive_int(engine, key, errors)

    for key in ("fp8_quant", "distill", "kv_offload", "enable_cuda_graph"):
        if key in engine:
            as_bool(engine, key, errors)

    distill = engine.get("distill") is True
    fp8_quant = engine.get("fp8_quant") is True
    cfg_number = runtime.get("cfg_number")
    if isinstance(cfg_number, int) and not isinstance(cfg_number, bool):
        expected_cfg = 1 if (distill or fp8_quant) else 3
        if cfg_number != expected_cfg:
            if distill or fp8_quant:
                errors.append("cfg_number must be 1 when engine_config.distill or engine_config.fp8_quant is true.")
            else:
                errors.append("cfg_number must be 3 for base configs when distill and fp8_quant are false.")
        summary["expected_cfg_number"] = expected_cfg

    if fp8_quant and not distill:
        warnings.append("fp8_quant is true while distill is false; release examples use distill+fp8 together.")

    backend = engine.get("distributed_backend")
    if backend not in VALID_BACKENDS:
        errors.append(f"engine_config.distributed_backend must be one of {sorted(VALID_BACKENDS)}.")
    elif backend == "gloo":
        warnings.append("Source distributed init still asserts CUDA availability; gloo is not a CPU inference fallback.")

    cp_strategy = engine.get("cp_strategy")
    if cp_strategy not in VALID_CP_STRATEGIES:
        errors.append(f"engine_config.cp_strategy must be one of {sorted(VALID_CP_STRATEGIES)}.")

    cp_size = engine.get("cp_size") if isinstance(engine.get("cp_size"), int) and not isinstance(engine.get("cp_size"), bool) else None
    pp_size = engine.get("pp_size") if isinstance(engine.get("pp_size"), int) and not isinstance(engine.get("pp_size"), bool) else None
    expected_world_size = None
    if cp_size and pp_size:
        expected_world_size = cp_size * pp_size
        summary["expected_world_size"] = expected_world_size
        if cp_strategy == "none" and cp_size != 1:
            errors.append("cp_strategy 'none' requires cp_size == 1.")
        requested_world_size = args.world_size
        if requested_world_size is None:
            env_world_size = os.environ.get("WORLD_SIZE")
            if env_world_size:
                try:
                    requested_world_size = int(env_world_size)
                except ValueError:
                    warnings.append(f"Ignoring non-integer WORLD_SIZE environment value: {env_world_size!r}")
        if requested_world_size is not None and requested_world_size != expected_world_size:
            errors.append(
                f"Launch world size {requested_world_size} does not match pp_size*cp_size={expected_world_size}."
            )
        if requested_world_size is None and expected_world_size != 1:
            warnings.append(f"Config expects distributed world size {expected_world_size}; pass --world-size to verify launch alignment.")

    t5_device = runtime.get("t5_device")
    if t5_device not in {"cpu", "cuda"}:
        warnings.append("runtime_config.t5_device is not one of the release-example values: cpu, cuda.")

    for key in ("load", "t5_pretrained", "vae_pretrained"):
        if not isinstance(runtime.get(key), str) or not runtime.get(key):
            errors.append(f"runtime_config.{key} must be a non-empty string path.")

    patch = model.get("patch_size")
    h = runtime.get("video_size_h")
    w = runtime.get("video_size_w")
    if isinstance(patch, int) and isinstance(h, int) and isinstance(w, int) and patch > 0:
        required_multiple = 8 * patch
        if h % required_multiple != 0 or w % required_multiple != 0:
            warnings.append(
                f"video_size_h/w are safest when divisible by 8*patch_size ({required_multiple}); "
                "otherwise latent patching may crop or fail."
            )

    num_frames = runtime.get("num_frames")
    temporal_downsample = runtime.get("temporal_downsample_factor")
    if isinstance(num_frames, int) and isinstance(temporal_downsample, int) and temporal_downsample > 0:
        if num_frames % temporal_downsample != 0:
            warnings.append("num_frames is not divisible by temporal_downsample_factor; check latent chunk expectations.")

    if args.check_paths:
        check_paths(runtime, engine, Path(args.repo_root), args.strict_paths, errors, warnings)

    summary["selected_weight_subdir"] = selected_weight_subdir(engine)
    summary["distill"] = distill
    summary["fp8_quant"] = fp8_quant
    return errors, warnings, summary


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    data, load_errors = load_config(config_path)
    if data is None:
        errors = load_errors
        warnings: list[str] = []
        summary: dict[str, Any] = {}
    else:
        errors, warnings, summary = validate(data, args)
        errors = load_errors + errors

    result = {
        "config": str(config_path),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"MAGI config preflight: {config_path}")
        if errors:
            print("ERRORS:")
            for error in errors:
                print(f"  - {error}")
        if warnings:
            print("WARNINGS:")
            for warning in warnings:
                print(f"  - {warning}")
        if summary:
            print("SUMMARY:")
            for key, value in summary.items():
                print(f"  - {key}: {value}")
        if not errors:
            print("OK: no blocking config errors detected. This is a preflight only; it does not load checkpoints or generate video.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
