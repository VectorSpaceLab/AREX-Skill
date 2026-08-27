#!/usr/bin/env python3
"""Validate high-value Helios training YAML invariants.

This is a safe preflight helper. It does not import model code, load weights, or
start a distributed job.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


def get(data: dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = data
    for key in path.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def truthy(data: dict[str, Any], path: str) -> bool:
    return bool(get(data, path, False))


def validate_config(data: dict[str, Any]) -> list[str]:
    issues: list[str] = []

    for list_path in [
        "validation_config.validation_latent_window_size",
        "validation_config.validation_stream_chunk_size",
    ]:
        value = get(data, list_path)
        if value is not None and not (isinstance(value, list) and len(value) == 1):
            issues.append(f"{list_path} must be a single-item list")

    if truthy(data, "data_config.use_stage1_dataset") and truthy(data, "training_config.offload"):
        issues.append("data_config.use_stage1_dataset and training_config.offload cannot both be true")

    if truthy(data, "data_config.single_res") and not truthy(data, "data_config.force_rebuild"):
        issues.append("data_config.single_res requires data_config.force_rebuild=true")

    lora_layers = get(data, "model_config.lora_layers")
    lora_targets = get(data, "model_config.lora_target_modules", [])
    if lora_layers is not None and lora_targets:
        issues.append("model_config.lora_layers requires an empty model_config.lora_target_modules list")

    if truthy(data, "training_config.restrict_lora") and not truthy(data, "training_config.restrict_self_attn"):
        issues.append("training_config.restrict_lora requires training_config.restrict_self_attn=true")

    if truthy(data, "training_config.is_train_restrict_lora") and not truthy(data, "training_config.restrict_lora"):
        issues.append("training_config.is_train_restrict_lora requires training_config.restrict_lora=true")

    if truthy(data, "validation_config.use_kv_cache") and not truthy(data, "training_config.restrict_self_attn"):
        issues.append("validation_config.use_kv_cache requires training_config.restrict_self_attn=true")

    if truthy(data, "training_config.use_ema_validation") and not truthy(data, "training_config.use_ema"):
        issues.append("training_config.use_ema_validation requires training_config.use_ema=true")

    if truthy(data, "training_config.efficient_sample") and get(data, "training_config.pyramid_sample_mode") != "full":
        issues.append("training_config.efficient_sample requires training_config.pyramid_sample_mode='full'")

    uses_clean_patch = any(
        truthy(data, path)
        for path in [
            "training_config.is_train_full_multi_term_memory_patchg",
            "training_config.is_train_lora_multi_term_memory_patchg",
            "training_config.zero_history_timestep",
        ]
    )
    if uses_clean_patch:
        if not truthy(data, "training_config.has_multi_term_memory_patch"):
            issues.append("clean patch embedding options require training_config.has_multi_term_memory_patch=true")
        if not truthy(data, "training_config.is_enable_stage1"):
            issues.append("clean patch embedding options require training_config.is_enable_stage1=true")

    if truthy(data, "training_config.is_train_full_multi_term_memory_patchg") and truthy(
        data, "training_config.is_train_lora_multi_term_memory_patchg"
    ):
        issues.append("full and LoRA multi-term memory patch training modes cannot both be enabled")

    if truthy(data, "training_config.is_train_full_patch_embedding") and truthy(
        data, "training_config.is_train_lora_patch_embedding"
    ):
        issues.append("full and LoRA patch-embedding training modes cannot both be enabled")

    if truthy(data, "training_config.use_error_recycling") and truthy(data, "training_config.corrupt_history"):
        issues.append("training_config.use_error_recycling and training_config.corrupt_history cannot both be true")

    if truthy(data, "training_config.use_error_recycling") and truthy(data, "training_config.corrupt_model_input"):
        issues.append("training_config.use_error_recycling and training_config.corrupt_model_input cannot both be true")

    if truthy(data, "training_config.is_multi_pyramid_stage_backward_simulated") and not truthy(
        data, "training_config.is_enable_stage2"
    ):
        issues.append("training_config.is_multi_pyramid_stage_backward_simulated requires is_enable_stage2=true")

    if truthy(data, "training_config.is_use_reward_model"):
        if not (get(data, "training_config.reward_weight_vq", 0) > 0 or get(data, "training_config.reward_weight_mq", 0) > 0):
            issues.append("training_config.is_use_reward_model requires reward_weight_vq>0 or reward_weight_mq>0")

    if truthy(data, "training_config.is_use_gan"):
        if not truthy(data, "training_config.is_train_dmd"):
            issues.append("training_config.is_use_gan requires training_config.is_train_dmd=true")
        if not (truthy(data, "training_config.is_use_gan_hooks") or truthy(data, "training_config.is_use_gan_final")):
            issues.append("training_config.is_use_gan requires is_use_gan_hooks or is_use_gan_final")

    stage_cold_start = get(data, "training_config.stage_cold_start_step")
    cold_start = get(data, "training_config.cold_start_step")
    if stage_cold_start is not None and cold_start is not None and stage_cold_start > cold_start:
        issues.append("training_config.stage_cold_start_step must be <= training_config.cold_start_step")

    if truthy(data, "training_config.is_decouple_dmd"):
        generator_dynamic_step = get(data, "training_config.generator_dynamic_step", 0)
        for path in ["training_config.decouple_ca_start_step", "training_config.decouple_ca_end_step"]:
            value = get(data, path)
            if value is not None and value < generator_dynamic_step:
                issues.append(f"{path} must be >= training_config.generator_dynamic_step")

    if truthy(data, "training_config.is_enable_stage2"):
        if truthy(data, "training_config.use_dynamic_shifting"):
            if not (truthy(data, "training_config.is_train_dmd") or truthy(data, "training_config.is_use_ode_regression")):
                issues.append(
                    "training_config.use_dynamic_shifting with stage2 requires is_train_dmd or is_use_ode_regression"
                )

    if truthy(data, "training_config.is_use_ode_regression") and not truthy(data, "training_config.use_dynamic_shifting"):
        issues.append("training_config.is_use_ode_regression requires training_config.use_dynamic_shifting=true")

    if truthy(data, "data_config.use_stage3_dataset"):
        has_gan = bool(get(data, "data_config.gan_data_root", []))
        has_ode = bool(get(data, "data_config.ode_data_root", []))
        has_text = bool(get(data, "data_config.text_data_root", []))
        if not (has_gan or has_ode or has_text):
            issues.append("stage3 dataset mode requires at least one of gan_data_root, ode_data_root, or text_data_root")

    ratios = get(data, "data_config.dataset_sampling_ratios", [])
    roots = get(data, "data_config.instance_data_root", [])
    if ratios:
        if not truthy(data, "data_config.use_stage1_dataset"):
            issues.append("dataset_sampling_ratios is only supported when data_config.use_stage1_dataset=true")
        if roots and len(roots) != len(ratios):
            issues.append("dataset_sampling_ratios length must match instance_data_root length")
        basenames = [str(root).rstrip("/") for root in roots]
        if len(basenames) != len(set(basenames)):
            issues.append("instance_data_root contains duplicate stripped basenames")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Helios training YAML config")
    parser.add_argument("config", type=Path, help="Config YAML path")
    args = parser.parse_args()

    data = yaml.safe_load(args.config.read_text())
    if not isinstance(data, dict):
        print("config root must be a YAML mapping")
        return 1

    issues = validate_config(data)
    if issues:
        print("Config validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Config validation OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
