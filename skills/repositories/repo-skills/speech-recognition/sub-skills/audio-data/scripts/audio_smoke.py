#!/usr/bin/env python3
"""Synthetic smoke checks for SpeechRecognition AudioData file workflows.

The script creates tiny WAV data at runtime and does not read source-repository
fixtures. It avoids microphones, sprc, model downloads, and recognition APIs.
"""

from __future__ import annotations

import argparse
import io
import math
import struct
import sys
import tempfile
import wave
from pathlib import Path


def _import_sr():
    try:
        import speech_recognition as sr  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on caller env
        print(
            "Could not import speech_recognition. Install SpeechRecognition "
            "with its declared runtime dependencies before using this smoke check.\n"
            f"Import error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    return sr


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate tiny WAV data and verify SpeechRecognition AudioData, "
            "from_file, AudioFile, conversions, and split without repo fixtures."
        )
    )
    parser.add_argument("--sample-rate", type=int, default=8000, help="synthetic sample rate in Hz")
    parser.add_argument("--duration-ms", type=int, default=120, help="synthetic duration in milliseconds")
    parser.add_argument(
        "--require-flac",
        action="store_true",
        help="fail if FLAC conversion is unavailable instead of reporting a skip",
    )
    return parser


def _pcm_tone(sample_rate: int, duration_ms: int) -> bytes:
    if sample_rate <= 0:
        raise ValueError("sample rate must be positive")
    if duration_ms <= 0:
        raise ValueError("duration must be positive")
    total = int(sample_rate * duration_ms / 1000)
    frames = bytearray()
    for i in range(total):
        value = int(0.25 * 32767 * math.sin(2 * math.pi * 440 * i / sample_rate))
        frames.extend(struct.pack("<h", value))
    return bytes(frames)


def _wav_bytes(pcm: bytes, sample_rate: int, sample_width: int = 2) -> bytes:
    bio = io.BytesIO()
    with wave.open(bio, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(sample_width)
        writer.setframerate(sample_rate)
        writer.writeframes(pcm)
    return bio.getvalue()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    sr = _import_sr()

    pcm = _pcm_tone(args.sample_rate, args.duration_ms)
    wav_data = _wav_bytes(pcm, args.sample_rate)
    direct = sr.AudioData(pcm, args.sample_rate, 2)

    _assert(direct.sample_rate == args.sample_rate, "AudioData sample_rate mismatch")
    _assert(direct.sample_width == 2, "AudioData sample_width mismatch")
    _assert(direct.get_raw_data() == pcm, "get_raw_data changed unconverted PCM")
    _assert(direct.get_wav_data().startswith(b"RIFF"), "get_wav_data did not produce WAV")
    _assert(direct.get_aiff_data().startswith((b"FORM", b"FORM")), "get_aiff_data did not produce AIFF")
    _assert(len(direct.get_raw_data(convert_rate=args.sample_rate * 2, convert_width=1)) > 0, "conversion returned empty data")

    segment = direct.get_segment(start_ms=10, end_ms=60)
    _assert(isinstance(segment, sr.AudioData), "get_segment did not return AudioData")
    _assert(0 < len(segment.frame_data) < len(direct.frame_data), "segment size is not bounded")

    max_bytes = 44 + 2 * max(1, len(pcm) // 4 // 2)
    chunks = direct.split(max_bytes=max_bytes)
    _assert(len(chunks) > 1, "split did not create multiple chunks")
    _assert(b"".join(chunk.frame_data for chunk in chunks) == pcm, "split chunks do not rejoin to original PCM")
    for chunk in chunks:
        _assert(len(chunk.frame_data) % chunk.sample_width == 0, "split produced unaligned chunk")
        _assert(len(chunk.get_wav_data()) <= max_bytes, "split chunk exceeded max_bytes")

    r = sr.Recognizer()
    with sr.AudioFile(io.BytesIO(wav_data)) as source:
        from_fileobj = r.record(source)
    _assert(from_fileobj.get_raw_data() == pcm, "AudioFile file-like round trip mismatch")

    with tempfile.TemporaryDirectory(prefix="sr-audio-smoke-") as tmp:
        wav_path = Path(tmp) / "synthetic.wav"
        wav_path.write_bytes(wav_data)
        loaded = sr.AudioData.from_file(str(wav_path))
    _assert(loaded.get_raw_data() == pcm, "AudioData.from_file round trip mismatch")

    flac_status = "not checked"
    try:
        flac_data = direct.get_flac_data()
    except Exception as exc:
        if args.require_flac:
            raise
        flac_status = f"skipped ({type(exc).__name__}: {exc})"
    else:
        _assert(flac_data.startswith(b"fLaC"), "get_flac_data did not produce FLAC magic bytes")
        flac_status = f"ok ({len(flac_data)} bytes)"

    print("audio smoke ok")
    print(f"sample_rate={args.sample_rate} duration_ms={args.duration_ms} pcm_bytes={len(pcm)}")
    print(f"split_chunks={len(chunks)} max_bytes={max_bytes}")
    print(f"flac={flac_status}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
