#!/usr/bin/env python3
"""Summarize small mcp-agent JSONL event logs safely.

This helper adapts the repository's event replay, event summary, and log trimmer
ideas into a non-interactive, stdlib-only utility. It validates tiny JSONL logs,
counts levels/namespaces/progress actions/tool events, redacts sensitive fields,
and never imports mcp-agent runtime modules.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

SENSITIVE_RE = re.compile(
    r"(api[_-]?key|authorization|token|secret|password|credential|cookie)",
    re.IGNORECASE,
)


def redact(value: Any, key: str = "") -> Any:
    if SENSITIVE_RE.search(key):
        if value in (None, ""):
            return value
        return "<redacted>"
    if isinstance(value, dict):
        return {item_key: redact(item_value, item_key) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [redact(item, key) for item in value]
    return value


def parse_timestamp(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).isoformat()
    except ValueError:
        return None


def normalize_event(raw: dict[str, Any]) -> dict[str, Any]:
    level = raw.get("level", raw.get("type", "info"))
    if isinstance(level, str):
        level = level.lower()
    else:
        level = "info"

    data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
    nested_data = data.get("data") if isinstance(data.get("data"), dict) else data
    trace = raw.get("trace") if isinstance(raw.get("trace"), dict) else {}

    return {
        "level": level,
        "timestamp": parse_timestamp(raw.get("timestamp")),
        "namespace": str(raw.get("namespace", "")),
        "name": raw.get("name"),
        "message": str(raw.get("message", "")),
        "data": data,
        "nested_data": nested_data if isinstance(nested_data, dict) else {},
        "trace_id": raw.get("trace_id") or trace.get("trace_id"),
        "span_id": raw.get("span_id") or trace.get("span_id"),
    }


def iter_events(path: Path, limit: int | None, strict: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    bad_lines: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if limit is not None and len(events) >= limit:
                break
            stripped = line.strip()
            if not stripped:
                continue
            try:
                raw = json.loads(stripped)
                if not isinstance(raw, dict):
                    raise ValueError("line is not a JSON object")
                events.append(normalize_event(raw))
            except Exception as exc:  # noqa: BLE001 - report and optionally continue
                bad = {"line": line_number, "error": str(exc)}
                bad_lines.append(bad)
                if strict:
                    raise ValueError(f"invalid JSONL at line {line_number}: {exc}") from exc
    return events, bad_lines


def summarize(events: list[dict[str, Any]], bad_lines: list[dict[str, Any]], path: Path, limit: int | None) -> dict[str, Any]:
    levels = Counter(event["level"] for event in events)
    namespaces = Counter(event["namespace"] or "(none)" for event in events)
    progress_actions = Counter(
        str(event["nested_data"].get("progress_action"))
        for event in events
        if event["nested_data"].get("progress_action")
    )
    agents = Counter(
        str(event["nested_data"].get("agent_name"))
        for event in events
        if event["nested_data"].get("agent_name")
    )
    tool_events = [
        event
        for event in events
        if "tool" in event["message"].lower()
        or "tool" in str(event["nested_data"].get("progress_action", "")).lower()
        or event["nested_data"].get("tool_name")
    ]
    traced = sum(1 for event in events if event.get("trace_id") or event.get("span_id"))
    timestamped = [event["timestamp"] for event in events if event.get("timestamp")]

    sample_events = []
    for event in events[:5]:
        sample_events.append(
            redact(
                {
                    "level": event["level"],
                    "timestamp": event["timestamp"],
                    "namespace": event["namespace"],
                    "message": event["message"][:160],
                    "progress_action": event["nested_data"].get("progress_action"),
                    "agent_name": event["nested_data"].get("agent_name"),
                    "tool_name": event["nested_data"].get("tool_name"),
                    "has_trace": bool(event.get("trace_id") or event.get("span_id")),
                }
            )
        )

    return {
        "path": str(path),
        "events_read": len(events),
        "limit": limit,
        "malformed_lines": bad_lines,
        "levels": dict(levels.most_common()),
        "top_namespaces": dict(namespaces.most_common(10)),
        "progress_actions": dict(progress_actions.most_common()),
        "agents": dict(agents.most_common(10)),
        "tool_event_count": len(tool_events),
        "events_with_trace_context": traced,
        "first_timestamp": min(timestamped) if timestamped else None,
        "last_timestamp": max(timestamped) if timestamped else None,
        "sample_events": sample_events,
    }


def print_text(report: dict[str, Any]) -> None:
    print(f"Event log: {report['path']}")
    print(f"Events read: {report['events_read']}")
    if report["limit"] is not None:
        print(f"Limit: {report['limit']}")
    print(f"Malformed lines: {len(report['malformed_lines'])}")
    print(f"Events with trace context: {report['events_with_trace_context']}")
    if report["first_timestamp"] or report["last_timestamp"]:
        print(f"Time range: {report['first_timestamp']} -> {report['last_timestamp']}")
    print("Levels:")
    for level, count in report["levels"].items():
        print(f"  - {level}: {count}")
    if report["progress_actions"]:
        print("Progress actions:")
        for action, count in report["progress_actions"].items():
            print(f"  - {action}: {count}")
    if report["top_namespaces"]:
        print("Top namespaces:")
        for namespace, count in report["top_namespaces"].items():
            print(f"  - {namespace}: {count}")
    if report["sample_events"]:
        print("Sample events:")
        for event in report["sample_events"]:
            print(f"  - [{event['level']}] {event['namespace']}: {event['message']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize an mcp-agent JSONL event log safely.")
    parser.add_argument("log_file", type=Path, help="Path to JSONL event log")
    parser.add_argument("--limit", type=int, default=None, help="Maximum valid events to read")
    parser.add_argument("--strict", action="store_true", help="Fail on the first malformed line")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args(argv)

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    if not args.log_file.exists():
        print(f"error: log file not found: {args.log_file}", file=sys.stderr)
        return 2

    try:
        events, bad_lines = iter_events(args.log_file, args.limit, args.strict)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    report = summarize(events, bad_lines, args.log_file, args.limit)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if not bad_lines or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
