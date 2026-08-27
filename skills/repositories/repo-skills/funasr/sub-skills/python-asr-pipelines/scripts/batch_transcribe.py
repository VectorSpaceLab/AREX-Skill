#!/usr/bin/env python3
"""Safe batch transcription helper for the python-asr-pipelines sub-skill.

Examples:
    python batch_transcribe.py ./audio --output transcripts.txt --model sensevoice
    python batch_transcribe.py ./audio --output transcripts.jsonl --output-format jsonl --recursive
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

_TAG_RE = re.compile(r"<\|[^|]*\|>")
MODEL_ALIASES = {
    "sensevoice": "iic/SenseVoiceSmall",
    "sensevoicesmall": "iic/SenseVoiceSmall",
    "paraformer": "paraformer-zh",
}


def resolve_model_name(model):
    return MODEL_ALIASES.get(str(model).lower(), model)


def strip_rich_tags(text):
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
    items = []
    for part in str(value).split(","):
        part = part.strip()
        if part:
            items.append(part)
    return items


def parse_extensions(values):
    extensions = set()
    for value in values:
        for part in str(value).split(","):
            part = part.strip().lower()
            if not part:
                continue
            if not part.startswith("."):
                part = "." + part
            extensions.add(part)
    return extensions


def collect_audio_paths(items, recursive, extensions):
    paths = []
    seen = set()

    for raw_item in items:
        path = Path(raw_item).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Input path not found: {path}")

        if path.is_file():
            resolved = path.resolve()
            if resolved not in seen:
                paths.append(path)
                seen.add(resolved)
            continue

        if not path.is_dir():
            raise ValueError(f"Input path is neither a file nor a directory: {path}")

        iterator = path.rglob("*") if recursive else path.iterdir()
        for candidate in sorted(iterator):
            if not candidate.is_file():
                continue
            if extensions and candidate.suffix.lower() not in extensions:
                continue
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            paths.append(candidate)
            seen.add(resolved)

    if not paths:
        raise FileNotFoundError("No audio files matched the requested inputs.")
    return paths


def import_funasr():
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - import-time guard
        raise SystemExit(
            "batch_transcribe.py requires PyTorch before AutoModel. Install torch and torchaudio first."
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

    return kwargs


def build_generate_kwargs(args):
    gen_kwargs = {"batch_size": 1, "input": None}
    gen_kwargs["language"] = args.language

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
        # Fuzzy correction is opt-in so explicit mappings still work in
        # environments without pypinyin.
        gen_kwargs["postprocess_hotword_fuzzy"] = bool(args.postprocess_hotword_fuzzy)
    if args.return_postprocess_hotword_matches:
        gen_kwargs["return_postprocess_hotword_matches"] = True

    return gen_kwargs


def clean_result(result):
    cleaned = dict(result)
    cleaned["text"] = strip_rich_tags(str(cleaned.get("text", "")))
    sentence_info = cleaned.get("sentence_info")
    if isinstance(sentence_info, list):
        cleaned_sentence_info = []
        for seg in sentence_info:
            if not isinstance(seg, dict):
                continue
            item = dict(seg)
            for field in ("text", "sentence"):
                if field in item and isinstance(item[field], str):
                    item[field] = strip_rich_tags(item[field])
            cleaned_sentence_info.append(item)
        cleaned["sentence_info"] = cleaned_sentence_info
    return cleaned


def transcribe_one(model, path, args):
    gen_kwargs = build_generate_kwargs(args)
    gen_kwargs["input"] = str(path)

    started = time.time()
    try:
        result_list = model.generate(**gen_kwargs)
    except Exception as exc:
        return {
            "file": str(path),
            "status": "error",
            "error": str(exc),
            "model": args.model,
            "hub": args.hub,
            "language": args.language,
            "elapsed_s": round(time.time() - started, 3),
        }

    if not result_list:
        return {
            "file": str(path),
            "status": "error",
            "error": "No results returned",
            "model": args.model,
            "hub": args.hub,
            "language": args.language,
            "elapsed_s": round(time.time() - started, 3),
        }

    result = result_list[0] if isinstance(result_list, list) else result_list
    if not isinstance(result, dict):
        result = {"text": str(result)}
    result = clean_result(result)

    record = {
        "file": str(path),
        "status": "ok",
        "text": result.get("text", ""),
        "model": args.model,
        "hub": args.hub,
        "language": args.language,
        "elapsed_s": round(time.time() - started, 3),
    }
    for key in ("timestamp", "timestamps", "sentence_info", "raw_text", "postprocess_hotword_matches"):
        value = result.get(key)
        if value not in (None, [], {}):
            record[key] = value
    return record


def write_records(records, output, output_format):
    output.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "jsonl":
        with output.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return

    with output.open("w", encoding="utf-8") as f:
        for record in records:
            text = record.get("text", "")
            if record.get("status") != "ok":
                text = f"<ERROR: {record.get('error', 'unknown error')}>"
            f.write(f"{record.get('file', '')}\t{text}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batch_transcribe.py",
        description="Batch transcription helper for FunASR.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Audio files or folders to transcribe. You can also use --input.",
    )
    parser.add_argument(
        "--input",
        "-i",
        dest="input_flags",
        action="append",
        default=[],
        metavar="INPUT",
        help="Audio file or folder to transcribe. Repeat for multiple inputs.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("funasr_batch_transcripts.txt"),
        help="Output report file.",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "jsonl"],
        default="text",
        help="Output format for the batch report.",
    )
    parser.add_argument("--model", "-m", default="sensevoice", help="Model alias or path.")
    parser.add_argument("--hub", "-H", default="ms", choices=["ms", "hf"], help="Model hub.")
    parser.add_argument("--device", "-d", default="auto", help="Device name or 'auto'.")
    parser.add_argument("--language", "--lang", "-l", default="auto", help="Language hint.")
    parser.add_argument("--ncpu", type=int, default=4, help="Torch thread count.")
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Recursively scan input folders.",
    )
    parser.add_argument(
        "--extensions",
        "-e",
        nargs="+",
        default=[".wav", ".mp3", ".flac", ".ogg", ".m4a", ".mp4", ".webm", ".pcm"],
        help="File extensions to include when scanning folders.",
    )
    parser.add_argument(
        "--vad-model",
        default="fsmn-vad",
        help="VAD model id, or 'none' to disable segmentation.",
    )
    parser.add_argument(
        "--vad-max-single-segment-time",
        type=int,
        default=30000,
        help="Maximum VAD segment length in milliseconds.",
    )
    parser.add_argument(
        "--punc-model",
        default="none",
        help="Optional punctuation model id, or 'none' to skip punctuation.",
    )
    parser.add_argument(
        "--hotwords",
        default=None,
        help="Comma-separated model-level hotwords.",
    )
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
    parser.add_argument(
        "--return-postprocess-hotword-matches",
        action="store_true",
        help="Include postprocess replacement details in jsonl output.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show model loading and progress information on stderr.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        raw_inputs = list(args.input_flags or []) + list(args.inputs or [])
        if not raw_inputs:
            parser.error("provide at least one input file or folder with --input or a positional argument")
        AutoModel, torch = import_funasr()
        device = resolve_device(args.device, torch)
        audio_paths = collect_audio_paths(raw_inputs, args.recursive, parse_extensions(args.extensions))
        model = AutoModel(**build_model_kwargs(args, device))
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(str(exc)) from exc

    if args.verbose:
        print(f"Loaded {args.model} on {device}", file=sys.stderr)
        print(f"Transcribing {len(audio_paths)} file(s)...", file=sys.stderr)

    records = []
    for index, path in enumerate(audio_paths, start=1):
        if args.verbose:
            print(f"[{index}/{len(audio_paths)}] {path}", file=sys.stderr)
        record = transcribe_one(model, path, args)
        records.append(record)
        if args.verbose and record.get("status") != "ok":
            print(f"  error: {record.get('error', 'unknown error')}", file=sys.stderr)

    write_records(records, args.output, args.output_format)

    if args.verbose:
        print(f"Wrote {len(records)} record(s) to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
