#!/usr/bin/env python3
"""Validate Baichuan2 supervised fine-tuning JSON data.

The expected file is a top-level JSON list. Each item contains a
``conversations`` list. Each message has ``from`` and ``value`` fields.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

HUMAN_ROLES = {"human", "user"}
ASSISTANT_ROLES = {"gpt", "assistant", "bot"}
DEFAULT_USER_TOKEN_ID = 195
DEFAULT_ASSISTANT_TOKEN_ID = 196


FIXTURE = [
    {
        "id": "fixture-1",
        "conversations": [
            {"from": "human", "value": "Write one sentence about the sea."},
            {"from": "gpt", "value": "The sea turns moonlight into a quiet silver road."},
        ],
    },
    {
        "id": "fixture-2",
        "conversations": [
            {"from": "human", "value": "Translate to Chinese: machine learning"},
            {"from": "gpt", "value": "机器学习"},
            {"from": "human", "value": "Use it in a short sentence."},
            {"from": "gpt", "value": "机器学习正在帮助人们更高效地分析数据。"},
        ],
    },
]


def role_class(role: Any, strict_roles: bool) -> Optional[str]:
    """Return normalized role class or None for invalid roles."""
    if not isinstance(role, str):
        return None
    normalized = role.strip().lower()
    if normalized in HUMAN_ROLES:
        return "human"
    if normalized in ASSISTANT_ROLES:
        return "assistant"
    if strict_roles:
        return None
    # The trainer treats any non-human role as assistant text. In permissive
    # mode, mirror that behavior but surface a warning in validation.
    return "assistant"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_limited(records: List[Any], max_records: int) -> Iterable[Tuple[int, Any]]:
    limit = len(records) if max_records <= 0 else min(max_records, len(records))
    for idx in range(limit):
        yield idx, records[idx]


def validate_records(
    records: Any,
    *,
    strict_roles: bool = True,
    require_alternating: bool = False,
    allow_empty_values: bool = True,
    max_records: int = 0,
) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """Validate schema and return errors, warnings, and stats."""
    errors: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, Any] = {
        "records_total": 0,
        "records_checked": 0,
        "messages_checked": 0,
        "role_counts": Counter(),
        "assistant_target_records": 0,
        "human_context_records": 0,
    }

    if not isinstance(records, list):
        return ["top-level JSON value must be a list of records"], warnings, stats
    stats["records_total"] = len(records)
    if not records:
        errors.append("top-level list is empty")
        return errors, warnings, stats

    for record_idx, record in iter_limited(records, max_records):
        stats["records_checked"] += 1
        prefix = f"record[{record_idx}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        conversations = record.get("conversations")
        if not isinstance(conversations, list):
            errors.append(f"{prefix}.conversations must be a list")
            continue
        if not conversations:
            errors.append(f"{prefix}.conversations is empty")
            continue

        previous_class: Optional[str] = None
        seen_human = False
        seen_assistant = False
        for msg_idx, message in enumerate(conversations):
            msg_prefix = f"{prefix}.conversations[{msg_idx}]"
            if not isinstance(message, dict):
                errors.append(f"{msg_prefix} must be an object")
                continue
            role = message.get("from")
            value = message.get("value")
            klass = role_class(role, strict_roles)
            if klass is None:
                errors.append(
                    f"{msg_prefix}.from must be one of human/user/gpt/assistant/bot; got {role!r}"
                )
                continue
            role_text = str(role).strip().lower()
            stats["role_counts"][role_text] += 1
            if role_text == "user":
                warnings.append(f"{msg_prefix}.from uses 'user'; normalize to 'human' for closest compatibility")
            if role_text == "assistant":
                warnings.append(f"{msg_prefix}.from uses 'assistant'; accepted, but 'gpt' matches the reference sample")
            if not strict_roles and role_text not in HUMAN_ROLES | ASSISTANT_ROLES:
                warnings.append(f"{msg_prefix}.from={role!r} will be treated as assistant text")

            if not isinstance(value, str):
                errors.append(f"{msg_prefix}.value must be a string")
            elif not value.strip():
                if allow_empty_values:
                    warnings.append(f"{msg_prefix}.value is empty or whitespace-only")
                else:
                    errors.append(f"{msg_prefix}.value is empty or whitespace-only")

            if msg_idx == 0 and klass != "human":
                warnings.append(f"{prefix} starts with {role!r}; recommended first role is 'human'")
            if previous_class is not None and klass == previous_class:
                message_text = f"{msg_prefix} repeats role class {klass!r}; expected alternating human/assistant turns"
                if require_alternating:
                    errors.append(message_text)
                else:
                    warnings.append(message_text)
            previous_class = klass
            if klass == "human":
                seen_human = True
            if klass == "assistant":
                seen_assistant = True
            stats["messages_checked"] += 1

        if seen_human:
            stats["human_context_records"] += 1
        else:
            errors.append(f"{prefix} contains no human/user turn")
        if seen_assistant:
            stats["assistant_target_records"] += 1
        else:
            errors.append(f"{prefix} contains no assistant/gpt target turn")

        last_role = conversations[-1].get("from") if isinstance(conversations[-1], dict) else None
        if role_class(last_role, strict_roles=False) != "assistant":
            warnings.append(f"{prefix} does not end with an assistant target turn")

    stats["role_counts"] = dict(stats["role_counts"])
    return errors, warnings, stats


def estimate_token_lengths(
    records: Any,
    *,
    tokenizer_name_or_path: str,
    model_max_length: int,
    max_records: int,
    user_token_id: int,
    assistant_token_id: int,
) -> Dict[str, Any]:
    """Estimate Baichuan-style sequence lengths with the requested tokenizer."""
    try:
        from transformers import AutoTokenizer
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("transformers is required for tokenizer length estimation") from exc

    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_name_or_path,
        use_fast=False,
        trust_remote_code=True,
        model_max_length=model_max_length,
    )
    eos_id = tokenizer.eos_token_id
    lengths: List[int] = []
    truncated = 0
    checked = 0
    for _, record in iter_limited(records, max_records):
        if not isinstance(record, dict) or not isinstance(record.get("conversations"), list):
            continue
        input_ids: List[int] = []
        for message in record["conversations"]:
            if not isinstance(message, dict):
                continue
            value = message.get("value")
            if not isinstance(value, str):
                continue
            marker = [user_token_id] if role_class(message.get("from"), strict_roles=False) == "human" else [assistant_token_id]
            input_ids.extend(marker)
            input_ids.extend(tokenizer.encode(value))
        if eos_id is not None:
            input_ids.append(eos_id)
        seq_len = len(input_ids)
        lengths.append(seq_len)
        checked += 1
        if seq_len > model_max_length:
            truncated += 1

    if not lengths:
        return {"tokenizer": tokenizer_name_or_path, "records_tokenized": 0}
    sorted_lengths = sorted(lengths)
    return {
        "tokenizer": tokenizer_name_or_path,
        "records_tokenized": checked,
        "model_max_length": model_max_length,
        "min_length": sorted_lengths[0],
        "max_length": sorted_lengths[-1],
        "mean_length": sum(sorted_lengths) / len(sorted_lengths),
        "p50_length": sorted_lengths[len(sorted_lengths) // 2],
        "p95_length": sorted_lengths[int(0.95 * (len(sorted_lengths) - 1))],
        "truncated_records": truncated,
        "truncated_fraction": truncated / checked if checked else 0.0,
    }


def write_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(FIXTURE, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data_path", type=Path, help="JSON file to validate")
    parser.add_argument("--write_fixture", type=Path, help="Write a tiny valid fixture JSON file and exit if --data_path is omitted")
    parser.add_argument("--json_report", type=Path, help="Optional path for a machine-readable validation report")
    parser.add_argument("--max_records", type=int, default=0, help="Maximum records to check; 0 means all")
    parser.add_argument("--strict_roles", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--require_alternating", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--allow_empty_values", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--tokenizer_name_or_path", help="Optional tokenizer for truncation estimates")
    parser.add_argument("--model_max_length", type=int, default=512)
    parser.add_argument("--user_token_id", type=int, default=DEFAULT_USER_TOKEN_ID)
    parser.add_argument("--assistant_token_id", type=int, default=DEFAULT_ASSISTANT_TOKEN_ID)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    if args.write_fixture:
        write_fixture(args.write_fixture)
        print(f"wrote fixture: {args.write_fixture}")
        if not args.data_path:
            return 0

    if not args.data_path:
        print("error: --data_path is required unless only --write_fixture is used", file=sys.stderr)
        return 2

    try:
        records = load_json(args.data_path)
    except Exception as exc:
        print(f"error: failed to read JSON {args.data_path}: {exc}", file=sys.stderr)
        return 1

    errors, warnings, stats = validate_records(
        records,
        strict_roles=args.strict_roles,
        require_alternating=args.require_alternating,
        allow_empty_values=args.allow_empty_values,
        max_records=args.max_records,
    )

    report: Dict[str, Any] = {
        "data_path": str(args.data_path),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }

    if args.tokenizer_name_or_path and not errors:
        try:
            report["token_lengths"] = estimate_token_lengths(
                records,
                tokenizer_name_or_path=args.tokenizer_name_or_path,
                model_max_length=args.model_max_length,
                max_records=args.max_records,
                user_token_id=args.user_token_id,
                assistant_token_id=args.assistant_token_id,
            )
        except Exception as exc:
            report["token_length_error"] = str(exc)
            warnings.append(f"token length estimation failed: {exc}")

    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        with args.json_report.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
