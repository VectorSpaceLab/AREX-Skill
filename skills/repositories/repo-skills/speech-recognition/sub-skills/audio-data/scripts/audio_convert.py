#!/usr/bin/env python3
"""Convert local SpeechRecognition-supported audio files to RAW/WAV/AIFF/FLAC.

This helper uses only local file loading and AudioData conversion APIs. It does
not call recognition services, microphones, model downloads, or sprc.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable


def _import_sr():
    try:
        import speech_recognition as sr  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on caller env
        print(
            "Could not import speech_recognition. Install SpeechRecognition "
            "with its declared runtime dependencies before using this helper.\n"
            f"Import error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    return sr


def _parse_formats(value: str) -> list[str]:
    allowed = {"raw", "wav", "aiff", "flac"}
    items = [item.strip().lower() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("at least one format is required")
    unknown = sorted(set(items) - allowed)
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown format(s): {', '.join(unknown)}; choose from raw,wav,aiff,flac"
        )
    result: list[str] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def _non_negative_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Load a local WAV/AIFF/native-FLAC file with SpeechRecognition and "
            "write converted RAW/WAV/AIFF/FLAC outputs."
        )
    )
    parser.add_argument("input", type=Path, help="input audio file path")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="directory for converted files (default: current directory)",
    )
    parser.add_argument(
        "--prefix",
        help="output filename prefix (default: input stem)",
    )
    parser.add_argument(
        "--formats",
        type=_parse_formats,
        default=["wav"],
        help="comma-separated output formats from raw,wav,aiff,flac (default: wav)",
    )
    parser.add_argument(
        "--convert-rate",
        type=_positive_int,
        help="optional output sample rate in Hz",
    )
    parser.add_argument(
        "--convert-width",
        type=_positive_int,
        choices=[1, 2, 3, 4],
        help="optional output sample width in bytes; FLAC supports only 1-3",
    )
    parser.add_argument(
        "--segment-start-ms",
        type=_non_negative_float,
        help="optional segment start time in milliseconds",
    )
    parser.add_argument(
        "--segment-end-ms",
        type=_non_negative_float,
        help="optional segment end time in milliseconds",
    )
    parser.add_argument(
        "--max-bytes",
        type=_positive_int,
        help="split before writing so each chunk's WAV serialization fits this byte limit",
    )
    parser.add_argument(
        "--silence-aware",
        action="store_true",
        help="use AudioData.split(..., silence_aware=True); requires SpeechRecognition[audio-split]",
    )
    return parser


def _output_bytes(audio, fmt: str, convert_rate: int | None, convert_width: int | None) -> bytes:
    method_name = {
        "raw": "get_raw_data",
        "wav": "get_wav_data",
        "aiff": "get_aiff_data",
        "flac": "get_flac_data",
    }[fmt]
    method = getattr(audio, method_name)
    return method(convert_rate=convert_rate, convert_width=convert_width)


def _converted_audio_for_split(sr, audio, convert_rate: int | None, convert_width: int | None):
    """Materialize conversion before split so --max-bytes matches final WAV size."""
    target_rate = convert_rate or audio.sample_rate
    target_width = convert_width or audio.sample_width
    if convert_rate is None and convert_width is None:
        return audio
    # Pass target_width even when it equals the source width so 8-bit PCM is
    # biased back into the canonical representation expected by AudioData.
    raw = audio.get_raw_data(convert_rate=convert_rate, convert_width=target_width)
    return sr.AudioData(raw, target_rate, target_width)


def _iter_output_paths(output_dir: Path, prefix: str, chunk_count: int, formats: Iterable[str]):
    for chunk_index in range(1, chunk_count + 1):
        chunk_suffix = f".part{chunk_index:03d}" if chunk_count > 1 else ""
        for fmt in formats:
            yield chunk_index, fmt, output_dir / f"{prefix}{chunk_suffix}.{fmt}"


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.segment_end_ms is not None and args.segment_start_ms is not None:
        if args.segment_end_ms < args.segment_start_ms:
            parser.error("--segment-end-ms must be greater than or equal to --segment-start-ms")

    if "flac" in args.formats and args.convert_width == 4:
        parser.error("FLAC output does not support --convert-width 4; choose 1, 2, or 3")

    sr = _import_sr()

    audio = sr.AudioData.from_file(str(args.input))
    if args.segment_start_ms is not None or args.segment_end_ms is not None:
        audio = audio.get_segment(args.segment_start_ms, args.segment_end_ms)

    if args.max_bytes is not None:
        audio = _converted_audio_for_split(sr, audio, args.convert_rate, args.convert_width)
        chunks = audio.split(args.max_bytes, silence_aware=args.silence_aware)
        output_convert_rate = None
        output_convert_width = None
    else:
        chunks = [audio]
        output_convert_rate = args.convert_rate
        output_convert_width = args.convert_width

    args.output_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix or args.input.stem

    path_iter = _iter_output_paths(args.output_dir, prefix, len(chunks), args.formats)
    for chunk_index, fmt, out_path in path_iter:
        data = _output_bytes(chunks[chunk_index - 1], fmt, output_convert_rate, output_convert_width)
        out_path.write_bytes(data)
        print(
            f"wrote {out_path} ({len(data)} bytes; format={fmt}; "
            f"chunk={chunk_index}/{len(chunks)})"
        )

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
