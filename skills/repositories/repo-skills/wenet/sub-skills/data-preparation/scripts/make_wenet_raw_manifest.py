#!/usr/bin/env python3
"""Create a WeNet raw data.list from wav.scp and text.

The helper is a safe, self-contained adaptation of WeNet's raw-manifest recipe
logic. It validates key alignment before writing JSON Lines.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def read_two_column(path: Path, value_name: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split(maxsplit=1)
            if len(parts) != 2:
                raise ValueError(f"{path}:{lineno}: expected '<key> <{value_name}>', got {stripped!r}")
            key, value = parts
            if key in rows:
                raise ValueError(f"{path}:{lineno}: duplicate key {key!r}")
            rows[key] = value
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate WeNet raw JSONL data.list from wav.scp and text.")
    parser.add_argument("--wav-scp", required=True, type=Path, help="Input wav.scp with '<key> <audio-path-or-command>'.")
    parser.add_argument("--text", required=True, type=Path, help="Input text with '<key> <transcript>'.")
    parser.add_argument("--output", required=True, type=Path, help="Output JSON Lines data.list path.")
    parser.add_argument("--allow-missing-audio", action="store_true", help="Do not fail when wav values look like missing local files. Commands and remote paths are never checked.")
    args = parser.parse_args()

    try:
        wavs = read_two_column(args.wav_scp, "wav")
        texts = read_two_column(args.text, "transcript")
        missing_text = sorted(set(wavs) - set(texts))
        missing_wav = sorted(set(texts) - set(wavs))
        if missing_text or missing_wav:
            raise ValueError(
                "key mismatch between wav.scp and text: "
                f"missing_text_for={missing_text[:10]} missing_wav_for={missing_wav[:10]}"
            )

        if not args.allow_missing_audio:
            missing_audio: list[str] = []
            for key, wav in wavs.items():
                # Plain local paths are checked; shell pipes/commands and URLs are not.
                if "|" in wav or "://" in wav:
                    continue
                if not Path(wav).expanduser().exists():
                    missing_audio.append(key)
            if missing_audio:
                raise ValueError(
                    "audio path missing for keys "
                    f"{missing_audio[:10]}; pass --allow-missing-audio if paths are valid only in the training environment"
                )

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as out:
            for key in wavs:
                out.write(json.dumps({"key": key, "wav": wavs[key], "txt": texts[key]}, ensure_ascii=False) + "\n")
        print(json.dumps({"ok": True, "utterances": len(wavs), "output": str(args.output)}, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
