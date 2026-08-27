#!/usr/bin/env python3
"""Interactive SpeechRecognition microphone capture template.

Purpose:
    Capture audio from a live microphone with bounded listen options, optional
    ambient-noise calibration, device listing, and optional WAV output.

Prerequisites:
    Importing this script and running --help do not require PyAudio. Device
    listing and microphone capture require SpeechRecognition's audio extra
    (PyAudio 0.2.11+) and working input hardware.

Examples:
    python microphone_capture_template.py --help
    python microphone_capture_template.py --list-devices
    python microphone_capture_template.py --device-index 3 --timeout 5 --phrase-limit 10 --output-wav captured.wav
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Optional


def parse_optional_float(value: str) -> Optional[float]:
    """Parse a non-negative float or a null-like value."""
    if value.lower() in {"none", "null", "off"}:
        return None
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a number or 'none', got {value!r}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def parse_positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Capture SpeechRecognition microphone audio without calling any "
            "transcription service. --help is safe without PyAudio."
        )
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="list PyAudio microphone names and exit; requires PyAudio and audio hardware",
    )
    parser.add_argument(
        "--device-index",
        type=int,
        default=None,
        help="microphone device index from --list-devices; default uses the OS default input device",
    )
    parser.add_argument(
        "--sample-rate",
        type=parse_positive_int,
        default=None,
        help="override the microphone sample rate in Hz; default uses PyAudio device default",
    )
    parser.add_argument(
        "--chunk-size",
        type=parse_positive_int,
        default=1024,
        help="frames per microphone buffer; default: 1024",
    )
    parser.add_argument(
        "--calibration-duration",
        type=parse_optional_float,
        default=1.0,
        metavar="SECONDS|none",
        help="ambient-noise calibration duration before listening; use 'none' to skip; default: 1",
    )
    parser.add_argument(
        "--mode",
        choices=("listen", "record", "stream"),
        default="listen",
        help="capture primitive: listen for one phrase, record a fixed window, or iterate listen(stream=True)",
    )
    parser.add_argument(
        "--timeout",
        type=parse_optional_float,
        default=5.0,
        metavar="SECONDS|none",
        help="maximum seconds to wait for speech to start in listen/stream mode; default: 5",
    )
    parser.add_argument(
        "--phrase-limit",
        type=parse_optional_float,
        default=10.0,
        metavar="SECONDS|none",
        help="maximum seconds for a phrase in listen/stream mode; default: 10",
    )
    parser.add_argument(
        "--record-duration",
        type=parse_optional_float,
        default=3.0,
        metavar="SECONDS|none",
        help="duration for --mode record; default: 3; use 'none' to read until source ends",
    )
    parser.add_argument(
        "--record-offset",
        type=parse_optional_float,
        default=None,
        metavar="SECONDS|none",
        help="offset for --mode record; usually useful for AudioFile sources, default: none",
    )
    parser.add_argument(
        "--energy-threshold",
        type=parse_optional_float,
        default=None,
        metavar="VALUE",
        help="set recognizer.energy_threshold before calibration/listening",
    )
    parser.add_argument(
        "--disable-dynamic-energy",
        action="store_true",
        help="set recognizer.dynamic_energy_threshold=False for controlled-noise environments",
    )
    parser.add_argument(
        "--pause-threshold",
        type=parse_optional_float,
        default=None,
        metavar="SECONDS",
        help="override seconds of non-speaking audio that ends a phrase",
    )
    parser.add_argument(
        "--output-wav",
        type=Path,
        default=None,
        help="optional path to write captured WAV bytes; parent directory must already exist",
    )
    return parser


def import_speech_recognition():
    try:
        import speech_recognition as sr  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Could not import speech_recognition. Install the SpeechRecognition package before capture."
        ) from exc
    return sr


def explain_pyaudio_failure(exc: BaseException) -> str:
    return (
        f"Microphone access failed: {exc}\n"
        "Microphone workflows require PyAudio 0.2.11+ and a working input device. "
        "Install SpeechRecognition with its audio extra and any required PortAudio "
        "system packages, then run --list-devices to choose an explicit device index."
    )


def list_devices(sr) -> int:
    try:
        names = sr.Microphone.list_microphone_names()
    except (AttributeError, OSError) as exc:
        print(explain_pyaudio_failure(exc), file=sys.stderr)
        return 2
    if not names:
        print("No microphones were reported by PyAudio.")
        return 1
    for index, name in enumerate(names):
        print(f"{index}: {name}")
    return 0


def make_recognizer(sr, args: argparse.Namespace):
    recognizer = sr.Recognizer()
    if args.energy_threshold is not None:
        recognizer.energy_threshold = args.energy_threshold
    if args.disable_dynamic_energy:
        recognizer.dynamic_energy_threshold = False
    if args.pause_threshold is not None:
        recognizer.pause_threshold = args.pause_threshold
    return recognizer


def write_wav(audio, output_wav: Optional[Path]) -> None:
    if output_wav is None:
        return
    if output_wav.exists() and output_wav.is_dir():
        raise SystemExit(f"--output-wav points to a directory: {output_wav}")
    if output_wav.parent and not output_wav.parent.exists():
        raise SystemExit(f"parent directory for --output-wav does not exist: {output_wav.parent}")
    output_wav.write_bytes(audio.get_wav_data())
    print(f"wrote WAV: {output_wav}")


def summarize_audio(label: str, audio) -> None:
    frame_bytes = len(audio.frame_data)
    sample_rate = getattr(audio, "sample_rate", "unknown")
    sample_width = getattr(audio, "sample_width", "unknown")
    print(f"{label}: {frame_bytes} frame bytes, sample_rate={sample_rate}, sample_width={sample_width}")


def capture(args: argparse.Namespace) -> int:
    sr = import_speech_recognition()
    if args.list_devices:
        return list_devices(sr)

    recognizer = make_recognizer(sr, args)
    try:
        microphone = sr.Microphone(
            device_index=args.device_index,
            sample_rate=args.sample_rate,
            chunk_size=args.chunk_size,
        )
    except (AttributeError, AssertionError, OSError) as exc:
        print(explain_pyaudio_failure(exc), file=sys.stderr)
        return 2

    try:
        with microphone as source:
            if args.calibration_duration is not None and args.calibration_duration > 0:
                print(f"Calibrating ambient noise for {args.calibration_duration:g} seconds; stay silent...")
                recognizer.adjust_for_ambient_noise(source, duration=args.calibration_duration)
                print(f"energy_threshold={recognizer.energy_threshold:.3f}")

            if args.mode == "record":
                print(f"Recording fixed window: duration={args.record_duration}, offset={args.record_offset}")
                audio = recognizer.record(
                    source,
                    duration=args.record_duration,
                    offset=args.record_offset,
                )
                summarize_audio("recorded", audio)
                write_wav(audio, args.output_wav)
                return 0

            if args.mode == "stream":
                chunks = []
                print(f"Listening as stream: timeout={args.timeout}, phrase_limit={args.phrase_limit}")
                try:
                    for idx, chunk in enumerate(
                        recognizer.listen(
                            source,
                            timeout=args.timeout,
                            phrase_time_limit=args.phrase_limit,
                            stream=True,
                        ),
                        start=1,
                    ):
                        chunks.append(chunk)
                        summarize_audio(f"chunk {idx}", chunk)
                except sr.WaitTimeoutError:
                    print("Timed out waiting for speech to start.", file=sys.stderr)
                    return 1
                if args.output_wav is not None:
                    # The stream yields AudioData chunks. Concatenate raw PCM only when
                    # all chunks share the microphone sample rate and width.
                    frame_data = b"".join(chunk.frame_data for chunk in chunks)
                    audio = sr.AudioData(frame_data, microphone.SAMPLE_RATE, microphone.SAMPLE_WIDTH)
                    write_wav(audio, args.output_wav)
                return 0

            print(f"Listening for one phrase: timeout={args.timeout}, phrase_limit={args.phrase_limit}")
            try:
                audio = recognizer.listen(
                    source,
                    timeout=args.timeout,
                    phrase_time_limit=args.phrase_limit,
                )
            except sr.WaitTimeoutError:
                print("Timed out waiting for speech to start.", file=sys.stderr)
                return 1
            summarize_audio("captured", audio)
            write_wav(audio, args.output_wav)
            return 0
    except (AssertionError, OSError) as exc:
        print(f"Capture failed: {exc}", file=sys.stderr)
        return 2


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return capture(args)


if __name__ == "__main__":
    raise SystemExit(main())
