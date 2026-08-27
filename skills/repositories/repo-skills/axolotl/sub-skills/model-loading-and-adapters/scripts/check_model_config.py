#!/usr/bin/env python3
"""Static Axolotl model/adapter/quantization config checker.

This helper reads a local YAML file and reports likely model-loading, adapter,
quantization, multimodal, and attention issues. It intentionally does not import
Axolotl, load tokenizers/models/processors, download anything, train, or mutate
files.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - depends on host environment
    yaml = None

VERSION = "1.0.0"

CANONICAL_ATTN = {
    "eager",
    "sdpa",
    "flash_attention_2",
    "flash_attention_3",
    "flex_attention",
    "xformers",
    "sage",
    "s2",
    "fp8",
    "kernels-community/flash-attn3",
    "kernels-community/sage-attention",
}
LEGACY_ATTN = {
    "flash_attention": "flash_attention_2",
    "sdp_attention": "sdpa",
    "xformers_attention": "xformers",
    "flex_attention": "flex_attention",
    "sage_attention": "sage",
    "eager_attention": "eager",
}
PACKING_ATTN = {
    "flash_attention_2",
    "flash_attention_3",
    "flex_attention",
    "xformers",
    "sage",
    "s2",
    "kernels-community/flash-attn3",
    "kernels-community/sage-attention",
}
MULTIMODAL_HINTS = {
    "vl",
    "vision",
    "pixtral",
    "llava",
    "mllama",
    "llama-4",
    "llama4",
    "gemma-3",
    "gemma3",
    "gemma-4",
    "gemma4",
    "qwen2-vl",
    "qwen2.5-vl",
    "qwen3-vl",
    "qwen3.5",
    "mistral-small",
    "magistral",
    "voxtral",
    "internvl",
    "smolvlm",
    "lfm2-vl",
}
VLM_CHAT_TEMPLATES = {
    "gemma4",
    "gemma3",
    "gemma3n",
    "qwen2_vl",
    "qwen3_5",
    "llama3_2_vision",
    "llama4",
    "pixtral",
    "llava",
}
QAT_DTYPES = {"int4", "int8", "float8", "fp8", "float8_e4m3fn", "nvfp4", "mxfp4"}
PTQ_WEIGHT_DTYPES = {"int4", "int8", "fp8", "float8", "float8_e4m3fn", "nvfp4", "mxfp4"}
PTQ_ACTIVATION_DTYPES = {"int4", "int8", "float8", "fp8", "float8_e4m3fn"}


class Finding:
    def __init__(self, severity: str, message: str) -> None:
        self.severity = severity
        self.message = message


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Statically check an Axolotl YAML for model loading, adapter, "
            "quantization, multimodal, and attention-field issues."
        )
    )
    parser.add_argument("config", nargs="?", help="Path to an Axolotl YAML config")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when warnings are found, not only errors",
    )
    parser.add_argument(
        "--show-ok",
        action="store_true",
        help="Print informational passes in addition to warnings/errors",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    args = parser.parse_args(argv)
    if not args.config:
        parser.error("the following arguments are required: config")
    return args


def strip_comment(value: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_double:
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if char == "#" and not in_single and not in_double:
            return value[:index]
    return value


def split_inline_list(value: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    escaped = False
    for char in value:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\" and in_double:
            current.append(char)
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            current.append(char)
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            current.append(char)
            continue
        if char == "," and not in_single and not in_double:
            items.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if current:
        items.append("".join(current).strip())
    return items


def parse_scalar(value: str) -> Any:
    cleaned = strip_comment(value).strip()
    if cleaned in {"", "null", "Null", "NULL", "~"}:
        return None
    lowered = cleaned.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (
        cleaned.startswith("'") and cleaned.endswith("'")
    ):
        return cleaned[1:-1]
    if cleaned.startswith("[") and cleaned.endswith("]"):
        inner = cleaned[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part) for part in split_inline_list(inner)]
    if re.fullmatch(r"[-+]?\d+", cleaned):
        try:
            return int(cleaned)
        except ValueError:
            return cleaned
    if re.fullmatch(r"[-+]?(\d+\.\d*|\d*\.\d+)([eE][-+]?\d+)?", cleaned):
        try:
            return float(cleaned)
        except ValueError:
            return cleaned
    return cleaned


def parse_fallback_yaml(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        raw = lines[index]
        index += 1
        if not raw.strip() or raw.lstrip().startswith("#") or raw.strip() in {"---", "..."}:
            continue
        if raw.startswith((" ", "\t")):
            continue
        if ":" not in raw:
            continue
        key, remainder = raw.split(":", 1)
        key = key.strip()
        if not key:
            continue
        value_part = strip_comment(remainder).strip()
        if value_part:
            data[key] = parse_scalar(value_part)
            continue

        child_lines: list[str] = []
        while index < len(lines):
            candidate = lines[index]
            if not candidate.strip() or candidate.lstrip().startswith("#"):
                index += 1
                continue
            if not candidate.startswith((" ", "\t")):
                break
            child_lines.append(candidate)
            index += 1
        data[key] = parse_fallback_block(child_lines)
    return data


def parse_fallback_block(lines: list[str]) -> Any:
    useful = [line for line in lines if strip_comment(line).strip()]
    if not useful:
        return None
    min_indent = min(len(line) - len(line.lstrip(" ")) for line in useful)
    normalized = [line[min_indent:] if len(line) >= min_indent else line for line in useful]
    if all(line.lstrip().startswith("-") for line in normalized):
        result: list[Any] = []
        current_map: dict[str, Any] | None = None
        current_key: str | None = None
        for line in normalized:
            stripped = strip_comment(line).strip()
            if not stripped:
                continue
            if stripped.startswith("-"):
                content = stripped[1:].strip()
                current_key = None
                if not content:
                    current_map = {}
                    result.append(current_map)
                elif ":" in content:
                    item_key, item_value = content.split(":", 1)
                    current_map = {item_key.strip(): parse_scalar(item_value)}
                    result.append(current_map)
                    current_key = item_key.strip() if strip_comment(item_value).strip() == "" else None
                else:
                    current_map = None
                    result.append(parse_scalar(content))
                continue
            if current_map is not None and ":" in stripped:
                child_key, child_value = stripped.split(":", 1)
                current_map[child_key.strip()] = parse_scalar(child_value)
                current_key = child_key.strip() if strip_comment(child_value).strip() == "" else None
            elif current_map is not None and current_key:
                current_map[current_key] = as_list(current_map.get(current_key)) + [parse_scalar(stripped.lstrip("- "))]
        return result

    mapping: dict[str, Any] = {}
    last_key: str | None = None
    for line in normalized:
        stripped = strip_comment(line).strip()
        if not stripped:
            continue
        if stripped.startswith("-") and last_key:
            mapping[last_key] = as_list(mapping.get(last_key)) + [parse_scalar(stripped[1:].strip())]
        elif ":" in stripped:
            child_key, child_value = stripped.split(":", 1)
            mapping[child_key.strip()] = parse_scalar(child_value)
            last_key = child_key.strip() if strip_comment(child_value).strip() == "" else None
    return mapping


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError(f"config file not found: {path}") from exc
    if yaml is not None:
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:  # type: ignore[union-attr]
            raise RuntimeError(f"could not parse YAML: {exc}") from exc
    else:
        data = parse_fallback_yaml(text)
    if data is None:
        raise RuntimeError("config YAML is empty")
    if not isinstance(data, dict):
        raise RuntimeError("config YAML must be a mapping at the top level")
    return data


def as_bool(data: dict[str, Any], key: str) -> bool:
    return data.get(key) is True


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def model_text(data: dict[str, Any]) -> str:
    parts = [
        data.get("base_model"),
        data.get("base_model_config"),
        data.get("tokenizer_config"),
        data.get("processor_type"),
        data.get("chat_template"),
    ]
    return " ".join(str(part).lower() for part in parts if part)


def looks_multimodal(data: dict[str, Any]) -> bool:
    text = model_text(data)
    if bool(data.get("processor_type")):
        return True
    if "qwen3.5" in text and not any(token in text for token in ("vl", "vision")):
        text = text.replace("qwen3.5", "")
    return any(hint in text for hint in MULTIMODAL_HINTS)


def looks_gemma4(data: dict[str, Any]) -> bool:
    text = model_text(data)
    return "gemma4" in text or "gemma-4" in text


def looks_moe(data: dict[str, Any]) -> bool:
    text = model_text(data)
    return any(token in text for token in ("moe", "a3b", "a4b", "a10b", "mixtral")) or bool(
        data.get("lora_target_parameters")
    )


def is_hub_kernel(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value))


def add(findings: list[Finding], severity: str, message: str) -> None:
    findings.append(Finding(severity, message))


def check_required(data: dict[str, Any], findings: list[Finding]) -> None:
    if not has_text(data.get("base_model")):
        add(findings, "ERROR", "Missing required `base_model`.")
    if not data.get("datasets") and not data.get("pretraining_dataset"):
        add(
            findings,
            "WARN",
            "No `datasets` or `pretraining_dataset` found; model checks can still run, but Axolotl training/preprocess usually needs data.",
        )
    if not has_text(data.get("output_dir")):
        add(findings, "WARN", "No `output_dir` set; most Axolotl workflows expect one.")


def check_attention(data: dict[str, Any], findings: list[Finding]) -> None:
    legacy_set = [key for key in LEGACY_ATTN if data.get(key) is True]
    attn = data.get("attn_implementation")
    if legacy_set and attn:
        add(
            findings,
            "ERROR",
            f"Do not combine `attn_implementation` with legacy attention flags {legacy_set}; keep only the canonical field.",
        )
    elif legacy_set:
        mapped = [f"{key}->{LEGACY_ATTN[key]}" for key in legacy_set]
        add(
            findings,
            "WARN",
            "Legacy attention flag(s) are deprecated; use `attn_implementation`: "
            + ", ".join(mapped),
        )
    if attn:
        if not isinstance(attn, str):
            add(findings, "ERROR", "`attn_implementation` must be a string.")
        elif attn in {"flash", "fa2", "flex", "sdp"}:
            add(
                findings,
                "ERROR",
                f"Short attention alias `{attn}` is not accepted; use a canonical value such as `flash_attention_2`, `flex_attention`, or `sdpa`.",
            )
        elif attn not in CANONICAL_ATTN and not is_hub_kernel(attn):
            add(findings, "ERROR", f"Unrecognized `attn_implementation`: {attn!r}.")
    effective_attn = attn if isinstance(attn, str) else None
    if not effective_attn and legacy_set:
        effective_attn = LEGACY_ATTN[legacy_set[0]]
    if data.get("gemma4_hybrid_attn_impl") and effective_attn not in (None, "flash_attention_2"):
        add(
            findings,
            "ERROR",
            "`gemma4_hybrid_attn_impl: true` requires `attn_implementation: flash_attention_2`.",
        )
    if data.get("scaling_softmax") and effective_attn != "flex_attention":
        add(findings, "ERROR", "`scaling_softmax` requires `attn_implementation: flex_attention`.")
    if data.get("sample_packing") and effective_attn in {"eager", "sdpa"}:
        add(
            findings,
            "WARN",
            f"`sample_packing: true` with `{effective_attn}` may not isolate packed samples; use a packing-capable backend or disable packing.",
        )
    if data.get("sample_packing") and not effective_attn:
        add(
            findings,
            "WARN",
            "`sample_packing: true` is set without `attn_implementation`; verify Axolotl selects a packing-safe backend.",
        )


def check_adapters(data: dict[str, Any], findings: list[Finding]) -> None:
    adapter = data.get("adapter")
    load4 = as_bool(data, "load_in_4bit")
    load8 = as_bool(data, "load_in_8bit")
    if adapter == "qlora":
        if not load4:
            add(findings, "ERROR", "`adapter: qlora` requires `load_in_4bit: true`.")
        if load8:
            add(findings, "ERROR", "QLoRA cannot be loaded in 8-bit; remove `load_in_8bit`.")
        if data.get("gptq"):
            add(findings, "ERROR", "QLoRA is incompatible with `gptq: true` in normal training configs.")
    if not adapter and (load4 or load8):
        add(
            findings,
            "ERROR",
            "`load_in_4bit`/`load_in_8bit` training requires an adapter such as `lora` or `qlora`; full fine-tuning should disable low-bit loading.",
        )
    if adapter and adapter not in {"lora", "qlora", "llama-adapter"}:
        if not data.get("plugins"):
            add(
                findings,
                "WARN",
                f"Adapter {adapter!r} is not built in; include the plugin that registers it in `plugins:`.",
            )
    if data.get("lora_target_parameters") and as_float(data.get("lora_dropout")) != 0:
        add(findings, "ERROR", "`lora_target_parameters` requires `lora_dropout: 0`.")
    if data.get("quantize_moe_experts"):
        if adapter not in {"lora", "qlora"}:
            add(findings, "ERROR", "`quantize_moe_experts` requires `adapter: lora` or `adapter: qlora`.")
        if not (load4 or load8):
            add(findings, "ERROR", "`quantize_moe_experts` requires `load_in_4bit: true` or `load_in_8bit: true`.")
        if data.get("lora_target_linear"):
            add(findings, "ERROR", "`quantize_moe_experts` is incompatible with `lora_target_linear: true`; use explicit targets.")
    if data.get("trust_remote_code") and any(
        data.get(key) for key in ("lora_mlp_kernel", "lora_qkv_kernel", "lora_o_kernel")
    ):
        add(findings, "ERROR", "LoRA kernel flags are not compatible with `trust_remote_code: true`.")
    if looks_multimodal(data) and data.get("lora_target_linear"):
        add(
            findings,
            "WARN",
            "`lora_target_linear: true` is risky for multimodal models; prefer language-backbone `lora_target_modules` regex/list targets.",
        )
    if looks_moe(data) and data.get("lora_target_linear"):
        add(
            findings,
            "WARN",
            "MoE configs often need explicit `lora_target_modules` and/or `lora_target_parameters`; broad linear targeting can miss routed expert tensors or hit wrong modules.",
        )
    if data.get("merge_lora") and adapter == "qlora" and (load4 or load8 or data.get("gptq")):
        add(
            findings,
            "ERROR",
            "Do not merge a QLoRA adapter while 4-bit/8-bit/GPTQ loading is enabled; use an Axolotl merge config that loads merge-compatible weights.",
        )


def check_multimodal(data: dict[str, Any], findings: list[Finding]) -> None:
    multimodal = looks_multimodal(data)
    if not multimodal:
        return
    if not data.get("processor_type"):
        add(
            findings,
            "WARN",
            "Model name/template looks multimodal but `processor_type` is unset; most VLM configs need `processor_type: AutoProcessor` or a family-specific processor.",
        )
    if data.get("sample_packing"):
        add(findings, "WARN", "Most multimodal/VLM configs should use `sample_packing: false`.")
    if data.get("remove_unused_columns") is not False:
        add(findings, "WARN", "Multimodal configs usually need `remove_unused_columns: false` to preserve image/audio fields.")
    if data.get("skip_prepare_dataset") is not True:
        add(findings, "WARN", "Multimodal configs usually need `skip_prepare_dataset: true`.")
    if not data.get("chat_template"):
        add(findings, "WARN", "Multimodal chat configs usually need an explicit model-appropriate `chat_template`.")
    elif data.get("chat_template") not in VLM_CHAT_TEMPLATES:
        add(
            findings,
            "INFO",
            f"`chat_template: {data.get('chat_template')}` is not in this helper's common VLM template list; verify it is intentional.",
        )
    if looks_gemma4(data):
        if not data.get("freeze_mm_modules"):
            add(
                findings,
                "WARN",
                "Gemma 4 loads as a multimodal wrapper; set `freeze_mm_modules: true` for text-only or language-model-only adapter training.",
            )
        targets = " ".join(str(item) for item in as_list(data.get("lora_target_modules")))
        if data.get("adapter") and "language_model" not in targets:
            add(
                findings,
                "WARN",
                "Gemma 4 adapter configs should usually restrict LoRA targets to the language model backbone.",
            )
        if data.get("gradient_checkpointing") and as_mapping(data.get("gradient_checkpointing_kwargs")).get("use_reentrant") is not False:
            add(
                findings,
                "WARN",
                "Gemma 4 gradient checkpointing should use `gradient_checkpointing_kwargs: {use_reentrant: false}`; Axolotl may auto-adjust during normalization.",
            )


def check_quantization(data: dict[str, Any], findings: list[Finding]) -> None:
    if data.get("model_quantization_config") and data.get("model_quantization_config") not in {
        "Mxfp4Config",
        "FineGrainedFP8Config",
    }:
        add(
            findings,
            "ERROR",
            "`model_quantization_config` must be `Mxfp4Config` or `FineGrainedFP8Config`.",
        )
    qat = data.get("qat")
    if qat is not None:
        if not isinstance(qat, dict):
            add(findings, "ERROR", "`qat` must be a mapping.")
        else:
            for key in ("activation_dtype", "weight_dtype"):
                value = qat.get(key)
                if value is not None and str(value) not in QAT_DTYPES:
                    add(findings, "ERROR", f"Unsupported `qat.{key}` value: {value!r}.")
    quant = data.get("quantization")
    if quant is not None:
        if not isinstance(quant, dict):
            add(findings, "ERROR", "`quantization` must be a mapping.")
        else:
            weight = quant.get("weight_dtype")
            activation = quant.get("activation_dtype")
            if weight is not None and str(weight) not in PTQ_WEIGHT_DTYPES:
                add(findings, "ERROR", f"Unsupported `quantization.weight_dtype` value: {weight!r}.")
            if activation is not None and str(activation) not in PTQ_ACTIVATION_DTYPES:
                add(findings, "ERROR", f"Unsupported `quantization.activation_dtype` value: {activation!r}.")
    if qat and quant:
        add(
            findings,
            "INFO",
            "Both `qat` and `quantization` are present; ensure this is deliberate because QAT training and PTQ/quantize workflows are distinct.",
        )


def check_datasets_for_template(data: dict[str, Any], findings: list[Finding]) -> None:
    chat_template = data.get("chat_template")
    datasets = data.get("datasets") or []
    if isinstance(datasets, dict):
        datasets = [datasets]
    if chat_template and isinstance(datasets, list):
        for index, dataset in enumerate(datasets):
            if not isinstance(dataset, dict):
                continue
            dtype = dataset.get("type")
            if dtype and "chat_template" in str(dtype) and dataset.get("chat_template") not in (None, chat_template):
                add(
                    findings,
                    "WARN",
                    f"Dataset #{index} has `type: {dtype}` and a different dataset-level `chat_template`; verify the override is intentional.",
                )


def run_checks(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    check_required(data, findings)
    check_attention(data, findings)
    check_adapters(data, findings)
    check_multimodal(data, findings)
    check_quantization(data, findings)
    check_datasets_for_template(data, findings)
    if not any(item.severity in {"ERROR", "WARN"} for item in findings):
        add(findings, "INFO", "No static model-loading or adapter issues found by this helper.")
    return findings


def print_findings(findings: list[Finding], show_ok: bool) -> None:
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for item in sorted(findings, key=lambda found: order.get(found.severity, 9)):
        if item.severity == "INFO" and not show_ok:
            continue
        print(f"{item.severity}: {item.message}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        data = load_yaml(Path(args.config))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    findings = run_checks(data)
    print_findings(findings, args.show_ok)
    has_error = any(item.severity == "ERROR" for item in findings)
    has_warn = any(item.severity == "WARN" for item in findings)
    if has_error or (args.strict and has_warn):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
