#!/usr/bin/env python3
"""Summarize InvokeAI model taxonomy values, with optional live package inspection."""

from __future__ import annotations

import argparse
import json
import sys
from enum import Enum
from typing import Any

STATIC_TAXONOMY: dict[str, list[str]] = {
    "BaseModelType": [
        "any",
        "sd-1",
        "sd-2",
        "sd-3",
        "sdxl",
        "sdxl-refiner",
        "flux",
        "flux2",
        "cogview4",
        "z-image",
        "external",
        "qwen-image",
        "anima",
        "unknown",
    ],
    "ModelType": [
        "onnx",
        "main",
        "vae",
        "lora",
        "control_lora",
        "controlnet",
        "embedding",
        "ip_adapter",
        "clip_vision",
        "clip_embed",
        "t2i_adapter",
        "t5_encoder",
        "qwen3_encoder",
        "qwen_vl_encoder",
        "spandrel_image_to_image",
        "siglip",
        "flux_redux",
        "llava_onevision",
        "text_llm",
        "external_image_generator",
        "unknown",
    ],
    "SubModelType": [
        "unet",
        "transformer",
        "text_encoder",
        "text_encoder_2",
        "text_encoder_3",
        "tokenizer",
        "tokenizer_2",
        "tokenizer_3",
        "vae",
        "vae_decoder",
        "vae_encoder",
        "scheduler",
        "safety_checker",
    ],
    "ModelFormat": [
        "omi",
        "diffusers",
        "checkpoint",
        "lycoris",
        "onnx",
        "olive",
        "embedding_file",
        "embedding_folder",
        "invokeai",
        "t5_encoder",
        "qwen3_encoder",
        "qwen_vl_encoder",
        "bnb_quantized_int8b",
        "bnb_quantized_nf4b",
        "gguf_quantized",
        "external_api",
        "unknown",
    ],
    "ModelVariantType": ["normal", "inpaint", "depth"],
    "FluxVariantType": ["schnell", "dev", "dev_fill"],
    "Flux2VariantType": ["klein_4b", "klein_4b_base", "klein_9b", "klein_9b_base"],
    "ZImageVariantType": ["turbo", "zbase"],
    "QwenImageVariantType": ["generate", "edit"],
    "Qwen3VariantType": ["qwen3_4b", "qwen3_8b", "qwen3_06b"],
    "ClipVariantType": ["large", "gigantic"],
    "SchedulerPredictionType": ["epsilon", "v_prediction", "sample"],
    "ModelRepoVariant": ["", "fp16", "fp32", "onnx", "openvino", "flax"],
    "ModelSourceType": ["path", "url", "hf_repo_id", "external"],
    "FluxLoRAFormat": [
        "flux.diffusers",
        "flux.kohya",
        "flux.onetrainer",
        "flux.control",
        "flux.aitoolkit",
        "flux.xlabs",
        "flux.bfl_peft",
        "flux.onetrainer_bfl",
    ],
}


def enum_values(enum_class: type[Enum]) -> list[str]:
    return [str(member.value) for member in enum_class]


def static_summary() -> dict[str, Any]:
    return {
        "source": "bundled-static",
        "taxonomy": STATIC_TAXONOMY,
        "notes": [
            "Static values are bundled for safe offline use and may be stale after repository changes.",
            "Use --live when the InvokeAI package is importable and exact installed values are required.",
        ],
    }


def live_summary(include_configs: bool) -> dict[str, Any]:
    import invokeai.backend.model_manager.taxonomy as taxonomy

    enum_names = [
        "BaseModelType",
        "ModelType",
        "SubModelType",
        "ModelFormat",
        "ModelVariantType",
        "FluxVariantType",
        "Flux2VariantType",
        "ZImageVariantType",
        "QwenImageVariantType",
        "Qwen3VariantType",
        "ClipVariantType",
        "SchedulerPredictionType",
        "ModelRepoVariant",
        "ModelSourceType",
        "FluxLoRAFormat",
    ]
    summary: dict[str, Any] = {
        "source": "live-import",
        "taxonomy": {enum_name: enum_values(getattr(taxonomy, enum_name)) for enum_name in enum_names},
    }
    if include_configs:
        from invokeai.backend.model_manager.configs.base import Config_Base
        import invokeai.backend.model_manager.configs.factory  # noqa: F401 - registers config classes

        config_rows: list[dict[str, Any]] = []
        for config_class in sorted(Config_Base.CONFIG_CLASSES, key=lambda candidate: candidate.__name__):
            try:
                tag = config_class.get_tag().tag
            except Exception as error:
                tag = f"<tag error: {error}>"
            fields = getattr(config_class, "model_fields", {})
            defaults: dict[str, Any] = {}
            for field_name in ("base", "type", "format", "variant"):
                field_info = fields.get(field_name)
                if field_info is None:
                    continue
                default_value = getattr(field_info, "default", None)
                defaults[field_name] = getattr(default_value, "value", str(default_value))
            config_rows.append({"class": config_class.__name__, "tag": tag, "defaults": defaults})
        summary["config_classes"] = config_rows
    return summary


def print_human(summary: dict[str, Any]) -> None:
    print(f"source: {summary.get('source')}")
    for enum_name, values in summary.get("taxonomy", {}).items():
        print(f"{enum_name}:")
        print("  " + ", ".join(values))
    if "config_classes" in summary:
        print("Config classes:")
        for config_info in summary["config_classes"]:
            print(f"  {config_info['tag']}: {config_info['class']}")
    for note in summary.get("notes", []):
        print(f"note: {note}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize InvokeAI model taxonomy enum values and config tags.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--live", action="store_true", help="Import InvokeAI and report live taxonomy values")
    parser.add_argument("--configs", action="store_true", help="With --live, include registered config class tags")
    parser.add_argument("--strict", action="store_true", help="Return nonzero if --live import fails")
    args = parser.parse_args()

    exit_code = 0
    if args.live:
        try:
            summary = live_summary(include_configs=args.configs)
        except Exception as error:
            exit_code = 1 if args.strict else 0
            summary = static_summary()
            summary["live_error"] = str(error)
    else:
        summary = static_summary()

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human(summary)
        if "live_error" in summary:
            print(f"live import warning: {summary['live_error']}", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
