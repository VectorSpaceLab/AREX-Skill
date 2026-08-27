#!/usr/bin/env python3
"""Validate a Transformers GenerationConfig without downloading a model."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

_UNSET = object()


def _parse_bool(value: str) -> bool:
    lowered = value.lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected a boolean, got {value!r}")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"could not read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("config JSON must contain an object")
    return payload


def _add_if_set(config: dict[str, Any], key: str, value: Any) -> None:
    if value is not _UNSET and value is not None:
        config[key] = value


def _finite_positive(name: str, value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return f"{name} must be numeric"
    if not math.isfinite(float(value)) or float(value) <= 0:
        return f"{name} must be finite and > 0"
    return None


def _validate_config(raw: dict[str, Any], strict: bool, require_pad_token: bool) -> list[str]:
    errors: list[str] = []
    warnings: list[str] = []

    max_new_tokens = raw.get("max_new_tokens")
    max_length = raw.get("max_length")
    if max_new_tokens is not None and max_length is not None:
        message = "prefer max_new_tokens; avoid combining it with max_length unless total length is intentional"
        (errors if strict else warnings).append(message)

    for name in ("max_new_tokens", "max_length", "min_new_tokens", "min_length", "num_beams", "num_return_sequences"):
        value = raw.get(name)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
            errors.append(f"{name} must be a non-negative integer")

    if raw.get("num_beams") == 0:
        errors.append("num_beams must be >= 1 when set")

    num_beams = raw.get("num_beams") or 1
    num_return_sequences = raw.get("num_return_sequences") or 1
    if isinstance(num_beams, int) and isinstance(num_return_sequences, int):
        if not raw.get("do_sample", False) and num_return_sequences > num_beams:
            errors.append("num_return_sequences cannot exceed num_beams for deterministic beam generation")

    do_sample = raw.get("do_sample", False)
    sampling_fields = ["temperature", "top_p", "top_k", "typical_p", "min_p", "epsilon_cutoff", "eta_cutoff"]
    active_sampling = [field for field in sampling_fields if raw.get(field) is not None]
    if active_sampling and not do_sample:
        message = f"sampling option(s) {', '.join(active_sampling)} require do_sample=True or should be removed"
        (errors if strict else warnings).append(message)

    for name in ("temperature", "typical_p", "epsilon_cutoff", "eta_cutoff"):
        message = _finite_positive(name, raw.get(name))
        if message:
            errors.append(message)

    for name in ("top_p", "min_p"):
        value = raw.get(name)
        if value is not None:
            message = _finite_positive(name, value)
            if message:
                errors.append(message)
            elif float(value) > 1:
                errors.append(f"{name} must be <= 1")

    top_k = raw.get("top_k")
    if top_k is not None and (not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 0):
        errors.append("top_k must be a non-negative integer")

    for name in ("pad_token_id", "eos_token_id", "bos_token_id", "decoder_start_token_id"):
        value = raw.get(name)
        if value is not None:
            values = value if isinstance(value, list) else [value]
            if not all(isinstance(item, int) and not isinstance(item, bool) and item >= 0 for item in values):
                errors.append(f"{name} must be a non-negative integer or list of integers")

    if require_pad_token and raw.get("pad_token_id") is None:
        errors.append("pad_token_id is required by --require-pad-token")

    repetition_penalty = raw.get("repetition_penalty")
    if repetition_penalty is not None:
        message = _finite_positive("repetition_penalty", repetition_penalty)
        if message:
            errors.append(message)

    no_repeat_ngram_size = raw.get("no_repeat_ngram_size")
    if no_repeat_ngram_size is not None and (
        not isinstance(no_repeat_ngram_size, int) or isinstance(no_repeat_ngram_size, bool) or no_repeat_ngram_size < 0
    ):
        errors.append("no_repeat_ngram_size must be a non-negative integer")

    return [f"ERROR {item}" for item in errors] + [f"WARNING {item}" for item in warnings]


def _load_generation_config_class(require_transformers: bool) -> Any | None:
    try:
        from transformers import GenerationConfig
    except Exception as exc:  # pragma: no cover - depends on caller environment
        message = f"failed to import transformers.GenerationConfig: {exc}"
        if require_transformers:
            print(f"ERROR {message}", file=sys.stderr)
            sys.exit(2)
        print(f"WARNING {message}; static validation only", file=sys.stderr)
        return None
    return GenerationConfig


def _summary(config: Any) -> dict[str, Any]:
    data = config.to_dict()
    keys = [
        "max_new_tokens",
        "max_length",
        "do_sample",
        "temperature",
        "top_p",
        "top_k",
        "num_beams",
        "num_return_sequences",
        "repetition_penalty",
        "no_repeat_ngram_size",
        "pad_token_id",
        "eos_token_id",
    ]
    return {key: data.get(key) for key in keys if data.get(key) is not None}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Construct and validate a Transformers GenerationConfig without loading model weights."
    )
    parser.add_argument("--config-json", type=Path, help="Path to a generation_config.json-style object.")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=JSON", help="Override or add a raw JSON value.")
    parser.add_argument("--max-new-tokens", type=int)
    parser.add_argument("--max-length", type=int)
    parser.add_argument(
        "--do-sample",
        nargs="?",
        const=True,
        default=_UNSET,
        type=_parse_bool,
        help="Enable or disable sampling; accepts optional true/false value.",
    )
    parser.add_argument("--no-sample", dest="do_sample_value", action="store_false", help="Force do_sample=False.")
    parser.set_defaults(do_sample_value=_UNSET)
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--top-p", type=float)
    parser.add_argument("--top-k", type=int)
    parser.add_argument("--num-beams", type=int)
    parser.add_argument("--num-return-sequences", type=int)
    parser.add_argument("--repetition-penalty", type=float)
    parser.add_argument("--no-repeat-ngram-size", type=int)
    parser.add_argument("--pad-token-id", type=int)
    parser.add_argument("--eos-token-id", type=int)
    parser.add_argument("--require-pad-token", action="store_true", help="Fail if pad_token_id is absent.")
    parser.add_argument("--strict", action="store_true", help="Treat contradiction warnings as errors.")
    parser.add_argument("--print-json", action="store_true", help="Print the normalized GenerationConfig dictionary.")
    parser.add_argument(
        "--require-transformers",
        action="store_true",
        help="Fail if transformers.GenerationConfig cannot be imported and constructed.",
    )
    parser.add_argument("--expect-sampling", type=_parse_bool, help="Fail unless do_sample matches this boolean.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw: dict[str, Any] = {}

    if args.config_json:
        try:
            raw.update(_load_json(args.config_json))
        except ValueError as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            return 1

    for item in args.set:
        if "=" not in item:
            print(f"ERROR --set expects KEY=JSON, got {item!r}", file=sys.stderr)
            return 1
        key, value = item.split("=", 1)
        try:
            raw[key] = json.loads(value)
        except json.JSONDecodeError as exc:
            print(f"ERROR invalid JSON for --set {key}: {exc}", file=sys.stderr)
            return 1

    _add_if_set(raw, "max_new_tokens", args.max_new_tokens)
    _add_if_set(raw, "max_length", args.max_length)
    _add_if_set(raw, "do_sample", args.do_sample)
    _add_if_set(raw, "do_sample", args.do_sample_value)
    _add_if_set(raw, "temperature", args.temperature)
    _add_if_set(raw, "top_p", args.top_p)
    _add_if_set(raw, "top_k", args.top_k)
    _add_if_set(raw, "num_beams", args.num_beams)
    _add_if_set(raw, "num_return_sequences", args.num_return_sequences)
    _add_if_set(raw, "repetition_penalty", args.repetition_penalty)
    _add_if_set(raw, "no_repeat_ngram_size", args.no_repeat_ngram_size)
    _add_if_set(raw, "pad_token_id", args.pad_token_id)
    _add_if_set(raw, "eos_token_id", args.eos_token_id)

    if args.expect_sampling is not None and raw.get("do_sample", False) is not args.expect_sampling:
        print(f"ERROR expected do_sample={args.expect_sampling}, got {raw.get('do_sample', False)}", file=sys.stderr)
        return 1

    messages = _validate_config(raw, strict=args.strict, require_pad_token=args.require_pad_token)
    errors = [message for message in messages if message.startswith("ERROR")]
    warnings = [message for message in messages if message.startswith("WARNING")]

    for message in warnings:
        print(message, file=sys.stderr)
    if errors:
        for message in errors:
            print(message, file=sys.stderr)
        return 1

    GenerationConfig = _load_generation_config_class(args.require_transformers)
    if GenerationConfig is None:
        print("OK generation config statically validated")
        print(json.dumps({key: raw[key] for key in sorted(raw) if raw[key] is not None}, indent=2, sort_keys=True))
        return 0

    try:
        config = GenerationConfig(**raw)
    except Exception as exc:
        print(f"ERROR GenerationConfig rejected settings: {exc}", file=sys.stderr)
        return 1

    print("OK generation config validated")
    print(json.dumps(_summary(config), indent=2, sort_keys=True))
    if args.print_json:
        print(json.dumps(config.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
