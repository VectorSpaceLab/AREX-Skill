#!/usr/bin/env python3
"""Static checker for NeMo SpeechLM2 YAML/JSON-like configs.

The checker is safe by default: it reads text, optionally parses JSON, applies
simple YAML-ish regex checks, and never imports NeMo, downloads models, starts
CUDA, mutates checkpoints, or writes outputs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_MISSING = object()


def _strip_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        in_single = False
        in_double = False
        escaped = False
        cut = len(line)
        for index, char in enumerate(line):
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
                cut = index
                break
        lines.append(line[:cut])
    return "\n".join(lines)


def _try_json(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return _MISSING


def _literal(value: str) -> Any:
    value = value.strip()
    if not value or value in {"???", "..."}:
        return value
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_literal(part) for part in re.split(r"\s*,\s*", inner)]
    try:
        if re.fullmatch(r"[-+]?\d+", value):
            return int(value)
        if re.fullmatch(r"[-+]?(\d+\.\d*|\d*\.\d+)([eE][-+]?\d+)?", value):
            return float(value)
    except Exception:
        pass
    return value


def _yamlish_map(text: str) -> dict[str, Any]:
    stripped = _strip_comments(text)
    result: dict[str, Any] = {}
    stack: list[tuple[int, str]] = []

    for raw_line in stripped.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("-"):
            match = re.match(r"^(\s*)-\s*([A-Za-z0-9_\-.]+)\s*:\s*(.*?)\s*$", raw_line)
            if not match:
                continue
            indent = len(match.group(1)) + 2
            key = match.group(2)
            value = match.group(3)
        else:
            match = re.match(r"^(\s*)([A-Za-z0-9_\-.]+)\s*:\s*(.*?)\s*$", raw_line)
            if not match:
                continue
            indent = len(match.group(1))
            key = match.group(2)
            value = match.group(3)

        while stack and stack[-1][0] >= indent:
            stack.pop()
        path = ".".join([item[1] for item in stack] + [key])
        if value == "":
            stack.append((indent, key))
            result.setdefault(path, {})
        else:
            result[path] = _literal(value)
    return result


def _flatten_json(obj: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(obj, dict):
        items = {}
        for key, value in obj.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            items.update(_flatten_json(value, child))
        return items
    if isinstance(obj, list):
        items = {prefix: obj}
        for index, value in enumerate(obj):
            child = f"{prefix}.{index}" if prefix else str(index)
            items.update(_flatten_json(value, child))
        return items
    return {prefix: obj}


def _load_fields(text: str) -> dict[str, Any]:
    parsed = _try_json(text)
    if parsed is not _MISSING:
        return _flatten_json(parsed)
    return _yamlish_map(text)


def _get(fields: dict[str, Any], path: str, default: Any = _MISSING) -> Any:
    return fields.get(path, default)


def _has_prefix(fields: dict[str, Any], prefix: str) -> bool:
    prefix_dot = f"{prefix}."
    return any(key == prefix or key.startswith(prefix_dot) for key in fields)


def _truthy(value: Any) -> bool:
    if value is _MISSING:
        return False
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "yes", "1", "on"}


def _number(value: Any, default: int = 1) -> int:
    if value is _MISSING or value is None:
        return default
    try:
        return int(value)
    except Exception:
        return default


def _contains_unresolved(text: str) -> bool:
    return bool(re.search(r"(^|[:\s])\?\?\?(\s|$)", _strip_comments(text)))


def _path_values(fields: dict[str, Any]) -> list[tuple[str, str]]:
    pathish = re.compile(r"(path|dir|file|shar|manifest|checkpoint|ckpt|output|out_dir|reference)", re.I)
    values = []
    for key, value in fields.items():
        if pathish.search(key) and isinstance(value, str) and value not in {"", "???"}:
            values.append((key, value))
    return values


def _warn_absolute_private_paths(fields: dict[str, Any]) -> list[str]:
    warnings = []
    private_prefix = re.compile(r"^/(?:home|root|lustre|workspace|tmp)/")
    for key, value in _path_values(fields):
        if private_prefix.match(value):
            warnings.append(f"{key} uses an absolute machine-specific path: {value}")
    return warnings


def check_config(path: Path) -> tuple[list[str], list[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    fields = _load_fields(text)
    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    if not fields:
        errors.append("Could not parse any YAML/JSON-like key/value fields.")
        return errors, warnings, notes

    if _contains_unresolved(text):
        errors.append("Config still contains unresolved Hydra placeholder '???'.")

    has_model = _has_prefix(fields, "model")
    has_trainer = _has_prefix(fields, "trainer")
    has_data = _has_prefix(fields, "data")
    has_voicechat_root = _has_prefix(fields, "checkpoint_path") and _has_prefix(fields, "model.stt")

    if not has_model:
        errors.append("Missing top-level model section.")
    if not has_trainer and not has_voicechat_root:
        warnings.append("No top-level trainer section found; this is unusual outside pure conversion configs.")
    if not has_data and not has_voicechat_root:
        warnings.append("No top-level data section found; training/evaluation configs usually need it.")

    use_nemo_automodel = _truthy(_get(fields, "model.use_nemo_automodel"))
    strategy_target = str(_get(fields, "trainer.strategy._target_", ""))
    tp_size = _number(_get(fields, "trainer.strategy.tp_size"), 1)
    pp_size = _number(_get(fields, "trainer.strategy.pp_size"), 1)
    cp_size = _number(_get(fields, "trainer.strategy.cp_size"), 1)
    ep_size = _number(_get(fields, "trainer.strategy.ep_size"), 1)
    distributed_requested = any(size > 1 for size in (tp_size, pp_size, cp_size, ep_size))

    if distributed_requested and not use_nemo_automodel:
        errors.append(
            "Distributed SpeechLM2 inference/training sizes are set but model.use_nemo_automodel is not true; use SALMAutomodel."
        )
    if use_nemo_automodel and "AutomodelParallelStrategy" not in strategy_target and has_trainer:
        warnings.append("model.use_nemo_automodel is true but trainer.strategy._target_ is not AutomodelParallelStrategy.")

    packed = _truthy(_get(fields, "model.packed_sequences"))
    attn_backend = _get(fields, "model.automodel_backend.attn", "te" if packed else _MISSING)
    if cp_size > 1 and not packed:
        errors.append("SALMAutomodel with cp_size > 1 requires model.packed_sequences: true.")
    if packed and attn_backend != "te":
        errors.append("model.packed_sequences: true requires model.automodel_backend.attn: te.")
    if packed:
        warnings.append("For packed TE attention, set NVTE_FUSED_ATTN=0 when THD gradients are unstable or on Blackwell sm_120.")

    audio_tag = _get(fields, "model.audio_locator_tag")
    if has_model and audio_tag is _MISSING and not has_voicechat_root:
        warnings.append("model.audio_locator_tag is missing; SALM/vLLM workflows require an explicit audio placeholder token.")
    if audio_tag not in (_MISSING, None, "<|audio|>") and "vllm" in text.lower():
        errors.append("vLLM SpeechLM plugin currently supports only audio_locator_tag '<|audio|>'.")

    if _has_prefix(fields, "model.lora") and use_nemo_automodel:
        if _get(fields, "model.lora.r") is not _MISSING or _get(fields, "model.lora.lora_alpha") is not _MISSING:
            warnings.append("SALMAutomodel LoRA uses Automodel keys such as dim/alpha, not HF PEFT r/lora_alpha.")
    if _has_prefix(fields, "model.lora") and not use_nemo_automodel:
        if _get(fields, "model.lora.dim") is not _MISSING or _get(fields, "model.lora.alpha") is not _MISSING:
            warnings.append("Classic SALM LoRA usually uses HF PEFT keys such as r/lora_alpha, not Automodel dim/alpha.")

    for required in ("model.pretrained_llm", "model.pretrained_asr"):
        if has_model and not has_voicechat_root and _get(fields, required) is _MISSING:
            warnings.append(f"{required} is missing; most SALM/SALMAutomodel configs require it.")

    if _has_prefix(fields, "data"):
        input_roles = _get(fields, "data.input_roles")
        output_roles = _get(fields, "data.output_roles")
        if _has_prefix(fields, "data.frame_length") and input_roles is _MISSING:
            warnings.append("Duplex-style data has frame_length but no data.input_roles.")
        if _has_prefix(fields, "data.frame_length") and output_roles is _MISSING:
            warnings.append("Duplex-style data has frame_length but no data.output_roles.")
        if _get(fields, "data.source_sample_rate") is _MISSING and _has_prefix(fields, "data.input_roles"):
            warnings.append("Duplex-style data should declare data.source_sample_rate, commonly 16000.")
        if _has_prefix(fields, "data.train_ds") and not any(
            "input_cfg" in key or key.endswith("shar_path") or key.endswith("cuts_path") or key.endswith("manifest_filepath")
            for key in fields
        ):
            warnings.append("data.train_ds exists but no obvious input_cfg/cuts_path/shar_path/manifest path was found.")

    if _has_prefix(fields, "model.stt") and _has_prefix(fields, "model.speech_generation"):
        notes.append("Detected Nemotron VoiceChat-style nested STT + speech_generation config.")
        if _get(fields, "checkpoint_path") is _MISSING:
            warnings.append("Nemotron VoiceChat evaluation usually needs checkpoint_path.")
        if _get(fields, "model.inference_speaker_name") is _MISSING and _get(fields, "model.inference_speaker_reference") is _MISSING:
            warnings.append("Nemotron VoiceChat has no inference_speaker_name or inference_speaker_reference.")

    if re.search(r"NemotronVoiceChat\s*\.\s*training_step|trainer\.fit\s*\(\s*.*NemotronVoiceChat", text):
        errors.append("NemotronVoiceChat is inference-only; train STT and EAR-TTS components separately.")

    warnings.extend(_warn_absolute_private_paths(fields))

    if _get(fields, "trainer.accelerator") not in (_MISSING, "gpu", "cuda"):
        warnings.append("SpeechLM2 training is GPU-oriented; non-GPU trainer.accelerator may fail or be impractically slow.")

    if not errors:
        notes.append("No blocking static issues detected by the lightweight checker.")
    return errors, warnings, notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Safely check NeMo SpeechLM2 YAML/JSON-like configs for common static issues.",
    )
    parser.add_argument("config", type=Path, help="Path to a SpeechLM2 YAML/JSON config or Hydra-style config file.")
    parser.add_argument("--quiet", action="store_true", help="Only print errors and warnings.")
    args = parser.parse_args(argv)

    if not args.config.exists():
        print(f"ERROR: config does not exist: {args.config}", file=sys.stderr)
        return 2
    if not args.config.is_file():
        print(f"ERROR: config is not a file: {args.config}", file=sys.stderr)
        return 2

    errors, warnings, notes = check_config(args.config)
    print(f"Checked: {args.config}")
    for error in errors:
        print(f"ERROR: {error}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    if not args.quiet:
        for note in notes:
            print(f"NOTE: {note}")

    if errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
