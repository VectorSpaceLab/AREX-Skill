#!/usr/bin/env python3
"""Train a tiny ChatterBot conversation and export response pairs as JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a tiny ChatterBot training corpus to JSON.")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON file path.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable summary.")
    args = parser.parse_args()

    from chatterbot import ChatBot
    from chatterbot.trainers import ListTrainer

    bot = ChatBot("Export Training Demo", database_uri=None)
    trainer = ListTrainer(bot, show_training_progress=False)
    trainer.train(["Hello", "Hi there!", "How are you?", "I'm doing well."])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    trainer.export_for_training(str(args.output))

    payload = json.loads(args.output.read_text(encoding="utf-8"))
    summary = {"output": str(args.output), "conversation_pairs": len(payload.get("conversations", []))}
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"wrote {summary['conversation_pairs']} conversation pairs to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
