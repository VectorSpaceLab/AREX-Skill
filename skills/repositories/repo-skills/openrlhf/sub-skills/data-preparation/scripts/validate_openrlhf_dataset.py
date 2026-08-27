#!/usr/bin/env python3
"""Validate tiny OpenRLHF dataset samples without importing heavy runtime deps."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


class IssueCollector:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, record_index: int | None, message: str) -> None:
        prefix = f"record {record_index}: " if record_index is not None else ""
        self.errors.append(prefix + message)

    def warning(self, record_index: int | None, message: str) -> None:
        prefix = f"record {record_index}: " if record_index is not None else ""
        self.warnings.append(prefix + message)


def load_records(path: Path, max_samples: int) -> list[Any]:
    if not path.exists():
        raise ValueError(f"input file does not exist: {path}")
    if max_samples <= 0:
        raise ValueError("--max-samples must be positive")

    suffix = path.suffix.lower()
    records: list[Any] = []
    if suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if len(records) >= max_samples:
                    break
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    records.append(json.loads(stripped))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid JSON on line {line_number}: {exc}") from exc
    elif suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            try:
                data = json.load(handle)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON: {exc}") from exc
        if isinstance(data, list):
            records = data[:max_samples]
        elif isinstance(data, dict):
            for key in ("train", "data", "records", "items"):
                if isinstance(data.get(key), list):
                    records = data[key][:max_samples]
                    break
            if not records:
                records = [data]
        else:
            raise ValueError("JSON input must be an object or a list of objects")
    else:
        raise ValueError("input must be a .json or .jsonl file")
    return records


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, tuple, dict)) and len(value) == 0:
        return True
    return False


def require_key(record: Any, key: str | None, record_index: int, issues: IssueCollector, role: str) -> Any:
    if not isinstance(record, dict):
        issues.error(record_index, f"record must be a JSON object, got {type(record).__name__}")
        return None
    if not key:
        issues.error(record_index, f"missing configured key for {role}")
        return None
    if key not in record:
        issues.error(record_index, f"missing key '{key}' for {role}")
        return None
    value = record[key]
    if is_empty(value):
        issues.error(record_index, f"key '{key}' for {role} is null or empty")
    return value


def optional_value(record: Any, key: str | None) -> Any:
    if key and isinstance(record, dict):
        return record.get(key)
    return None


def validate_chat_messages(value: Any, record_index: int, issues: IssueCollector, key: str, *, require_assistant: bool = False) -> None:
    if not isinstance(value, list):
        issues.error(record_index, f"key '{key}' should be a chat message list when --apply-chat-template is used")
        return
    assistant_count = 0
    for msg_index, message in enumerate(value):
        if not isinstance(message, dict):
            issues.error(record_index, f"key '{key}' message {msg_index} must be an object")
            continue
        role = message.get("role")
        if not isinstance(role, str) or not role:
            issues.error(record_index, f"key '{key}' message {msg_index} missing string role")
        if role == "assistant":
            assistant_count += 1
        if "content" not in message or is_empty(message.get("content")):
            issues.error(record_index, f"key '{key}' message {msg_index} missing non-empty content")
    if require_assistant and assistant_count == 0:
        issues.error(record_index, f"key '{key}' must include at least one assistant message for multiturn SFT")


def count_image_placeholders(value: Any) -> int:
    if isinstance(value, str):
        return value.count("<image>")
    if isinstance(value, list):
        total = 0
        for item in value:
            if isinstance(item, dict):
                content = item.get("content")
                total += count_image_placeholders(content)
            elif isinstance(item, str):
                total += item.count("<image>")
        return total
    if isinstance(value, dict):
        if value.get("type") == "image":
            return 1
        return count_image_placeholders(value.get("text", "")) + count_image_placeholders(value.get("content", ""))
    return 0


def count_image_refs(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, list):
        return sum(1 for item in value if item is not None)
    return 1


def rough_length(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        return len(value)
    return len(json.dumps(value, ensure_ascii=False))


def check_length(record_index: int, issues: IssueCollector, max_len_chars: int | None, values: Iterable[Any]) -> None:
    if not max_len_chars:
        return
    total = sum(rough_length(value) for value in values)
    if total > max_len_chars:
        issues.warning(
            record_index,
            f"rough serialized length {total} exceeds --max-len-chars {max_len_chars}; check tokenizer max_len truncation/filtering",
        )


def validate_dataset_probs(args: argparse.Namespace, issues: IssueCollector) -> None:
    if not args.dataset_list and not args.dataset_probs:
        return
    if not args.dataset_list or not args.dataset_probs:
        issues.error(None, "--dataset-list and --dataset-probs must be provided together for mix validation")
        return
    datasets = [part.strip() for part in args.dataset_list.split(",") if part.strip()]
    probs_raw = [part.strip() for part in args.dataset_probs.split(",") if part.strip()]
    if len(datasets) != len(probs_raw):
        issues.error(None, f"dataset_probs length mismatch: {len(probs_raw)} probabilities for {len(datasets)} datasets")
    for index, raw in enumerate(probs_raw):
        try:
            value = float(raw)
        except ValueError:
            issues.error(None, f"dataset_probs entry {index} is not a float: {raw!r}")
            continue
        if value < 0:
            issues.error(None, f"dataset_probs entry {index} is negative: {value}")
    if probs_raw:
        try:
            total = sum(float(raw) for raw in probs_raw)
        except ValueError:
            return
        if total <= 0:
            issues.error(None, "dataset_probs must sum to a positive value")
        elif abs(total - 1.0) > 0.01:
            issues.warning(None, f"dataset_probs sum to {total:.6g}; OpenRLHF accepts probabilities but normalized intent should be checked")


def validate_vlm_alignment(
    record: dict[str, Any],
    prompt_value: Any,
    record_index: int,
    args: argparse.Namespace,
    issues: IssueCollector,
) -> None:
    image_value = record.get(args.image_key) if args.image_key else None
    placeholders = count_image_placeholders(prompt_value)
    image_refs = count_image_refs(image_value)
    if args.max_images_per_prompt and image_refs > args.max_images_per_prompt:
        issues.error(record_index, f"image reference count {image_refs} exceeds --max-images-per-prompt {args.max_images_per_prompt}")
    if args.require_image_alignment or placeholders or image_refs:
        if placeholders != image_refs:
            issues.error(
                record_index,
                f"image placeholder mismatch: found {placeholders} '<image>' placeholder(s) but {image_refs} non-null image reference(s) in key '{args.image_key}'; align media tokens with image inputs",
            )
        if image_refs and args.packing_samples:
            issues.error(record_index, "VLM image data should not be used with --ds.packing_samples in OpenRLHF PPO/RL training")


def validate_sft(records: list[Any], args: argparse.Namespace, issues: IssueCollector) -> None:
    for record_index, record in enumerate(records):
        prompt = require_key(record, args.input_key, record_index, issues, "SFT input")
        response = optional_value(record, args.output_key)
        if args.multiturn:
            if args.output_key and not is_empty(response):
                issues.error(record_index, "multiturn SFT should put the full trajectory in input_key and not set a populated output_key")
            if not args.apply_chat_template:
                issues.error(record_index, "multiturn SFT requires --apply-chat-template")
            validate_chat_messages(prompt, record_index, issues, args.input_key, require_assistant=True)
        elif args.output_key:
            response = require_key(record, args.output_key, record_index, issues, "SFT output")
            if args.apply_chat_template:
                if isinstance(prompt, list):
                    validate_chat_messages(prompt, record_index, issues, args.input_key)
                if isinstance(response, list):
                    validate_chat_messages(response, record_index, issues, args.output_key)
        else:
            if is_empty(prompt):
                issues.error(record_index, f"key '{args.input_key}' is empty")
            issues.warning(record_index, "no --output-key supplied; this matches continued pretraining or prompt-only SFT, not normal prompt/response SFT")
        if isinstance(record, dict):
            validate_vlm_alignment(record, prompt, record_index, args, issues)
        check_length(record_index, issues, args.max_len_chars, [prompt, response])


def validate_rm_or_dpo(records: list[Any], args: argparse.Namespace, issues: IssueCollector) -> None:
    mode_label = "DPO" if args.mode == "dpo" else "reward"
    for record_index, record in enumerate(records):
        prompt = optional_value(record, args.prompt_key)
        if args.prompt_key:
            prompt = require_key(record, args.prompt_key, record_index, issues, f"{mode_label} prompt")
        chosen = require_key(record, args.chosen_key, record_index, issues, f"{mode_label} chosen")
        rejected = require_key(record, args.rejected_key, record_index, issues, f"{mode_label} rejected")
        if chosen == rejected and chosen is not None:
            issues.error(record_index, f"{mode_label} chosen and rejected values are identical")
        if args.apply_chat_template:
            if args.prompt_key and isinstance(prompt, list):
                validate_chat_messages(prompt, record_index, issues, args.prompt_key)
            if isinstance(chosen, list):
                validate_chat_messages(chosen, record_index, issues, args.chosen_key)
            elif args.mode == "dpo" and not args.prompt_key:
                issues.error(record_index, "DPO with --apply-chat-template and no --prompt-key expects chosen as a chat trajectory list")
            if isinstance(rejected, list):
                validate_chat_messages(rejected, record_index, issues, args.rejected_key)
            elif args.mode == "dpo" and not args.prompt_key:
                issues.error(record_index, "DPO with --apply-chat-template and no --prompt-key expects rejected as a chat trajectory list")
        if args.mode == "dpo" and not args.prompt_key:
            issues.warning(record_index, "DPO without --prompt-key derives the prompt from chosen[:-1]; ensure chosen/rejected share the same conversation prefix")
        check_length(record_index, issues, args.max_len_chars, [prompt, chosen, rejected])


def validate_ppo(records: list[Any], args: argparse.Namespace, issues: IssueCollector) -> None:
    for record_index, record in enumerate(records):
        prompt = require_key(record, args.input_key, record_index, issues, "PPO prompt")
        if args.apply_chat_template and isinstance(prompt, list):
            validate_chat_messages(prompt, record_index, issues, args.input_key)
        label = optional_value(record, args.label_key)
        if args.label_key and is_empty(label):
            issues.error(record_index, f"key '{args.label_key}' for PPO label is null or empty")
        if isinstance(record, dict):
            validate_vlm_alignment(record, prompt, record_index, args, issues)
        check_length(record_index, issues, args.max_len_chars, [prompt, label])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate tiny OpenRLHF JSON/JSONL datasets without heavy dependencies.")
    parser.add_argument("--mode", choices=("sft", "rm", "dpo", "ppo"), required=True)
    parser.add_argument("--input", required=True, help="Local .json or .jsonl sample file")
    parser.add_argument("--max-samples", type=int, default=100, help="Maximum records to inspect")
    parser.add_argument("--input-key", default="input", help="SFT/PPO input key")
    parser.add_argument("--output-key", default=None, help="SFT output key")
    parser.add_argument("--prompt-key", default=None, help="RM/DPO shared prompt key")
    parser.add_argument("--chosen-key", default="chosen", help="RM/DPO chosen key")
    parser.add_argument("--rejected-key", default="rejected", help="RM/DPO rejected key")
    parser.add_argument("--label-key", default=None, help="Optional PPO label key")
    parser.add_argument("--image-key", default="images", help="Optional VLM image key")
    parser.add_argument("--apply-chat-template", action="store_true", help="Expect chat-template-compatible records")
    parser.add_argument("--multiturn", action="store_true", help="Validate compacted multiturn SFT records")
    parser.add_argument("--require-image-alignment", action="store_true", help="Require <image> count to match non-null image refs")
    parser.add_argument("--max-images-per-prompt", type=int, default=0, help="Configured VLM max images per prompt; 0 means text-only")
    parser.add_argument("--packing-samples", action="store_true", help="Flag if planned command enables ds.packing_samples")
    parser.add_argument("--max-len-chars", type=int, default=None, help="Rough serialized character length warning threshold")
    parser.add_argument("--dataset-list", default=None, help="Comma-separated dataset list for mix-count validation")
    parser.add_argument("--dataset-probs", default=None, help="Comma-separated probabilities for mix-count validation")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    issues = IssueCollector()
    validate_dataset_probs(args, issues)
    try:
        records = load_records(Path(args.input), args.max_samples)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not records:
        issues.error(None, "no records found in input")
    elif args.mode == "sft":
        validate_sft(records, args, issues)
    elif args.mode in {"rm", "dpo"}:
        validate_rm_or_dpo(records, args, issues)
    elif args.mode == "ppo":
        validate_ppo(records, args, issues)
    else:
        issues.error(None, f"unsupported mode {args.mode}")

    for warning in issues.warnings:
        print(f"WARNING: {warning}")
    for error in issues.errors:
        print(f"ERROR: {error}", file=sys.stderr)

    checked = len(records)
    print(f"checked {checked} record(s); warnings={len(issues.warnings)} errors={len(issues.errors)}")
    return 1 if issues.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
