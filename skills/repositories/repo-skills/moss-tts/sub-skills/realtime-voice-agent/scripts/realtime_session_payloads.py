#!/usr/bin/env python3
"""Print safe example payloads for MOSS-TTS-Realtime FastAPI sessions.

This helper has no server, model, torch, or repository imports. It only splits
assistant text into deltas and prints a start/audio/push/close request plan that
matches the documented FastAPI session flow.

Examples:
  python scripts/realtime_session_payloads.py --text "Hello world" --chunk-chars 20
  python scripts/realtime_session_payloads.py --text "Hello world" --session-id demo --json
"""

from __future__ import annotations

import argparse
import json as jsonlib
import sys
import uuid
from typing import Iterable

DEFAULT_TEXT = (
    "Welcome to MOSS-TTS-Realtime. This text is split into deltas so a "
    "voice-agent client can start the session, stream audio, push text, and "
    "finalize the turn."
)


def split_text(text: str, chunk_chars: int) -> list[str]:
    """Split text into fixed-width character deltas with safe bounds."""
    step = max(1, int(chunk_chars))
    text = text or ""
    if not text:
        return []
    return [text[index : index + step] for index in range(0, len(text), step)]


def build_flow(text: str, chunk_chars: int, session_id: str) -> dict:
    """Build a documented request sequence for one FastAPI turn."""
    chunks = split_text(text, chunk_chars)
    first_delta = chunks[0] if chunks else ""
    remaining = chunks[1:]

    flow: list[dict] = [
        {
            "step": "start",
            "method": "POST",
            "path": "/tts/session/start",
            "json": {
                "session_id": session_id,
                "user_text": None,
                "assistant_text": first_delta,
                "prompt_audio": None,
                "user_audio": None,
                "new_turn": True,
            },
        },
        {
            "step": "audio",
            "method": "GET",
            "path": f"/tts/session/{session_id}/audio",
            "expect_headers": {
                "X-Audio-Codec": "pcm_s16le",
                "X-Audio-Sample-Rate": "24000",
                "X-Audio-Channels": "1",
            },
            "note": "Read raw PCM16 bytes until the stream ends after finalization.",
        },
    ]

    if remaining:
        for index, delta in enumerate(remaining, start=2):
            flow.append(
                {
                    "step": f"push-{index}",
                    "method": "POST",
                    "path": "/tts/session/push",
                    "json": {
                        "session_id": session_id,
                        "text": delta,
                        "is_final": index == len(chunks),
                    },
                }
            )
    else:
        flow.append(
            {
                "step": "push-final-empty",
                "method": "POST",
                "path": "/tts/session/push",
                "json": {
                    "session_id": session_id,
                    "text": "",
                    "is_final": True,
                },
            }
        )

    flow.append(
        {
            "step": "close",
            "method": "POST",
            "path": "/tts/session/close",
            "json": {"session_id": session_id},
        }
    )

    return {
        "session_id": session_id,
        "chunk_chars": max(1, int(chunk_chars)),
        "chunks": chunks,
        "flow": flow,
    }


def print_human(plan: dict) -> None:
    """Pretty-print payloads for shell/manual use."""
    print(f"session_id: {plan['session_id']}")
    print(f"chunk_chars: {plan['chunk_chars']}")
    print("text_deltas:")
    for index, chunk in enumerate(plan["chunks"], start=1):
        print(f"  {index:02d}: {chunk!r}")
    if not plan["chunks"]:
        print("  <empty text; final push is still shown>")

    print("\nrequest_flow:")
    for item in plan["flow"]:
        print(f"\n[{item['step']}] {item['method']} {item['path']}")
        if "json" in item:
            print(jsonlib.dumps(item["json"], ensure_ascii=False, indent=2))
        if "expect_headers" in item:
            print("expected response headers:")
            print(jsonlib.dumps(item["expect_headers"], ensure_ascii=False, indent=2))
        if item.get("note"):
            print(f"note: {item['note']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print example JSON payloads and text deltas for a MOSS-TTS-Realtime FastAPI session."
    )
    parser.add_argument(
        "--text",
        default=DEFAULT_TEXT,
        help="Assistant text to split into streamed deltas.",
    )
    parser.add_argument(
        "--chunk-chars",
        type=int,
        default=50,
        help="Maximum characters per text delta; values below 1 are coerced to 1.",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Session id to use. Defaults to a generated UUID.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit one machine-readable JSON object instead of labeled text.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    session_id = args.session_id or str(uuid.uuid4())
    plan = build_flow(args.text, args.chunk_chars, session_id)
    if args.json:
        print(jsonlib.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print_human(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
