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

"""Static preflight checks for LlamaFactory export YAML/JSON configs.

This helper intentionally does not import LlamaFactory, Transformers, PyTorch, or
other ML dependencies. It catches common config pitfalls before a user runs a
large model export, adapter merge, quantization, or hub push.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


EXPORT_KEYS = {
    "export_dir",
    "export_size",
    "export_device",
    "export_quantization_bit",
    "export_quantization_dataset",
    "export_quantization_nsamples",
    "export_quantization_maxlen",
    "export_legacy_format",
    "export_hub_model_id",
}

TRAINING_HINT_KEYS = {
    "do_train",
    "stage",
    "output_dir",
    "per_device_train_batch_size",
    "gradient_accumulation_steps",
    "learning_rate",
    "num_train_epochs",
    "max_steps",
}

SUPPORTED_EXPORT_QUANT_BITS = {2, 3, 4, 8}
SUPPORTED_OTF_QUANT = {
    "bnb": {4, 8},
    "hqq": {1, 2, 3, 4, 5, 6, 8},
    "eetq": {8},
}


class ConfigError(ValueError):
    """Raised when the input config cannot be parsed."""


def _strip_inline_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    result: list[str] = []
    for char in line:
        if escaped:
            result.append(char)
            escaped = False
            continue
        if char == "\\" and in_double:
            result.append(char)
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            result.append(char)
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            result.append(char)
            continue
        if char == "#" and not in_single and not in_double:
            break
        result.append(char)
    return "".join(result).strip()


def _parse_scalar(raw_value: str) -> Any:
    value = raw_value.strip()
    if value == "":
        return ""
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") or value.startswith("{"):
        try:
            return json.loads(value.replace("'", '"'))
        except json.JSONDecodeError:
            return value
    try:
        if any(marker in value for marker in (".", "e", "E")):
            return float(value)
        return int(value)
    except ValueError:
        return value


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[Any] | None = None

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line[:1].isspace() and current_list is not None:
            stripped = _strip_inline_comment(raw_line)
            if stripped.startswith("-"):
                current_list.append(_parse_scalar(stripped[1:].strip()))
            continue
        current_key = None
        current_list = None
        line = _strip_inline_comment(raw_line)
        if not line:
            continue
        if ":" not in line:
            raise ConfigError(f"Cannot parse YAML line {line_number}: {raw_line}")
        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            raise ConfigError(f"Empty YAML key on line {line_number}.")
        value = value.strip()
        if value == "":
            current_key = key
            current_list = []
            data[current_key] = current_list
        else:
            data[key] = _parse_scalar(value)
    return data


def load_config(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Cannot read {path}: {exc}") from exc

    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Invalid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ConfigError("Top-level JSON value must be an object.")
        return parsed

    try:
        import yaml  # type: ignore
    except ImportError:
        parsed = _parse_simple_yaml(text)
    else:
        try:
            parsed = yaml.safe_load(text)
        except Exception as exc:  # pragma: no cover - depends on optional PyYAML
            raise ConfigError(f"Invalid YAML: {exc}") from exc
        if parsed is None:
            parsed = {}
        if not isinstance(parsed, dict):
            raise ConfigError("Top-level YAML value must be a mapping.")
    return parsed


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _present(config: dict[str, Any], key: str) -> bool:
    value = config.get(key)
    return value is not None and value != ""


def _adapter_count(value: Any) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, list):
        return len(value)
    if isinstance(value, str):
        return len([part for part in value.split(",") if part.strip()])
    return 1


def check_config(config: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not _present(config, "model_name_or_path"):
        errors.append("Missing required `model_name_or_path`.")

    if not _present(config, "export_dir"):
        errors.append("Missing required `export_dir` for `llamafactory-cli export`.")

    export_quant_bit = _as_int(config.get("export_quantization_bit"))
    quant_bit = _as_int(config.get("quantization_bit"))
    quant_method = str(config.get("quantization_method", "bnb")).lower()
    adapter_count = _adapter_count(config.get("adapter_name_or_path"))

    if export_quant_bit is not None:
        if export_quant_bit not in SUPPORTED_EXPORT_QUANT_BITS:
            errors.append("`export_quantization_bit` must be one of 2, 3, 4, or 8.")
        if not _present(config, "export_quantization_dataset"):
            errors.append("`export_quantization_dataset` is required when `export_quantization_bit` is set.")
        if adapter_count:
            errors.append(
                "Do not combine `adapter_name_or_path` with `export_quantization_bit`; "
                "merge adapters first, then quantize the merged export."
            )
        warnings.append("Export-time quantization requires Optimum and GPTQModel, a calibration dataset with `text`, and substantial compute.")

    if quant_bit is not None:
        allowed_bits = SUPPORTED_OTF_QUANT.get(quant_method)
        if allowed_bits is None:
            errors.append("`quantization_method` must be one of bnb, hqq, or eetq for on-the-fly quantization.")
        elif quant_bit not in allowed_bits:
            errors.append(f"`quantization_method: {quant_method}` does not support `quantization_bit: {quant_bit}`.")
        if adapter_count and any(key in config for key in EXPORT_KEYS):
            warnings.append(
                "A config with `quantization_bit`, `adapter_name_or_path`, and export fields may try to merge into a "
                "quantized model; use an unquantized merge export first."
            )

    if adapter_count > 1:
        warnings.append(
            "Multiple adapters are only mergeable in some paths; quantized, ZeRO-3, KTransformers, and Unsloth paths "
            "generally restrict adapter handling to one adapter."
        )

    if config.get("use_dora") is True and quant_bit is not None and quant_method != "bnb":
        errors.append("DoRA is not compatible with PTQ/non-bitsandbytes quantized model paths.")

    if config.get("resize_vocab") is True and quant_bit is not None:
        warnings.append("`resize_vocab: true` with quantization is risky; resize/tokenizer-finalize before quantizing when possible.")

    export_device = config.get("export_device")
    if export_device is not None and export_device not in {"cpu", "auto"}:
        errors.append("`export_device` must be `cpu` or `auto`.")

    export_size = _as_int(config.get("export_size"))
    if export_size is not None and export_size <= 0:
        errors.append("`export_size` must be a positive integer shard size in GB.")

    if _present(config, "export_hub_model_id"):
        warnings.append("`export_hub_model_id` will push artifacts to the Hugging Face Hub; confirm repo and token source before running.")

    if any(key in config for key in TRAINING_HINT_KEYS):
        warnings.append("Training keys are present in this export config; verify this is not a training YAML used accidentally.")

    if config.get("trust_remote_code") is True:
        warnings.append("`trust_remote_code: true` executes model repository code; use only for trusted sources.")

    if _present(config, "hf_hub_token") or _present(config, "ms_hub_token") or _present(config, "om_hub_token"):
        warnings.append("Hub token fields appear in the config; prefer environment/secret injection over checked-in tokens.")

    if export_quant_bit is None and _present(config, "export_quantization_dataset"):
        warnings.append("`export_quantization_dataset` is set but `export_quantization_bit` is missing; the dataset will not drive export quantization.")

    if quant_bit is not None and export_quant_bit is not None:
        warnings.append("Both `quantization_bit` and `export_quantization_bit` are set; these are different modes and rarely belong together.")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="YAML or JSON export config to check")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        errors, warnings = check_config(config)
    except ConfigError as exc:
        if args.json:
            print(json.dumps({"ok": False, "errors": [str(exc)], "warnings": []}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    ok = not errors
    if args.json:
        print(json.dumps({"ok": ok, "errors": errors, "warnings": warnings}, indent=2))
    else:
        if ok:
            print("OK: no blocking export config errors found.")
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARN: {warning}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
