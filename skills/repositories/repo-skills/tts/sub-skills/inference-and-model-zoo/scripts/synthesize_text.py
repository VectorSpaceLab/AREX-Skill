#!/usr/bin/env python3
"""Safe Coqui TTS Python API synthesis wrapper.

The script deliberately refuses to load released registry models unless
--allow-download is supplied, because loading can download large files, write a
model cache, and prompt for terms-of-service acceptance. Use --dry-run to check
arguments without importing heavy model modules or loading checkpoints.

Examples:
  python scripts/synthesize_text.py --model-name tts_models/en/ljspeech/tacotron2-DDC --text "Hello" --out-path hello.wav --dry-run
  python scripts/synthesize_text.py --model-name tts_models/en/ljspeech/tacotron2-DDC --text "Hello" --out-path hello.wav --allow-download
  python scripts/synthesize_text.py --model-path checkpoint.pth --config-path config.json --text "Hello" --out-path custom.wav --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synthesize text with Coqui TTS through a safe TTS.api wrapper."
    )
    model = parser.add_mutually_exclusive_group(required=True)
    model.add_argument(
        "--model-name",
        help="Released TTS model name or supported alias. Requires --allow-download to actually load.",
    )
    model.add_argument(
        "--model-path",
        type=Path,
        help="Custom TTS checkpoint path. Requires --config-path. Does not use the registry downloader.",
    )
    parser.add_argument("--config-path", type=Path, help="Custom TTS config path for --model-path.")
    parser.add_argument("--vocoder-path", type=Path, help="Optional custom vocoder checkpoint path.")
    parser.add_argument("--vocoder-config-path", type=Path, help="Optional custom vocoder config path.")
    parser.add_argument("--text", required=True, help="Text to synthesize.")
    parser.add_argument("--out-path", type=Path, required=True, help="Output wav file path.")
    parser.add_argument("--speaker", help="Speaker name/id for multi-speaker models.")
    parser.add_argument("--language", help="Language code/name for multilingual models.")
    parser.add_argument(
        "--speaker-wav",
        nargs="+",
        help="One or more reference wav paths for voice-cloning-capable models.",
    )
    split = parser.add_mutually_exclusive_group()
    split.add_argument(
        "--split-sentences",
        dest="split_sentences",
        action="store_true",
        default=True,
        help="Split text into sentences before synthesis. Default.",
    )
    split.add_argument(
        "--no-split-sentences",
        dest="split_sentences",
        action="store_false",
        help="Keep text as one segment; may use more memory and hit model context limits.",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Torch device: cpu, cuda, cuda:0, or auto. Default: cpu.",
    )
    parser.add_argument(
        "--progress-bar",
        action="store_true",
        help="Show Coqui download progress bars when downloads are approved. Default: disabled.",
    )
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="Acknowledge that released --model-name loading may download files, write cache, and prompt for TOS.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate arguments and print the execution plan without importing TTS.api or loading models.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing output wav. Default refuses to overwrite during real runs.",
    )
    return parser.parse_args(argv)


def fail(message: str, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def check_file(path: Optional[Path], label: str) -> None:
    if path is not None and not path.is_file():
        fail(f"{label} does not exist or is not a file: {path}")


def validate_args(args: argparse.Namespace) -> None:
    if args.model_name:
        if args.model_name.startswith("vocoder_models/"):
            fail("--model-name must be a TTS model, not a vocoder model. Use a custom vocoder with --vocoder-path or route CLI pairing elsewhere.")
        if args.model_name.startswith("voice_conversion_models/"):
            fail("This helper synthesizes text. Use the voice-conversion sub-skill for voice_conversion_models.")
    else:
        if args.config_path is None:
            fail("--config-path is required with --model-path.")
        check_file(args.model_path, "--model-path")
        check_file(args.config_path, "--config-path")

    if bool(args.vocoder_path) != bool(args.vocoder_config_path):
        fail("Provide both --vocoder-path and --vocoder-config-path, or neither.")
    check_file(args.vocoder_path, "--vocoder-path")
    check_file(args.vocoder_config_path, "--vocoder-config-path")

    if not args.text.strip():
        fail("--text must not be empty.")

    if args.out_path.exists() and not args.overwrite and not args.dry_run:
        fail(f"Output already exists: {args.out_path}. Pass --overwrite to replace it.")

    if args.model_name and not args.allow_download and not args.dry_run:
        fail(
            "Released --model-name loading can download large files, write cache, and prompt for TOS. "
            "Rerun with --allow-download only after explicit user approval, or use --dry-run."
        )


def plan_payload(args: argparse.Namespace) -> dict:
    return {
        "mode": "released-model" if args.model_name else "custom-checkpoint",
        "model_name": args.model_name,
        "model_path": str(args.model_path) if args.model_path else None,
        "config_path": str(args.config_path) if args.config_path else None,
        "vocoder_path": str(args.vocoder_path) if args.vocoder_path else None,
        "vocoder_config_path": str(args.vocoder_config_path) if args.vocoder_config_path else None,
        "text_chars": len(args.text),
        "out_path": str(args.out_path),
        "speaker": args.speaker,
        "language": args.language,
        "speaker_wav_count": len(args.speaker_wav or []),
        "split_sentences": args.split_sentences,
        "device": args.device,
        "released_model_download_acknowledged": bool(args.allow_download),
    }


def resolve_device(device: str) -> str:
    if device == "auto":
        try:
            import torch  # type: ignore
        except Exception:
            return "cpu"
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device.startswith("cuda"):
        try:
            import torch  # type: ignore
        except Exception as exc:  # noqa: BLE001
            fail(f"CUDA requested but torch could not be imported: {exc.__class__.__name__}: {exc}")
        if not torch.cuda.is_available():
            fail("CUDA was requested but torch.cuda.is_available() is false. Use --device cpu or a CUDA-capable environment.")
    return device


def run_synthesis(args: argparse.Namespace) -> dict:
    try:
        from TTS.api import TTS  # type: ignore
    except Exception as exc:  # noqa: BLE001
        fail(
            "Could not import TTS.api.TTS. Install Coqui TTS with its inference dependencies "
            "in a supported Python 3.9-3.11 environment. "
            f"Import error: {exc.__class__.__name__}: {exc}"
        )

    device = resolve_device(args.device)
    if args.model_name:
        tts = TTS(model_name=args.model_name, progress_bar=args.progress_bar).to(device)
    else:
        tts = TTS(
            model_path=str(args.model_path),
            config_path=str(args.config_path),
            vocoder_path=str(args.vocoder_path) if args.vocoder_path else None,
            vocoder_config_path=str(args.vocoder_config_path) if args.vocoder_config_path else None,
            progress_bar=args.progress_bar,
        ).to(device)

    speaker_wav = None
    if args.speaker_wav:
        speaker_wav = args.speaker_wav if len(args.speaker_wav) > 1 else args.speaker_wav[0]

    args.out_path.parent.mkdir(parents=True, exist_ok=True)
    result_path = tts.tts_to_file(
        text=args.text,
        speaker=args.speaker,
        language=args.language,
        speaker_wav=speaker_wav,
        file_path=str(args.out_path),
        split_sentences=args.split_sentences,
    )
    return {
        "output_path": result_path,
        "device": device,
        "model_name": args.model_name,
        "custom_model": bool(args.model_path),
        "speaker": args.speaker,
        "language": args.language,
        "speaker_wav_count": len(args.speaker_wav or []),
        "split_sentences": args.split_sentences,
    }


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    validate_args(args)
    if args.dry_run:
        print(json.dumps({"dry_run": True, "plan": plan_payload(args)}, indent=2, sort_keys=True))
        if args.model_name and not args.allow_download:
            print(
                "NOTE: A real run with --model-name will require --allow-download after user approval.",
                file=sys.stderr,
            )
        return 0

    result = run_synthesis(args)
    print(json.dumps({"ok": True, "result": result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
