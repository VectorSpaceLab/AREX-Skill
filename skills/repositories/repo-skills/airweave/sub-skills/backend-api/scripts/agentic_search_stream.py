#!/usr/bin/env python3
"""CLI viewer for Airweave agentic search SSE events.

This helper is intentionally self-contained and safe by default: it only sends a
single POST request to a user-provided Airweave API host and prints received
Server-Sent Events. It does not depend on the original repository checkout.

Example:
    python scripts/agentic_search_stream.py my-collection "find deployment docs" \
        --host http://localhost:8001 --api-key "$AIRWEAVE_API_KEY" --limit 5

Current endpoint:
    POST /collections/{readable_id}/search/agentic/stream
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any


class Palette:
    """ANSI color helper that can be disabled."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def _wrap(self, code: str, text: str) -> str:
        if not self.enabled:
            return text
        return f"\033[{code}m{text}\033[0m"

    def dim(self, text: str) -> str:
        return self._wrap("2", text)

    def bold(self, text: str) -> str:
        return self._wrap("1", text)

    def cyan(self, text: str) -> str:
        return self._wrap("36", text)

    def green(self, text: str) -> str:
        return self._wrap("32", text)

    def yellow(self, text: str) -> str:
        return self._wrap("33", text)

    def red(self, text: str) -> str:
        return self._wrap("31", text)

    def magenta(self, text: str) -> str:
        return self._wrap("35", text)


PALETTE = Palette(enabled=True)


def wrap_text(text: Any, width: int = 94, indent: str = "  ") -> str:
    """Wrap a value as display text."""
    raw = str(text if text is not None else "")
    words = raw.split()
    if not words:
        return ""
    lines: list[str] = []
    current = ""
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        lines.append(current)
    return f"\n{indent}".join(lines)


def normalize_host(host: str) -> str:
    """Remove a trailing slash from the host/base URL."""
    return host.rstrip("/")


def bearer_header(api_key: str | None) -> str | None:
    """Return an Authorization header value for a supplied key/token."""
    if not api_key:
        return None
    value = api_key.strip()
    if not value:
        return None
    if value.lower().startswith("bearer "):
        return value
    return f"Bearer {value}"


def parse_filter(raw_filter: str | None) -> list[dict[str, Any]] | None:
    """Parse and validate the v2 filter JSON argument."""
    if not raw_filter:
        return None
    try:
        parsed = json.loads(raw_filter)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--filter must be valid JSON: {exc}") from exc
    if not isinstance(parsed, list):
        raise SystemExit("--filter must be a v2 filter list, e.g. '[{\"conditions\":[...]}]'")
    return parsed


def build_body(args: argparse.Namespace) -> dict[str, Any]:
    """Build the AgenticSearchRequest body."""
    body: dict[str, Any] = {"query": args.query}
    if args.thinking:
        body["thinking"] = True
    if args.limit is not None:
        body["limit"] = args.limit
    parsed_filter = parse_filter(args.filter)
    if parsed_filter:
        body["filter"] = parsed_filter
    return body


def build_headers(args: argparse.Namespace) -> dict[str, str]:
    """Build request headers without printing secrets."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache",
    }
    auth = bearer_header(args.api_key or os.getenv("AIRWEAVE_API_KEY"))
    if auth:
        headers["Authorization"] = auth
    org_id = args.organization_id or os.getenv("AIRWEAVE_ORG_ID")
    if org_id:
        headers["X-Organization-ID"] = org_id
    return headers


def parse_sse_frame(frame: str) -> dict[str, Any] | None:
    """Parse one SSE frame and return its JSON object, if any."""
    data_lines: list[str] = []
    for line in frame.splitlines():
        if line.startswith("data:"):
            data_lines.append(line[5:].strip())
    if not data_lines:
        return None
    payload = "\n".join(data_lines)
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        print(PALETTE.dim(f"[raw] {payload}"))
        return None
    if isinstance(event, dict):
        return event
    return None


def iter_sse_events(response: Any) -> Iterator[dict[str, Any]]:
    """Yield parsed JSON objects from an SSE byte stream."""
    buffer = ""
    while True:
        chunk = response.read(4096)
        if not chunk:
            break
        buffer += chunk.decode("utf-8", errors="replace")
        while "\n\n" in buffer:
            frame, buffer = buffer.split("\n\n", 1)
            event = parse_sse_frame(frame)
            if event is not None:
                yield event
    if buffer.strip():
        event = parse_sse_frame(buffer)
        if event is not None:
            yield event


def diagnostics_summary(event: dict[str, Any]) -> str:
    """Format common diagnostics fields compactly."""
    diag = event.get("diagnostics") or {}
    if not isinstance(diag, dict) or not diag:
        return ""
    parts: list[str] = []
    for key in (
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "result_count",
        "results_count",
        "collected_count",
        "iteration",
    ):
        if key in diag and diag[key] is not None:
            parts.append(f"{key}={diag[key]}")
    return ", ".join(parts)


def render_started(event: dict[str, Any]) -> None:
    print(PALETTE.cyan(PALETTE.bold("started")))
    print(f"  request_id: {event.get('request_id', '?')}")
    print(f"  collection: {event.get('collection_readable_id', '?')}")
    print(f"  tier: {event.get('tier', '?')}")


def render_thinking(event: dict[str, Any]) -> None:
    label = "thinking"
    duration = event.get("duration_ms")
    if duration is not None:
        label += f" ({duration}ms)"
    print("\n" + PALETTE.magenta(PALETTE.bold(label)))
    text = event.get("text") or event.get("thinking") or ""
    if text:
        print(f"  {wrap_text(text)}")
    summary = diagnostics_summary(event)
    if summary:
        print(PALETTE.dim(f"  diagnostics: {summary}"))


def render_tool_call(event: dict[str, Any]) -> None:
    tool = event.get("tool_name", "unknown")
    duration = event.get("duration_ms")
    suffix = f" ({duration}ms)" if duration is not None else ""
    print("\n" + PALETTE.yellow(PALETTE.bold(f"tool_call: {tool}{suffix}")))
    diag = event.get("diagnostics") or {}
    if isinstance(diag, dict):
        for key in (
            "arguments",
            "args",
            "stats",
            "error",
            "result_count",
            "found",
            "added",
            "removed",
        ):
            if key in diag and diag[key] not in (None, {}, []):
                rendered = json.dumps(diag[key], default=str, ensure_ascii=False)
                print(PALETTE.dim(f"  {key}: {wrap_text(rendered, indent='    ')}"))
    summary = diagnostics_summary(event)
    if summary:
        print(PALETTE.dim(f"  diagnostics: {summary}"))


def render_reranking(event: dict[str, Any]) -> None:
    duration = event.get("duration_ms")
    suffix = f" ({duration}ms)" if duration is not None else ""
    print("\n" + PALETTE.yellow(PALETTE.bold(f"reranking{suffix}")))
    summary = diagnostics_summary(event)
    if summary:
        print(PALETTE.dim(f"  diagnostics: {summary}"))


def render_done(event: dict[str, Any]) -> None:
    results = event.get("results") or []
    duration = event.get("duration_ms")
    suffix = f" in {duration}ms" if duration is not None else ""
    print("\n" + "─" * 72)
    print(PALETTE.green(PALETTE.bold(f"done: {len(results)} result(s){suffix}")))
    for idx, result in enumerate(results[:10], 1):
        if not isinstance(result, dict):
            continue
        meta = result.get("airweave_system_metadata") or {}
        source = meta.get("source_name", "?") if isinstance(meta, dict) else "?"
        entity_type = meta.get("entity_type", "?") if isinstance(meta, dict) else "?"
        score = result.get("relevance_score", "?")
        name = result.get("name") or result.get("entity_id") or "?"
        meta_text = PALETTE.dim(f"[{source}/{entity_type} score={score}]")
        print(f"  {idx:>2}. {PALETTE.bold(str(name))} {meta_text}")
    if len(results) > 10:
        print(PALETTE.dim(f"  ... {len(results) - 10} more result(s) not printed"))


def render_error(event: dict[str, Any]) -> None:
    print("\n" + PALETTE.red(PALETTE.bold("error")))
    print("  " + PALETTE.red(wrap_text(event.get("message", "Search failed"))))
    summary = diagnostics_summary(event)
    if summary:
        print(PALETTE.dim(f"  diagnostics: {summary}"))


def render_event(event: dict[str, Any], raw: bool = False) -> None:
    """Render one event."""
    if raw:
        print(json.dumps(event, indent=2, ensure_ascii=False, default=str))
        return
    event_type = str(event.get("type", "unknown"))
    if event_type == "started":
        render_started(event)
    elif event_type == "thinking":
        render_thinking(event)
    elif event_type == "tool_call":
        render_tool_call(event)
    elif event_type == "reranking":
        render_reranking(event)
    elif event_type == "done":
        render_done(event)
    elif event_type == "error":
        render_error(event)
    elif event_type == "heartbeat":
        print(PALETTE.dim("heartbeat"))
    else:
        print(PALETTE.dim(f"unknown event: {json.dumps(event, ensure_ascii=False, default=str)}"))


def positive_int(value: str) -> int:
    """argparse validator for positive integers."""
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def make_parser() -> argparse.ArgumentParser:
    """Create the CLI parser."""
    parser = argparse.ArgumentParser(
        description="View Airweave agentic search SSE events from the current backend route."
    )
    parser.add_argument("collection_id", help="Collection readable ID, not UUID")
    parser.add_argument("query", help="Agentic search query")
    default_host = (
        os.getenv("AIRWEAVE_API_URL")
        or os.getenv("AIRWEAVE_BASE_URL")
        or "http://localhost:8001"
    )
    parser.add_argument(
        "--host",
        default=default_host,
        help=(
            "API host/base URL (default: AIRWEAVE_API_URL, AIRWEAVE_BASE_URL, "
            "or http://localhost:8001)"
        ),
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Bearer token or API key. Defaults to AIRWEAVE_API_KEY when set.",
    )
    parser.add_argument(
        "--organization-id",
        default=None,
        help="Organization ID header. Defaults to AIRWEAVE_ORG_ID when set.",
    )
    parser.add_argument(
        "--filter",
        default=None,
        help=(
            "V2 filter JSON list, e.g. "
            "'[{\"conditions\":[{\"field\":\"airweave_system_metadata.source_name\","
            "\"operator\":\"equals\",\"value\":\"slack\"}]}]'"
        ),
    )
    parser.add_argument("--thinking", action="store_true", help="Set thinking=true in request")
    parser.add_argument("--limit", type=positive_int, default=None, help="Optional result limit")
    parser.add_argument("--timeout", type=positive_int, default=300, help="HTTP timeout in seconds")
    parser.add_argument("--raw", action="store_true", help="Print raw event JSON")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""
    global PALETTE
    parser = make_parser()
    args = parser.parse_args(argv)
    PALETTE = Palette(enabled=not args.no_color and sys.stdout.isatty())

    host = normalize_host(args.host)
    url = f"{host}/collections/{args.collection_id}/search/agentic/stream"
    body = build_body(args)
    headers = build_headers(args)

    print("─" * 72)
    print(PALETTE.bold("Airweave agentic search stream"))
    print(f"  endpoint: POST {url}")
    print(f"  collection: {args.collection_id}")
    print(f"  query: {args.query}")
    if args.limit is not None:
        print(f"  limit: {args.limit}")
    if "filter" in body:
        print(f"  filter: {json.dumps(body['filter'], ensure_ascii=False)}")
    if args.thinking:
        print("  thinking: true")
    print("─" * 72)

    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    started = time.monotonic()
    saw_terminal = False
    saw_error = False
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:  # noqa: S310
            status = getattr(response, "status", None) or response.getcode()
            if status != 200:
                print(PALETTE.red(f"HTTP {status}"), file=sys.stderr)
                return 1
            for event in iter_sse_events(response):
                render_event(event, raw=args.raw)
                if event.get("type") in {"done", "error"}:
                    saw_terminal = True
                    saw_error = event.get("type") == "error"
                    break
    except urllib.error.HTTPError as exc:
        body_bytes = exc.read()
        body_text = body_bytes.decode("utf-8", errors="replace") if body_bytes else ""
        print(PALETTE.red(f"HTTP {exc.code}: {exc.reason}"), file=sys.stderr)
        if body_text:
            print(body_text, file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(PALETTE.red(f"Connection failed: {exc.reason}"), file=sys.stderr)
        return 1
    except TimeoutError:
        print(PALETTE.red(f"Timed out after {args.timeout}s"), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n" + PALETTE.yellow("Interrupted by user; request stream closed."), file=sys.stderr)
        return 130

    elapsed = time.monotonic() - started
    print("\n" + "─" * 72)
    if not saw_terminal:
        print(PALETTE.yellow("Stream ended before a terminal done/error event."))
    print(PALETTE.dim(f"total time: {elapsed:.1f}s"))
    print("─" * 72)
    return 2 if saw_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
