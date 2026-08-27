#!/usr/bin/env python3
"""Safe preflight inspector for EasyR1 actor checkpoint directories.

The inspector is deterministic and metadata-only: it parses filenames and JSON
metadata, but it never imports torch and never loads model weight shards.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SHARD_RE = re.compile(r"^model_world_size_(?P<world_size>\d+)_rank_(?P<rank>\d+)\.pt$")
OPTIM_RE = re.compile(r"^optim_world_size_(?P<world_size>\d+)_rank_(?P<rank>\d+)\.pt$")
EXTRA_RE = re.compile(r"^extra_state_world_size_(?P<world_size>\d+)_rank_(?P<rank>\d+)\.pt$")
SUPPORTED_ARCHITECTURE_MARKERS = (
    "ForTokenClassification",
    "ForConditionalGeneration",
    "ForCausalLM",
)


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _read_json(path: Path, root: Path, errors: list[str]) -> Any | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        errors.append(f"Missing JSON file: {_rel(path, root)}")
    except json.JSONDecodeError as exc:
        errors.append(
            f"Invalid JSON in {_rel(path, root)}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        )
    except OSError as exc:
        errors.append(f"Could not read {_rel(path, root)}: {exc}")
    return None


def _parse_rank_files(root: Path, pattern: re.Pattern[str]) -> dict[int, list[int]]:
    groups: dict[int, list[int]] = {}
    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if not child.is_file():
            continue
        match = pattern.match(child.name)
        if not match:
            continue
        world_size = int(match.group("world_size"))
        rank = int(match.group("rank"))
        groups.setdefault(world_size, []).append(rank)
    return {world_size: sorted(set(ranks)) for world_size, ranks in sorted(groups.items())}


def _check_rank_group(
    *,
    label: str,
    groups: dict[int, list[int]],
    errors: list[str],
    warnings: list[str],
    required: bool,
) -> dict[str, Any]:
    report: dict[str, Any] = {"present": bool(groups), "groups": groups}
    if not groups:
        message = f"No {label} files matched the expected EasyR1 naming pattern."
        if required:
            errors.append(message)
        else:
            warnings.append(message)
        return report

    if len(groups) > 1:
        errors.append(f"Multiple {label} world_size groups found: {sorted(groups)}")

    world_size = sorted(groups)[0]
    ranks = groups[world_size]
    report.update({"world_size": world_size, "ranks": ranks})

    if world_size <= 0:
        errors.append(f"Invalid {label} world_size {world_size}; expected a positive integer.")
        return report

    if 0 not in ranks:
        errors.append(f"{label} rank 0 is missing; rank 0 is required for EasyR1 merge preflight.")

    out_of_range = [rank for rank in ranks if rank < 0 or rank >= world_size]
    if out_of_range:
        errors.append(
            f"{label} rank(s) outside advertised world_size {world_size}: {out_of_range}"
        )

    expected = list(range(world_size))
    missing = [rank for rank in expected if rank not in ranks]
    report["missing_ranks"] = missing
    if missing:
        errors.append(
            f"{label} ranks are incomplete for world_size {world_size}; missing rank(s): {missing}"
        )

    if ranks:
        contiguous_seen = list(range(min(ranks), max(ranks) + 1))
        gaps = [rank for rank in contiguous_seen if rank not in ranks]
        report["gaps_within_seen_range"] = gaps
        if gaps:
            errors.append(f"{label} ranks are non-contiguous within observed range: missing {gaps}")

    return report


def inspect_actor_checkpoint(actor_dir: Path, *, expect_huggingface: bool = True) -> dict[str, Any]:
    actor_dir = actor_dir.expanduser()
    result: dict[str, Any] = {
        "actor_dir": str(actor_dir),
        "ok": False,
        "errors": [],
        "warnings": [],
        "info": [],
        "checks": {},
    }
    errors: list[str] = result["errors"]
    warnings: list[str] = result["warnings"]
    info: list[str] = result["info"]
    checks: dict[str, Any] = result["checks"]

    if not actor_dir.exists():
        errors.append("Actor checkpoint directory does not exist.")
        return result
    if not actor_dir.is_dir():
        errors.append("Actor checkpoint path is not a directory.")
        return result
    if actor_dir.name == "huggingface":
        errors.append(
            "The provided directory is named 'huggingface'; pass the parent actor checkpoint directory instead."
        )

    try:
        children = sorted(actor_dir.iterdir(), key=lambda p: p.name)
    except OSError as exc:
        errors.append(f"Could not list actor checkpoint directory: {exc}")
        return result

    if not children:
        errors.append("Actor checkpoint directory is empty.")
        return result

    model_groups = _parse_rank_files(actor_dir, SHARD_RE)
    checks["model_shards"] = _check_rank_group(
        label="model shard",
        groups=model_groups,
        errors=errors,
        warnings=warnings,
        required=True,
    )

    for group_label, pattern in (("optimizer shard", OPTIM_RE), ("extra-state shard", EXTRA_RE)):
        groups = _parse_rank_files(actor_dir, pattern)
        if groups:
            checks[group_label.replace("-", "_").replace(" ", "_")] = _check_rank_group(
                label=group_label,
                groups=groups,
                errors=[],
                warnings=warnings,
                required=False,
            )
        else:
            info.append(
                f"No {group_label} files found; this can be normal for model-only export checks."
            )

    zero_sized_model_files = [
        child.name
        for child in children
        if child.is_file() and SHARD_RE.match(child.name) and child.stat().st_size == 0
    ]
    checks["zero_sized_model_shards"] = zero_sized_model_files
    if zero_sized_model_files:
        errors.append(f"Zero-sized model shard file(s): {zero_sized_model_files}")

    hf_dir = actor_dir / "huggingface"
    hf_report: dict[str, Any] = {"present": hf_dir.exists(), "path": "huggingface"}
    checks["huggingface_metadata"] = hf_report
    if not hf_dir.exists():
        message = "Missing huggingface/ metadata directory."
        if expect_huggingface:
            errors.append(message)
        else:
            warnings.append(message)
    elif not hf_dir.is_dir():
        errors.append("huggingface exists but is not a directory.")
    else:
        config_path = hf_dir / "config.json"
        hf_report["config_json_present"] = config_path.is_file()
        if not config_path.is_file():
            message = "Missing huggingface/config.json; the merger needs it to choose an auto model class."
            if expect_huggingface:
                errors.append(message)
            else:
                warnings.append(message)
        else:
            config = _read_json(config_path, actor_dir, errors)
            if isinstance(config, dict):
                architectures = config.get("architectures")
                hf_report["architectures"] = architectures
                first_arch = None
                if isinstance(architectures, list) and architectures:
                    first_arch = str(architectures[0])
                if not first_arch:
                    errors.append(
                        "huggingface/config.json has no architectures[0]; the merger would treat it as unsupported."
                    )
                elif not any(marker in first_arch for marker in SUPPORTED_ARCHITECTURE_MARKERS):
                    errors.append(
                        "Unsupported architecture for EasyR1 merger auto-class selection: "
                        f"{first_arch!r}"
                    )

        generation_config_path = hf_dir / "generation_config.json"
        hf_report["generation_config_json_present"] = generation_config_path.is_file()
        if generation_config_path.is_file():
            generation_config = _read_json(generation_config_path, actor_dir, errors)
            if isinstance(generation_config, dict):
                interesting_keys = [
                    key
                    for key in ("eos_token_id", "pad_token_id", "bos_token_id", "max_new_tokens")
                    if key in generation_config
                ]
                hf_report["generation_config_keys_seen"] = interesting_keys
        else:
            info.append("No huggingface/generation_config.json found; merger will save model defaults if absent.")

        tokenizer_like = [
            child.name
            for child in sorted(hf_dir.iterdir(), key=lambda p: p.name)
            if child.name
            in {
                "tokenizer.json",
                "tokenizer_config.json",
                "special_tokens_map.json",
                "preprocessor_config.json",
                "processor_config.json",
                "chat_template.json",
                "vocab.json",
                "merges.txt",
                "sentencepiece.bpe.model",
                "spiece.model",
            }
        ]
        hf_report["tokenizer_or_processor_metadata_seen"] = tokenizer_like
        if not tokenizer_like:
            warnings.append(
                "No common tokenizer/processor metadata files were detected under huggingface/; "
                "weights may export, but downstream inference may still need tokenizer or processor files."
            )

        existing_weight_outputs = [
            child.name
            for child in sorted(hf_dir.iterdir(), key=lambda p: p.name)
            if child.is_file()
            and (
                child.name.endswith(".safetensors")
                or child.name.endswith(".bin")
                or child.name.endswith(".index.json")
            )
        ]
        hf_report["existing_weight_outputs"] = existing_weight_outputs
        if existing_weight_outputs:
            info.append(
                "Existing Hugging Face weight files were detected; a new merge may overwrite or coexist with them."
            )

    lora_dir = actor_dir / "lora_adapter"
    lora_report: dict[str, Any] = {"present": lora_dir.exists(), "path": "lora_adapter"}
    checks["lora_adapter"] = lora_report
    if lora_dir.exists():
        if not lora_dir.is_dir():
            errors.append("lora_adapter exists but is not a directory.")
        else:
            adapter_config_path = lora_dir / "adapter_config.json"
            lora_report["adapter_config_json_present"] = adapter_config_path.is_file()
            if not adapter_config_path.is_file():
                errors.append(
                    "lora_adapter exists but adapter_config.json is missing; LoRA merge cannot proceed."
                )
            else:
                adapter_config = _read_json(adapter_config_path, actor_dir, errors)
                if isinstance(adapter_config, dict):
                    base_model = adapter_config.get("base_model_name_or_path")
                    lora_report["base_model_name_or_path"] = base_model
                    if not base_model:
                        errors.append(
                            "lora_adapter/adapter_config.json is missing base_model_name_or_path; "
                            "the dense LoRA merge needs the base model."
                        )
                    for key in ("peft_type", "task_type", "target_modules", "r", "lora_alpha"):
                        if key in adapter_config:
                            lora_report[key] = adapter_config[key]
            adapter_weights_path = lora_dir / "adapter_model.safetensors"
            lora_report["adapter_model_safetensors_present"] = adapter_weights_path.is_file()
            if not adapter_weights_path.is_file():
                warnings.append(
                    "lora_adapter/adapter_model.safetensors was not found. EasyR1 dense merge primarily uses "
                    "checkpoint state dict plus adapter_config.json, but adapter-only reuse may need this file."
                )
    else:
        info.append("No lora_adapter/ directory found; treating checkpoint as a non-LoRA dense export candidate.")

    result["ok"] = not errors
    return result


def _print_human(result: dict[str, Any]) -> None:
    status = "PASS" if result["ok"] else "FAIL"
    print("EasyR1 actor checkpoint preflight")
    print(f"Status: {status}")
    print(f"Directory: {result['actor_dir']}")

    model = result.get("checks", {}).get("model_shards", {})
    if model.get("present"):
        print(
            "Model shards: "
            f"world_size={model.get('world_size')}, ranks={model.get('ranks')}, "
            f"missing={model.get('missing_ranks', [])}"
        )

    hf = result.get("checks", {}).get("huggingface_metadata", {})
    if hf:
        print(
            "Hugging Face metadata: "
            f"present={hf.get('present')}, config={hf.get('config_json_present')}, "
            f"generation_config={hf.get('generation_config_json_present')}, "
            f"architectures={hf.get('architectures')}"
        )

    lora = result.get("checks", {}).get("lora_adapter", {})
    if lora:
        print(
            "LoRA adapter: "
            f"present={lora.get('present')}, config={lora.get('adapter_config_json_present')}, "
            f"base_model={lora.get('base_model_name_or_path')}"
        )

    for label in ("errors", "warnings", "info"):
        values = result.get(label, [])
        if not values:
            continue
        print(f"\n{label.capitalize()}:")
        for value in values:
            print(f"- {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely inspect an EasyR1 actor checkpoint directory before running a Hugging Face export merge. "
            "This tool never loads .pt model shards."
        )
    )
    parser.add_argument(
        "actor_dir",
        type=Path,
        help="Path to the actor checkpoint directory, usually global_step_<N>/actor.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full inspection report as JSON.",
    )
    parser.add_argument(
        "--no-expect-huggingface",
        action="store_true",
        help=(
            "Downgrade missing huggingface/ metadata from an error to a warning. "
            "Use only for partial-copy diagnostics, not for merge readiness."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = inspect_actor_checkpoint(
        args.actor_dir,
        expect_huggingface=not args.no_expect_huggingface,
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_human(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
