#!/usr/bin/env python3
"""Validate a small Unsloth Core training config and optional local sample data.

The checker is intentionally lightweight: it reads YAML/JSON configs and small
local JSONL/JSON/text samples, reports warnings/errors, and never imports
Unsloth, downloads models, or starts training.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys
from typing import Any, Iterable

try:
    import yaml  # type: ignore
except Exception:  # PyYAML is optional for JSON-only usage.
    yaml = None

ALLOWED_LOADERS = {
    "FastLanguageModel",
    "FastModel",
    "FastVisionModel",
    "FastTextModel",
    "FastSentenceTransformer",
}

DEFAULT_ROLE_ALIASES = {
    "system": {"system", "developer"},
    "user": {"user", "human", "input"},
    "assistant": {"assistant", "gpt", "output", "model"},
}

DEFAULT_TEXT_FIELDS = ["text", "content", "message", "body", "description", "prompt"]


class Finding:
    def __init__(self, level: str, path: str, message: str) -> None:
        self.level = level
        self.path = path
        self.message = message

    def as_dict(self) -> dict[str, str]:
        return {"level": self.level, "path": self.path, "message": self.message}


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", "~"}:
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the small mapping/inline-list YAML subset used by recipe configs."""
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if "\t" in raw_line[: len(raw_line) - len(raw_line.lstrip())]:
            raise RuntimeError(f"Tabs are not supported in fallback YAML parser at line {line_number}.")
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if stripped.startswith("- "):
            raise RuntimeError(
                f"Block lists are not supported in fallback YAML parser at line {line_number}; use inline lists."
            )
        if ":" not in stripped:
            raise RuntimeError(f"Expected key: value at line {line_number}.")
        key, value = stripped.split(":", 1)
        key = key.strip()
        if not key:
            raise RuntimeError(f"Empty key at line {line_number}.")
        while indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value.strip() == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(value)
    return root


def load_config(path: pathlib.Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is not None:
            return yaml.safe_load(text)
        return parse_simple_yaml(text)
    return json.loads(text)


def as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def validate_config(config: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(config, dict):
        return [Finding("error", "$", "Config must be a mapping/object.")]

    model = as_mapping(config.get("model"))
    if not model:
        findings.append(Finding("error", "model", "Missing required model section."))
    model_name = model.get("name") or model.get("model_name")
    if not isinstance(model_name, str) or not model_name.strip():
        findings.append(Finding("error", "model.name", "Model name is required."))

    loader = model.get("loader", "FastLanguageModel")
    if loader not in ALLOWED_LOADERS:
        findings.append(
            Finding(
                "error",
                "model.loader",
                f"Loader should be one of {sorted(ALLOWED_LOADERS)}.",
            )
        )

    max_seq_length = model.get("max_seq_length", model.get("context_length"))
    if max_seq_length is not None and not (
        isinstance(max_seq_length, int) and not isinstance(max_seq_length, bool) and max_seq_length > 0
    ):
        findings.append(Finding("error", "model.max_seq_length", "max_seq_length must be a positive integer."))

    quant_flags = ["load_in_4bit", "load_in_8bit", "load_in_16bit", "load_in_fp8"]
    enabled_quant = [flag for flag in quant_flags if bool(model.get(flag, False))]
    if len(enabled_quant) > 1:
        findings.append(
            Finding("error", "model", f"Only one quantization flag may be enabled; found {enabled_quant}.")
        )

    full_finetuning = bool(model.get("full_finetuning", False))
    if full_finetuning and enabled_quant:
        findings.append(
            Finding(
                "error",
                "model.full_finetuning",
                "full_finetuning should not be combined with quantization flags.",
            )
        )
    if bool(model.get("trust_remote_code", False)):
        findings.append(
            Finding(
                "warning",
                "model.trust_remote_code",
                "trust_remote_code=true should be explicitly approved by the user.",
            )
        )

    lora = as_mapping(config.get("lora"))
    if full_finetuning and lora:
        findings.append(
            Finding("warning", "lora", "LoRA config is ignored for full finetuning recipes.")
        )
    if lora:
        rank = lora.get("r")
        if rank is not None and not (isinstance(rank, int) and not isinstance(rank, bool) and rank > 0):
            findings.append(Finding("error", "lora.r", "LoRA rank r must be a positive integer."))
        alpha = lora.get("lora_alpha")
        if alpha is not None and not positive_number(alpha):
            findings.append(Finding("error", "lora.lora_alpha", "lora_alpha must be positive."))
        dropout = lora.get("lora_dropout")
        if dropout is not None and not (
            isinstance(dropout, (int, float)) and not isinstance(dropout, bool) and 0 <= dropout <= 1
        ):
            findings.append(Finding("error", "lora.lora_dropout", "lora_dropout must be between 0 and 1."))
        modules_to_save = as_list(lora.get("modules_to_save"))
        invalid_modules_to_save = [m for m in modules_to_save if m not in {"embed_tokens", "lm_head"}]
        if invalid_modules_to_save:
            findings.append(
                Finding(
                    "error",
                    "lora.modules_to_save",
                    "Only embed_tokens and lm_head are supported in modules_to_save.",
                )
            )
        target_modules = lora.get("target_modules")
        if target_modules is not None and not isinstance(target_modules, (list, str)):
            findings.append(
                Finding("error", "lora.target_modules", "target_modules must be a string or list of strings.")
            )
        if isinstance(target_modules, list) and not all(isinstance(item, str) for item in target_modules):
            findings.append(Finding("error", "lora.target_modules", "Every target module must be a string."))
        last_n = lora.get("finetune_last_n_layers")
        if last_n is not None and not (isinstance(last_n, int) and not isinstance(last_n, bool) and last_n > 0):
            findings.append(
                Finding("error", "lora.finetune_last_n_layers", "finetune_last_n_layers must be a positive integer.")
            )

    data = as_mapping(config.get("data"))
    if data:
        data_format = data.get("format")
        if data_format is not None and data_format not in {
            "chat_jsonl",
            "sharegpt_jsonl",
            "text",
            "raw_text",
            "jsonl",
            "json",
            "csv",
            "vision",
        }:
            findings.append(Finding("warning", "data.format", "Unknown data format; validator will apply generic checks."))
        chunk_size = data.get("chunk_size")
        stride = data.get("stride")
        if chunk_size is not None and not (
            isinstance(chunk_size, int) and not isinstance(chunk_size, bool) and chunk_size > 0
        ):
            findings.append(Finding("error", "data.chunk_size", "chunk_size must be a positive integer."))
        if stride is not None and not (isinstance(stride, int) and not isinstance(stride, bool) and stride >= 0):
            findings.append(Finding("error", "data.stride", "stride must be a non-negative integer."))
        if isinstance(chunk_size, int) and isinstance(stride, int) and stride >= chunk_size:
            findings.append(Finding("error", "data.stride", "stride must be smaller than chunk_size."))

    training = as_mapping(config.get("training"))
    for key in ("per_device_train_batch_size", "gradient_accumulation_steps", "learning_rate"):
        value = training.get(key)
        if value is not None and not positive_number(value):
            findings.append(Finding("error", f"training.{key}", f"{key} must be positive."))
    max_steps = training.get("max_steps")
    num_epochs = training.get("num_train_epochs")
    if max_steps is not None and not positive_number(max_steps):
        findings.append(Finding("error", "training.max_steps", "max_steps must be positive when provided."))
    if num_epochs is not None and not positive_number(num_epochs):
        findings.append(Finding("error", "training.num_train_epochs", "num_train_epochs must be positive when provided."))
    if not training:
        findings.append(Finding("warning", "training", "No training section found; recipe may be incomplete."))

    if loader == "FastVisionModel" and data.get("format") not in {None, "vision"}:
        findings.append(
            Finding("warning", "data.format", "FastVisionModel recipes usually need vision/multimodal data checks.")
        )
    if loader == "FastSentenceTransformer" and model.get("load_in_4bit"):
        findings.append(
            Finding("warning", "model.load_in_4bit", "Sentence-transformer recipes default to 16-bit; confirm 4-bit support.")
        )

    return findings


def normalize_aliases(config: dict[str, Any]) -> dict[str, set[str]]:
    data = as_mapping(config.get("data"))
    raw = as_mapping(data.get("role_aliases"))
    aliases = {key: set(values) for key, values in DEFAULT_ROLE_ALIASES.items()}
    for canonical, values in raw.items():
        if canonical in aliases:
            aliases[canonical].update(str(v) for v in as_list(values))
    return aliases


def canonical_role(role: Any, aliases: dict[str, set[str]]) -> str | None:
    if not isinstance(role, str):
        return None
    role_lower = role.strip().lower()
    for canonical, values in aliases.items():
        if role_lower in values:
            return canonical
    return None


def iter_json_records(path: pathlib.Path, limit: int) -> Iterable[tuple[int, Any]]:
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if line_number > limit:
                    break
                stripped = line.strip()
                if not stripped:
                    continue
                yield line_number, json.loads(stripped)
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            for index, record in enumerate(data[:limit], start=1):
                yield index, record
        else:
            yield 1, data


def validate_chat_records(config: dict[str, Any], data_path: pathlib.Path, limit: int) -> list[Finding]:
    findings: list[Finding] = []
    data_cfg = as_mapping(config.get("data"))
    messages_field = data_cfg.get("messages_field") or (
        "conversations" if data_cfg.get("format") == "sharegpt_jsonl" else "messages"
    )
    role_field = data_cfg.get("role_field") or ("from" if messages_field == "conversations" else "role")
    content_field = data_cfg.get("content_field") or ("value" if messages_field == "conversations" else "content")
    aliases = normalize_aliases(config)

    try:
        rows = list(iter_json_records(data_path, limit))
    except Exception as exc:
        return [Finding("error", str(data_path), f"Could not parse JSON/JSONL: {type(exc).__name__}: {exc}")]

    if not rows:
        return [Finding("error", str(data_path), "No non-empty JSON records found.")]

    for row_number, record in rows:
        path_prefix = f"{data_path}:{row_number}"
        if not isinstance(record, dict):
            findings.append(Finding("error", path_prefix, "Record must be an object."))
            continue
        messages = record.get(messages_field)
        if not isinstance(messages, list) or not messages:
            findings.append(Finding("error", f"{path_prefix}.{messages_field}", "Messages field must be a non-empty list."))
            continue
        seen_user = False
        seen_assistant = False
        previous_role = None
        for index, message in enumerate(messages):
            message_path = f"{path_prefix}.{messages_field}[{index}]"
            if not isinstance(message, dict):
                findings.append(Finding("error", message_path, "Message must be an object."))
                continue
            role = canonical_role(message.get(role_field), aliases)
            if role is None:
                findings.append(
                    Finding("error", f"{message_path}.{role_field}", "Unknown or missing role after alias mapping.")
                )
                continue
            content = message.get(content_field)
            if not isinstance(content, str) or not content.strip():
                findings.append(Finding("error", f"{message_path}.{content_field}", "Content must be non-empty text."))
            if role == "user":
                seen_user = True
            if role == "assistant":
                seen_assistant = True
            if role in {"user", "assistant"} and previous_role == role:
                findings.append(
                    Finding("warning", message_path, f"Consecutive {role} messages may violate some chat templates.")
                )
            if role in {"user", "assistant"}:
                previous_role = role
        if not seen_user:
            findings.append(Finding("error", path_prefix, "Conversation has no user message."))
        if not seen_assistant:
            findings.append(Finding("error", path_prefix, "Conversation has no assistant message."))
    return findings


def validate_text_data(data_path: pathlib.Path, limit: int) -> list[Finding]:
    suffix = data_path.suffix.lower()
    findings: list[Finding] = []
    try:
        if suffix in {".txt", ".md"}:
            text = data_path.read_text(encoding="utf-8")
            if not text.strip():
                findings.append(Finding("error", str(data_path), "Text file is empty or whitespace-only."))
            elif len(text.strip()) < 10:
                findings.append(Finding("warning", str(data_path), "Text sample is very short."))
        elif suffix in {".json", ".jsonl"}:
            rows = list(iter_json_records(data_path, limit))
            if not rows:
                findings.append(Finding("error", str(data_path), "No JSON records found."))
            for row_number, record in rows:
                if not isinstance(record, dict):
                    findings.append(Finding("error", f"{data_path}:{row_number}", "Record must be an object."))
                    continue
                if not any(isinstance(record.get(field), str) and record.get(field).strip() for field in DEFAULT_TEXT_FIELDS):
                    findings.append(
                        Finding(
                            "error",
                            f"{data_path}:{row_number}",
                            f"Record needs one text field from {DEFAULT_TEXT_FIELDS}.",
                        )
                    )
        elif suffix == ".csv":
            with data_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                rows = []
                for index, row in enumerate(reader, start=1):
                    if index > limit:
                        break
                    rows.append((index, row))
                if not rows:
                    findings.append(Finding("error", str(data_path), "CSV has no data rows."))
                for row_number, row in rows:
                    if not any(row.get(field, "").strip() for field in DEFAULT_TEXT_FIELDS):
                        findings.append(
                            Finding(
                                "error",
                                f"{data_path}:{row_number}",
                                f"CSV row needs one text-like column from {DEFAULT_TEXT_FIELDS}.",
                            )
                        )
        else:
            findings.append(Finding("warning", str(data_path), "Unknown data extension; no structural data check applied."))
    except Exception as exc:
        findings.append(Finding("error", str(data_path), f"Could not read data: {type(exc).__name__}: {exc}"))
    return findings


def validate_data(config: dict[str, Any], data_path: pathlib.Path, limit: int) -> list[Finding]:
    data_cfg = as_mapping(config.get("data"))
    data_format = data_cfg.get("format")
    if data_format in {"chat_jsonl", "sharegpt_jsonl"}:
        return validate_chat_records(config, data_path, limit)
    if data_format in {"text", "raw_text", "jsonl", "json", "csv", None}:
        return validate_text_data(data_path, limit)
    if data_format == "vision":
        return [Finding("warning", str(data_path), "Vision records need project-specific path checks; only config was validated.")]
    return validate_text_data(data_path, limit)


def summarize(findings: list[Finding]) -> dict[str, Any]:
    errors = [finding for finding in findings if finding.level == "error"]
    warnings = [finding for finding in findings if finding.level == "warning"]
    return {
        "ok": not errors,
        "errors": len(errors),
        "warnings": len(warnings),
        "findings": [finding.as_dict() for finding in findings],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate an Unsloth Core YAML/JSON config and optional tiny local dataset sample.",
    )
    parser.add_argument("config", type=pathlib.Path, help="YAML or JSON config file to validate.")
    parser.add_argument("--data", type=pathlib.Path, help="Optional local sample data file to validate.")
    parser.add_argument("--max-records", type=int, default=20, help="Maximum JSON/CSV records to inspect.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    try:
        config = load_config(args.config)
    except Exception as exc:
        result = summarize([Finding("error", str(args.config), f"Could not read config: {type(exc).__name__}: {exc}")])
        print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
        return 2

    findings.extend(validate_config(config))
    if args.data is not None:
        if not args.data.exists():
            findings.append(Finding("error", str(args.data), "Data file does not exist."))
        elif not isinstance(config, dict):
            findings.append(Finding("error", str(args.data), "Cannot validate data because config is not an object."))
        else:
            findings.extend(validate_data(config, args.data, max(args.max_records, 1)))

    result = summarize(findings)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
