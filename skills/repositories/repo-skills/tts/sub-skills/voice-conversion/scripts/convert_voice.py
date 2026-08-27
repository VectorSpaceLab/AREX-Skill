#!/usr/bin/env python3
"""Safe wrapper for Coqui TTS FreeVC and TTS+VC conversion.

By default this helper only validates and plans. It refuses to import/load Coqui
TTS models unless --allow-download is explicit, because model loading can touch
the network or cache.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_voice_conversion_inputs import (  # noqa: E402
    render_report,
    report_has_errors,
    validate_voice_conversion_request,
)

FREEVC_MODEL = "voice_conversion_models/multilingual/vctk/freevc24"


def _str_to_bool(value: str) -> bool:
    value = value.lower().strip()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected a boolean value, got {value!r}")


def _validation_namespace(args: argparse.Namespace) -> argparse.Namespace:
    if args.mode == "freevc":
        mode = "voice-conversion"
        speaker_wav = None
    else:
        mode = "tts-with-vc"
        speaker_wav = [args.speaker_wav] if args.speaker_wav else None
    return argparse.Namespace(
        mode=mode,
        source_wav=args.source_wav,
        target_wav=args.target_wav,
        speaker_wav=speaker_wav,
        reference_wav=None,
        output_wav=args.out_path,
        allow_overwrite=args.allow_overwrite,
        create_output_dir=args.create_output_dir,
        allow_non_wav=args.allow_non_wav,
        strict_wave_header=args.strict_wave_header,
        no_sample_rate_warning=args.no_sample_rate_warning,
        json=False,
    )


def _print_plan(args: argparse.Namespace) -> None:
    print("conversion plan:")
    print(f"  mode: {args.mode}")
    print(f"  FreeVC model: {args.freevc_model_name}")
    if args.mode == "freevc":
        print(f"  source_wav: {args.source_wav}")
        print(f"  target_wav: {args.target_wav}")
    else:
        print(f"  TTS model: {args.tts_model_name}")
        print(f"  text characters: {len(args.text or '')}")
        print(f"  speaker_wav target reference: {args.speaker_wav}")
        if args.language:
            print(f"  TTS language: {args.language}")
        if args.speaker:
            print(f"  TTS speaker: {args.speaker}")
        print(f"  split_sentences: {args.split_sentences}")
    print(f"  out_path: {args.out_path}")
    print(f"  requested device: {args.device}")
    if args.dry_run:
        print("dry-run: no TTS import, model load, download, or output wav write performed")


def _resolve_device(device: str) -> str:
    if device == "cpu":
        return "cpu"
    try:
        import torch
    except Exception as exc:  # pragma: no cover - depends on runtime installation
        raise RuntimeError(f"cannot inspect CUDA because torch import failed: {exc}") from exc
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("--device cuda was requested, but torch.cuda.is_available() is False")
    return device


def _run_freevc(args: argparse.Namespace, device: str) -> str:
    from TTS.api import TTS

    api = TTS(progress_bar=args.progress_bar)
    api.load_vc_model_by_name(args.freevc_model_name, gpu=(device == "cuda"))
    api.to(device)
    return api.voice_conversion_to_file(
        source_wav=args.source_wav,
        target_wav=args.target_wav,
        file_path=args.out_path,
    )


def _run_tts_with_vc(args: argparse.Namespace, device: str) -> str:
    from TTS.api import TTS

    api = TTS(model_name=args.tts_model_name, progress_bar=args.progress_bar)
    api.to(device)
    # Preload explicitly so a lazy FreeVC download cannot happen invisibly inside tts_with_vc().
    api.load_vc_model_by_name(args.freevc_model_name, gpu=(device == "cuda"))
    api.to(device)
    return api.tts_with_vc_to_file(
        text=args.text,
        language=args.language,
        speaker_wav=args.speaker_wav,
        file_path=args.out_path,
        speaker=args.speaker,
        split_sentences=args.split_sentences,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and optionally run Coqui TTS FreeVC or TTS+VC conversion with explicit download approval."
    )
    parser.add_argument("--mode", choices=["freevc", "tts-with-vc"], required=True)
    parser.add_argument("--source-wav", help="Source utterance to convert for --mode freevc.")
    parser.add_argument("--target-wav", help="Target speaker reference for --mode freevc.")
    parser.add_argument("--speaker-wav", help="Target/reference speaker wav for --mode tts-with-vc.")
    parser.add_argument("--text", help="Text to synthesize before conversion in --mode tts-with-vc.")
    parser.add_argument("--tts-model-name", help="TTS model name for --mode tts-with-vc.")
    parser.add_argument("--freevc-model-name", default=FREEVC_MODEL, help="Voice conversion model name to load.")
    parser.add_argument("--language", help="Language ID/code for multilingual TTS models when needed.")
    parser.add_argument("--speaker", help="Speaker ID/name for multi-speaker TTS models when needed.")
    parser.add_argument("--split-sentences", type=_str_to_bool, default=True, help="Whether the TTS step splits text into sentences (default: true).")
    parser.add_argument("--out-path", default="output.wav", help="Output wav path.")
    parser.add_argument("--device", choices=["cpu", "cuda", "auto"], default="cpu")
    parser.add_argument("--progress-bar", action="store_true", help="Show Coqui model download progress bars.")
    parser.add_argument("--allow-download", action="store_true", help="Allow model load/download/cache access. Required for non-dry-run execution.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the plan without importing TTS or loading models.")
    parser.add_argument("--allow-overwrite", action="store_true", help="Allow replacing an existing output wav.")
    parser.add_argument("--create-output-dir", action="store_true", help="Create the output parent directory if missing.")
    parser.add_argument("--allow-non-wav", action="store_true", help="Warn instead of failing on non-.wav inputs.")
    parser.add_argument("--strict-wave-header", action="store_true", help="Fail if Python cannot parse a standard wav header.")
    parser.add_argument("--no-sample-rate-warning", action="store_true", help="Suppress warnings for inputs not already at 16 kHz.")
    return parser


def _check_required_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.mode == "freevc":
        if not args.source_wav:
            parser.error("--source-wav is required for --mode freevc")
        if not args.target_wav:
            parser.error("--target-wav is required for --mode freevc")
    if args.mode == "tts-with-vc":
        if not args.text:
            parser.error("--text is required for --mode tts-with-vc")
        if not args.tts_model_name:
            parser.error("--tts-model-name is required for --mode tts-with-vc")
        if not args.speaker_wav:
            parser.error("--speaker-wav is required for --mode tts-with-vc")


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _check_required_args(parser, args)

    validation_report = validate_voice_conversion_request(_validation_namespace(args))
    print(render_report(validation_report))
    if report_has_errors(validation_report):
        return 1

    _print_plan(args)
    if args.dry_run:
        return 0
    if not args.allow_download:
        print("error: refusing to import/load models without --allow-download; rerun with --dry-run for planning", file=sys.stderr)
        return 2

    try:
        device = _resolve_device(args.device)
        if args.mode == "freevc":
            output_path = _run_freevc(args, device)
        else:
            output_path = _run_tts_with_vc(args, device)
    except Exception as exc:  # pragma: no cover - runtime/model/cache dependent
        print(f"conversion failed: {exc}", file=sys.stderr)
        return 3

    print(f"wrote: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
