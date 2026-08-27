#!/usr/bin/env python3
"""Safe tokenizer smoke check for Transformers tokenizers.

The script defaults to local-only loading. Pass --allow-remote to permit Hub
resolution for the requested model id.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load a Transformers tokenizer, encode text, inspect special tokens, decode, and optionally apply a chat template. Defaults to local-only loading.",
    )
    parser.add_argument(
        "--model-or-path",
        required=True,
        help="Local tokenizer directory/file or approved Hub id.",
    )
    parser.add_argument(
        "--text",
        default="Hello from Transformers tokenizers.",
        help="Text to tokenize for the smoke check.",
    )
    parser.add_argument(
        "--text-pair",
        default=None,
        help="Optional second sequence for pair tokenization.",
    )
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="Permit remote Hub resolution. Without this flag, local_files_only=True is used.",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Force local-only loading even if --allow-remote is also passed.",
    )
    parser.add_argument(
        "--slow",
        action="store_true",
        help="Request a slow/Python tokenizer with use_fast=False.",
    )
    parser.add_argument(
        "--trust-remote-code",
        action="store_true",
        help="Allow custom remote code execution for trusted repositories only.",
    )
    parser.add_argument(
        "--revision",
        default=None,
        help="Optional Hub revision, branch, tag, or commit.",
    )
    parser.add_argument(
        "--padding",
        default=None,
        choices=["true", "false", "longest", "max_length"],
        help="Padding strategy for tokenization.",
    )
    parser.add_argument(
        "--truncation",
        action="store_true",
        help="Enable truncation.",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=None,
        help="Optional maximum sequence length.",
    )
    parser.add_argument(
        "--return-offsets",
        action="store_true",
        help="Request offset mappings; requires fast tokenizer support.",
    )
    parser.add_argument(
        "--chat-json",
        default=None,
        help='Optional JSON list of chat messages, e.g. ''[{"role":"user","content":"Hi"}]''.',
    )
    parser.add_argument(
        "--chat-add-generation-prompt",
        action="store_true",
        help="Pass add_generation_prompt=True when applying the chat template.",
    )
    parser.add_argument(
        "--chat-tokenize",
        action="store_true",
        help="Return token ids from apply_chat_template instead of formatted text.",
    )
    return parser.parse_args()


def padding_value(raw: str | None) -> bool | str:
    if raw is None or raw == "false":
        return False
    if raw == "true":
        return True
    return raw


def preview(value: Any, limit: int = 240) -> str:
    text = repr(value)
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def main() -> int:
    args = parse_args()

    try:
        from transformers import AutoTokenizer
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"ERROR: could not import transformers.AutoTokenizer: {exc}", file=sys.stderr)
        return 2

    local_files_only = args.local_files_only or not args.allow_remote
    load_kwargs: dict[str, Any] = {
        "local_files_only": local_files_only,
        "use_fast": not args.slow,
        "trust_remote_code": args.trust_remote_code,
    }
    if args.revision:
        load_kwargs["revision"] = args.revision

    print("== load ==")
    print(f"model_or_path: {args.model_or_path}")
    print(f"local_files_only: {local_files_only}")
    print(f"use_fast requested: {not args.slow}")
    print(f"trust_remote_code: {args.trust_remote_code}")

    try:
        tokenizer = AutoTokenizer.from_pretrained(args.model_or_path, **load_kwargs)
    except Exception as exc:
        print(f"ERROR: tokenizer load failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        if local_files_only:
            print("Hint: pass --allow-remote only if network access is intended, or provide a local tokenizer directory.", file=sys.stderr)
        print("Hint: missing optional packages may include tokenizers, sentencepiece, tiktoken, or mistral-common.", file=sys.stderr)
        return 1

    print(f"class: {type(tokenizer).__name__}")
    print(f"name_or_path: {getattr(tokenizer, 'name_or_path', None)}")
    print(f"is_fast: {getattr(tokenizer, 'is_fast', None)}")
    print(f"vocab_size: {getattr(tokenizer, 'vocab_size', None)}")
    print(f"len(tokenizer): {len(tokenizer)}")
    print("special_tokens_map:")
    print(json.dumps(getattr(tokenizer, "special_tokens_map", {}), indent=2, sort_keys=True, default=str))

    encode_kwargs: dict[str, Any] = {
        "padding": padding_value(args.padding),
        "truncation": args.truncation,
        "return_special_tokens_mask": True,
    }
    if args.max_length is not None:
        encode_kwargs["max_length"] = args.max_length
    if args.return_offsets:
        encode_kwargs["return_offsets_mapping"] = True

    print("\n== encode ==")
    try:
        if args.text_pair is None:
            encoding = tokenizer(args.text, **encode_kwargs)
        else:
            encoding = tokenizer(args.text, args.text_pair, **encode_kwargs)
    except Exception as exc:
        print(f"ERROR: tokenization failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"keys: {list(encoding.keys())}")
    input_ids = encoding.get("input_ids")
    print(f"input_ids length: {len(input_ids) if hasattr(input_ids, '__len__') else 'unknown'}")
    print(f"input_ids preview: {preview(input_ids)}")
    if "attention_mask" in encoding:
        print(f"attention_mask preview: {preview(encoding['attention_mask'])}")
    if "special_tokens_mask" in encoding:
        print(f"special_tokens_mask preview: {preview(encoding['special_tokens_mask'])}")
    if "offset_mapping" in encoding:
        print(f"offset_mapping preview: {preview(encoding['offset_mapping'])}")

    print("\n== decode ==")
    try:
        print(f"with special tokens: {tokenizer.decode(input_ids, skip_special_tokens=False)}")
        print(f"skip special tokens: {tokenizer.decode(input_ids, skip_special_tokens=True)}")
    except Exception as exc:
        print(f"ERROR: decode failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.chat_json:
        print("\n== chat template ==")
        try:
            messages = json.loads(args.chat_json)
            if not isinstance(messages, list):
                raise ValueError("--chat-json must decode to a list of messages")
            chat_output = tokenizer.apply_chat_template(
                messages,
                tokenize=args.chat_tokenize,
                add_generation_prompt=args.chat_add_generation_prompt,
            )
            print(f"chat output type: {type(chat_output).__name__}")
            print(f"chat output preview: {preview(chat_output, limit=600)}")
        except Exception as exc:
            print(f"ERROR: chat template failed: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1

    print("\nOK: tokenizer smoke check completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
