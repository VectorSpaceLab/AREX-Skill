#!/usr/bin/env python3
"""Build a Nesa-style encrypted LLM request preview without contacting a service."""

from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
import uuid
from pathlib import Path
from typing import Any

DEFAULT_MODEL_MAP = {
    "nesaorg_Llama-3.1-8B-Instruct-Encrypted": "meta-llama/Llama-3.1-8B-Instruct-ee",
}


def clean_string(message: str | None) -> str:
    if not message:
        return ""
    decoded = html.unescape(message)
    printable = re.sub(r"[^ -~]", "", decoded)
    return unicodedata.normalize("NFKC", printable).strip()


def parse_history(raw: str | None) -> list[tuple[str, str]]:
    if not raw:
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("history JSON must be a list of [user, assistant] pairs")
    out: list[tuple[str, str]] = []
    for item in data:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError("each history item must be [user, assistant]")
        out.append((str(item[0]), str(item[1])))
    return out


def prompt_messages(prompt: str, system: str, history: list[tuple[str, str]], lookback: int) -> list[dict[str, str]]:
    messages = [{"role": "system", "content": clean_string(system)}]
    for user_msg, assistant_msg in history[-lookback:]:
        messages.append({"role": "user", "content": clean_string(user_msg)})
        messages.append({"role": "assistant", "content": clean_string(assistant_msg.split("[file]", 1)[0])})
    messages.append({"role": "user", "content": clean_string(prompt)})
    return messages


def token_ids_from_args(args: argparse.Namespace, messages: list[dict[str, str]]) -> tuple[list[int] | None, list[str]]:
    warnings: list[str] = []
    if args.token_ids:
        value = json.loads(args.token_ids)
        if not isinstance(value, list) or not all(isinstance(x, int) for x in value):
            raise ValueError("--token-ids must be a JSON list of integers")
        return value, warnings
    if args.tokenizer:
        try:
            from transformers import AutoTokenizer
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"transformers is required for --tokenizer: {exc}") from exc
        tokenizer_ref = str(Path(args.tokenizer).expanduser()) if Path(args.tokenizer).expanduser().exists() else args.tokenizer
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_ref, local_files_only=not args.allow_download)
        ids = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
        return list(map(int, ids)), warnings
    warnings.append("No token ids or tokenizer supplied; payload content is a placeholder, not an exact source payload.")
    return None, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview a Nesa encrypted LLM inference payload; no HTTP request is sent.")
    parser.add_argument("--prompt", required=True, help="Current user prompt.")
    parser.add_argument("--system", default="", help="System prompt.")
    parser.add_argument("--history-json", help="JSON list of [user, assistant] pairs.")
    parser.add_argument("--lookback", type=int, default=10, help="History pairs to include.")
    parser.add_argument("--model-key", default="nesaorg_Llama-3.1-8B-Instruct-Encrypted", help="UI/model registry key.")
    parser.add_argument("--backend-model-id", help="Override backend model id.")
    parser.add_argument("--token-ids", help="JSON list of already-tokenized integer IDs.")
    parser.add_argument("--tokenizer", help="Optional local tokenizer path or HF id for exact tokenization.")
    parser.add_argument("--allow-download", action="store_true", help="Allow tokenizer download if --tokenizer is an HF id.")
    parser.add_argument("--max-tokens", type=int, default=16, help="Preview max_tokens parameter.")
    args = parser.parse_args()

    history = parse_history(args.history_json)
    messages = prompt_messages(args.prompt, args.system, history, args.lookback)
    token_ids, warnings = token_ids_from_args(args, messages)
    backend_model = args.backend_model_id or DEFAULT_MODEL_MAP.get(args.model_key, args.model_key)
    content = str(token_ids) if token_ids is not None else "<token_ids omitted: provide --token-ids or --tokenizer>"

    payload: dict[str, Any] = {
        "stream": True,
        "model": backend_model,
        "correlation_id": str(uuid.uuid4()),
        "messages": [{"role": "assistant", "content": content}],
        "session_id": {"ee": True},
        "model_params": {"max_tokens": args.max_tokens},
    }
    preview = {
        "model_key": args.model_key,
        "prompt_messages": messages,
        "token_ids_available": token_ids is not None,
        "payload": payload,
        "network_calls": False,
        "warnings": warnings,
    }
    print(json.dumps(preview, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
