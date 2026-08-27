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

"""Render a safe LlamaFactory train command from YAML/JSON config.

This helper intentionally does not import LlamaFactory, download models, or run
training. It performs lightweight config loading, simple key=value overrides,
and warnings for common train-config mistakes.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any


MISSING = object()


def parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"none", "null"}:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_override(text: str) -> tuple[list[str], Any]:
    if "=" not in text:
        raise ValueError(f"Override must use key=value syntax: {text!r}")
    key, value = text.split("=", 1)
    key = key.strip()
    if not key:
        raise ValueError(f"Override has empty key: {text!r}")
    return key.split("."), parse_scalar(value.strip())


def set_nested(config: dict[str, Any], key_path: list[str], value: Any) -> None:
    target = config
    for part in key_path[:-1]:
        current = target.get(part)
        if not isinstance(current, dict):
            current = {}
            target[part] = current
        target = current
    target[key_path[-1]] = value


def strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:index]
    return line


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the flat YAML shape used by LlamaFactory examples.

    This fallback intentionally supports only simple mappings and indentation.
    If a config needs anchors, lists, block scalars, or complex YAML tags,
    install PyYAML and this helper will use it automatically.
    """

    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        line = strip_comment(raw_line).rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith("-"):
            raise SystemExit("This helper's built-in YAML parser does not support list items; install PyYAML.")
        indent = len(line) - len(line.lstrip(" "))
        if ":" not in line:
            raise SystemExit(f"Cannot parse YAML line without ':' using built-in parser: {raw_line}")
        key, value_text = line.strip().split(":", 1)
        key = key.strip().strip("'\"")
        value_text = value_text.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise SystemExit(f"Invalid YAML indentation near: {raw_line}")
        parent = stack[-1][1]
        if value_text == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(value_text.strip("'\""))
    return root


def load_json_or_yaml(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        data = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError:
            data = parse_simple_yaml(text)
        else:
            data = yaml.safe_load(text)
    else:
        raise SystemExit("Config path must end with .yaml, .yml, or .json")
    if not isinstance(data, dict):
        raise SystemExit("Top-level config must be a mapping/object.")
    return data


def flatten_keys(value: Any, prefix: str = "") -> dict[str, Any]:
    if not isinstance(value, dict):
        return {prefix: value}
    flattened: dict[str, Any] = {}
    for key, item in value.items():
        next_prefix = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(item, dict):
            flattened.update(flatten_keys(item, next_prefix))
        else:
            flattened[next_prefix] = item
    return flattened


def shell_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def warn(config: dict[str, Any]) -> list[str]:
    flat = flatten_keys(config)
    get = flat.get
    warnings: list[str] = []

    if get("model_name_or_path") in {None, ""}:
        warnings.append("Missing model_name_or_path; LlamaFactory train args require it.")
    if get("output_dir") in {None, ""}:
        warnings.append("Missing output_dir; Hugging Face Trainer requires an output directory.")
    if get("stage") not in {"pt", "sft", "rm", "ppo", "dpo", "kto", None}:
        warnings.append("Unknown stage for v0. Use pt/sft/rm/ppo/dpo/kto; ORPO/SimPO use stage=dpo.")
    if get("stage") == "ppo" and not get("reward_model"):
        warnings.append("PPO requires reward_model.")
    if get("pref_loss") in {"orpo", "simpo"} and get("stage") != "dpo":
        warnings.append("ORPO/SimPO are DPO loss variants; set stage=dpo.")
    if get("quantization_bit") is not None and get("finetuning_type") not in {"lora", "oft", None}:
        warnings.append("quantization_bit is only compatible with finetuning_type lora or oft.")
    if get("quantization_bit") is not None and get("resize_vocab") is True:
        warnings.append("resize_vocab is not allowed with quantized training.")
    if get("adapter_name_or_path") and get("finetuning_type") not in {"lora", None}:
        warnings.append("adapter_name_or_path is valid for LoRA train args; check finetuning_type.")
    if get("eval_dataset") and get("val_size") not in {None, 0, 0.0, "0", "0.0"}:
        warnings.append("Use either eval_dataset or val_size, not both.")
    if get("streaming") is True and get("max_samples") is not None:
        warnings.append("max_samples is incompatible with streaming.")
    if get("mask_history") is True and get("train_on_prompt") is True:
        warnings.append("mask_history is incompatible with train_on_prompt.")
    if get("report_to") not in {None, "none", "None"} and not get("run_name"):
        warnings.append("External logging is enabled; consider setting run_name and credentials outside YAML.")
    if get("report_to") == "trackio" and not get("project"):
        warnings.append("Trackio requires project.")
    return warnings


def build_command(args: argparse.Namespace, config_path: Path, config: dict[str, Any]) -> list[str]:
    command = [args.cli, "train", str(config_path)]
    for key_path, value in args.parsed_overrides:
        command.append(f"{'.'.join(key_path)}={shell_value(value)}")
    if args.max_steps is not MISSING:
        command.append(f"max_steps={shell_value(args.max_steps)}")
    if args.report_to_none:
        command.append("report_to=none")
    if args.output_dir:
        command.append(f"output_dir={args.output_dir}")
    if args.force_torchrun:
        command = ["FORCE_TORCHRUN=1", *command]
    return command


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Path to a LlamaFactory train YAML/JSON config.")
    parser.add_argument("overrides", nargs="*", help="OmegaConf-style key=value overrides to append and inspect.")
    parser.add_argument("--cli", default="llamafactory-cli", choices=["llamafactory-cli", "lmf"], help="CLI executable name.")
    parser.add_argument("--force-torchrun", action="store_true", help="Prefix the rendered command with FORCE_TORCHRUN=1.")
    parser.add_argument("--max-steps", type=parse_scalar, default=MISSING, help="Append max_steps=<value> for smoke-test rendering.")
    parser.add_argument("--report-to-none", action="store_true", help="Append report_to=none for safe smoke-test rendering.")
    parser.add_argument("--output-dir", help="Append output_dir=<value>.")
    parser.add_argument("--print-json", action="store_true", help="Print merged lightweight config JSON before the command.")
    args = parser.parse_args(argv)

    config_path = args.config
    config = load_json_or_yaml(config_path)
    parsed_overrides = [parse_override(text) for text in args.overrides]
    args.parsed_overrides = parsed_overrides
    for key_path, value in parsed_overrides:
        set_nested(config, key_path, value)
    if args.max_steps is not MISSING:
        config["max_steps"] = args.max_steps
    if args.report_to_none:
        config["report_to"] = "none"
    if args.output_dir:
        config["output_dir"] = args.output_dir

    if args.print_json:
        print(json.dumps(config, indent=2, ensure_ascii=False, sort_keys=True))
        print()

    warnings = warn(config)
    for item in warnings:
        print(f"warning: {item}", file=sys.stderr)

    command = build_command(args, config_path, config)
    print(" ".join(shlex.quote(part) if "=" not in part[: max(part.find("/"), 0) + 1] else shlex.quote(part) for part in command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
