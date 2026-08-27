#!/usr/bin/env python3
"""Porcupine file checker.

Safe modes:
- --help: show the parser without requiring an AccessKey
- --list-devices: enumerate inference devices without scanning audio

Example invocations:
    python porcupine_file_check.py --help
    python porcupine_file_check.py --list-devices
    python porcupine_file_check.py --access-key "$ACCESS_KEY" --input-wav sample.wav --keyword picovoice
    python porcupine_file_check.py --access-key "$ACCESS_KEY" --input-wav sample.wav --keyword-path ./custom.ppn --model-path ./porcupine_params.pv
"""

from __future__ import annotations

import argparse
import struct
import sys
import wave
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan a 16-bit WAV file with Porcupine or list available inference devices.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--access-key", help="Picovoice AccessKey for engine initialization.")
    parser.add_argument("--input-wav", help="Path to a 16-bit WAV file.")

    keyword_group = parser.add_mutually_exclusive_group()
    keyword_group.add_argument(
        "--keyword",
        dest="keywords",
        action="append",
        nargs="+",
        default=[],
        metavar="KEYWORD",
        help="Built-in keyword phrase from pvporcupine.KEYWORDS. Repeat or pass multiple values after one flag.",
    )
    keyword_group.add_argument(
        "--keyword-path",
        dest="keyword_paths",
        action="append",
        nargs="+",
        default=[],
        metavar="PATH",
        help="Path to a custom .ppn keyword model. Repeat or pass multiple paths after one flag.",
    )

    parser.add_argument(
        "--sensitivity",
        dest="sensitivities",
        action="append",
        nargs="+",
        type=float,
        default=[],
        metavar="VALUE",
        help="Sensitivity per keyword in the inclusive range [0, 1]. Supply one value per keyword.",
    )
    parser.add_argument("--model-path", help="Path to the Porcupine .pv model file.")
    parser.add_argument("--library-path", help="Path to the Porcupine native library.")
    parser.add_argument(
        "--device",
        help="Inference device string such as best, cpu, cpu:N, gpu, or gpu:N.",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="Print available inference devices and exit.",
    )
    return parser


def _flatten(nested_values):
    return [value for group in nested_values for value in group]


def _load_pvporcupine():
    try:
        import pvporcupine
    except ModuleNotFoundError as exc:
        missing = exc.name or "pvporcupine"
        raise RuntimeError(
            f"Missing dependency while importing pvporcupine: {missing}. Install with: pip install pvporcupine"
        ) from exc
    return pvporcupine


def keyword_label_from_path(keyword_path: str) -> str:
    stem = Path(keyword_path).stem
    parts = stem.split("_")
    if len(parts) > 6:
        return " ".join(parts[:-6])
    if parts:
        return parts[0]
    return stem


def read_wav_frames(input_wav: str, expected_sample_rate: int, frame_length: int):
    input_path = Path(input_wav).expanduser()
    if not input_path.exists():
        raise FileNotFoundError(f"Could not find input WAV at '{input_path}'.")

    try:
        with wave.open(str(input_path), "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            num_frames = wav_file.getnframes()

            if sample_width != 2:
                raise ValueError(f"Audio file should be 16-bit PCM; got {sample_width}-byte samples.")
            if sample_rate != expected_sample_rate:
                raise ValueError(
                    f"Audio file should have a sample rate of {expected_sample_rate}, got {sample_rate}."
                )
            if channels not in (1, 2):
                raise ValueError(f"Porcupine expects mono or stereo WAV input; got {channels} channels.")

            pcm_bytes = wav_file.readframes(num_frames)
    except wave.Error as exc:
        raise ValueError(f"Failed to read WAV file: {exc}") from exc

    sample_count = num_frames * channels
    pcm = struct.unpack(f"<{sample_count}h", pcm_bytes) if sample_count else tuple()

    if channels == 2:
        print("INFO: stereo input detected; processing the left channel only.", file=sys.stderr)
        pcm = pcm[::2]

    pcm = list(pcm)
    if len(pcm) < frame_length:
        raise ValueError(
            f"Input WAV contains only {len(pcm)} sample(s); Porcupine needs at least one frame of {frame_length} samples."
        )

    remainder = len(pcm) % frame_length
    if remainder:
        print(
            f"WARNING: ignoring {remainder} trailing sample(s) because Porcupine processes {frame_length}-sample frames.",
            file=sys.stderr,
        )

    return pcm


def resolve_targets(pvporcupine, keywords, keyword_paths, sensitivities):
    keyword_names = _flatten(keywords)
    keyword_model_paths = _flatten(keyword_paths)
    sensitivity_values = _flatten(sensitivities)

    if keyword_names and keyword_model_paths:
        raise ValueError("Use either --keyword or --keyword-path, not both.")
    if not keyword_names and not keyword_model_paths:
        raise ValueError("Provide at least one --keyword or --keyword-path.")

    if keyword_model_paths:
        labels = [keyword_label_from_path(path) for path in keyword_model_paths]
        resolved_paths = [str(Path(path).expanduser()) for path in keyword_model_paths]
    else:
        unknown = [keyword for keyword in keyword_names if keyword not in pvporcupine.KEYWORDS]
        if unknown:
            available = ", ".join(sorted(pvporcupine.KEYWORDS))
            raise ValueError(
                f"Unknown built-in keyword(s): {', '.join(unknown)}. Available keywords: {available}"
            )
        labels = keyword_names
        resolved_paths = [pvporcupine.KEYWORD_PATHS[keyword] for keyword in keyword_names]

    if not sensitivity_values:
        sensitivity_values = [0.5] * len(resolved_paths)

    if len(sensitivity_values) != len(resolved_paths):
        raise ValueError(
            f"Number of keywords does not match the number of sensitivities: {len(resolved_paths)} keyword(s) vs {len(sensitivity_values)} sensitivity value(s)."
        )

    for sensitivity in sensitivity_values:
        if not 0.0 <= sensitivity <= 1.0:
            raise ValueError("Sensitivity values must be within [0, 1].")

    return labels, resolved_paths, sensitivity_values


def list_devices(pvporcupine, library_path):
    try:
        devices = pvporcupine.available_devices(library_path=library_path)
    except pvporcupine.PorcupineError as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    for device in devices:
        print(device)
    return 0


def run_detection(args, pvporcupine):
    if not args.access_key:
        raise ValueError("Argument --access-key is required for detection. Use --help or --list-devices for safe checks.")
    if not args.input_wav:
        raise ValueError("Argument --input-wav is required for detection.")

    labels, keyword_paths, sensitivities = resolve_targets(
        pvporcupine,
        args.keywords,
        args.keyword_paths,
        args.sensitivities,
    )

    porcupine = None
    try:
        porcupine = pvporcupine.create(
            access_key=args.access_key,
            library_path=args.library_path,
            model_path=args.model_path,
            device=args.device,
            keyword_paths=keyword_paths,
            sensitivities=sensitivities,
        )
    except pvporcupine.PorcupineError as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        print(f"Porcupine version: {porcupine.version}")
        print(f"Frame length: {porcupine.frame_length} samples @ {porcupine.sample_rate} Hz")

        pcm = read_wav_frames(args.input_wav, porcupine.sample_rate, porcupine.frame_length)
        total_frames = len(pcm) // porcupine.frame_length

        for frame_index in range(total_frames):
            frame = pcm[frame_index * porcupine.frame_length : (frame_index + 1) * porcupine.frame_length]
            keyword_index = porcupine.process(frame)
            if keyword_index >= 0:
                timestamp = (frame_index * porcupine.frame_length) / float(porcupine.sample_rate)
                print(f"Detected '{labels[keyword_index]}' at {timestamp:.2f}s")
    except pvporcupine.PorcupineError as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        if porcupine is not None:
            porcupine.delete()

    return 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        pvporcupine = _load_pvporcupine()

        if args.list_devices:
            return list_devices(pvporcupine, args.library_path)

        return run_detection(args, pvporcupine)
    except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
