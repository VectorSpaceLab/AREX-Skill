#!/usr/bin/env python3
"""Lightweight structural validator for Axolotl YAML configs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

VALID_TRAIN_ON_EOS = {"all", "turn", "last", "none"}
COMMON_SFT_TYPES = {
    "alpaca",
    "alpaca_chat",
    "chat_template",
    "completion",
    "context_qa",
    "gpteacher",
    "input_output",
    "oasst",
    "reflection",
    "stepwise_supervised",
}
PREFERENCE_RL_TYPES = {"dpo", "ipo", "orpo", "kto", "simpo", "gdpo"}


class ConfigError(ValueError):
    """Raised for expected user-facing config validation failures."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate common Axolotl config and dataset structure without importing "
            "Axolotl, loading models, downloading datasets, or writing files."
        )
    )
    parser.add_argument("config", help="Path to an Axolotl YAML config")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of a human-readable report.",
    )
    return parser.parse_args()


def strip_yaml_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(line):
        if escaped:
            escaped = False
            continue
        if character == "\\" and quote == '"':
            escaped = True
            continue
        if character in {"'", '"'}:
            if quote == character:
                quote = None
            elif quote is None:
                quote = character
        elif character == "#" and quote is None:
            return line[:index]
    return line


def parse_scalar(raw_value: str) -> Any:
    value = raw_value.strip()
    if value in {"", "null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value.startswith("[") and value.endswith("]"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            inner = value[1:-1].strip()
            if not inner:
                return []
            return [parse_scalar(item) for item in inner.split(",")]
    try:
        if any(marker in value for marker in (".", "e", "E")):
            return float(value)
        return int(value)
    except ValueError:
        return value


def split_key_value(content: str, line_number: int) -> tuple[str, str]:
    if ":" not in content:
        raise ConfigError(f"line {line_number}: expected key: value syntax")
    key, raw_value = content.split(":", 1)
    key = key.strip()
    if not key:
        raise ConfigError(f"line {line_number}: empty mapping key")
    return key, raw_value.strip()


def fallback_safe_load_yaml(text: str) -> Any:
    lines: list[tuple[int, str, int]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if "\t" in raw_line[: len(raw_line) - len(raw_line.lstrip())]:
            raise ConfigError(f"line {line_number}: tabs are not supported for indentation")
        stripped_comment = strip_yaml_comment(raw_line).rstrip()
        if not stripped_comment.strip():
            continue
        indent = len(stripped_comment) - len(stripped_comment.lstrip(" "))
        lines.append((indent, stripped_comment.lstrip(), line_number))

    def parse_block(position: int, indent: int) -> tuple[Any, int]:
        if position >= len(lines):
            return {}, position
        current_indent, current_content, _ = lines[position]
        if current_indent < indent:
            return {}, position
        if current_indent != indent:
            raise ConfigError(
                f"line {lines[position][2]}: unexpected indentation; expected {indent} spaces"
            )
        if current_content.startswith("- "):
            return parse_list(position, indent)
        return parse_mapping(position, indent)

    def parse_mapping(position: int, indent: int) -> tuple[dict[str, Any], int]:
        result: dict[str, Any] = {}
        while position < len(lines):
            current_indent, content, line_number = lines[position]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise ConfigError(f"line {line_number}: unexpected nested mapping")
            if content.startswith("- "):
                break
            key, raw_value = split_key_value(content, line_number)
            position += 1
            if raw_value:
                result[key] = parse_scalar(raw_value)
            elif position < len(lines) and lines[position][0] > indent:
                result[key], position = parse_block(position, lines[position][0])
            else:
                result[key] = None
        return result, position

    def parse_list(position: int, indent: int) -> tuple[list[Any], int]:
        result: list[Any] = []
        while position < len(lines):
            current_indent, content, line_number = lines[position]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise ConfigError(f"line {line_number}: unexpected nested list")
            if not content.startswith("- "):
                break
            item_text = content[2:].strip()
            position += 1
            if not item_text:
                if position < len(lines) and lines[position][0] > indent:
                    item, position = parse_block(position, lines[position][0])
                else:
                    item = None
            elif ":" in item_text and not item_text.startswith(('"', "'")):
                key, raw_value = split_key_value(item_text, line_number)
                item = {key: parse_scalar(raw_value) if raw_value else None}
                if not raw_value and position < len(lines) and lines[position][0] > indent:
                    item[key], position = parse_block(position, lines[position][0])
                if position < len(lines) and lines[position][0] > indent:
                    continuation, position = parse_block(position, lines[position][0])
                    if isinstance(continuation, dict):
                        item.update(continuation)
                    else:
                        raise ConfigError(
                            f"line {line_number}: list item mapping continuation must be a mapping"
                        )
            else:
                item = parse_scalar(item_text)
                if position < len(lines) and lines[position][0] > indent:
                    raise ConfigError(
                        f"line {line_number}: scalar list item cannot have nested content"
                    )
            result.append(item)
        return result, position

    if not lines:
        return None
    parsed, final_position = parse_block(0, lines[0][0])
    if final_position != len(lines):
        raise ConfigError(f"line {lines[final_position][2]}: could not parse remaining YAML")
    return parsed


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")
    if path.is_dir():
        raise ConfigError(f"expected a YAML file, got a directory: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        if yaml is not None:
            value = yaml.safe_load(text)
        else:
            value = fallback_safe_load_yaml(text)
    except Exception as exc:
        error_type = getattr(yaml, "YAMLError", ConfigError) if yaml is not None else ConfigError
        if isinstance(exc, error_type):
            raise ConfigError(f"invalid YAML: {exc}") from exc
        raise
    if value is None:
        raise ConfigError("config is empty")
    if not isinstance(value, dict):
        raise ConfigError("config root must be a YAML mapping/object")
    return value


def is_blank(value: Any) -> bool:
    return value is None or value == ""


def validate_dataset_entry(index: int, entry: Any, cfg: dict[str, Any], warnings: list[str], errors: list[str]) -> None:
    prefix = f"datasets[{index}]"
    if not isinstance(entry, dict):
        errors.append(f"{prefix} must be a mapping/object")
        return

    path = entry.get("path")
    ds_type = entry.get("type")
    if is_blank(path) and path != "synthetic":
        errors.append(f"{prefix}.path is required for normal dataset entries")

    if isinstance(ds_type, str) and ds_type.startswith("sharegpt"):
        errors.append(f"{prefix}.type uses deprecated sharegpt; migrate to type: chat_template")

    if ds_type == "chat_template" or (isinstance(ds_type, str) and ds_type.startswith("chat_template")):
        validate_chat_dataset(prefix, entry, cfg, warnings, errors)
    elif ds_type == "input_output":
        warnings.append(f"{prefix}: type input_output expects rows with a segments list of {{text, label}} objects")
    elif ds_type == "completion":
        if not entry.get("field"):
            warnings.append(f"{prefix}: type completion defaults to field: text when field is omitted")
    elif ds_type is None:
        warnings.append(
            f"{prefix}: empty type means pre-tokenized rows; require input_ids, attention_mask, labels"
        )
    elif isinstance(ds_type, dict):
        required_custom = ["format", "no_input_format"]
        missing = [field for field in required_custom if is_blank(ds_type.get(field))]
        if missing:
            warnings.append(f"{prefix}.type custom prompt is missing common fields: {', '.join(missing)}")
    elif isinstance(ds_type, str):
        base_type = ds_type.split(".", 1)[0]
        if base_type not in COMMON_SFT_TYPES and cfg.get("rl") not in PREFERENCE_RL_TYPES:
            warnings.append(f"{prefix}.type {ds_type!r} is not in this script's common SFT type list")
    else:
        errors.append(f"{prefix}.type must be a string, mapping, null, or omitted")

    for list_key in ("data_files",):
        value = entry.get(list_key)
        if value is not None and not isinstance(value, (str, list)):
            errors.append(f"{prefix}.{list_key} must be a string or list of strings")

    if "shards" in entry and "preprocess_shards" in entry:
        warnings.append(f"{prefix}: shards and preprocess_shards serve different purposes; do not use both casually")


def validate_chat_dataset(prefix: str, entry: dict[str, Any], cfg: dict[str, Any], warnings: list[str], errors: list[str]) -> None:
    mappings = entry.get("message_property_mappings")
    legacy_role = entry.get("message_field_role")
    legacy_content = entry.get("message_field_content")

    if mappings is not None:
        if not isinstance(mappings, dict):
            errors.append(f"{prefix}.message_property_mappings must be a mapping/object")
        else:
            for key in ("role", "content"):
                if is_blank(mappings.get(key)):
                    errors.append(f"{prefix}.message_property_mappings.{key} is required for explicit mappings")
    elif legacy_role or legacy_content:
        warnings.append(
            f"{prefix}: message_field_role/message_field_content are legacy; prefer message_property_mappings"
        )
    else:
        warnings.append(
            f"{prefix}: no message_property_mappings set; Axolotl defaults to role/content message keys"
        )

    if not entry.get("field_messages"):
        warnings.append(f"{prefix}: field_messages omitted; Axolotl defaults to messages")

    dataset_template = entry.get("chat_template")
    root_template = cfg.get("chat_template")
    jinja = entry.get("chat_template_jinja") or cfg.get("chat_template_jinja")
    if dataset_template == "jinja" and not jinja:
        errors.append(f"{prefix}: chat_template: jinja requires chat_template_jinja")
    if root_template == "jinja" and not jinja:
        errors.append("chat_template: jinja requires chat_template_jinja")
    if jinja and not (dataset_template or root_template):
        warnings.append("chat_template_jinja is set; Axolotl will infer jinja mode when chat_template is empty")
    if not dataset_template and not root_template:
        warnings.append(
            f"{prefix}: no chat_template override; tokenizer_default must exist on the tokenizer or preprocessing will fail"
        )

    roles_to_train = entry.get("roles_to_train", cfg.get("roles_to_train"))
    if roles_to_train is not None and not isinstance(roles_to_train, list):
        errors.append(f"{prefix}.roles_to_train must be a list when provided")

    train_on_eos = entry.get("train_on_eos", cfg.get("train_on_eos"))
    if train_on_eos is not None and train_on_eos not in VALID_TRAIN_ON_EOS:
        errors.append(
            f"{prefix}.train_on_eos must be one of {', '.join(sorted(VALID_TRAIN_ON_EOS))}"
        )

    roles = entry.get("roles")
    if roles is not None:
        if not isinstance(roles, dict):
            errors.append(f"{prefix}.roles must be a mapping of canonical role to source-role list")
        else:
            for target, sources in roles.items():
                if not isinstance(sources, list) or not all(isinstance(item, str) for item in sources):
                    errors.append(f"{prefix}.roles.{target} must be a list of strings")


def validate_pretraining_entry(index: int, entry: Any, cfg: dict[str, Any], warnings: list[str], errors: list[str]) -> None:
    prefix = f"pretraining_dataset[{index}]"
    if not isinstance(entry, dict):
        errors.append(f"{prefix} must be a mapping/object")
        return
    if is_blank(entry.get("path")):
        errors.append(f"{prefix}.path is required")
    if entry.get("type") not in (None, "pretrain"):
        warnings.append(f"{prefix}.type is usually pretrain")
    if is_blank(entry.get("text_column")):
        warnings.append(f"{prefix}.text_column omitted; Axolotl defaults to text")
    if not cfg.get("streaming"):
        warnings.append(
            "pretraining_dataset without explicit streaming: true is deprecated in current Axolotl behavior"
        )
    if is_blank(cfg.get("max_steps")):
        warnings.append("streaming pretraining configs should set max_steps")


def validate_top_level(cfg: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    datasets = cfg.get("datasets")
    pretraining_dataset = cfg.get("pretraining_dataset")

    if datasets is None and pretraining_dataset is None:
        errors.append("either datasets or pretraining_dataset is required")

    if datasets is not None and not isinstance(datasets, list):
        errors.append("datasets must be a list")
    if pretraining_dataset is not None and not isinstance(pretraining_dataset, list):
        errors.append("pretraining_dataset must be a list")

    if isinstance(datasets, list):
        if not datasets:
            errors.append("datasets must not be empty")
        for index, entry in enumerate(datasets):
            validate_dataset_entry(index, entry, cfg, warnings, errors)

    if isinstance(pretraining_dataset, list):
        if not pretraining_dataset:
            errors.append("pretraining_dataset must not be empty")
        for index, entry in enumerate(pretraining_dataset):
            validate_pretraining_entry(index, entry, cfg, warnings, errors)

    if datasets is not None and pretraining_dataset is not None:
        warnings.append("both datasets and pretraining_dataset are set; confirm this is intentional")

    batch_fields = ["micro_batch_size", "gradient_accumulation_steps", "batch_size"]
    present_batch_fields = [field for field in batch_fields if not is_blank(cfg.get(field))]
    if len(present_batch_fields) < 2:
        warnings.append(
            "Axolotl validation requires at least two of micro_batch_size, gradient_accumulation_steps, batch_size"
        )
    if not is_blank(cfg.get("gradient_accumulation_steps")) and not is_blank(cfg.get("batch_size")):
        warnings.append("set only one of gradient_accumulation_steps or batch_size in many training configs")

    if cfg.get("test_datasets") and cfg.get("val_set_size"):
        errors.append("non-zero val_set_size should not be used with test_datasets")

    if cfg.get("sample_packing"):
        if cfg.get("pad_to_sequence_len") is False:
            warnings.append("pad_to_sequence_len: true is recommended with sample_packing")
        if cfg.get("eval_table_size") and cfg.get("eval_sample_packing") is not False:
            errors.append(
                "eval_table_size and eval_sample_packing are not supported together with sample_packing; set eval_sample_packing: false"
            )
        if cfg.get("eval_sample_packing") is False and cfg.get("remove_unused_columns") is None:
            warnings.append(
                "when sample_packing and eval_sample_packing differ, Axolotl may set remove_unused_columns: false"
            )

    if cfg.get("skip_prepare_dataset"):
        warnings.append("skip_prepare_dataset is set; axolotl preprocess is usually not needed")
    if pretraining_dataset is not None:
        warnings.append("pretraining_dataset is set; axolotl preprocess is not the primary validation command")

    rl = cfg.get("rl")
    if rl and isinstance(datasets, list):
        if rl in PREFERENCE_RL_TYPES:
            warnings.append(f"rl: {rl} uses preference-style dataset semantics; route method-specific choices to preference-tuning")
        elif rl in {"grpo", "ebft"}:
            warnings.append(f"rl: {rl} reward/runtime choices belong in rl-and-rewards")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "has_datasets": isinstance(datasets, list),
            "datasets_count": len(datasets) if isinstance(datasets, list) else 0,
            "has_pretraining_dataset": isinstance(pretraining_dataset, list),
            "pretraining_dataset_count": len(pretraining_dataset) if isinstance(pretraining_dataset, list) else 0,
            "rl": rl,
            "sample_packing": bool(cfg.get("sample_packing")),
        },
    }


def print_human(report: dict[str, Any]) -> None:
    print("Axolotl config structural validation")
    print(f"ok: {str(report['ok']).lower()}")
    for key, value in report["summary"].items():
        print(f"{key}: {value}")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in report["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)


def main() -> int:
    args = parse_args()
    try:
        cfg = load_yaml(Path(args.config))
        report = validate_top_level(cfg)
    except ConfigError as exc:
        report = {
            "ok": False,
            "errors": [str(exc)],
            "warnings": [],
            "summary": {},
        }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
