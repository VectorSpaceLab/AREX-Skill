#!/usr/bin/env python3
"""Build a simple character-level WeNet units dictionary from a text file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def iter_transcripts(path: Path, start_field: int) -> list[str]:
    transcripts: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            stripped = line.rstrip("\n")
            if not stripped.strip():
                continue
            fields = stripped.split()
            if len(fields) <= start_field:
                raise ValueError(f"{path}:{lineno}: not enough fields for transcript start index {start_field}")
            transcripts.append("".join(fields[start_field:]))
    return transcripts


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a deterministic character units.txt for WeNet recipes.")
    parser.add_argument("--text", required=True, type=Path, help="Input text file with '<key> <transcript>'.")
    parser.add_argument("--output", required=True, type=Path, help="Output units/dictionary file.")
    parser.add_argument("--transcript-start-field", type=int, default=1, help="Zero-based field index where transcript content begins; default skips utterance key.")
    parser.add_argument("--blank", default="<blank>", help="CTC blank token string.")
    parser.add_argument("--unk", default="<unk>", help="Unknown token string.")
    parser.add_argument("--sos-eos", default="<sos/eos>", help="Shared start/end token string.")
    args = parser.parse_args()

    try:
        chars: set[str] = set()
        for transcript in iter_transcripts(args.text, args.transcript_start_field):
            chars.update(ch for ch in transcript if not ch.isspace())
        reserved = [args.blank, args.unk, args.sos_eos]
        if any(token in chars for token in reserved):
            raise ValueError("reserved token appears as a normal character in the corpus")

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as out:
            out.write(f"{args.blank} 0\n")
            out.write(f"{args.unk} 1\n")
            for idx, token in enumerate(sorted(chars), start=2):
                out.write(f"{token} {idx}\n")
            out.write(f"{args.sos_eos} {len(chars) + 2}\n")
        print(json.dumps({"ok": True, "tokens": len(chars) + 3, "output": str(args.output)}, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
