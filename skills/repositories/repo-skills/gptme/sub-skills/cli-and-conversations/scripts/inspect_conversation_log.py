#!/usr/bin/env python3
"""Summarize and redact gptme conversation logs without importing gptme.

The script is read-only. It accepts one conversation.jsonl file, one conversation
log directory containing conversation.jsonl, or a directory containing multiple
conversation directories.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"(?i)\b(authorization\s*[:=]\s*bearer)\s+[A-Za-z0-9._~+/=-]{8,}"
        ),
        r"\1 [REDACTED]",
    ),
    (
        re.compile(
            r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|passwd)\b"
            r"\s*[:=]\s*['\"]?[^\s'\"]{6,}"
        ),
        r"\1=[REDACTED]",
    ),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b"), "sk-[REDACTED]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"), "gh[REDACTED]"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{16,}\b"), "xox[REDACTED]"),
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[EMAIL]",
    ),
)

TOOL_FENCE_TAGS = {
    "append",
    "browser",
    "computer",
    "ipython",
    "patch",
    "python",
    "read",
    "save",
    "shell",
    "sh",
    "subagent",
    "tmux",
    "vision",
}


def redact(text: str) -> str:
    """Return text with common secret-like values replaced."""
    result = text
    for pattern, replacement in SECRET_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def compact_snippet(text: str, limit: int) -> str:
    redacted = redact(text or "")
    one_line = " ".join(redacted.split())
    if len(one_line) <= limit:
        return one_line
    return one_line[: max(0, limit - 1)].rstrip() + "…"


@dataclass
class MessageSample:
    index: int
    role: str
    timestamp: str | None
    snippet: str
    files: int = 0
    model: str | None = None
    tool: str | None = None


@dataclass
class LogSummary:
    path: str
    conversation_id: str
    messages: int = 0
    blank_lines: int = 0
    malformed_lines: int = 0
    roles: Counter[str] = field(default_factory=Counter)
    models: Counter[str] = field(default_factory=Counter)
    tools: Counter[str] = field(default_factory=Counter)
    fence_tags: Counter[str] = field(default_factory=Counter)
    files: int = 0
    file_refs: list[str] = field(default_factory=list)
    hidden_messages: int = 0
    quiet_messages: int = 0
    call_ids: int = 0
    total_cost: float = 0.0
    usage: Counter[str] = field(default_factory=Counter)
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    queue_exists: bool = False
    queue_items: int = 0
    closed_sentinel_exists: bool = False
    samples: list[MessageSample] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "conversation_id": self.conversation_id,
            "messages": self.messages,
            "blank_lines": self.blank_lines,
            "malformed_lines": self.malformed_lines,
            "roles": dict(self.roles),
            "models": dict(self.models),
            "tools": dict(self.tools),
            "fence_tags": dict(self.fence_tags),
            "files": self.files,
            "file_refs_sample": self.file_refs[:20],
            "hidden_messages": self.hidden_messages,
            "quiet_messages": self.quiet_messages,
            "call_ids": self.call_ids,
            "total_cost": round(self.total_cost, 8),
            "usage": dict(self.usage),
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "queue_exists": self.queue_exists,
            "queue_items": self.queue_items,
            "closed_sentinel_exists": self.closed_sentinel_exists,
            "samples": [sample.__dict__ for sample in self.samples],
        }


def discover_logs(path: Path, recursive: bool, max_logs: int) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.is_dir():
        raise FileNotFoundError(f"not a file or directory: {path}")

    direct = path / "conversation.jsonl"
    if direct.exists():
        return [direct]

    pattern = "**/conversation.jsonl" if recursive else "*/conversation.jsonl"
    logs = sorted(path.glob(pattern))
    if len(logs) > max_logs:
        raise RuntimeError(
            f"found {len(logs)} conversation logs, exceeding --max-logs {max_logs}"
        )
    return logs


def _extract_metadata(message: dict[str, Any]) -> dict[str, Any]:
    metadata = message.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _record_usage(summary: LogSummary, metadata: dict[str, Any]) -> None:
    cost = metadata.get("cost")
    if isinstance(cost, (int, float)):
        summary.total_cost += float(cost)

    usage = metadata.get("usage")
    if isinstance(usage, dict):
        for key, value in usage.items():
            if isinstance(value, int):
                summary.usage[key] += value


def _record_tools(summary: LogSummary, message: dict[str, Any], content: str) -> None:
    metadata = _extract_metadata(message)
    tool = metadata.get("tool")
    if isinstance(tool, str) and tool:
        summary.tools[tool] += 1

    if message.get("call_id"):
        summary.call_ids += 1

    for tag in re.findall(r"```([A-Za-z0-9_.-]+)", content):
        normalized = tag.lower()
        if normalized in TOOL_FENCE_TAGS:
            summary.fence_tags[normalized] += 1

    for name in re.findall(r"@([A-Za-z_][A-Za-z0-9_-]*)\([^)]*\):", content):
        summary.tools[name] += 1


def summarize_log(log_path: Path, sample_limit: int, sample_mode: str, snippet_limit: int) -> LogSummary:
    logdir = log_path.parent
    summary = LogSummary(path=str(log_path), conversation_id=logdir.name)
    queue_path = logdir / "prompt-queue.jsonl"
    summary.queue_exists = queue_path.exists()
    if summary.queue_exists:
        try:
            summary.queue_items = sum(1 for line in queue_path.read_text(encoding="utf-8").splitlines() if line.strip())
        except OSError:
            summary.queue_items = -1
    summary.closed_sentinel_exists = (logdir / "prompt-queue-closed").exists()

    tail_samples: deque[MessageSample] = deque(maxlen=max(0, sample_limit))
    head_samples: list[MessageSample] = []

    with log_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                summary.blank_lines += 1
                continue
            try:
                message = json.loads(stripped)
            except json.JSONDecodeError:
                summary.malformed_lines += 1
                continue
            if not isinstance(message, dict):
                summary.malformed_lines += 1
                continue

            summary.messages += 1
            role = str(message.get("role", "unknown"))
            content = str(message.get("content", ""))
            summary.roles[role] += 1

            timestamp = message.get("timestamp")
            timestamp_str = str(timestamp) if timestamp else None
            if timestamp_str and summary.first_timestamp is None:
                summary.first_timestamp = timestamp_str
            if timestamp_str:
                summary.last_timestamp = timestamp_str

            metadata = _extract_metadata(message)
            model = metadata.get("model")
            model_str = str(model) if model else None
            if model_str:
                summary.models[model_str] += 1

            if message.get("hide"):
                summary.hidden_messages += 1
            if message.get("quiet"):
                summary.quiet_messages += 1

            files = message.get("files")
            file_count = len(files) if isinstance(files, list) else 0
            summary.files += file_count
            if isinstance(files, list) and len(summary.file_refs) < 20:
                for ref in files:
                    if len(summary.file_refs) >= 20:
                        break
                    summary.file_refs.append(redact(str(ref)))

            _record_usage(summary, metadata)
            _record_tools(summary, message, content)

            if sample_limit > 0:
                sample = MessageSample(
                    index=line_no,
                    role=role,
                    timestamp=timestamp_str,
                    snippet=compact_snippet(content, snippet_limit),
                    files=file_count,
                    model=model_str,
                    tool=str(metadata.get("tool")) if metadata.get("tool") else None,
                )
                if sample_mode == "head":
                    if len(head_samples) < sample_limit:
                        head_samples.append(sample)
                else:
                    tail_samples.append(sample)

    summary.samples = head_samples if sample_mode == "head" else list(tail_samples)
    return summary


def format_counter(counter: Counter[str], limit: int = 6) -> str:
    if not counter:
        return "-"
    return ", ".join(f"{key}:{value}" for key, value in counter.most_common(limit))


def print_text(summaries: list[LogSummary]) -> None:
    if len(summaries) > 1:
        print(f"Conversation logs: {len(summaries)}")
        total_messages = sum(s.messages for s in summaries)
        total_cost = sum(s.total_cost for s in summaries)
        print(f"Total messages: {total_messages}")
        print(f"Total cost metadata: {total_cost:.6f}")
        print()
        for summary in summaries:
            print(
                f"- {summary.conversation_id}: {summary.messages} messages; "
                f"roles={format_counter(summary.roles)}; "
                f"models={format_counter(summary.models, 3)}; "
                f"cost={summary.total_cost:.6f}; "
                f"malformed={summary.malformed_lines}; "
                f"queue_items={summary.queue_items if summary.queue_exists else 0}"
            )
        return

    summary = summaries[0]
    print(f"Path: {summary.path}")
    print(f"Conversation: {summary.conversation_id}")
    print(f"Messages: {summary.messages}")
    print(f"Roles: {format_counter(summary.roles)}")
    print(f"Models: {format_counter(summary.models)}")
    print(f"Tools from metadata/output: {format_counter(summary.tools)}")
    print(f"Tool fence tags: {format_counter(summary.fence_tags)}")
    print(f"Files referenced: {summary.files}")
    print(f"Hidden messages: {summary.hidden_messages}")
    print(f"Quiet messages: {summary.quiet_messages}")
    print(f"Call IDs: {summary.call_ids}")
    print(f"Total cost metadata: {summary.total_cost:.8f}")
    print(f"Usage metadata: {format_counter(summary.usage)}")
    print(f"First timestamp: {summary.first_timestamp or '-'}")
    print(f"Last timestamp: {summary.last_timestamp or '-'}")
    print(f"Blank lines: {summary.blank_lines}")
    print(f"Malformed lines: {summary.malformed_lines}")
    print(f"Queue exists: {summary.queue_exists}")
    print(f"Queue items: {summary.queue_items}")
    print(f"Closed sentinel exists: {summary.closed_sentinel_exists}")
    if summary.file_refs:
        print("File references sample:")
        for ref in summary.file_refs[:20]:
            print(f"  - {ref}")
    if summary.samples:
        print("Samples (redacted):")
        for sample in summary.samples:
            extras = []
            if sample.files:
                extras.append(f"files={sample.files}")
            if sample.model:
                extras.append(f"model={sample.model}")
            if sample.tool:
                extras.append(f"tool={sample.tool}")
            suffix = f" ({', '.join(extras)})" if extras else ""
            timestamp = f" {sample.timestamp}" if sample.timestamp else ""
            print(f"  #{sample.index} {sample.role}{timestamp}{suffix}: {sample.snippet}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize and redact gptme conversation.jsonl logs without executing gptme.",
    )
    parser.add_argument(
        "path",
        type=Path,
        help="conversation.jsonl file, conversation directory, or directory of conversation directories",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="when PATH is a directory without a direct conversation.jsonl, search recursively",
    )
    parser.add_argument(
        "--max-logs",
        type=int,
        default=200,
        help="maximum conversation logs to summarize from a parent directory (default: 200)",
    )
    parser.add_argument(
        "--sample",
        choices=("head", "tail"),
        default="tail",
        help="show first or last messages for a single-log text report (default: tail)",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=8,
        help="maximum redacted sample messages to include for one log (default: 8; use 0 for none)",
    )
    parser.add_argument(
        "--snippet-chars",
        type=int,
        default=240,
        help="maximum characters per redacted sample snippet (default: 240)",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="emit JSON instead of text",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.max_logs < 1:
        print("--max-logs must be positive", file=sys.stderr)
        return 2
    if args.max_messages < 0:
        print("--max-messages must be non-negative", file=sys.stderr)
        return 2
    if args.snippet_chars < 20:
        print("--snippet-chars must be at least 20", file=sys.stderr)
        return 2

    try:
        logs = discover_logs(args.path, recursive=args.recursive, max_logs=args.max_logs)
        if not logs:
            print(f"no conversation.jsonl files found under {args.path}", file=sys.stderr)
            return 1
        summaries = [
            summarize_log(
                log_path,
                sample_limit=args.max_messages,
                sample_mode=args.sample,
                snippet_limit=args.snippet_chars,
            )
            for log_path in logs
        ]
    except (OSError, RuntimeError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps([summary.as_dict() for summary in summaries], indent=2))
    else:
        print_text(summaries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
