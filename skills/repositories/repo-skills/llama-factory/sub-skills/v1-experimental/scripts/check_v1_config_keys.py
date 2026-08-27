#!/usr/bin/env python3
# Copyright 2025 the LlamaFactory team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Statically warn about likely v0/v1 key mixing in LlamaFactory configs.

This helper intentionally avoids importing LlamaFactory. JSON is parsed with the
standard library. YAML uses PyYAML when available; otherwise a conservative
indentation-aware subset parser handles common LlamaFactory example configs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

V1_TOP_LEVEL_KEYS = {
    "model",
    "template",
    "trust_remote_code",
    "flash_attn",
    "model_class",
    "init_config",
    "peft_config",
    "kernel_config",
    "quant_config",
    "train_dataset",
    "eval_dataset",
    "output_dir",
    "micro_batch_size",
    "global_batch_size",
    "cutoff_len",
    "learning_rate",
    "num_train_epochs",
    "max_steps",
    "max_grad_norm",
    "bf16",
    "batching_strategy",
    "batching_workers",
    "enable_activation_checkpointing",
    "dist_config",
    "optim_config",
    "lr_scheduler_config",
    "seed",
    "full_determinism",
    "resume_from_checkpoint",
    "save_steps",
    "save_epochs",
    "save_ckpt_as_hf",
    "save_total_limit",
    "logging_steps",
    "sample_backend",
    "max_new_tokens",
}

V0_LIKELY_KEYS = {
    "stage": "select the v1 CLI command instead, usually `sft`, `train`, or `rm`",
    "do_train": "training is implied by the v1 training command",
    "do_eval": "v1 eval flow is not equivalent to v0 TrainingArguments eval",
    "do_predict": "v1 prediction flow is not equivalent to v0 predict configs",
    "dataset": "use `train_dataset` or `eval_dataset`",
    "dataset_dir": "v1 does not use the v0 dataset registry path the same way",
    "dataset_info": "use a v1 dataset-info YAML path through `train_dataset`",
    "finetuning_type": "use `peft_config.name`, for example `lora` or `freeze`",
    "lora_rank": "put LoRA rank under `peft_config.r`",
    "lora_alpha": "put LoRA alpha under `peft_config.lora_alpha`",
    "lora_dropout": "put LoRA dropout under `peft_config.lora_dropout`",
    "lora_target": "put target modules under `peft_config.target_modules`",
    "per_device_train_batch_size": "use `micro_batch_size`",
    "per_device_eval_batch_size": "v1 does not expose the same eval batch field",
    "gradient_accumulation_steps": "express the intent with `global_batch_size` and `micro_batch_size`",
    "lr_scheduler_type": "use `lr_scheduler_config` when a v1 scheduler plugin is available",
    "optim": "use `optim_config` when a v1 optimizer plugin is available",
    "deepspeed": "use `dist_config: {name: deepspeed, config_file: ...}`",
    "fsdp": "use `dist_config.name: fsdp2` when targeting v1 FSDP2",
    "report_to": "v1 callback/logging integration is not the same as v0 trainer reporting",
    "logging_dir": "v1 exposes `logging_steps`, not the full v0 logging argument set",
    "save_strategy": "use v1 `save_steps` or `save_epochs`",
    "eval_strategy": "v1 does not mirror v0 eval strategy fields",
    "evaluation_strategy": "v1 does not mirror v0 evaluation strategy fields",
    "predict_with_generate": "v1 sampling uses `sample_backend` and `max_new_tokens`",
    "packing": "v1 batching is selected with `batching_strategy`",
    "preprocessing_num_workers": "v1 data engine does not expose this v0 preprocessing field",
    "val_size": "v1 does not expose this v0 split helper",
    "ddp_timeout": "v1 distributed launch is configured differently",
    "plot_loss": "v1 does not expose this v0 plotting helper",
    "export_dir": "for v1 merge, place export settings under `peft_config`",
    "adapter_name_or_path": "for v1 LoRA load/merge, place this under `peft_config`",
}

PLUGIN_KEYS = {
    "init_config",
    "peft_config",
    "kernel_config",
    "quant_config",
    "dist_config",
    "optim_config",
    "lr_scheduler_config",
}

ENUMS = {
    "model_class": {"llm", "cls", "other"},
    "flash_attn": {"eager", "sdpa", "flash_attention_2"},
    "batching_strategy": {"normal", "padding_free", "dynamic_batching", "dynamic_padding_free"},
    "sample_backend": {"hf", "vllm"},
}

PLUGIN_NAMES = {
    "init_config": {"init_on_meta", "init_on_rank0", "init_on_default"},
    "peft_config": {"lora", "freeze"},
    "kernel_config": {"auto", "liger_kernel"},
    "quant_config": {"auto", "bnb"},
    "dist_config": {"fsdp2", "deepspeed"},
}


def strip_inline_comment(value: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(value):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return value[:index].rstrip()
    return value.strip()


def parse_scalar(raw_value: str) -> Any:
    value = strip_inline_comment(raw_value)
    if value == "":
        return ""
    lowered = value.lower()
    if lowered in {"null", "none", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_yaml_subset(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.lstrip().startswith("-"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        content = raw_line.strip()
        if ":" not in content:
            continue
        key, raw_value = content.split(":", 1)
        key = key.strip()
        if not key:
            continue
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError(f"Invalid indentation near line {line_number}")
        parent = stack[-1][1]
        raw_value = raw_value.strip()
        if raw_value == "" or raw_value.startswith("#"):
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(raw_value)

    return root


def load_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        try:
            import yaml  # type: ignore[import-not-found]
        except Exception:
            data = parse_yaml_subset(text)
        else:
            data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise TypeError("Top-level config must be a mapping/dictionary.")
    return data


def flatten_keys(data: Any, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    if isinstance(data, dict):
        for key, value in data.items():
            key_text = str(key)
            full_key = f"{prefix}.{key_text}" if prefix else key_text
            keys.add(full_key)
            keys.update(flatten_keys(value, full_key))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            keys.update(flatten_keys(value, f"{prefix}[{index}]"))
    return keys


def add(messages: list[tuple[str, str]], level: str, message: str) -> None:
    messages.append((level, message))


def check_config(data: dict[str, Any]) -> list[tuple[str, str]]:
    messages: list[tuple[str, str]] = []
    top_keys = {str(key) for key in data}
    flat_keys = flatten_keys(data)
    v0_keys = top_keys & set(V0_LIKELY_KEYS)
    v1_keys = top_keys & V1_TOP_LEVEL_KEYS

    if v0_keys:
        for key in sorted(v0_keys):
            add(messages, "WARN", f"Likely v0-only key `{key}` found: {V0_LIKELY_KEYS[key]}.")

    if v0_keys and v1_keys:
        add(messages, "WARN", "Config mixes likely v0-only keys with v1 keys; confirm `USE_V1=1` and migrate fields.")
    elif v0_keys and not v1_keys:
        add(messages, "INFO", "Config looks more like v0 than v1; route to default v0 skills unless v1 migration is intended.")

    unknown_v1ish = sorted(top_keys - V1_TOP_LEVEL_KEYS - set(V0_LIKELY_KEYS))
    for key in unknown_v1ish:
        add(messages, "INFO", f"Top-level key `{key}` is not in the known v1 dataclass surface; verify or use ALLOW_EXTRA_KEYS intentionally.")

    if "stage" in data:
        add(messages, "WARN", "V1 selects trainer behavior from the CLI subcommand, not `stage`.")
    if "finetuning_type" in data and "peft_config" not in data:
        add(messages, "WARN", "V1 fine-tuning type should be expressed as `peft_config.name`, such as `lora` or `freeze`.")
    if "dataset" in data and "train_dataset" not in data:
        add(messages, "WARN", "V1 training expects `train_dataset`, not v0 `dataset`.")

    for key in sorted(PLUGIN_KEYS & top_keys):
        value = data[key]
        if value is None:
            continue
        if not isinstance(value, dict):
            add(messages, "WARN", f"`{key}` should be null or a mapping with a `name` field.")
            continue
        name = value.get("name")
        if not name:
            add(messages, "WARN", f"`{key}` is missing required plugin field `name`.")
        elif key in PLUGIN_NAMES and str(name) not in PLUGIN_NAMES[key]:
            allowed = ", ".join(sorted(PLUGIN_NAMES[key]))
            add(messages, "INFO", f"`{key}.name` is `{name}`; known names in this skill are: {allowed}.")

    for key, allowed_values in ENUMS.items():
        if key in data and data[key] is not None and str(data[key]) not in allowed_values:
            allowed = ", ".join(sorted(allowed_values))
            add(messages, "WARN", f"`{key}` value `{data[key]}` is not one of known v1 values: {allowed}.")

    if data.get("sample_backend") == "vllm":
        add(messages, "WARN", "`sample_backend: vllm` appears in the enum, but current v1 BaseSampler only constructs the HF backend.")

    batching_strategy = data.get("batching_strategy")
    if batching_strategy == "dynamic_batching":
        max_steps = data.get("max_steps")
        if not isinstance(max_steps, (int, float)) or max_steps <= 0:
            add(messages, "WARN", "`dynamic_batching` requires a positive `max_steps`.")
        if data.get("save_epochs") is not None:
            add(messages, "WARN", "`dynamic_batching` does not support `save_epochs`; use `save_steps`.")
    if batching_strategy == "padding_free" and data.get("flash_attn") != "flash_attention_2":
        add(messages, "WARN", "`padding_free` requires `flash_attn: flash_attention_2`.")

    dist_config = data.get("dist_config")
    if isinstance(dist_config, dict):
        if dist_config.get("name") == "deepspeed" and not dist_config.get("config_file"):
            add(messages, "WARN", "DeepSpeed v1 dist config requires `config_file`.")
        if dist_config.get("cp_size", 1) not in (None, 1) and dist_config.get("name") != "fsdp2":
            add(messages, "WARN", "Context parallelism currently requires `dist_config.name: fsdp2`.")

    quant_config = data.get("quant_config")
    init_config = data.get("init_config")
    if isinstance(quant_config, dict):
        bit = quant_config.get("quantization_bit")
        if bit is not None and bit not in (4, 8, "4", "8"):
            add(messages, "WARN", "Known v1 bitsandbytes quantization bits are 4 and 8.")
        if isinstance(init_config, dict) and init_config.get("name") == "init_on_meta":
            add(messages, "WARN", "Quantization is not supported with meta-device initialization.")

    if "train_dataset" not in data and any(key in data for key in ("micro_batch_size", "global_batch_size", "max_steps")):
        add(messages, "WARN", "Training-like v1 config is missing `train_dataset`.")

    if any(key.startswith("peft_config.") for key in flat_keys) and "peft_config.name" not in flat_keys:
        add(messages, "WARN", "Nested `peft_config` keys are present but `peft_config.name` was not found.")

    return messages


def main() -> int:
    parser = argparse.ArgumentParser(description="Warn about likely LlamaFactory v0/v1 config key mixing.")
    parser.add_argument("configs", nargs="+", type=Path, help="YAML or JSON config files to inspect.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when warnings are emitted.")
    args = parser.parse_args()

    warning_count = 0
    for path in args.configs:
        print(f"== {path} ==")
        try:
            data = load_config(path)
        except Exception as exc:
            print(f"ERROR: failed to parse config: {exc}")
            warning_count += 1
            continue

        messages = check_config(data)
        if not messages:
            print("OK: no obvious v0/v1 key-mixing issues found.")
            continue
        for level, message in messages:
            print(f"{level}: {message}")
            if level in {"WARN", "ERROR"}:
                warning_count += 1
        print()

    if args.strict and warning_count:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
