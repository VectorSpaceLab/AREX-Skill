#!/usr/bin/env python3
"""Create a tiny CSV or JSON fixture and train ChatterBot from it.

The script writes only inside a temporary directory unless --data-dir is given.
"""
from __future__ import annotations

import argparse
import csv
import json
import tempfile
from pathlib import Path


def write_csv(data_dir: Path) -> Path:
    path = data_dir / "tiny_conversation.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["created_at", "persona", "text", "conversation"])
        writer.writerow(["2026-01-01T00:00:00Z", "user", "Is anyone there?", "demo"])
        writer.writerow(["2026-01-01T00:00:01Z", "bot", "Yes", "demo"])
    return path


def write_json(data_dir: Path) -> Path:
    path = data_dir / "tiny_conversation.json"
    payload = {
        "conversation": [
            {"created_at": "2026-01-01T00:00:00Z", "persona": "user", "text": "Is anyone there?", "conversation": "demo", "in_response_to": None},
            {"created_at": "2026-01-01T00:00:01Z", "persona": "bot", "text": "Yes", "conversation": "demo", "in_response_to": "Is anyone there?"},
        ]
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def run_demo(fmt: str, data_dir: Path, prompt: str) -> dict:
    from chatterbot import ChatBot
    from chatterbot.trainers import CsvFileTrainer, JsonFileTrainer

    bot = ChatBot("File Training Demo", database_uri=None)

    if fmt == "csv":
        fixture = write_csv(data_dir)
        trainer = CsvFileTrainer(
            bot,
            show_training_progress=False,
            field_map={"created_at": "created_at", "persona": "persona", "text": "text", "conversation": "conversation"},
        )
    else:
        fixture = write_json(data_dir)
        trainer = JsonFileTrainer(
            bot,
            show_training_progress=False,
            field_map={"created_at": "created_at", "persona": "persona", "text": "text", "conversation": "conversation", "in_response_to": "in_response_to"},
        )

    trainer.train(str(data_dir))
    response = bot.get_response(prompt)
    return {"format": fmt, "fixture": fixture.name, "prompt": prompt, "response": response.text, "confidence": response.confidence, "statement_count": bot.storage.count()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Train from a generated tiny CSV or JSON fixture.")
    parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Fixture format to generate and train from.")
    parser.add_argument("--prompt", default="Is anyone there?", help="Prompt to ask after training.")
    parser.add_argument("--data-dir", type=Path, help="Directory for generated fixture. Defaults to a temporary directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    if args.data_dir:
        args.data_dir.mkdir(parents=True, exist_ok=True)
        result = run_demo(args.format, args.data_dir, args.prompt)
    else:
        with tempfile.TemporaryDirectory(prefix="chatterbot-file-training-") as tmp:
            result = run_demo(args.format, Path(tmp), args.prompt)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"format={result['format']} fixture={result['fixture']} response={result['response']!r} confidence={result['confidence']} statements={result['statement_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
