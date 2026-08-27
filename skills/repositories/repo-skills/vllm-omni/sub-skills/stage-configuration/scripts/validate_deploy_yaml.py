#!/usr/bin/env python3
"""Validate a vLLM-Omni deploy YAML shape without importing vLLM-Omni or loading models.

This helper checks the schema patterns distilled into this skill: top-level
`stages`, optional connector references, platform overrides, and common scalar
fields. It is intentionally a sanity checker, not a replacement for vLLM-Omni's
runtime configuration factory.

Example:
    python scripts/validate_deploy_yaml.py my_deploy.yaml
    python scripts/validate_deploy_yaml.py my_deploy.yaml --format json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency path
    yaml = None

KNOWN_TOP_LEVEL = {
    "base_config",
    "async_chunk",
    "session_mode",
    "active_stream_window",
    "duplex_session",
    "connectors",
    "edges",
    "stages",
    "platforms",
    "pipeline",
    "trust_remote_code",
    "distributed_executor_backend",
    "dtype",
    "quantization",
    "enable_prefix_caching",
    "enable_chunked_prefill",
    "data_parallel_size",
    "pipeline_parallel_size",
    "custom_voice_dir",
}

KNOWN_STAGE_FIELDS = {
    "stage_id",
    "devices",
    "num_replicas",
    "env",
    "output_connectors",
    "input_connectors",
    "default_sampling_params",
    "default_pooling_params",
    "subtalker_sampling_params",
    "tensor_parallel_size",
    "enable_expert_parallel",
    "gpu_memory_utilization",
    "max_num_seqs",
    "max_num_batched_tokens",
    "max_model_len",
    "enforce_eager",
    "async_scheduling",
    "disable_hybrid_kv_cache_manager",
    "mm_processor_cache_gb",
    "mamba_ssm_cache_dtype",
    "compilation_config",
    "profiler_config",
    "skip_mm_profiling",
    "enable_flashinfer_autotune",
    "config_format",
    "load_format",
    "tokenizer_mode",
    "ulysses_degree",
    "ulysses_mode",
    "ring_degree",
    "allgather_degree",
    "sequence_parallel_size",
    "cfg_parallel_size",
    "vae_patch_parallel_size",
    "vae_parallel_mode",
    "text_encoder_tp_size",
    "use_hsdp",
    "hsdp_shard_size",
    "hsdp_replicate_size",
    "model_class_name",
    "diffusion_load_format",
    "lora_path",
    "lora_backend",
    "lora_scale",
    "diffusers_load_kwargs",
    "diffusers_call_kwargs",
    "diffusion_quantization_config",
    "diffusion_attention_backend",
    "diffusion_attention_config",
    "diffusion_compile_granularity",
    "diffusion_compile_dynamic",
    "fa_deterministic",
    "cache_backend",
    "cache_config",
    "enable_cache_dit_summary",
    "step_execution",
    "vae_use_slicing",
    "vae_use_tiling",
    "boundary_ratio",
    "flow_shift",
    "diffusion_kv_cache_dtype",
    "diffusion_kv_cache_skip_steps",
    "diffusion_kv_cache_skip_layers",
    "auxiliary_text_encoder",
    "enable_multithread_weight_load",
    "num_weight_load_threads",
    "enable_cpu_offload",
    "enable_layerwise_offload",
    "enable_distributed_layerwise_offload",
    "dlo_use_allgather",
    "dlo_resident_layers",
    "enable_diffusion_pipeline_profiler",
    "max_generated_image_size",
    "tts_max_instructions_length",
    "engine_extras",
}


def load_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if yaml is None:
        try:
            data = json.loads(text)
        except Exception as exc:
            raise SystemExit(
                "PyYAML is not installed and the file is not JSON. Install PyYAML or pass JSON-compatible YAML."
            ) from exc
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise SystemExit("deploy config root must be a mapping")
    return data


def connector_names(config: dict[str, Any]) -> set[str]:
    connectors = config.get("connectors") or {}
    if not isinstance(connectors, dict):
        return set()
    return set(connectors)


def stage_refs(stage: dict[str, Any]) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for field in ("input_connectors", "output_connectors"):
        value = stage.get(field) or {}
        if isinstance(value, dict):
            for edge, conn in value.items():
                refs.append((f"stage {stage.get('stage_id')} {field}.{edge}", str(conn)))
    return refs


def validate(config: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for key in sorted(set(config) - KNOWN_TOP_LEVEL):
        warnings.append(f"unknown top-level key {key!r}; vLLM-Omni may forward or reject it depending on version")

    stages = config.get("stages")
    if not isinstance(stages, list) or not stages:
        errors.append("top-level 'stages' must be a non-empty list")
        stages = []

    seen: set[int] = set()
    known_connectors = connector_names(config)
    for idx, stage in enumerate(stages):
        if not isinstance(stage, dict):
            errors.append(f"stages[{idx}] must be a mapping")
            continue
        sid = stage.get("stage_id")
        if not isinstance(sid, int):
            errors.append(f"stages[{idx}].stage_id must be an integer")
        elif sid in seen:
            errors.append(f"duplicate stage_id {sid}")
        else:
            seen.add(sid)
        for field in ("gpu_memory_utilization",):
            value = stage.get(field)
            if value is not None and not (isinstance(value, (int, float)) and 0 < float(value) < 1):
                errors.append(f"stage {sid} {field} should be a number between 0 and 1")
        for field in ("max_num_seqs", "max_num_batched_tokens", "max_model_len", "num_replicas"):
            value = stage.get(field)
            if value is not None and not (isinstance(value, int) and value > 0):
                errors.append(f"stage {sid} {field} should be a positive integer")
        for key in sorted(set(stage) - KNOWN_STAGE_FIELDS):
            warnings.append(f"stage {sid} has unknown field {key!r}; it may land in engine_extras")
        for label, conn in stage_refs(stage):
            if known_connectors and conn not in known_connectors:
                errors.append(f"{label} references connector {conn!r}, not present under top-level connectors")

    connectors = config.get("connectors")
    if connectors is not None and not isinstance(connectors, dict):
        errors.append("top-level 'connectors' must be a mapping when present")
    elif isinstance(connectors, dict):
        for name, spec in connectors.items():
            if not isinstance(spec, dict) or not spec.get("name"):
                errors.append(f"connector {name!r} must be a mapping with a non-empty 'name'")

    platforms = config.get("platforms") or {}
    if platforms and not isinstance(platforms, dict):
        errors.append("top-level 'platforms' must be a mapping when present")
    elif isinstance(platforms, dict):
        for platform_name, platform_cfg in platforms.items():
            pstages = platform_cfg.get("stages") if isinstance(platform_cfg, dict) else None
            if pstages is None:
                warnings.append(f"platform {platform_name!r} has no stages override")
            elif not isinstance(pstages, list):
                errors.append(f"platform {platform_name!r}.stages must be a list")
            else:
                for pstage in pstages:
                    if not isinstance(pstage, dict) or not isinstance(pstage.get("stage_id"), int):
                        errors.append(f"platform {platform_name!r} stage override must include integer stage_id")
                    elif seen and pstage["stage_id"] not in seen:
                        warnings.append(
                            f"platform {platform_name!r} overrides stage_id {pstage['stage_id']} not present in base stages"
                        )

    if config.get("base_config"):
        warnings.append("base_config overlays are not recursively loaded by this helper; validate the resolved base separately")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a vLLM-Omni deploy YAML shape without model loading.")
    parser.add_argument("config", type=Path, help="Deploy YAML or JSON file to validate")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    cfg = load_config(args.config)
    errors, warnings = validate(cfg)
    payload = {"ok": not errors, "errors": errors, "warnings": warnings, "stage_count": len(cfg.get("stages") or [])}
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"stage_count: {payload['stage_count']}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        for error in errors:
            print(f"ERROR: {error}")
        print("OK" if payload["ok"] else "INVALID")
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
