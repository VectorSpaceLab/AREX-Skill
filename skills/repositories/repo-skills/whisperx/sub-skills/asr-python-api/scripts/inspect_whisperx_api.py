#!/usr/bin/env python3
"""Safely inspect the installed WhisperX ASR Python API.

This helper imports modules and prints signatures only. It intentionally does
not call whisperx.load_model, download model weights, decode user audio, or run
transcription.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import inspect
import json
import sys
from typing import Any


PUBLIC_LAZY_NAMES = [
    "load_model",
    "load_audio",
    "load_align_model",
    "align",
    "assign_word_speakers",
    "setup_logging",
    "get_logger",
]


def import_optional(module_name: str):
    try:
        return importlib.import_module(module_name), None
    except Exception as exc:  # pragma: no cover - diagnostic path
        return None, f"{type(exc).__name__}: {exc}"


def package_version(dist_name: str) -> str:
    try:
        return importlib.metadata.version(dist_name)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"unavailable ({type(exc).__name__}: {exc})"


def safe_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"unavailable ({type(exc).__name__}: {exc})"


def build_report() -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    report: dict[str, Any] = {
        "package": "whisperx",
        "version": package_version("whisperx"),
        "public_lazy_api": {},
        "signatures": {},
        "constants": {},
        "schema": {},
        "torch": {},
        "warnings": [],
    }

    whisperx, err = import_optional("whisperx")
    if err:
        warnings.append(f"Could not import whisperx: {err}")
        report["warnings"] = warnings + [
            "Install the whisperx distribution before running ASR API workflows."
        ]
        return report, warnings

    for name in PUBLIC_LAZY_NAMES:
        value = getattr(whisperx, name, None)
        report["public_lazy_api"][name] = {
            "present": value is not None,
            "callable": callable(value),
            "signature": safe_signature(value) if callable(value) else None,
        }
        if value is None:
            warnings.append(f"Missing public lazy API: whisperx.{name}")

    asr, err = import_optional("whisperx.asr")
    if err:
        warnings.append(f"Could not import whisperx.asr: {err}")
    else:
        report["signatures"]["whisperx.asr.load_model"] = safe_signature(asr.load_model)
        report["signatures"]["FasterWhisperPipeline.transcribe"] = safe_signature(
            asr.FasterWhisperPipeline.transcribe
        )
        report["signatures"]["WhisperModel.generate_segment_batched"] = safe_signature(
            asr.WhisperModel.generate_segment_batched
        )
        report["signatures"]["find_numeral_symbol_tokens"] = safe_signature(
            asr.find_numeral_symbol_tokens
        )

    audio, err = import_optional("whisperx.audio")
    if err:
        warnings.append(f"Could not import whisperx.audio: {err}")
    else:
        report["signatures"]["whisperx.audio.load_audio"] = safe_signature(audio.load_audio)
        report["signatures"]["whisperx.audio.log_mel_spectrogram"] = safe_signature(
            audio.log_mel_spectrogram
        )
        for name in [
            "SAMPLE_RATE",
            "N_FFT",
            "HOP_LENGTH",
            "CHUNK_LENGTH",
            "N_SAMPLES",
            "N_FRAMES",
            "FRAMES_PER_SECOND",
            "TOKENS_PER_SECOND",
        ]:
            report["constants"][name] = getattr(audio, name, None)

    schema, err = import_optional("whisperx.schema")
    if err:
        warnings.append(f"Could not import whisperx.schema: {err}")
    else:
        for name in ["SingleSegment", "TranscriptionResult", "ProgressCallback"]:
            obj = getattr(schema, name, None)
            annotations = getattr(obj, "__annotations__", None)
            report["schema"][name] = {
                "present": obj is not None,
                "annotations": {k: str(v) for k, v in annotations.items()} if annotations else None,
            }
            if obj is None:
                warnings.append(f"Missing schema object: whisperx.schema.{name}")

    torch_mod, err = import_optional("torch")
    if err:
        warnings.append(f"Could not import torch: {err}")
    else:
        cuda_available = False
        cuda_count = 0
        try:
            cuda_available = bool(torch_mod.cuda.is_available())
            cuda_count = int(torch_mod.cuda.device_count()) if cuda_available else 0
        except Exception as exc:  # pragma: no cover - diagnostic path
            warnings.append(f"Could not query torch CUDA availability: {type(exc).__name__}: {exc}")
        report["torch"] = {
            "version": getattr(torch_mod, "__version__", "unknown"),
            "cuda_available": cuda_available,
            "cuda_device_count": cuda_count,
        }

    report["warnings"] = warnings + [
        "This helper does not call load_model or transcribe.",
        "Full ASR execution may download model weights unless local_files_only=True is used with a populated cache.",
        "Path audio decoding requires the ffmpeg executable; use check_audio_loading.py for a tiny audio smoke check.",
    ]
    return report, warnings


def print_text(report: dict[str, Any]) -> None:
    print(f"WhisperX distribution version: {report['version']}")
    print("\nPublic lazy API:")
    for name, info in report["public_lazy_api"].items():
        status = "ok" if info["present"] and info["callable"] else "missing"
        print(f"  whisperx.{name}: {status}; signature={info['signature']}")

    print("\nImportant signatures:")
    if report["signatures"]:
        for name, signature in report["signatures"].items():
            print(f"  {name}: {signature}")
    else:
        print("  unavailable")

    print("\nAudio constants:")
    if report["constants"]:
        for name, value in report["constants"].items():
            print(f"  {name}: {value}")
    else:
        print("  unavailable")

    print("\nSchemas:")
    if report["schema"]:
        for name, info in report["schema"].items():
            print(f"  {name}: present={info['present']}; annotations={info['annotations']}")
    else:
        print("  unavailable")

    print("\nTorch:")
    if report["torch"]:
        for name, value in report["torch"].items():
            print(f"  {name}: {value}")
    else:
        print("  unavailable")

    print("\nWarnings / execution boundary:")
    for warning in report["warnings"]:
        print(f"  - {warning}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect WhisperX ASR Python API signatures without model downloads or transcription."
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report instead of text")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if expected imports or public APIs are missing",
    )
    args = parser.parse_args(argv)

    report, strict_warnings = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    if args.strict and strict_warnings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
