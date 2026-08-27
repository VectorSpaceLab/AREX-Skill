#!/usr/bin/env python3
"""Validate a Facenet learning-rate schedule file."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_schedule(path: Path):
    items = []
    problems = []
    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            problems.append(f"line {lineno}: missing ':' separator")
            continue
        epoch_text, lr_text = line.split(":", 1)
        try:
            epoch = int(epoch_text.strip())
        except ValueError:
            problems.append(f"line {lineno}: invalid epoch {epoch_text!r}")
            continue
        lr_text = lr_text.strip()
        if lr_text == "-":
            lr = None
        else:
            try:
                lr = float(lr_text)
            except ValueError:
                problems.append(f"line {lineno}: invalid learning rate {lr_text!r}")
                continue
        items.append({"epoch": epoch, "learning_rate": lr})
    return items, problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Facenet learning-rate schedule file.")
    parser.add_argument("schedule_file", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.schedule_file.exists():
        payload = {"ok": False, "problems": [f"schedule file missing: {args.schedule_file}"], "items": []}
    else:
        items, problems = parse_schedule(args.schedule_file)
        epochs = [item["epoch"] for item in items]
        if epochs != sorted(epochs):
            problems.append("epochs are not sorted ascending")
        payload = {"ok": not problems, "problems": problems, "items": items}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"OK={payload['ok']} entries={len(payload['items'])}")
        for problem in payload["problems"]:
            print(f"PROBLEM: {problem}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
