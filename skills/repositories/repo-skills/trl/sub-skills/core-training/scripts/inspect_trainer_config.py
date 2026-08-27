#!/usr/bin/env python3
"""Print TRL stable trainer signatures and selected config defaults without training or downloading."""

from __future__ import annotations

import argparse
import dataclasses
import importlib
import inspect
import json
import sys
from typing import Any

TRAINERS = {
    "sft": ("trl", "SFTTrainer", "SFTConfig"),
    "dpo": ("trl", "DPOTrainer", "DPOConfig"),
    "grpo": ("trl", "GRPOTrainer", "GRPOConfig"),
    "reward": ("trl", "RewardTrainer", "RewardConfig"),
    "rloo": ("trl", "RLOOTrainer", "RLOOConfig"),
}

DEFAULT_FIELDS = {
    "learning_rate",
    "dataset_text_field",
    "dataset_num_proc",
    "max_length",
    "max_prompt_length",
    "max_completion_length",
    "packing",
    "padding_free",
    "completion_only_loss",
    "assistant_only_loss",
    "loss_type",
    "beta",
    "label_smoothing",
    "num_generations",
    "generation_batch_size",
    "steps_per_generation",
    "num_iterations",
    "reward_weights",
    "mask_truncated_completions",
    "sync_ref_model",
    "remove_unused_columns",
    "use_vllm",
    "vllm_mode",
    "center_rewards_coefficient",
}

MODEL_FIELDS = {
    "model_name_or_path",
    "model_revision",
    "torch_dtype",
    "trust_remote_code",
    "attn_implementation",
    "use_peft",
    "lora_r",
    "lora_alpha",
    "load_in_8bit",
    "load_in_4bit",
}


def field_default(field: dataclasses.Field[Any]) -> Any:
    if field.default is not dataclasses.MISSING:
        return field.default
    if field.default_factory is not dataclasses.MISSING:  # type: ignore[attr-defined]
        try:
            return field.default_factory()  # type: ignore[misc]
        except Exception as exc:  # pragma: no cover - defensive display only
            return f"<default_factory failed: {exc}>"
    return "<required>"


def selected_defaults(config_class: type, names: set[str]) -> dict[str, Any]:
    if not dataclasses.is_dataclass(config_class):
        return {}
    defaults = {}
    for field in dataclasses.fields(config_class):
        if field.name in names:
            defaults[field.name] = field_default(field)
    return defaults


def load_trl() -> Any:
    try:
        return importlib.import_module("trl")
    except Exception as exc:
        raise SystemExit(
            "Could not import TRL. Install TRL with its runtime dependencies before using this inspector. "
            f"Import error: {exc}"
        ) from exc


def inspect_trainer(trl_module: Any, key: str) -> dict[str, Any]:
    _, trainer_name, config_name = TRAINERS[key]
    item: dict[str, Any] = {"trainer": trainer_name, "config": config_name}
    try:
        trainer_class = getattr(trl_module, trainer_name)
        item["trainer_init_signature"] = str(inspect.signature(trainer_class.__init__))
    except Exception as exc:
        item["trainer_init_error"] = str(exc)
    try:
        config_class = getattr(trl_module, config_name)
        item["selected_config_defaults"] = selected_defaults(config_class, DEFAULT_FIELDS)
    except Exception as exc:
        item["config_error"] = str(exc)
        item["selected_config_defaults"] = {}
    return item


def build_report(selected: list[str]) -> dict[str, Any]:
    trl_module = load_trl()
    report = {
        "trl_version": getattr(trl_module, "__version__", "<unknown>"),
        "trainers": [inspect_trainer(trl_module, key) for key in selected],
    }
    try:
        model_config = getattr(trl_module, "ModelConfig")
        report["model_config_defaults"] = selected_defaults(model_config, MODEL_FIELDS)
    except Exception as exc:
        report["model_config_error"] = str(exc)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trainer",
        choices=sorted(TRAINERS),
        action="append",
        help="Trainer family to inspect. Repeat to inspect multiple. Defaults to all stable core trainers.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of readable text.")
    args = parser.parse_args()

    selected = args.trainer or sorted(TRAINERS)
    report = build_report(selected)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
        return 0

    print(f"TRL version: {report['trl_version']}")
    for item in report["trainers"]:
        print(f"\n## {item['trainer']}")
        if "trainer_init_signature" in item:
            print(item["trainer_init_signature"])
        else:
            print(f"signature unavailable: {item['trainer_init_error']}")
        if "config_error" in item:
            print(f"{item['config']} defaults unavailable: {item['config_error']}")
            continue
        print(f"{item['config']} selected defaults:")
        for name, value in item["selected_config_defaults"].items():
            print(f"  {name} = {value!r}")
    if "model_config_defaults" in report:
        print("\n## ModelConfig selected defaults")
        for name, value in report["model_config_defaults"].items():
            print(f"  {name} = {value!r}")
    elif "model_config_error" in report:
        print(f"\nModelConfig error: {report['model_config_error']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
