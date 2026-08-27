#!/usr/bin/env python3
"""Recommend a Cognee search mode from query intent flags.

Safe helper:
- does not import Cognee
- does not contact services
- only prints a recommended `SearchType` and reason
"""

from __future__ import annotations

import argparse


def choose_mode(args: argparse.Namespace) -> tuple[str, str]:
    if args.code:
        return "CODE", "code or repository traversal was requested"
    if args.agentic:
        return "AGENTIC_COMPLETION", "tool use or skill selection was requested"
    if args.temporal:
        return "TEMPORAL", "time-aware retrieval was requested"
    if args.summaries:
        return "SUMMARIES", "the user asked for a quick summary"
    if args.chunks:
        return "CHUNKS", "the user asked for raw supporting passages"
    if args.lucky:
        return "FEELING_LUCKY", "the user wants the router to pick a mode"
    if args.recall or args.session_id:
        return "GRAPH_COMPLETION", "recall/session intent usually wants graph-backed memory"
    return "GRAPH_COMPLETION", "general question about stored knowledge"


def main() -> int:
    parser = argparse.ArgumentParser(description="Recommend a Cognee search mode.")
    parser.add_argument("query", nargs="?", default="", help="Optional user query text")
    parser.add_argument("--session-id", help="Session id, if the query is session-aware")
    parser.add_argument("--code", action="store_true", help="Request code traversal or code graph search")
    parser.add_argument("--temporal", action="store_true", help="Request time-aware retrieval")
    parser.add_argument("--agentic", action="store_true", help="Request tool use or agentic completion")
    parser.add_argument("--chunks", action="store_true", help="Request raw chunk passages")
    parser.add_argument("--summaries", action="store_true", help="Request a quick summary")
    parser.add_argument("--lucky", action="store_true", help="Let Cognee choose a mode")
    parser.add_argument("--recall", action="store_true", help="Treat the task as session-aware recall")
    args = parser.parse_args()

    mode, reason = choose_mode(args)
    print(f"recommended_mode={mode}")
    print(f"reason={reason}")
    if args.query:
        print(f"query={args.query}")
    if args.session_id:
        print(f"session_id={args.session_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
