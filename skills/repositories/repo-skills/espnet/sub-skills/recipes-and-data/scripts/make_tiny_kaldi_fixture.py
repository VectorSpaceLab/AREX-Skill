#!/usr/bin/env python3
"""Create tiny Kaldi-style fixtures for ESPnet data validation examples."""
from __future__ import annotations
import argparse
from pathlib import Path

TEXT = """utt1 hello world
utt2 test sentence
"""
UTT2SPK = """utt1 spk1
utt2 spk1
"""
SPK2UTT_VALID = """spk1 utt1 utt2
"""
SPK2UTT_BAD = """spk1 utt1
"""
WAV_UTTERANCE = """utt1 /tmp/not-real-1.wav
utt2 /tmp/not-real-2.wav
"""
WAV_RECORDING = """rec1 /tmp/not-real.wav
"""
SEGMENTS_VALID = """utt1 rec1 0.0 1.0
utt2 rec1 1.0 2.0
"""
SEGMENTS_BAD = """utt1 missing-rec 2.0 1.0
utt2 rec1 1.0 2.0
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create valid or intentionally invalid tiny ESPnet data fixtures.")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--with-segments", action="store_true")
    parser.add_argument("--invalid", choices=["none", "missing-wavscp", "bad-spk2utt", "bad-segments"], default="none")
    args = parser.parse_args()
    out = args.output_dir
    write(out / "text", TEXT)
    write(out / "utt2spk", UTT2SPK)
    write(out / "spk2utt", SPK2UTT_BAD if args.invalid == "bad-spk2utt" else SPK2UTT_VALID)
    if args.with_segments:
        write(out / "wav.scp", WAV_RECORDING)
        write(out / "segments", SEGMENTS_BAD if args.invalid == "bad-segments" else SEGMENTS_VALID)
    elif args.invalid != "missing-wavscp":
        write(out / "wav.scp", WAV_UTTERANCE)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
