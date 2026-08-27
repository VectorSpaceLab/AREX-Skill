#!/usr/bin/env python3
"""Validate WAV inputs and optionally create a PaddleSpeech job file."""
from __future__ import annotations

import argparse
import json
import wave
from pathlib import Path


def inspect_wav(path: Path) -> dict[str, object]:
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return {
            "path": str(path),
            "channels": wf.getnchannels(),
            "sample_width_bytes": wf.getsampwidth(),
            "sample_rate": rate,
            "frames": frames,
            "duration_sec": frames / float(rate) if rate else None,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate WAV files for PaddleSpeech ASR/ST/SSL/Whisper workflows")
    parser.add_argument("audio", nargs="+", type=Path)
    parser.add_argument("--sample-rate", type=int, default=16000)
    parser.add_argument("--max-duration", type=float, default=None, help="Fail if duration exceeds this many seconds")
    parser.add_argument("--write-job", type=Path, help="Write id/path lines suitable for most PaddleSpeech audio commands")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rows = []
    exit_code = 0
    for idx, path in enumerate(args.audio, 1):
        row = {"path": str(path), "status": "ok", "problems": []}
        if not path.is_file():
            row["status"] = "fail"
            row["problems"].append("not a file")
            exit_code = 1
        else:
            try:
                row.update(inspect_wav(path))
                if row["sample_rate"] != args.sample_rate:
                    row["status"] = "fail"
                    row["problems"].append(f"sample_rate {row['sample_rate']} != expected {args.sample_rate}")
                    exit_code = 1
                if args.max_duration is not None and row.get("duration_sec") and row["duration_sec"] > args.max_duration:
                    row["status"] = "fail"
                    row["problems"].append(f"duration {row['duration_sec']:.2f}s > {args.max_duration:.2f}s")
                    exit_code = 1
            except Exception as exc:  # noqa: BLE001
                row["status"] = "fail"
                row["problems"].append(f"{type(exc).__name__}: {exc}")
                exit_code = 1
        row["id"] = f"utt{idx}"
        rows.append(row)

    if args.write_job:
        ok_rows = [r for r in rows if r["status"] == "ok"]
        args.write_job.write_text("".join(f"{r['id']} {r['path']}\n" for r in ok_rows))

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for row in rows:
            print(f"[{row['status']}] {row['path']} rate={row.get('sample_rate')} duration={row.get('duration_sec')} problems={'; '.join(row['problems'])}")
        if args.write_job:
            print(f"wrote job file: {args.write_job}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
