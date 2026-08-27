#!/usr/bin/env python3
"""Safe config and dataset schema probe for ChatLLaMA RLHF.

Examples:
  python scripts/chatllama_rlhf_probe.py --config config.yaml
  python scripts/chatllama_rlhf_probe.py --dataset actor_training_data.json --dataset-kind actor
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path

import yaml


def required_keys_for_section(cls, exclude=()):
    required = []
    for field in dataclasses.fields(cls):
        if field.name in exclude:
            continue
        if field.default is dataclasses.MISSING and field.default_factory is dataclasses.MISSING:  # type: ignore[attr-defined]
            required.append(field.name)
    return required


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="Optional config.yaml path to validate")
    parser.add_argument("--dataset", default=None, help="Optional JSON dataset path to validate")
    parser.add_argument("--dataset-kind", choices=["actor", "reward", "rlhf"], default="actor", help="Dataset schema to validate")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    report = {"imports": {}, "config": None, "dataset": None}

    try:
        from chatllama.rlhf.config import ConfigActor, ConfigReward, ConfigTrainer
        import chatllama

        report["imports"]["chatllama"] = {
            "status": "ok",
            "file": getattr(chatllama, "__file__", None),
        }
        report["imports"]["helpers"] = {
            "config_sections": ["trainer_config", "actor_config", "critic_config", "reward_config"],
            "trainer_required": required_keys_for_section(ConfigTrainer, exclude=("device", "debug")),
            "actor_required": required_keys_for_section(ConfigActor, exclude=("device", "debug")),
            "reward_required": required_keys_for_section(ConfigReward, exclude=("device", "debug")),
        }
    except Exception as exc:
        report["imports"]["chatllama"] = {"status": "missing", "error": f"{type(exc).__name__}: {exc}"}

    if args.config:
        config_path = Path(args.config)
        try:
            config_data = yaml.safe_load(config_path.read_text())
            expected_sections = {
                "trainer_config": ["actor_lr", "critic_lr", "examples_path", "num_episodes", "max_timesteps", "update_timesteps", "num_examples", "batch_size", "epochs", "checkpoint_steps"],
                "actor_config": ["model", "model_folder", "tokenizer_path", "train_dataset_path", "froze_embeddings", "use_fairscale", "max_sequence_length", "max_tokens", "min_tokens", "additonal_prompt_tokens", "temperature", "batch_size", "iteration_per_print", "lr", "epochs", "checkpoint_steps", "n_checkpoints_to_keep", "deepspeed_enable", "deepspeed_config_path", "accelerate_enable", "peft_enable", "peft_config_path"],
                "critic_config": ["model", "model_head_hidden_size", "max_sequence_length", "model_folder"],
                "reward_config": ["model", "model_folder", "model_head_hidden_size", "max_sequence_length", "train_dataset_path", "batch_size", "epochs", "iteration_per_print", "checkpoint_steps", "lr", "deepspeed_enable", "deepspeed_config_path", "accelerate_enable"],
            }
            missing = {}
            for section, required in expected_sections.items():
                section_data = config_data.get(section, {}) if isinstance(config_data, dict) else {}
                missing[section] = [key for key in required if key not in section_data]
            report["config"] = {"status": "ok", "path": str(config_path), "missing_keys": missing}
        except Exception as exc:
            report["config"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}

    if args.dataset:
        dataset_path = Path(args.dataset)
        try:
            dataset = json.loads(dataset_path.read_text())
            if not isinstance(dataset, list):
                raise TypeError("dataset root must be a list")
            required_fields = {
                "actor": {"user_input", "completion"},
                "reward": {"user_input", "completion", "score"},
                "rlhf": {"user_input", "completion"},
            }[args.dataset_kind]
            missing = []
            for idx, item in enumerate(dataset[:5]):
                if not isinstance(item, dict):
                    missing.append({"index": idx, "error": "item is not an object"})
                    continue
                absent = sorted(required_fields - set(item))
                if absent:
                    missing.append({"index": idx, "missing": absent})
            report["dataset"] = {
                "status": "ok",
                "path": str(dataset_path),
                "kind": args.dataset_kind,
                "sample_missing": missing,
                "count": len(dataset),
            }
        except Exception as exc:
            report["dataset"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
