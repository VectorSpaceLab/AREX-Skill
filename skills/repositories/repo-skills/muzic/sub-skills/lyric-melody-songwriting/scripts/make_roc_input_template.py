#!/usr/bin/env python3
"""Create starter lyrics.txt and chord.txt files for ROC lyric-to-melody runs."""

from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_LYRICS = [
    "When the morning light is shining",
    "I will sing along the way",
    "Every heartbeat keeps the timing",
    "Turning night into the day",
]

DEFAULT_CHORDS = [
    "C G Am F",
    "C G F G",
    "Am F C G",
    "F G C C",
]


def write_lines(path: Path, lines: list[str], overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists; pass --overwrite to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Write ROC lyrics/chord starter files without running ROC inference.")
    parser.add_argument("--output-dir", default=".", help="Directory in which to create lyrics.txt and chord.txt.")
    parser.add_argument("--lyrics-file", default="lyrics.txt")
    parser.add_argument("--chord-file", default="chord.txt")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--language", choices=["en", "zh"], default="en", help="Template language; zh creates placeholder Chinese lines.")
    args = parser.parse_args()

    out = Path(args.output_dir).expanduser()
    lyrics = DEFAULT_LYRICS
    if args.language == "zh":
        lyrics = ["清晨阳光照进窗", "我把旋律轻轻唱", "心跳跟着节拍走", "梦在夜色里发光"]
    try:
        write_lines(out / args.lyrics_file, lyrics, args.overwrite)
        write_lines(out / args.chord_file, DEFAULT_CHORDS, args.overwrite)
    except FileExistsError as exc:
        print(f"ERROR: {exc}")
        return 2
    print(f"Wrote {(out / args.lyrics_file)}")
    print(f"Wrote {(out / args.chord_file)}")
    print("Next: verify ROC database and checkpoint paths before running lyrics_to_melody.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
