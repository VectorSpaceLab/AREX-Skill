#!/usr/bin/env python3
"""Generate SRT or VTT subtitles with FunASR AutoModel.

Examples:
    python generate_subtitles.py meeting.wav --output meeting.srt --device cpu
    python generate_subtitles.py meeting.wav --format vtt --spk --output meeting.vtt
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_TAG_RE = re.compile(r"<\|[^|]*\|>")
MODEL_ALIASES = {
    "sensevoice": "iic/SenseVoiceSmall",
    "sensevoicesmall": "iic/SenseVoiceSmall",
    "paraformer": "paraformer-zh",
}


def resolve_model_name(model):
    return MODEL_ALIASES.get(str(model).lower(), model)


def clean_text(text):
    return _TAG_RE.sub("", text or "").strip()


def normalize_optional(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value or value.lower() in {"none", "null"}:
        return None
    return value


def split_csv(value):
    if not value:
        return []
    return [part.strip() for part in str(value).split(",") if part.strip()]


def parse_ms(value, *, seconds=False):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if seconds:
        number *= 1000
    return int(round(number))


def timestamp_bounds_ms(result):
    bounds = []
    for key in ("timestamp", "timestamps"):
        for ts in result.get(key, []) or []:
            if isinstance(ts, dict):
                start = ts.get("start_time", ts.get("start"))
                end = ts.get("end_time", ts.get("end"))
                start_ms = parse_ms(start, seconds=True)
                end_ms = parse_ms(end, seconds=True)
            elif isinstance(ts, (list, tuple)) and len(ts) >= 2:
                start_ms = parse_ms(ts[0])
                end_ms = parse_ms(ts[1])
            else:
                continue
            if start_ms is None or end_ms is None:
                continue
            if end_ms > start_ms:
                bounds.append((start_ms, end_ms))
    if not bounds:
        return None
    return min(start for start, _ in bounds), max(end for _, end in bounds)


def audio_duration_ms(path):
    try:
        import soundfile as sf

        return int(round(sf.info(str(path)).duration * 1000))
    except Exception:
        return None


def format_time(ms, *, vtt=False):
    ms = max(0, int(round(ms)))
    hours = ms // 3_600_000
    minutes = (ms % 3_600_000) // 60_000
    seconds = (ms % 60_000) // 1000
    millis = ms % 1000
    sep = "." if vtt else ","
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{sep}{millis:03d}"


def import_funasr():
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - import-time guard
        raise SystemExit(
            "generate_subtitles.py requires PyTorch before AutoModel. Install torch and torchaudio first."
        ) from exc

    try:
        from funasr import AutoModel
    except ModuleNotFoundError as exc:  # pragma: no cover - import-time guard
        if exc.name == "torch":
            raise SystemExit(
                "FunASR requires PyTorch before using AutoModel. Install torch and torchaudio first."
            ) from exc
        raise SystemExit(f"Unable to import FunASR: {exc}") from exc

    return AutoModel, torch


def resolve_device(requested, torch):
    if requested and requested != "auto":
        return requested
    return "cuda:0" if torch.cuda.is_available() else "cpu"


def build_model_kwargs(args, device):
    kwargs = {
        "model": resolve_model_name(args.model),
        "device": device,
        "hub": args.hub,
        "disable_update": True,
        "ncpu": args.ncpu,
    }

    vad_model = normalize_optional(args.vad_model)
    if vad_model is not None:
        kwargs["vad_model"] = vad_model
        kwargs["vad_kwargs"] = {"max_single_segment_time": args.vad_max_single_segment_time}

    punc_model = normalize_optional(args.punc_model)
    if punc_model is not None:
        kwargs["punc_model"] = punc_model

    if args.spk:
        spk_model = normalize_optional(args.spk_model) or "cam++"
        kwargs["spk_model"] = spk_model

    return kwargs


def build_generate_kwargs(args, input_path):
    gen_kwargs = {
        "input": str(input_path),
        "batch_size": 1,
        "language": args.language,
        "sentence_timestamp": True,
        "output_timestamp": True,
        "return_time_stamps": True,
    }

    hotwords = split_csv(args.hotwords)
    if hotwords:
        if "paraformer" in args.model.lower():
            gen_kwargs["hotword"] = " ".join(hotwords)
        else:
            gen_kwargs["hotwords"] = hotwords

    if args.postprocess_hotwords:
        gen_kwargs["postprocess_hotwords"] = args.postprocess_hotwords
    if args.postprocess_hotword_file:
        gen_kwargs["postprocess_hotword_file"] = str(args.postprocess_hotword_file)
    if args.postprocess_hotword_threshold is not None:
        gen_kwargs["postprocess_hotword_threshold"] = args.postprocess_hotword_threshold
    if args.postprocess_hotwords or args.postprocess_hotword_file:
        gen_kwargs["postprocess_hotword_fuzzy"] = bool(args.postprocess_hotword_fuzzy)

    return gen_kwargs


def extract_segments(result, fallback_duration_ms):
    segments = []
    for seg in result.get("sentence_info", []) or []:
        if not isinstance(seg, dict):
            continue
        text = clean_text(seg.get("sentence") or seg.get("text"))
        start = parse_ms(seg.get("start")) or 0
        end = parse_ms(seg.get("end")) or 0
        if text and end > start:
            segments.append({"start": start, "end": end, "text": text, "spk": seg.get("spk")})

    if segments:
        return segments

    text = clean_text(result.get("text"))
    if not text:
        return []

    bounds = timestamp_bounds_ms(result)
    if bounds is not None:
        start, end = bounds
    elif fallback_duration_ms and fallback_duration_ms > 0:
        start, end = 0, fallback_duration_ms
    else:
        start, end = 0, 0
    return [{"start": start, "end": end, "text": text, "spk": None}]


def write_subtitles(segments, output, output_format, include_spk):
    output.parent.mkdir(parents=True, exist_ok=True)
    is_vtt = output_format == "vtt"
    with output.open("w", encoding="utf-8") as f:
        if is_vtt:
            f.write("WEBVTT\n\n")
        for index, seg in enumerate(segments, start=1):
            text = seg["text"]
            if include_spk and seg.get("spk") is not None:
                text = f"[Speaker {seg['spk']}] {text}"
            time_line = f"{format_time(seg['start'], vtt=is_vtt)} --> {format_time(seg['end'], vtt=is_vtt)}"
            if is_vtt:
                f.write(f"{time_line}\n{text}\n\n")
            else:
                f.write(f"{index}\n{time_line}\n{text}\n\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_subtitles.py",
        description="Generate SRT or VTT subtitles from audio/video with FunASR.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="Audio or video file path.")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output subtitle file.")
    parser.add_argument("--format", "-f", choices=["srt", "vtt"], default="srt", help="Subtitle format.")
    parser.add_argument("--model", "-m", default="iic/SenseVoiceSmall", help="Model id, alias, or local path.")
    parser.add_argument("--hub", "-H", default="ms", choices=["ms", "hf"], help="Model hub.")
    parser.add_argument("--device", "-d", default="auto", help="Device name or 'auto'.")
    parser.add_argument("--language", "--lang", "-l", default="auto", help="Language hint.")
    parser.add_argument("--ncpu", type=int, default=4, help="Torch thread count.")
    parser.add_argument("--vad-model", default="fsmn-vad", help="VAD model id, or 'none'.")
    parser.add_argument(
        "--vad-max-single-segment-time",
        type=int,
        default=30000,
        help="Maximum VAD segment length in milliseconds.",
    )
    parser.add_argument("--punc-model", default="ct-punc", help="Punctuation model id, or 'none'.")
    parser.add_argument("--spk", action="store_true", help="Include speaker labels when available.")
    parser.add_argument("--spk-model", default="cam++", help="Speaker model id used with --spk.")
    parser.add_argument("--hotwords", default=None, help="Comma-separated model-level hotwords.")
    parser.add_argument(
        "--postprocess-hotwords",
        default=None,
        help="Explicit postprocess mappings or newline-separated targets.",
    )
    parser.add_argument(
        "--postprocess-hotword-file",
        type=Path,
        default=None,
        help="File containing postprocess hotword targets or explicit mappings.",
    )
    parser.add_argument(
        "--postprocess-hotword-threshold",
        type=float,
        default=0.85,
        help="Fuzzy postprocess threshold in [0, 1].",
    )
    parser.add_argument(
        "--postprocess-hotword-fuzzy",
        action="store_true",
        help="Enable fuzzy postprocess matching when optional deps are installed.",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Print progress to stderr.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_path = args.input.expanduser()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    if not input_path.is_file():
        raise SystemExit(f"Input path is not a file: {input_path}")

    output = args.output or input_path.with_suffix("." + args.format)

    try:
        AutoModel, torch = import_funasr()
        device = resolve_device(args.device, torch)
        if args.verbose:
            print(f"Loading {args.model} on {device}", file=sys.stderr)
        model = AutoModel(**build_model_kwargs(args, device))
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(f"Failed to load model: {exc}") from exc

    if args.verbose:
        print(f"Transcribing {input_path}", file=sys.stderr)
    try:
        result_list = model.generate(**build_generate_kwargs(args, input_path))
    except Exception as exc:
        raise SystemExit(f"Transcription failed: {exc}") from exc
    result = result_list[0] if result_list and isinstance(result_list, list) else {}
    if not isinstance(result, dict):
        result = {"text": str(result)}

    segments = extract_segments(result, audio_duration_ms(input_path))
    if not segments:
        if args.verbose:
            print("No speech detected; no subtitle file written.", file=sys.stderr)
        return

    write_subtitles(segments, output, args.format, args.spk)
    if args.verbose:
        print(f"Wrote {len(segments)} subtitle cue(s) to {output}", file=sys.stderr)


if __name__ == "__main__":
    main()
