#!/usr/bin/env python3
"""Run a safe ChatterBot core smoke test.

Examples:
  python sub-skills/core-chatbot/scripts/core_chat_smoke.py --check-model en_core_web_sm
  python sub-skills/core-chatbot/scripts/core_chat_smoke.py --text "Hello" --read-only
"""
from __future__ import annotations

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Instantiate ChatterBot with in-memory SQL and call get_response.")
    parser.add_argument("--name", default="Core Smoke Bot", help="Bot name to pass to ChatBot.")
    parser.add_argument("--text", default="Hello", help="Input text for get_response.")
    parser.add_argument("--conversation", default="core-smoke", help="Conversation label for the smoke call.")
    parser.add_argument("--read-only", action="store_true", help="Set read_only=True during construction.")
    parser.add_argument("--check-model", help="Optional spaCy model to import/load before constructing ChatBot.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args()

    report = {"ok": False, "input": args.text}

    if args.check_model:
        try:
            import spacy
            nlp = spacy.load(args.check_model)
            report["spacy_model"] = {"ok": True, "name": args.check_model, "pipeline": list(nlp.pipe_names)}
        except Exception as exc:
            report["spacy_model"] = {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}
            print(json.dumps(report, indent=2) if args.json else report["spacy_model"]["error"], file=sys.stderr)
            return 1

    try:
        from chatterbot import ChatBot
        bot = ChatBot(args.name, database_uri=None, read_only=args.read_only)
        response = bot.get_response(args.text, conversation=args.conversation)
        report.update({
            "ok": True,
            "response_text": response.text,
            "confidence": response.confidence,
            "conversation": response.conversation,
            "read_only": bot.read_only,
        })
    except Exception as exc:
        report["error"] = f"{exc.__class__.__name__}: {exc}"
        print(json.dumps(report, indent=2) if args.json else report["error"], file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"ok: response={report['response_text']!r} confidence={report['confidence']} conversation={report['conversation']!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
