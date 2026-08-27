#!/usr/bin/env python3
"""Tiny safe smoke check for whisperx.load_audio.

The script creates a short temporary WAV file with the Python standard library,
loads it through whisperx.load_audio, and reports the resulting array shape. It
requires ffmpeg because WhisperX delegates file decoding to the ffmpeg CLI. It
does not load ASR models or run transcription.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import struct
import sys
import tempfile
import wave
from typing import Any


def write_tiny_wav(path: str, sample_rate: int, duration: float, frequency: float) -> int:
    frame_count = max(1, int(sample_rate * duration))
    amplitude = 0.2
    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for index in range(frame_count):
            value = int(32767 * amplitude * math.sin(2 * math.pi * frequency * index / sample_rate))
            wav_file.writeframes(struct.pack("<h", value))
    return frame_count


def run_check(duration: float, sample_rate: int, frequency: float) -> tuple[dict[str, Any], int]:
    report: dict[str, Any] = {
        "ok": False,
        "generated_wav": {
            "sample_rate": sample_rate,
            "duration_seconds": duration,
            "channels": 1,
        },
        "load_audio": {},
        "warnings": [
            "This check does not load ASR models or run transcription.",
            "whisperx.load_audio requires the ffmpeg executable for file decoding.",
        ],
    }

    try:
        import whisperx
    except Exception as exc:
        report["error"] = f"Could not import whisperx: {type(exc).__name__}: {exc}"
        return report, 2

    with tempfile.TemporaryDirectory(prefix="whisperx-audio-check-") as tmpdir:
        wav_path = os.path.join(tmpdir, "tiny.wav")
        frames_written = write_tiny_wav(wav_path, sample_rate, duration, frequency)
        report["generated_wav"]["frames_written"] = frames_written
        try:
            audio = whisperx.load_audio(wav_path)
        except FileNotFoundError as exc:
            report["error"] = f"ffmpeg executable was not found: {exc}"
            return report, 3
        except RuntimeError as exc:
            report["error"] = f"whisperx.load_audio failed: {exc}"
            return report, 4
        except Exception as exc:  # pragma: no cover - diagnostic path
            report["error"] = f"Unexpected load_audio failure: {type(exc).__name__}: {exc}"
            return report, 5

    try:
        shape = tuple(int(part) for part in audio.shape)
        dtype = str(audio.dtype)
        min_value = float(audio.min()) if audio.size else None
        max_value = float(audio.max()) if audio.size else None
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["error"] = f"Loaded object was not a NumPy-like audio array: {type(exc).__name__}: {exc}"
        return report, 6

    report["ok"] = True
    report["load_audio"] = {
        "shape": shape,
        "dtype": dtype,
        "expected_sample_rate": 16000,
        "min": min_value,
        "max": max_value,
    }
    return report, 0


def print_text(report: dict[str, Any]) -> None:
    print("WhisperX load_audio tiny WAV check")
    print(f"  ok: {report['ok']}")
    generated = report.get("generated_wav", {})
    print(
        "  generated wav: "
        f"sample_rate={generated.get('sample_rate')}, "
        f"duration={generated.get('duration_seconds')}s, "
        f"frames={generated.get('frames_written')}"
    )
    if report.get("load_audio"):
        loaded = report["load_audio"]
        print(
            "  loaded audio: "
            f"shape={loaded.get('shape')}, dtype={loaded.get('dtype')}, "
            f"expected_sample_rate={loaded.get('expected_sample_rate')}, "
            f"min={loaded.get('min')}, max={loaded.get('max')}"
        )
    if report.get("error"):
        print(f"  error: {report['error']}")
    print("  warnings:")
    for warning in report.get("warnings", []):
        print(f"    - {warning}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a tiny WAV and verify whisperx.load_audio/ffmpeg without model execution."
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report instead of text")
    parser.add_argument(
        "--duration",
        type=float,
        default=0.25,
        help="generated WAV duration in seconds; must be >0 and <=2 (default: 0.25)",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="generated WAV sample rate before ffmpeg conversion (default: 16000)",
    )
    parser.add_argument(
        "--frequency",
        type=float,
        default=440.0,
        help="generated sine tone frequency in Hz (default: 440)",
    )
    args = parser.parse_args(argv)

    if not (0 < args.duration <= 2):
        parser.error("--duration must be >0 and <=2 seconds")
    if args.sample_rate <= 0:
        parser.error("--sample-rate must be positive")
    if args.frequency <= 0:
        parser.error("--frequency must be positive")

    report, exit_code = run_check(args.duration, args.sample_rate, args.frequency)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
