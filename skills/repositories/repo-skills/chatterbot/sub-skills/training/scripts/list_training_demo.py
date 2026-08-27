#!/usr/bin/env python3
"""Tiny ChatterBot ListTrainer demo.

This script uses an in-memory SQLite database and does not write files.
"""
from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description="Train a tiny ChatterBot conversation with ListTrainer.")
    parser.add_argument("--prompt", default="Hello", help="Prompt to ask after training.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    from chatterbot import ChatBot
    from chatterbot.trainers import ListTrainer

    bot = ChatBot("List Training Demo", database_uri=None)
    trainer = ListTrainer(bot, show_training_progress=False)
    trainer.train(["Hello", "Hi there!", "How are you?", "I'm doing well."])
    response = bot.get_response(args.prompt)

    payload = {"prompt": args.prompt, "response": response.text, "confidence": response.confidence, "statement_count": bot.storage.count()}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"prompt={args.prompt!r} response={response.text!r} confidence={response.confidence} statements={payload['statement_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
