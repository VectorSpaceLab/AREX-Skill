#!/usr/bin/env python3
"""Safely inspect an LTX-Video pipeline YAML config.

This script only reads the YAML file supplied with --config. It does not import
ltx_video, download checkpoints, instantiate models, or run inference.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

try:
    import yaml
except ImportError as exc:  # pragma: no cover - depends on user environment
    raise SystemExit(
        "PyYAML is required to parse LTX-Video YAML configs. Install pyyaml in "
        "the inspection environment, then rerun this script."
    ) from exc

ALLOWED_PIPELINE_TYPES = {"base", "multi-scale"}
ALLOWED_PRECISIONS = {"bfloat16", "float8_e4m3fn", "mixed_precision"}
ALLOWED_STG_MODES = {
    "attention_values",
    "attention_skip",
    "residual",
    "transformer_block",
    "stg_av",
    "stg_as",
    "stg_r",
    "stg_t",
}
ALLOWED_SAMPLERS = {"from_checkpoint", "uniform", "linear-quadratic"}
COMMON_REQUIRED_KEYS = [
    "pipeline_type",
    "checkpoint_path",
    "precision",
    "text_encoder_model_name_or_path",
    "prompt_enhancement_words_threshold",
    "prompt_enhancer_image_caption_model_name_or_path",
    "prompt_enhancer_llm_model_name_or_path",
    "stg_mode",
    "decode_timestep",
    "decode_noise_scale",
]
BASE_DENOISE_KEYS = ["guidance_scale", "stg_scale", "rescaling_scale"]
PASS_DENOISE_KEYS = ["guidance_scale", "stg_scale", "rescaling_scale"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect and validate an LTX-Video YAML pipeline config without "
            "running downloads, model loading, or inference."
        )
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to an LTX-Video pipeline YAML config to inspect.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of the text report.",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> Dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text())
    except FileNotFoundError:
        raise SystemExit(f"Config file not found: {path}")
    except yaml.YAMLError as exc:
        raise SystemExit(f"YAML parse error in {path}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"Config root must be a YAML mapping, got {type(data).__name__}")
    return data


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def numeric_value(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def has_positive_scale(value: Any) -> bool:
    if isinstance(value, list):
        return any(has_positive_scale(item) for item in value)
    num = numeric_value(value)
    return bool(num is not None and num > 0)


def is_list_of_lists(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(x, list) for x in value)


def check_missing(data: Dict[str, Any], keys: Iterable[str], errors: List[str], scope: str) -> None:
    for key in keys:
        if key not in data:
            errors.append(f"{scope}: missing required key `{key}`")


def classify(config_path: Path, data: Dict[str, Any]) -> Dict[str, Any]:
    text = " ".join(
        str(x)
        for x in [
            config_path.name,
            data.get("checkpoint_path", ""),
            data.get("precision", ""),
            data.get("pipeline_type", ""),
        ]
    ).lower()
    if "13b" in text:
        family = "13B"
    elif "2b" in text:
        family = "2B"
    else:
        family = "unknown"

    if "distilled" in text:
        flavor = "distilled"
    elif "dev" in text:
        flavor = "dev"
    else:
        flavor = "legacy-or-unspecified"

    pipeline_type = data.get("pipeline_type", "unknown")
    precision = data.get("precision", "unknown")
    return {
        "family": family,
        "flavor": flavor,
        "pipeline_type": pipeline_type,
        "precision": precision,
        "is_fp8": precision == "float8_e4m3fn" or "fp8" in text,
        "is_multi_scale": pipeline_type == "multi-scale",
    }


def local_path_status(value: Any, config_path: Path) -> Dict[str, Any]:
    status: Dict[str, Any] = {
        "value": value,
        "kind": "missing",
        "exists_as_provided": False,
        "exists_relative_to_config": False,
    }
    if not is_nonempty_string(value):
        return status

    raw = Path(value).expanduser()
    status["exists_as_provided"] = raw.is_file()
    if status["exists_as_provided"]:
        status["kind"] = "local-file"
        return status

    if not raw.is_absolute():
        config_relative = (config_path.parent / raw).resolve()
        status["exists_relative_to_config"] = config_relative.is_file()
        if status["exists_relative_to_config"]:
            status["kind"] = "config-relative-file"
            status["config_relative_path"] = str(config_relative)
            return status

    status["kind"] = "will-download-or-missing"
    return status


def validate_path_field(
    data: Dict[str, Any],
    key: str,
    config_path: Path,
    warnings: List[str],
    errors: List[str],
    *,
    required: bool,
    download_label: str,
) -> Dict[str, Any] | None:
    value = data.get(key)
    if required and not is_nonempty_string(value):
        errors.append(f"missing or empty `{key}`")
        return None
    if not is_nonempty_string(value):
        return None
    status = local_path_status(value, config_path)
    if status["kind"] == "config-relative-file":
        warnings.append(
            f"`{key}` exists relative to the config file, but LTX-Video infer checks "
            "checkpoint/upscaler paths from the process working directory; use an "
            "absolute path or run from the matching directory."
        )
    elif status["kind"] == "will-download-or-missing":
        warnings.append(
            f"`{key}: {value}` is not an existing local file as provided; infer will "
            f"treat it as a {download_label} filename for the Lightricks/LTX-Video "
            "model repo, which can trigger a large download or fail offline."
        )
    return status


def validate_sampler(data: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    sampler = data.get("sampler")
    if sampler is None:
        warnings.append("`sampler` is missing; infer will use the checkpoint scheduler. Bundled configs use `from_checkpoint`.")
        return
    if not isinstance(sampler, str):
        errors.append("`sampler` must be a string when present")
        return
    if sampler not in ALLOWED_SAMPLERS:
        errors.append(
            f"`sampler: {sampler}` is not one of {sorted(ALLOWED_SAMPLERS)}; "
            "misspellings can silently route to the linear-quadratic code branch."
        )


def validate_prompt_enhancement(data: Dict[str, Any], warnings: List[str], errors: List[str]) -> None:
    threshold = data.get("prompt_enhancement_words_threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, int):
        errors.append("`prompt_enhancement_words_threshold` must be an integer")
        return
    if threshold > 0:
        warnings.append(
            f"short prompts with fewer than {threshold} words will enable prompt enhancement, "
            "which can load/download the configured caption model and LLM. Set the threshold to 0 to disable."
        )


def validate_schedule(scope: str, block: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    has_steps = "num_inference_steps" in block
    has_timesteps = "timesteps" in block
    if not has_steps and not has_timesteps:
        errors.append(f"{scope}: expected either `num_inference_steps` or `timesteps`")
    if has_steps:
        steps = block.get("num_inference_steps")
        if isinstance(steps, bool) or not isinstance(steps, int) or steps <= 0:
            errors.append(f"{scope}: `num_inference_steps` must be a positive integer")
    if has_timesteps:
        timesteps = block.get("timesteps")
        if not isinstance(timesteps, list) or not timesteps:
            errors.append(f"{scope}: `timesteps` must be a non-empty list when provided")
        elif not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in timesteps):
            errors.append(f"{scope}: every `timesteps` entry must be numeric")

    for key in ("skip_initial_inference_steps", "skip_final_inference_steps"):
        if key in block:
            value = block[key]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                errors.append(f"{scope}: `{key}` must be a non-negative integer")
    if has_steps:
        steps = block.get("num_inference_steps")
        initial = block.get("skip_initial_inference_steps", 0)
        final = block.get("skip_final_inference_steps", 0)
        if all(isinstance(x, int) and not isinstance(x, bool) for x in (steps, initial, final)):
            if initial + final >= steps:
                errors.append(
                    f"{scope}: skip_initial_inference_steps + skip_final_inference_steps must be less than num_inference_steps"
                )

    guidance_timesteps = block.get("guidance_timesteps")
    if guidance_timesteps is not None:
        if not isinstance(guidance_timesteps, list) or not guidance_timesteps:
            errors.append(f"{scope}: `guidance_timesteps` must be a non-empty list when provided")
        elif not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in guidance_timesteps):
            errors.append(f"{scope}: every `guidance_timesteps` entry must be numeric")
        else:
            expected_len = len(guidance_timesteps)
            for key in ("guidance_scale", "stg_scale", "rescaling_scale"):
                value = block.get(key)
                if isinstance(value, list) and len(value) != expected_len:
                    errors.append(
                        f"{scope}: `{key}` length {len(value)} does not match `guidance_timesteps` length {expected_len}"
                    )
            skip_value = block.get("skip_block_list")
            if is_list_of_lists(skip_value) and len(skip_value) != expected_len:
                errors.append(
                    f"{scope}: list-of-lists `skip_block_list` length {len(skip_value)} does not match `guidance_timesteps` length {expected_len}"
                )
    else:
        for key in ("guidance_scale", "stg_scale", "rescaling_scale"):
            if isinstance(block.get(key), list):
                warnings.append(f"{scope}: `{key}` is a list but `guidance_timesteps` is absent")


def validate_base(data: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    check_missing(data, BASE_DENOISE_KEYS, errors, "base")
    validate_schedule("base", data, errors, warnings)
    if has_positive_scale(data.get("stg_scale")) and "skip_block_list" not in data:
        warnings.append("base: `stg_scale` is positive but `skip_block_list` is missing")
    if "first_pass" in data or "second_pass" in data:
        warnings.append("base config contains `first_pass`/`second_pass`; those are ignored by ordinary base pipeline calls")


def validate_multi_scale(data: Dict[str, Any], errors: List[str], warnings: List[str], config_path: Path) -> None:
    if "downscale_factor" not in data:
        errors.append("multi-scale: missing required key `downscale_factor`")
    else:
        downscale = numeric_value(data.get("downscale_factor"))
        if downscale is None or downscale <= 0:
            errors.append("multi-scale: `downscale_factor` must be a positive number")
        elif downscale > 1:
            warnings.append("multi-scale: `downscale_factor` is greater than 1; bundled configs use 0.6666666")

    validate_path_field(
        data,
        "spatial_upscaler_model_path",
        config_path,
        warnings,
        errors,
        required=True,
        download_label="spatial upscaler",
    )

    for pass_name in ("first_pass", "second_pass"):
        block = data.get(pass_name)
        if not isinstance(block, dict):
            errors.append(f"multi-scale: `{pass_name}` must be a mapping")
            continue
        check_missing(block, PASS_DENOISE_KEYS, errors, pass_name)
        validate_schedule(pass_name, block, errors, warnings)
        if has_positive_scale(block.get("stg_scale")) and "skip_block_list" not in block:
            warnings.append(f"{pass_name}: `stg_scale` is positive but `skip_block_list` is missing")

    for key in BASE_DENOISE_KEYS + ["num_inference_steps", "timesteps", "skip_block_list"]:
        if key in data:
            warnings.append(f"multi-scale: top-level `{key}` is unusual; pass-specific values belong in `first_pass`/`second_pass`")


def inspect_config(config_path: Path) -> Dict[str, Any]:
    data = load_yaml(config_path)
    errors: List[str] = []
    warnings: List[str] = []

    check_missing(data, COMMON_REQUIRED_KEYS, errors, "common")

    pipeline_type = data.get("pipeline_type")
    if pipeline_type not in ALLOWED_PIPELINE_TYPES:
        errors.append(f"`pipeline_type` must be one of {sorted(ALLOWED_PIPELINE_TYPES)}, got {pipeline_type!r}")

    precision = data.get("precision")
    if precision not in ALLOWED_PRECISIONS:
        errors.append(f"`precision` must be one of {sorted(ALLOWED_PRECISIONS)}, got {precision!r}")

    stg_mode = data.get("stg_mode")
    if isinstance(stg_mode, str):
        if stg_mode.lower() not in ALLOWED_STG_MODES:
            errors.append(f"`stg_mode: {stg_mode}` is invalid; expected one of {sorted(ALLOWED_STG_MODES)}")
    elif stg_mode is not None:
        errors.append("`stg_mode` must be a string")

    validate_sampler(data, errors, warnings)
    if "prompt_enhancement_words_threshold" in data:
        validate_prompt_enhancement(data, warnings, errors)

    checkpoint_status = validate_path_field(
        data,
        "checkpoint_path",
        config_path,
        warnings,
        errors,
        required=True,
        download_label="checkpoint",
    )

    classification = classify(config_path, data)
    if classification["is_fp8"]:
        warnings.append(
            "FP8 config detected (`precision: float8_e4m3fn` or fp8 filename). LTX-Video's FP8 path requires external `q8_kernels`; the base package does not install them."
        )
    if classification["is_multi_scale"]:
        warnings.append("multi-scale config detected; inference requires the spatial upscaler and performs a low-resolution first pass plus an upscaled second pass.")

    if pipeline_type == "base":
        validate_base(data, errors, warnings)
    elif pipeline_type == "multi-scale":
        validate_multi_scale(data, errors, warnings, config_path)

    summary_fields = {
        "checkpoint_path": data.get("checkpoint_path"),
        "spatial_upscaler_model_path": data.get("spatial_upscaler_model_path"),
        "sampler": data.get("sampler"),
        "stg_mode": data.get("stg_mode"),
        "prompt_enhancement_words_threshold": data.get("prompt_enhancement_words_threshold"),
        "text_encoder_model_name_or_path": data.get("text_encoder_model_name_or_path"),
    }

    return {
        "config": str(config_path),
        "valid": not errors,
        "classification": classification,
        "fields": summary_fields,
        "checkpoint_status": checkpoint_status,
        "errors": errors,
        "warnings": warnings,
    }


def print_text(report: Dict[str, Any]) -> None:
    cls = report["classification"]
    print(f"Config: {report['config']}")
    print(f"Valid: {'yes' if report['valid'] else 'no'}")
    print(
        "Classification: "
        f"family={cls['family']}, flavor={cls['flavor']}, "
        f"pipeline_type={cls['pipeline_type']}, precision={cls['precision']}, "
        f"fp8={'yes' if cls['is_fp8'] else 'no'}, multi_scale={'yes' if cls['is_multi_scale'] else 'no'}"
    )
    print("Key fields:")
    for key, value in report["fields"].items():
        print(f"  - {key}: {value}")

    if report["errors"]:
        print("Errors:")
        for item in report["errors"]:
            print(f"  - {item}")
    else:
        print("Errors: none")

    if report["warnings"]:
        print("Warnings:")
        for item in report["warnings"]:
            print(f"  - {item}")
    else:
        print("Warnings: none")

    print("No downloads, model imports, or inference were performed.")


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser()
    report = inspect_config(config_path)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
