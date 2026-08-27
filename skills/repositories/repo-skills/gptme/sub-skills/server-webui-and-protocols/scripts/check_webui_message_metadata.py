#!/usr/bin/env python3
"""Validate REST/SSE message dictionaries for Web UI metadata consistency.

The main Web UI reads assistant message metadata from both the REST conversation
payload and the SSE completion path. This helper loads representative samples,
checks that the message shape is sane, and compares the metadata keys that the
UI actually reads.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

ALLOWED_ROLES = {"user", "assistant", "system", "tool"}
CORE_METADATA_FIELDS = ("model", "resolved_model", "cost", "usage", "tool", "panel_hints")
USAGE_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_creation_tokens",
)
PANEL_KINDS = {"iframe", "live_app"}
LIVE_APP_STATUSES = {"loading", "running", "stopped", "error", "unavailable"}


@dataclass
class Issue:
    source: str
    message: str


@dataclass
class Sample:
    source: str
    path: str
    messages: list[dict[str, Any]]
    representative: dict[str, Any] | None


@dataclass
class ValidationSummary:
    rest: Sample | None
    sse: Sample | None
    issues: list[Issue]
    compared: bool


def _read_text(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).expanduser().read_text(encoding="utf-8")


def _parse_documents(text: str) -> list[Any]:
    """Parse JSON, JSON lines, or SSE-style `data:` envelopes.

    The parser is intentionally permissive so it can handle:

    - a single JSON object
    - a JSON list
    - newline-delimited JSON objects
    - SSE event streams that use `data: {...}` lines
    """
    decoder = json.JSONDecoder()
    docs: list[Any] = []
    idx = 0
    length = len(text)

    while idx < length:
        while idx < length and text[idx].isspace():
            idx += 1
        if idx >= length:
            break
        if text.startswith("data:", idx):
            idx += len("data:")
            while idx < length and text[idx].isspace():
                idx += 1
        obj, end = decoder.raw_decode(text, idx)
        docs.append(obj)
        idx = end

    return docs


def _extract_messages(node: Any) -> list[dict[str, Any]]:
    """Recursively extract message-like dictionaries from a parsed payload."""
    messages: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("role"), str) and isinstance(value.get("content"), str):
                messages.append(value)
            message = value.get("message")
            if isinstance(message, dict):
                walk(message)
            for child in value.values():
                if child is not message:
                    walk(child)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(node)
    return messages


def _select_representative(messages: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not messages:
        return None
    for msg in messages:
        if msg.get("role") == "assistant" and isinstance(msg.get("metadata"), dict):
            return msg
    for msg in messages:
        if isinstance(msg.get("metadata"), dict):
            return msg
    for msg in messages:
        if msg.get("role") == "assistant":
            return msg
    return messages[0]


def _normalize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    return {key: metadata[key] for key in CORE_METADATA_FIELDS if key in metadata}


def _validate_panel_hint(hint: Any, source: str, index: int) -> list[Issue]:
    issues: list[Issue] = []
    prefix = f"{source}: metadata.panel_hints[{index}]"
    if not isinstance(hint, dict):
        issues.append(Issue(prefix, "panel hint must be an object"))
        return issues

    kind = hint.get("kind")
    if kind not in PANEL_KINDS:
        issues.append(Issue(prefix, f"kind must be one of {sorted(PANEL_KINDS)}"))
    panel_id = hint.get("id")
    if not isinstance(panel_id, str) or not panel_id.strip():
        issues.append(Issue(prefix, "id must be a non-empty string"))

    title = hint.get("title")
    if title is not None and not isinstance(title, str):
        issues.append(Issue(prefix, "title must be a string when present"))

    if kind == "iframe":
        src = hint.get("src")
        if not isinstance(src, str) or not src.strip():
            issues.append(Issue(prefix, "iframe hints need a non-empty src"))
        resize = hint.get("resize")
        if resize is not None and resize not in {"auto", "fixed"}:
            issues.append(Issue(prefix, "resize must be 'auto' or 'fixed' when present"))
    elif kind == "live_app":
        url = hint.get("url")
        if not isinstance(url, str) or not url.strip():
            issues.append(Issue(prefix, "live_app hints need a non-empty url"))
        status = hint.get("status")
        if status is not None and status not in LIVE_APP_STATUSES:
            issues.append(Issue(prefix, f"status must be one of {sorted(LIVE_APP_STATUSES)}"))

    sandbox = hint.get("sandbox")
    if sandbox is not None:
        if not isinstance(sandbox, list) or not all(isinstance(item, str) for item in sandbox):
            issues.append(Issue(prefix, "sandbox must be a list of strings when present"))

    bootstrap = hint.get("bootstrap")
    if bootstrap is not None and not isinstance(bootstrap, dict):
        issues.append(Issue(prefix, "bootstrap must be an object when present"))

    return issues


def _validate_message(message: dict[str, Any], source: str, index: int) -> list[Issue]:
    issues: list[Issue] = []
    prefix = f"{source}: message[{index}]"

    role = message.get("role")
    content = message.get("content")
    timestamp = message.get("timestamp")
    metadata = message.get("metadata")

    if not isinstance(role, str):
        issues.append(Issue(prefix, "role must be a string"))
    elif role not in ALLOWED_ROLES:
        issues.append(Issue(prefix, f"role must be one of {sorted(ALLOWED_ROLES)}"))

    if not isinstance(content, str):
        issues.append(Issue(prefix, "content must be a string"))

    if timestamp is not None and not isinstance(timestamp, str):
        issues.append(Issue(prefix, "timestamp must be a string when present"))

    if "call_id" in message and not isinstance(message["call_id"], str):
        issues.append(Issue(prefix, "call_id must be a string when present"))

    files = message.get("files")
    if files is not None:
        if not isinstance(files, list) or not all(isinstance(item, str) for item in files):
            issues.append(Issue(prefix, "files must be a list of strings when present"))

    if metadata is None:
        return issues
    if not isinstance(metadata, dict):
        issues.append(Issue(prefix, "metadata must be an object when present"))
        return issues

    model = metadata.get("model")
    resolved_model = metadata.get("resolved_model")
    cost = metadata.get("cost")
    usage = metadata.get("usage")
    tool = metadata.get("tool")
    panel_hints = metadata.get("panel_hints")

    if model is not None and not isinstance(model, str):
        issues.append(Issue(prefix, "metadata.model must be a string when present"))
    if resolved_model is not None and not isinstance(resolved_model, str):
        issues.append(
            Issue(prefix, "metadata.resolved_model must be a string when present")
        )
    if cost is not None and not isinstance(cost, (int, float)):
        issues.append(Issue(prefix, "metadata.cost must be numeric when present"))
    if tool is not None and not isinstance(tool, str):
        issues.append(Issue(prefix, "metadata.tool must be a string when present"))

    if usage is not None:
        if not isinstance(usage, dict):
            issues.append(Issue(prefix, "metadata.usage must be an object when present"))
        else:
            for field in USAGE_FIELDS:
                value = usage.get(field)
                if value is not None and not isinstance(value, int):
                    issues.append(
                        Issue(prefix, f"metadata.usage.{field} must be an integer when present")
                    )

    if panel_hints is not None:
        if not isinstance(panel_hints, list):
            issues.append(Issue(prefix, "metadata.panel_hints must be a list when present"))
        else:
            for panel_index, hint in enumerate(panel_hints):
                issues.extend(_validate_panel_hint(hint, source, panel_index))

    if role == "assistant" and metadata and model is None and resolved_model is None:
        issues.append(
            Issue(
                prefix,
                "assistant metadata should include model or resolved_model for Web UI labels",
            )
        )

    return issues


def _load_sample(path: str, source: str) -> Sample:
    text = _read_text(path)
    docs = _parse_documents(text)
    messages: list[dict[str, Any]] = []
    for doc in docs:
        messages.extend(_extract_messages(doc))
    representative = _select_representative(messages)
    return Sample(source=source, path=path, messages=messages, representative=representative)


def _compare_samples(rest: Sample | None, sse: Sample | None) -> list[Issue]:
    issues: list[Issue] = []
    if rest is None or sse is None:
        return issues

    rest_meta = _normalize_metadata((rest.representative or {}).get("metadata"))
    sse_meta = _normalize_metadata((sse.representative or {}).get("metadata"))

    if rest_meta != sse_meta:
        rest_keys = set(rest_meta)
        sse_keys = set(sse_meta)
        missing_on_rest = sorted(sse_keys - rest_keys)
        missing_on_sse = sorted(rest_keys - sse_keys)
        if missing_on_rest:
            issues.append(
                Issue(
                    "comparison",
                    f"REST sample is missing metadata keys present in SSE: {missing_on_rest}",
                )
            )
        if missing_on_sse:
            issues.append(
                Issue(
                    "comparison",
                    f"SSE sample is missing metadata keys present in REST: {missing_on_sse}",
                )
            )
        for key in sorted(rest_keys & sse_keys):
            if rest_meta.get(key) != sse_meta.get(key):
                issues.append(
                    Issue(
                        "comparison",
                        f"metadata.{key} differs between REST and SSE samples",
                    )
                )

    return issues


def _render_text(summary: ValidationSummary) -> str:
    lines: list[str] = []
    for sample in (summary.rest, summary.sse):
        if sample is None:
            continue
        rep = sample.representative or {}
        metadata = _normalize_metadata(rep.get("metadata"))
        lines.append(
            f"{sample.source}: {len(sample.messages)} message(s), "
            f"representative_role={rep.get('role', 'none')!r}, metadata_keys={sorted(metadata)}"
        )
    if summary.issues:
        lines.append("")
        lines.append("issues:")
        for issue in summary.issues:
            lines.append(f"- {issue.source}: {issue.message}")
    else:
        lines.append("ok")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate REST/SSE message dictionaries against the Web UI metadata contract.",
    )
    parser.add_argument(
        "--rest",
        metavar="PATH",
        help="REST sample (conversation response, message dict, or JSON/JSONL file). Use '-' for stdin.",
    )
    parser.add_argument(
        "--sse",
        metavar="PATH",
        help="SSE sample (generation_complete, message_added, or JSON/JSONL file). Use '-' for stdin.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not args.rest and not args.sse:
        print("error: provide at least --rest or --sse", file=sys.stderr)
        return 2

    rest_sample = _load_sample(args.rest, "rest") if args.rest else None
    sse_sample = _load_sample(args.sse, "sse") if args.sse else None

    issues: list[Issue] = []
    if rest_sample is not None:
        for index, message in enumerate(rest_sample.messages):
            issues.extend(_validate_message(message, rest_sample.source, index))
    if sse_sample is not None:
        for index, message in enumerate(sse_sample.messages):
            issues.extend(_validate_message(message, sse_sample.source, index))

    issues.extend(_compare_samples(rest_sample, sse_sample))
    summary = ValidationSummary(rest=rest_sample, sse=sse_sample, issues=issues, compared=rest_sample is not None and sse_sample is not None)

    if args.json:
        payload = {
            "rest": asdict(rest_sample) if rest_sample is not None else None,
            "sse": asdict(sse_sample) if sse_sample is not None else None,
            "issues": [asdict(issue) for issue in issues],
            "ok": not issues,
            "compared": summary.compared,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_render_text(summary))

    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
