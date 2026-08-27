#!/usr/bin/env python3
"""Safely collect a DeepXiv hosted agentic answer.

The default mode buffers the answer and writes it to stdout only after a normal,
non-truncated ``done`` event. ``--live`` is opt-in provisional output: deltas are
written as they arrive, but an error or truncation still returns non-zero.
Credentials are read only from DEEPXIV_TOKEN and are never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stream a DeepXiv Reader answer with safe completion checks."
    )
    parser.add_argument("query", nargs="+", help="specific research question")
    parser.add_argument("--source", choices=("arxiv", "web"), default="arxiv")
    parser.add_argument("--effort", choices=("default", "high", "xhigh"), default="default")
    parser.add_argument("--language", help="optional answer language override")
    parser.add_argument("--max-answer-tokens", type=int, help="inclusive 256..16384 cap")
    parser.add_argument("--top-k", type=int, help="arXiv-only first-round retrieval size (1..30)")
    parser.add_argument(
        "--search-type",
        choices=("search", "scholar", "news", "images"),
        help="web-only search vertical",
    )
    parser.add_argument("--gl", help="web-only Google country code")
    parser.add_argument("--hl", help="web-only Google interface language")
    parser.add_argument("--timeout", type=int, help="agentic request timeout in seconds")
    parser.add_argument("--verbose", action="store_true", help="retain verbose service events")
    parser.add_argument(
        "--single-answer",
        action="store_true",
        help="request one answer event instead of answer_delta events",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="write answer text before completion (provisional; default buffers)",
    )
    return parser


def write_diagnostic(payload: dict[str, Any]) -> None:
    sys.stderr.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    sys.stderr.flush()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        from deepxiv_sdk import Reader, agent_search_sources
        from deepxiv_sdk import APIError, BadRequestError, AuthenticationError, RateLimitError
    except ImportError as exc:
        write_diagnostic({"status": "import_error", "message": str(exc)})
        return 1

    kwargs: dict[str, Any] = {
        "source": args.source,
        "effort": args.effort,
        "verbose": args.verbose,
        "stream_answer": not args.single_answer,
    }
    for name in ("language", "max_answer_tokens", "top_k", "search_type", "gl", "hl", "timeout"):
        value = getattr(args, name)
        if value is not None:
            kwargs[name] = value

    # Reader itself does not need to resolve local configuration. This wrapper
    # deliberately reads one conventional environment variable and never echoes it.
    reader = Reader(token=os.environ.get("DEEPXIV_TOKEN"))
    chunks: list[str] = []
    sources: list[dict[str, Any]] = []
    saw_done = False
    complete = False
    error_event: dict[str, Any] | None = None
    done_event: dict[str, Any] | None = None

    try:
        for event in reader.agent_search_stream(" ".join(args.query), **kwargs):
            kind = event.get("event")
            if kind in ("answer_delta", "answer"):
                value = event.get("text")
                if value is None:
                    value = event.get("answer", "")
                if isinstance(value, str):
                    chunks.append(value)
                    if args.live:
                        sys.stdout.write(value)
                        sys.stdout.flush()
            elif kind == "sources":
                normalized = agent_search_sources(event)
                if isinstance(normalized, list):
                    sources = normalized
            elif kind == "done":
                saw_done = True
                done_event = event
                # Require an explicit false, not a missing or truthy value.
                complete = event.get("answer_truncated") is False
            elif kind == "error":
                error_event = {
                    "stage": event.get("stage"),
                    "message": event.get("message"),
                }
    except (APIError, BadRequestError, AuthenticationError, RateLimitError) as exc:
        write_diagnostic({"status": "request_error", "error": type(exc).__name__, "message": str(exc)})
        return 1
    except Exception as exc:  # keep an adapter failure actionable without a traceback
        write_diagnostic({"status": "adapter_error", "error": type(exc).__name__, "message": str(exc)})
        return 1

    answer = "".join(chunks)
    if not args.live and not error_event and saw_done and complete:
        sys.stdout.write(answer + "\n")
        sys.stdout.flush()

    summary: dict[str, Any] = {
        "status": "complete" if (saw_done and complete and not error_event) else "incomplete",
        "source": args.source,
        "answer_truncated": None if done_event is None else done_event.get("answer_truncated"),
        "answer_characters": len(answer),
        "source_count": len(sources),
        "sources": sources,
    }
    if error_event:
        summary["error"] = error_event
    write_diagnostic(summary)

    if error_event:
        return 1
    if not saw_done or not complete:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
