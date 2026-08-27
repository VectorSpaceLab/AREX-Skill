#!/usr/bin/env python3
"""Validate XTuner V1 JSONL datasets without importing XTuner or third-party packages.

The validator is intentionally schema-level: it checks JSONL shape, message fields,
reward fields, and local media references. It does not tokenize, inspect image bytes,
or require a model checkout.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

REMOTE_PREFIXES = ("http://", "https://", "s3://", "gs://", "oss://")

ROLE_ALIASES = {
    "human": "user",
    "user": "user",
    "assistant": "assistant",
    "gpt": "assistant",
    "bot": "assistant",
    "ai": "assistant",
    "system": "system",
    "developer": "developer",
    "tool": "tool",
    "pretrain": "pretrain",
    "environment": "environment",
    "pretrain_content": "pretrain_content",
    "pretrain_meta": "pretrain_meta",
    "answer_prefix": "answer_prefix",
    "answer_middle": "answer_middle",
    "answer_postfix": "answer_postfix",
}

OPENAI_ROLES = {"system", "developer", "user", "assistant", "tool", "pretrain"}
FTDP_EXTRA_ROLES = {"environment", "pretrain_content", "pretrain_meta", "answer_prefix", "answer_middle", "answer_postfix"}
SFT_ALLOWED_ROLES = OPENAI_ROLES | FTDP_EXTRA_ROLES
MLLM_ALLOWED_ROLES = OPENAI_ROLES
RL_ALLOWED_ROLES = {"system", "developer", "user", "assistant", "tool"}

IMAGE_TYPES = {"image", "image_url"}
VIDEO_TYPES = {"video", "video_url"}
TEXT_TYPES = {"text"}


class Report:
    def __init__(self, max_messages: int = 80) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.max_messages = max_messages
        self.records = 0
        self.messages = 0
        self.media_refs = 0
        self.checked_media_refs = 0
        self.remote_media_refs = 0
        self.approx_truncation_warnings = 0

    def error(self, line: int, path: str, message: str) -> None:
        text = f"line {line}{' ' + path if path else ''}: {message}"
        if len(self.errors) < self.max_messages:
            self.errors.append(text)
        elif len(self.errors) == self.max_messages:
            self.errors.append("... further errors suppressed ...")

    def warn(self, line: int, path: str, message: str) -> None:
        text = f"line {line}{' ' + path if path else ''}: {message}"
        if len(self.warnings) < self.max_messages:
            self.warnings.append(text)
        elif len(self.warnings) == self.max_messages:
            self.warnings.append("... further warnings suppressed ...")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate XTuner SFT, MLLM, or RL JSONL data with stdlib only.")
    parser.add_argument("jsonl", help="Path to a JSONL file.")
    parser.add_argument("--mode", choices=["sft", "mllm", "rl"], required=True, help="Schema family to validate.")
    parser.add_argument("--media-root", default=None, help="Root directory for local MLLM image/video references.")
    parser.add_argument(
        "--max-length",
        type=int,
        default=None,
        help="Optional tokenizer-free approximate token budget; emits warnings only.",
    )
    parser.add_argument(
        "--chars-per-token",
        type=float,
        default=4.0,
        help="Approximation used with --max-length. Default: 4 characters per token.",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=80,
        help="Maximum errors and warnings to print before suppressing extras.",
    )
    parser.add_argument(
        "--json-summary",
        action="store_true",
        help="Print a machine-readable summary after human-readable diagnostics.",
    )
    return parser.parse_args(argv)


def load_jsonl(path: Path, report: Report) -> list[tuple[int, Any]]:
    items: list[tuple[int, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line_no, raw in enumerate(f, start=1):
                text = raw.strip()
                if not text:
                    report.error(line_no, "", "blank JSONL lines are invalid")
                    continue
                try:
                    items.append((line_no, json.loads(text)))
                except json.JSONDecodeError as exc:
                    report.error(line_no, "", f"invalid JSON: {exc.msg} at column {exc.colno}")
    except FileNotFoundError:
        report.error(0, "", f"file not found: {path}")
    except OSError as exc:
        report.error(0, "", f"cannot read file: {exc}")
    return items


def normalize_role(raw_role: Any, line: int, path: str, allowed: set[str], report: Report) -> str | None:
    if not isinstance(raw_role, str) or not raw_role:
        report.error(line, path, "message role must be a non-empty string")
        return None
    normalized = ROLE_ALIASES.get(raw_role, raw_role)
    if raw_role != normalized:
        report.warn(line, path, f"role alias '{raw_role}' normalized to '{normalized}'")
    if normalized not in allowed:
        report.error(line, path, f"unsupported role '{raw_role}' for this mode")
        return None
    return normalized


def get_message_fields(msg: Any, line: int, path: str, allowed: set[str], report: Report) -> tuple[str | None, Any, bool]:
    if not isinstance(msg, dict):
        report.error(line, path, "message must be an object")
        return None, None, False

    used_variant = False
    if "role" in msg:
        raw_role = msg.get("role")
    elif "from" in msg:
        raw_role = msg.get("from")
        used_variant = True
        report.warn(line, path, "uses legacy 'from' role field; prefer 'role'")
    else:
        report.error(line, path, "missing message role")
        return None, None, used_variant

    role = normalize_role(raw_role, line, path, allowed, report)

    if "content" in msg:
        content = msg.get("content")
    elif "value" in msg:
        content = msg.get("value")
        used_variant = True
        report.warn(line, path, "uses legacy 'value' content field; prefer 'content'")
    else:
        report.error(line, path, "missing message content")
        content = None

    if role != "assistant" and msg.get("thinking") is not None:
        report.warn(line, path, "'thinking' is only meaningful on assistant messages")

    return role, content, used_variant


def extract_messages(obj: Any, line: int, report: Report, *, allow_bare_list: bool) -> list[Any] | None:
    if isinstance(obj, list):
        if allow_bare_list:
            return obj
        report.error(line, "", "bare message-list lines are not valid for this mode")
        return None
    if not isinstance(obj, dict):
        report.error(line, "", "record must be an object or a message list")
        return None
    if "messages" in obj:
        messages = obj["messages"]
    elif "dialogs" in obj:
        messages = obj["dialogs"]
        report.warn(line, ".dialogs", "uses 'dialogs'; ensure the selected tokenizer expects it")
    else:
        report.error(line, "", "missing 'messages' or 'dialogs'")
        return None
    if not isinstance(messages, list) or not messages:
        report.error(line, ".messages", "must be a non-empty list")
        return None
    return messages


def text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
        return "\n".join(parts)
    return ""


def media_ref_from_item(item: dict[str, Any]) -> tuple[str | None, str | None]:
    item_type = item.get("type")
    if item_type in IMAGE_TYPES or "image" in item or "image_url" in item:
        if isinstance(item.get("path"), str):
            return "image", item["path"]
        media_obj = item.get("image", item.get("image_url"))
        if isinstance(media_obj, dict):
            ref = media_obj.get("url") or media_obj.get("path")
            return "image", ref if isinstance(ref, str) else None
        if isinstance(media_obj, str):
            return "image", media_obj
        return "image", None
    if item_type in VIDEO_TYPES or "video" in item or "video_url" in item:
        if isinstance(item.get("path"), str):
            return "video", item["path"]
        media_obj = item.get("video", item.get("video_url"))
        if isinstance(media_obj, dict):
            ref = media_obj.get("url") or media_obj.get("path")
            return "video", ref if isinstance(ref, str) else None
        if isinstance(media_obj, str):
            return "video", media_obj
        return "video", None
    return None, None


def check_media_exists(ref: str, line: int, path: str, jsonl_path: Path, media_root: str | None, report: Report) -> None:
    report.media_refs += 1
    if ref.startswith(REMOTE_PREFIXES):
        report.remote_media_refs += 1
        return
    if os.path.isabs(ref):
        candidate = Path(ref)
        should_check = True
    elif media_root is not None:
        candidate = Path(media_root) / ref
        should_check = True
    else:
        candidate = jsonl_path.parent / ref
        should_check = False
    if should_check:
        report.checked_media_refs += 1
        if not candidate.exists():
            report.error(line, path, f"missing media file '{ref}' resolved as '{candidate}'")


def validate_content(
    content: Any,
    *,
    line: int,
    path: str,
    mode: str,
    role: str | None,
    jsonl_path: Path,
    media_root: str | None,
    report: Report,
) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts: list[str] = []
        for idx, item in enumerate(content):
            item_path = f"{path}.content[{idx}]"
            if not isinstance(item, dict):
                report.error(line, item_path, "content item must be an object")
                continue
            item_type = item.get("type")
            if item_type in TEXT_TYPES or "text" in item:
                if isinstance(item.get("text"), str):
                    texts.append(item["text"])
                elif isinstance(item.get("content"), str):
                    texts.append(item["content"])
                    report.warn(line, item_path, "text item uses 'content'; prefer 'text'")
                else:
                    report.error(line, item_path, "text item requires string 'text'")
                continue
            media_kind, ref = media_ref_from_item(item)
            if media_kind is not None:
                if mode == "sft":
                    report.warn(line, item_path, "media content found in SFT mode; use MLLM mode if media should be loaded")
                if not ref:
                    report.error(line, item_path, f"{media_kind} item requires a string URL or path")
                else:
                    check_media_exists(ref, line, item_path, jsonl_path, media_root, report)
                continue
            report.error(line, item_path, f"unsupported content item type {item_type!r}")
        return "\n".join(texts)
    report.error(line, path, "content must be a string or a list of content items")
    return ""


def maybe_warn_length(text: str, line: int, mode: str, args: argparse.Namespace, report: Report) -> None:
    if args.max_length is None:
        return
    divisor = args.chars_per_token if args.chars_per_token > 0 else 4.0
    approx_tokens = int(len(text) / divisor) + 1
    if approx_tokens > args.max_length:
        report.approx_truncation_warnings += 1
        report.warn(
            line,
            "",
            f"approx {approx_tokens} tokens may exceed max_length={args.max_length} in {mode} mode; confirm with real tokenizer",
        )


def validate_messages(
    messages: list[Any],
    *,
    line: int,
    mode: str,
    allowed_roles: set[str],
    jsonl_path: Path,
    media_root: str | None,
    report: Report,
) -> tuple[list[str], str]:
    roles: list[str] = []
    texts: list[str] = []
    for idx, msg in enumerate(messages):
        msg_path = f".messages[{idx}]"
        role, content, _ = get_message_fields(msg, line, msg_path, allowed_roles, report)
        if role:
            roles.append(role)
        if content is not None:
            texts.append(
                validate_content(
                    content,
                    line=line,
                    path=msg_path,
                    mode=mode,
                    role=role,
                    jsonl_path=jsonl_path,
                    media_root=media_root,
                    report=report,
                )
            )
        report.messages += 1
    return roles, "\n".join(t for t in texts if t)


def validate_sft(obj: Any, line: int, jsonl_path: Path, args: argparse.Namespace, report: Report) -> None:
    messages = extract_messages(obj, line, report, allow_bare_list=True)
    if not messages:
        return
    roles, text = validate_messages(
        messages,
        line=line,
        mode="sft",
        allowed_roles=SFT_ALLOWED_ROLES,
        jsonl_path=jsonl_path,
        media_root=args.media_root,
        report=report,
    )
    if "assistant" not in roles and "pretrain" not in roles:
        report.warn(line, "", "no assistant or pretrain message found; sample may not contribute supervised labels")
    maybe_warn_length(text, line, "sft", args, report)


def validate_mllm(obj: Any, line: int, jsonl_path: Path, args: argparse.Namespace, report: Report) -> None:
    messages = extract_messages(obj, line, report, allow_bare_list=False)
    if not messages:
        return
    before_media = report.media_refs
    roles, text = validate_messages(
        messages,
        line=line,
        mode="mllm",
        allowed_roles=MLLM_ALLOWED_ROLES,
        jsonl_path=jsonl_path,
        media_root=args.media_root,
        report=report,
    )
    if "assistant" not in roles and "pretrain" not in roles:
        report.warn(line, "", "no assistant or pretrain message found")
    if report.media_refs == before_media:
        report.warn(line, "", "MLLM mode record contains no image/video content")
    maybe_warn_length(text, line, "mllm", args, report)


def validate_rl(obj: Any, line: int, jsonl_path: Path, args: argparse.Namespace, report: Report) -> None:
    if not isinstance(obj, dict):
        report.error(line, "", "RL record must be an object")
        return
    prompt = obj.get("prompt")
    if not isinstance(prompt, list) or not prompt:
        report.error(line, ".prompt", "must be a non-empty list of messages")
        prompt = []
    _, text = validate_messages(
        prompt,
        line=line,
        mode="rl",
        allowed_roles=RL_ALLOWED_ROLES,
        jsonl_path=jsonl_path,
        media_root=args.media_root,
        report=report,
    )
    if not obj.get("data_source"):
        report.error(line, ".data_source", "is required by RL tokenization/judger mapping")
    reward_model = obj.get("reward_model")
    if not isinstance(reward_model, dict):
        report.error(line, ".reward_model", "must be an object with ground_truth")
    else:
        ground_truth = reward_model.get("ground_truth")
        if ground_truth is None or str(ground_truth) == "":
            report.error(line, ".reward_model.ground_truth", "is required and must be non-empty")
        if reward_model.get("style") not in (None, "rule"):
            report.warn(line, ".reward_model.style", "unexpected style for GSM8K-style rule reward")
    if "ability" not in obj:
        report.warn(line, ".ability", "missing ability field; GSM8K examples use 'math'")
    maybe_warn_length(text, line, "rl", args, report)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    jsonl_path = Path(args.jsonl)
    report = Report(max_messages=args.max_messages)

    items = load_jsonl(jsonl_path, report)
    for line, obj in items:
        report.records += 1
        if args.mode == "sft":
            validate_sft(obj, line, jsonl_path, args, report)
        elif args.mode == "mllm":
            validate_mllm(obj, line, jsonl_path, args, report)
        elif args.mode == "rl":
            validate_rl(obj, line, jsonl_path, args, report)
        else:  # pragma: no cover - argparse prevents this
            raise AssertionError(args.mode)

    summary = {
        "ok": not report.errors,
        "records": report.records,
        "messages": report.messages,
        "media_refs": report.media_refs,
        "checked_media_refs": report.checked_media_refs,
        "remote_media_refs": report.remote_media_refs,
        "errors": len(report.errors),
        "warnings": len(report.warnings),
        "approx_truncation_warnings": report.approx_truncation_warnings,
    }

    if args.json_summary:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    else:
        if report.errors:
            print(f"FAILED: {len(report.errors)} error entries while validating {jsonl_path} (mode={args.mode})")
            for err in report.errors:
                print(f"ERROR: {err}")
        else:
            print(
                f"OK: validated {report.records} records, {report.messages} messages, "
                f"{report.media_refs} media refs ({report.checked_media_refs} checked) in {jsonl_path} (mode={args.mode})"
            )

        if report.warnings:
            print(f"WARNINGS: {len(report.warnings)} warning entries")
            for warning in report.warnings:
                print(f"WARNING: {warning}")

    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
