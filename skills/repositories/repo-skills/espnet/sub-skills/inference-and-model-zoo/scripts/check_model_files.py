#!/usr/bin/env python3
"""Validate ESPnet local inference/packaging file arguments without loading weights."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

TASKS = {
    "asr": ["config", "model"], "st": ["config", "model"], "s2t": ["config", "model"],
    "tts": ["config", "model"], "enh": ["config", "model"], "diar": ["config", "model"],
    "svs": ["config", "model"], "spk": ["config", "model"], "s2st": ["config", "model"],
}


def exists(label: str, value: str | None) -> dict[str, object]:
    if not value:
        return {"label": label, "provided": False, "exists": False, "error": "missing argument"}
    path = Path(value)
    # Report only a basename for absolute paths to avoid leaking user-specific locations in copied output.
    reported_path = str(path) if not path.is_absolute() else path.name
    return {"label": label, "provided": True, "exists": path.exists(), "path": reported_path}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ESPnet local config/model/vocoder files without loading weights.")
    parser.add_argument("--task", choices=sorted(TASKS), required=True)
    parser.add_argument("--config")
    parser.add_argument("--model")
    parser.add_argument("--lm-config")
    parser.add_argument("--lm-file")
    parser.add_argument("--vocoder-config")
    parser.add_argument("--vocoder-file")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    checks = [exists("config", args.config), exists("model", args.model)]
    for label, value in [("lm_config", args.lm_config), ("lm_file", args.lm_file), ("vocoder_config", args.vocoder_config), ("vocoder_file", args.vocoder_file)]:
        if value:
            checks.append(exists(label, value))
    required = set(TASKS[args.task])
    ok = all(item.get("exists") for item in checks if item.get("label") in required)
    payload = {"ok": ok, "task": args.task, "checks": checks}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("PASS" if ok else "FAIL")
        for item in checks:
            print(f"- {item['label']}: {'exists' if item.get('exists') else 'missing'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
