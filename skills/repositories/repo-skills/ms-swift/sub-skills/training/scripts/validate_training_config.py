#!/usr/bin/env python3
"""Validate ms-swift training YAML/JSON configs for high-risk mistakes."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover - only used when PyYAML is absent.
    yaml = None

FLASH_ATTN_IMPLS = {"flash_attn", "flash_attention_2", "flash_attention_3", "flash_attention_4"}
DEEPSPEED_PRESETS = {"zero0", "zero1", "zero2", "zero3", "zero2_offload", "zero3_offload"}
BOOL_TRUE = {"1", "true", "yes", "y", "on"}
BOOL_FALSE = {"0", "false", "no", "n", "off"}


def parse_scalar(text: str) -> Any:
    text = text.strip()
    if text == "":
        return ""
    if (text.startswith("'") and text.endswith("'")) or (text.startswith('"') and text.endswith('"')):
        return text[1:-1]
    lowered = text.lower()
    if lowered in BOOL_TRUE:
        return True
    if lowered in BOOL_FALSE:
        return False
    if lowered in {"null", "none", "~"}:
        return None
    if text.startswith(("[", "{")):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def simple_yaml_load(text: str) -> Dict[str, Any]:
    """Parse the simple YAML shape used by ms-swift config examples.

    This fallback intentionally supports only nested mappings and scalar lists;
    use PyYAML for advanced YAML features such as anchors or multi-line blocks.
    """
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Any]] = [(-1, root)]
    pending_key_at_indent: Dict[int, Tuple[Dict[str, Any], str]] = {}

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if "\t" in raw_line[:indent]:
            raise SystemExit(f"error: tab indentation is not supported in fallback YAML parser at line {line_number}")
        stripped = raw_line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if stripped.startswith("- "):
            item = parse_scalar(stripped[2:])
            if not isinstance(parent, list):
                pending = pending_key_at_indent.get(indent - 2)
                if pending is None:
                    raise SystemExit(f"error: list item without parent key at line {line_number}")
                container, key = pending
                new_list: List[Any] = []
                container[key] = new_list
                parent = new_list
                stack.append((indent - 1, parent))
            parent.append(item)
            continue

        if ":" not in stripped:
            raise SystemExit(f"error: unsupported YAML syntax at line {line_number}: {stripped!r}")
        key, value = stripped.split(":", 1)
        key = key.strip()
        if not key:
            raise SystemExit(f"error: empty YAML key at line {line_number}")
        if not isinstance(parent, dict):
            raise SystemExit(f"error: mapping entry under a list is not supported at line {line_number}")
        if value.strip() == "":
            child: Dict[str, Any] = {}
            parent[key] = child
            pending_key_at_indent[indent] = (parent, key)
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(value)
    return root


def load_config(path: Path) -> Dict[str, Any]:
    suffix = path.suffix.lower()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise SystemExit(f"error: cannot read {path}: {error}") from error
    try:
        if suffix == ".json":
            value = json.loads(text)
        elif suffix in {".yaml", ".yml"}:
            value = yaml.safe_load(text) if yaml is not None else simple_yaml_load(text)
        else:
            raise SystemExit("error: config path must end with .json, .yaml, or .yml")
    except Exception as error:
        if isinstance(error, SystemExit):
            raise
        raise SystemExit(f"error: cannot parse {path}: {error}") from error
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise SystemExit("error: config root must be a mapping/object")
    return value


def as_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in BOOL_TRUE:
        return True
    if text in BOOL_FALSE:
        return False
    return None


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def number(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def has_any(config: Dict[str, Any], keys: Iterable[str]) -> bool:
    return any(key in config and config[key] not in (None, [], "") for key in keys)


def add(messages: List[Tuple[str, str]], level: str, text: str) -> None:
    messages.append((level, text))


def validate(config: Dict[str, Any], route: str) -> List[Tuple[str, str]]:
    messages: List[Tuple[str, str]] = []

    if "ENV" in config and not isinstance(config["ENV"], dict):
        add(messages, "error", "ENV must be a mapping of environment variable names to values.")
    elif isinstance(config.get("ENV"), dict):
        for key, value in config["ENV"].items():
            if not isinstance(key, str) or not key:
                add(messages, "error", "ENV keys must be non-empty strings.")
            if key in os.environ and str(value) != os.environ[key]:
                add(messages, "warn", f"ENV.{key} will not override the already-set shell value.")

    if not has_any(config, ["model"]):
        add(messages, "error", "Missing required model field.")
    if not has_any(config, ["dataset", "cached_dataset"]):
        add(messages, "error", "Training requires dataset or cached_dataset.")
    if has_any(config, ["dataset"]) and has_any(config, ["cached_dataset"]):
        add(messages, "warn", "Both dataset and cached_dataset are set; confirm this is intentional.")

    dataset_values = as_list(config.get("dataset")) + as_list(config.get("val_dataset")) + as_list(config.get("eval_dataset"))
    for dataset in dataset_values:
        if isinstance(dataset, str) and dataset.startswith(("http://", "https://")):
            add(messages, "warn", f"Dataset {dataset!r} is remote; use a local path for offline/reproducible training.")

    train_type = str(config.get("train_type", "")).lower()
    if train_type == "qlora":
        add(messages, "warn", "QLoRA saves memory but is a poor fit when the user needs merged vLLM/SGLang/LMDeploy acceleration after training.")
    if train_type == "full" and not has_any(config, ["learning_rate"]):
        add(messages, "info", "Full tuning defaults to a lower learning rate than LoRA; set learning_rate explicitly for reproducibility.")
    if train_type in {"lora", "qlora"} and not has_any(config, ["target_modules", "target_regex", "target_parameters"]):
        add(messages, "info", "LoRA target modules are implicit; set target_modules/target_regex when targeting a narrow module subset.")

    use_chat_template = as_bool(config.get("use_chat_template"))
    loss_scale = config.get("loss_scale")
    if route == "pt":
        if use_chat_template is True:
            add(messages, "warn", "swift pt normally uses use_chat_template=false.")
        if loss_scale not in (None, "all"):
            add(messages, "warn", "swift pt normally uses loss_scale=all.")
    if route == "sft" and use_chat_template is False and loss_scale == "all":
        add(messages, "info", "This SFT config resembles continued pre-training; consider swift pt if the dataset is corpus-style.")

    max_length = number(config.get("max_length"))
    if max_length is None:
        add(messages, "warn", "Set max_length explicitly; it is the most important memory/truncation control.")
    elif max_length <= 0:
        add(messages, "error", "max_length must be positive.")

    per_device_batch = number(config.get("per_device_train_batch_size"))
    grad_accum = number(config.get("gradient_accumulation_steps"))
    if per_device_batch is not None and per_device_batch <= 0:
        add(messages, "error", "per_device_train_batch_size must be positive.")
    if grad_accum is not None and grad_accum <= 0:
        add(messages, "error", "gradient_accumulation_steps must be positive.")
    if per_device_batch and per_device_batch > 4:
        add(messages, "warn", "Large per-device batch sizes often OOM for LLM training; consider gradient accumulation.")

    split_ratio = number(config.get("split_dataset_ratio"))
    if split_ratio is not None and not (0 <= split_ratio < 1):
        add(messages, "error", "split_dataset_ratio must be in [0, 1).")
    if not has_any(config, ["val_dataset", "eval_dataset"]) and not split_ratio:
        add(messages, "info", "No validation data is configured; eval_strategy will become no.")

    streaming = as_bool(config.get("streaming"))
    if streaming and not has_any(config, ["max_steps"]):
        add(messages, "error", "streaming=true requires explicit max_steps because dataset length is undefined.")

    packing = as_bool(config.get("packing"))
    padding_free = as_bool(config.get("padding_free"))
    attn_impl = config.get("attn_impl")
    if (packing or padding_free) and attn_impl not in FLASH_ATTN_IMPLS:
        add(messages, "error", "packing/padding_free require attn_impl to be a supported flash attention implementation.")
    if packing:
        add(messages, "info", "packing changes effective sample counts; review learning rate, accumulation, save_steps, and eval_steps.")

    cached_dataset = has_any(config, ["cached_dataset"])
    truncation_strategy = config.get("truncation_strategy")
    if cached_dataset and truncation_strategy == "split" and max_length is None:
        add(messages, "warn", "cached_dataset with truncation_strategy=split should reuse the cache-time max_length.")

    deepspeed = config.get("deepspeed")
    fsdp = config.get("fsdp")
    device_map = config.get("device_map")
    if deepspeed and fsdp:
        add(messages, "error", "DeepSpeed and FSDP2 are not compatible; choose one.")
    if deepspeed and device_map not in (None, "", "none", "None"):
        add(messages, "error", "DeepSpeed is not compatible with device_map in this training path.")
    if fsdp and device_map not in (None, "", "none", "None"):
        add(messages, "error", "FSDP2 is not compatible with device_map in this training path.")
    if deepspeed and isinstance(deepspeed, str) and deepspeed not in DEEPSPEED_PRESETS and not deepspeed.endswith(".json"):
        add(messages, "warn", "deepspeed should be a built-in preset or a JSON config path.")
    if fsdp and str(fsdp) == "fsdp2" and as_bool(config.get("gradient_checkpointing")) is True:
        add(messages, "warn", "FSDP2 works better with activation_checkpointing in fsdp_config than ordinary gradient_checkpointing.")
    if config.get("deepspeed_autotp_size") and not deepspeed:
        add(messages, "error", "deepspeed_autotp_size requires deepspeed.")
    if config.get("deepspeed_autotp_size") and train_type not in {"", "full"}:
        add(messages, "warn", "deepspeed_autotp_size is intended for full-parameter fine-tuning.")

    gc_kwargs = config.get("gradient_checkpointing_kwargs")
    if gc_kwargs is not None:
        if isinstance(gc_kwargs, str):
            try:
                parsed = json.loads(gc_kwargs)
            except json.JSONDecodeError:
                add(messages, "error", "gradient_checkpointing_kwargs string must be valid JSON.")
            else:
                if not isinstance(parsed, dict):
                    add(messages, "error", "gradient_checkpointing_kwargs must decode to an object.")
        elif not isinstance(gc_kwargs, dict):
            add(messages, "error", "gradient_checkpointing_kwargs must be a mapping/object or JSON object string.")
    elif not deepspeed and not fsdp:
        add(messages, "info", "For DDP reducer errors, add gradient_checkpointing_kwargs: {use_reentrant: false}.")

    if as_bool(config.get("resume_only_model")) and not has_any(config, ["resume_from_checkpoint"]):
        add(messages, "warn", "resume_only_model has no effect without resume_from_checkpoint.")
    if has_any(config, ["resume_from_checkpoint"]) and has_any(config, ["adapters"]):
        add(messages, "warn", "resume_from_checkpoint restores training state; adapters only load adapter weights. Confirm both are intended.")
    if has_any(config, ["adapters"]) and not has_any(config, ["model"]):
        add(messages, "warn", "Adapter loading usually still needs the base model unless checkpoint args are intentionally loaded.")

    if as_bool(config.get("eval_use_evalscope")):
        add(messages, "warn", "eval_use_evalscope requires the optional evalscope dependency; install ms-swift[eval] or equivalent.")
    if config.get("report_to"):
        reports = {str(item).lower() for item in as_list(config.get("report_to"))}
        if "swanlab" in reports:
            add(messages, "warn", "report_to=swanlab requires the optional swanlab package and credentials/mode setup.")
        if "wandb" in reports:
            add(messages, "warn", "report_to=wandb requires the optional wandb package and login/offline setup.")

    env = config.get("ENV") if isinstance(config.get("ENV"), dict) else {}
    max_pixels = env.get("MAX_PIXELS", os.environ.get("MAX_PIXELS"))
    video_max_pixels = env.get("VIDEO_MAX_PIXELS", os.environ.get("VIDEO_MAX_PIXELS"))
    for key, value in [("MAX_PIXELS", max_pixels), ("VIDEO_MAX_PIXELS", video_max_pixels)]:
        if value is not None:
            parsed = number(value)
            if parsed is None or parsed <= 0:
                add(messages, "error", f"{key} must be a positive integer-like value.")
    if has_any(config, ["freeze_vit", "freeze_aligner", "vit_gradient_checkpointing"]) and not (max_pixels or video_max_pixels):
        add(messages, "info", "For multimodal training, set MAX_PIXELS/VIDEO_MAX_PIXELS explicitly when memory is tight.")

    use_hf = as_bool(config.get("use_hf"))
    model = str(config.get("model", ""))
    check_model = as_bool(config.get("check_model"))
    if model.startswith(("./", "../", "/")) and check_model is not False:
        add(messages, "info", "For trusted local/offline model paths, consider check_model=false.")
    if use_hf is None:
        add(messages, "info", "use_hf is not set; ms-swift defaults to ModelScope source behavior.")

    return messages


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an ms-swift training YAML/JSON config without loading models.")
    parser.add_argument("config", type=Path)
    parser.add_argument("--route", choices=["sft", "pt"], default="sft")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    config = load_config(args.config)
    messages = validate(config, args.route)
    counts = {"error": 0, "warn": 0, "info": 0}
    for level, text in messages:
        counts[level] += 1
        print(f"{level}: {text}")
    if not messages:
        print("ok: no high-risk issues found")
    print(f"summary: {counts['error']} error(s), {counts['warn']} warning(s), {counts['info']} info item(s)")
    if counts["error"]:
        return 2
    if args.strict and counts["warn"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
