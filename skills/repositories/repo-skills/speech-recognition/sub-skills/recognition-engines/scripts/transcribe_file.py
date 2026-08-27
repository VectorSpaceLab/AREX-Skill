#!/usr/bin/env python3
"""Inspect or transcribe an audio file with SpeechRecognition.

The default ``inspect`` engine loads only ``AudioData.from_file`` and prints
local metadata. Network services and optional local models are used only after
an explicit non-default ``--engine`` selection.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from pprint import pprint
from typing import Any


ENGINE_CHOICES = (
    "inspect",
    "google",
    "sphinx",
    "vosk",
    "whisper",
    "faster-whisper",
    "openai",
    "groq",
    "cohere",
)


class RecognitionScriptError(RuntimeError):
    """User-fixable command, credential, or argument error."""


def keyword_entry(text: str) -> tuple[str, float]:
    """Parse ``word:sensitivity`` and enforce SpeechRecognition's [0, 1] range."""
    if ":" not in text:
        raise argparse.ArgumentTypeError(
            f"expected KEYWORD:SENSITIVITY, got {text!r}"
        )
    keyword, sensitivity_text = text.rsplit(":", 1)
    keyword = keyword.strip()
    if not keyword:
        raise argparse.ArgumentTypeError("keyword must not be empty")
    try:
        sensitivity = float(sensitivity_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"sensitivity must be a number, got {sensitivity_text!r}"
        ) from exc
    if not 0.0 <= sensitivity <= 1.0:
        raise argparse.ArgumentTypeError(
            f"sensitivity must be between 0 and 1, got {sensitivity}"
        )
    return keyword, sensitivity


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect an audio file locally, or explicitly transcribe it with "
            "one SpeechRecognition recognizer engine."
        )
    )
    parser.add_argument(
        "audio_path",
        help="Path to a user-supplied WAV, AIFF/AIFF-C, or native FLAC audio file.",
    )
    parser.add_argument(
        "--engine",
        choices=ENGINE_CHOICES,
        default="inspect",
        help="Engine to use. Default: inspect, which performs no network/model call.",
    )
    parser.add_argument(
        "--language",
        help=(
            "Engine language value, such as en-US for Google/Sphinx, en for "
            "OpenAI/Groq, or english/en for local Whisper variants."
        ),
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help=(
            "Request detailed output where supported: Google show_all, Sphinx "
            "decoder summary, Vosk verbose dict, or Whisper show_dict."
        ),
    )
    parser.add_argument(
        "--model",
        help="Engine model name for Whisper, Faster-Whisper, OpenAI, Groq, or Cohere.",
    )
    parser.add_argument(
        "--prompt",
        help="Prompt/initial prompt for engines that expose prompt conditioning.",
    )
    parser.add_argument(
        "--key-env",
        help=(
            "Name of an environment variable containing the selected provider key. "
            "The key value is read at runtime and is never printed."
        ),
    )
    parser.add_argument(
        "--credentials-json-path",
        help=(
            "Path to a credential JSON file for Google Cloud-style workflows. "
            "This helper's --engine google calls recognize_google, not "
            "recognize_google_cloud, so the file contents are not read."
        ),
    )
    parser.add_argument(
        "--grammar",
        help="PocketSphinx JSGF or FSG grammar path for --engine sphinx.",
    )
    parser.add_argument(
        "--keyword",
        action="append",
        type=keyword_entry,
        default=[],
        metavar="WORD:SENSITIVITY",
        help=(
            "PocketSphinx keyword entry, e.g. --keyword wake:0.8. "
            "Repeat for multiple keywords."
        ),
    )
    parser.add_argument(
        "--cohere-language",
        help="Cohere language code; overrides --language for --engine cohere.",
    )
    parser.add_argument(
        "--openai-base-url",
        help="Set OPENAI_BASE_URL before calling --engine openai.",
    )
    parser.add_argument(
        "--task",
        choices=("transcribe", "translate"),
        help="Local Whisper/Faster-Whisper task option.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        help="Temperature option for Whisper/OpenAI-compatible engines.",
    )
    parser.add_argument(
        "--beam-size",
        type=int,
        help="Faster-Whisper beam_size option.",
    )
    return parser.parse_args(argv)


def load_speech_recognition():
    """Import SpeechRecognition only after argparse has handled ``--help``."""
    import speech_recognition as sr
    from speech_recognition.exceptions import (  # type: ignore[attr-defined]
        RequestError,
        SetupError,
        UnknownValueError,
    )

    return sr, UnknownValueError, RequestError, SetupError


def read_key_from_env(env_name: str) -> str:
    value = os.environ.get(env_name)
    if not value:
        raise RecognitionScriptError(
            f"--key-env {env_name!r} is unset or empty; export the credential before running"
        )
    return value


def require_provider_environment(args: argparse.Namespace, default_env: str, provider: str) -> None:
    """Populate the SDK's expected env var from --key-env or require it already exists."""
    if args.key_env:
        os.environ[default_env] = read_key_from_env(args.key_env)
    elif not os.environ.get(default_env):
        raise RecognitionScriptError(
            f"{provider} requires credentials in {default_env}; export it or pass --key-env ENV_NAME"
        )


def validate_paths(args: argparse.Namespace) -> tuple[Path, str | None]:
    audio_path = Path(args.audio_path).expanduser()
    if not audio_path.is_file():
        raise RecognitionScriptError(f"audio file does not exist: {audio_path}")

    grammar = None
    if args.grammar:
        grammar_path = Path(args.grammar).expanduser()
        if not grammar_path.is_file():
            raise RecognitionScriptError(f"grammar file does not exist: {grammar_path}")
        grammar = str(grammar_path)

    if args.credentials_json_path:
        credentials_path = Path(args.credentials_json_path).expanduser()
        if not credentials_path.is_file():
            raise RecognitionScriptError(
                f"credentials JSON path does not exist: {credentials_path}"
            )
        print(
            "warning: --credentials-json-path was validated but is not read by "
            "the listed engines; --engine google uses Recognizer.recognize_google. "
            "Use --key-env for that API key.",
            file=sys.stderr,
        )

    if args.keyword and args.engine != "sphinx":
        print("warning: --keyword is only used by --engine sphinx", file=sys.stderr)
    if args.grammar and args.engine != "sphinx":
        print("warning: --grammar is only used by --engine sphinx", file=sys.stderr)
    if args.openai_base_url and args.engine != "openai":
        print("warning: --openai-base-url is only used by --engine openai", file=sys.stderr)
    return audio_path, grammar


def audio_metadata(audio: Any, path: Path) -> dict[str, Any]:
    raw_bytes = len(audio.frame_data)
    sample_width = int(audio.sample_width)
    sample_rate = int(audio.sample_rate)
    frame_count = raw_bytes // sample_width if sample_width else None
    duration = frame_count / sample_rate if frame_count is not None and sample_rate else None
    return {
        "engine": "inspect",
        "path": str(path),
        "network": False,
        "model_loaded": False,
        "sample_rate_hz": sample_rate,
        "sample_width_bytes": sample_width,
        "channels": 1,
        "frame_data_bytes": raw_bytes,
        "sample_count": frame_count,
        "duration_seconds": duration,
        "estimated_wav_bytes": raw_bytes + 44,
    }


def json_default(value: Any) -> str:
    return str(value)


def print_result(result: Any) -> None:
    if isinstance(result, str):
        print(result)
        return
    try:
        print(json.dumps(result, indent=2, sort_keys=True, default=json_default))
    except TypeError:
        pprint(result)


def summarize_decoder(decoder: Any) -> dict[str, Any]:
    """Return a JSON-safe summary for PocketSphinx decoder objects."""
    summary: dict[str, Any] = {"decoder_type": type(decoder).__name__}
    try:
        hypothesis = decoder.hyp()
    except Exception as exc:  # noqa: BLE001 - decoder APIs vary by version.
        summary["hypothesis_error"] = f"{type(exc).__name__}: {exc}"
    else:
        if hypothesis is not None:
            summary["hypothesis"] = getattr(hypothesis, "hypstr", str(hypothesis))
            for attr in ("best_score", "prob"):
                if hasattr(hypothesis, attr):
                    summary[attr] = getattr(hypothesis, attr)
        else:
            summary["hypothesis"] = None
    try:
        summary["segments"] = [
            {
                "word": getattr(segment, "word", str(segment)),
                "start_frame": getattr(segment, "start_frame", None),
                "end_frame": getattr(segment, "end_frame", None),
                "prob": getattr(segment, "prob", None),
            }
            for segment in decoder.seg()
        ]
    except Exception:  # noqa: BLE001 - not all decoder objects expose seg().
        pass
    return summary


def recognize_with_engine(sr: Any, audio: Any, args: argparse.Namespace, grammar: str | None) -> Any:
    recognizer = sr.Recognizer()

    if args.engine == "google":
        key = read_key_from_env(args.key_env) if args.key_env else None
        return recognizer.recognize_google(
            audio,
            key=key,
            language=args.language or "en-US",
            show_all=args.show_all,
        )

    if args.engine == "sphinx":
        result = recognizer.recognize_sphinx(
            audio,
            language=args.language or "en-US",
            keyword_entries=args.keyword or None,
            grammar=grammar,
            show_all=args.show_all,
        )
        return summarize_decoder(result) if args.show_all else result

    if args.engine == "vosk":
        return recognizer.recognize_vosk(audio, verbose=args.show_all)

    if args.engine == "whisper":
        kwargs: dict[str, Any] = {}
        if args.language:
            kwargs["language"] = args.language
        if args.task:
            kwargs["task"] = args.task
        if args.temperature is not None:
            kwargs["temperature"] = args.temperature
        if args.prompt:
            kwargs["initial_prompt"] = args.prompt
        return recognizer.recognize_whisper(
            audio,
            model=args.model or "base",
            show_dict=args.show_all,
            **kwargs,
        )

    if args.engine == "faster-whisper":
        kwargs = {}
        if args.language:
            kwargs["language"] = args.language
        if args.task:
            kwargs["task"] = args.task
        if args.beam_size is not None:
            kwargs["beam_size"] = args.beam_size
        if args.prompt:
            kwargs["initial_prompt"] = args.prompt
        return recognizer.recognize_faster_whisper(
            audio,
            model=args.model or "base",
            show_dict=args.show_all,
            **kwargs,
        )

    if args.engine == "openai":
        require_provider_environment(args, "OPENAI_API_KEY", "OpenAI")
        if args.openai_base_url:
            os.environ["OPENAI_BASE_URL"] = args.openai_base_url
        kwargs = {}
        if args.language:
            kwargs["language"] = args.language
        if args.prompt:
            kwargs["prompt"] = args.prompt
        if args.temperature is not None:
            kwargs["temperature"] = args.temperature
        if args.show_all:
            print("warning: recognize_openai returns text only in this package", file=sys.stderr)
        return recognizer.recognize_openai(audio, model=args.model or "whisper-1", **kwargs)

    if args.engine == "groq":
        require_provider_environment(args, "GROQ_API_KEY", "Groq")
        kwargs = {}
        if args.language:
            kwargs["language"] = args.language
        if args.prompt:
            kwargs["prompt"] = args.prompt
        if args.temperature is not None:
            kwargs["temperature"] = args.temperature
        if args.show_all:
            print("warning: recognize_groq returns text only in this package", file=sys.stderr)
        return recognizer.recognize_groq(
            audio,
            model=args.model or "whisper-large-v3-turbo",
            **kwargs,
        )

    if args.engine == "cohere":
        require_provider_environment(args, "CO_API_KEY", "Cohere")
        language = args.cohere_language or args.language
        if not language:
            raise RecognitionScriptError(
                "Cohere requires --cohere-language or --language, e.g. --cohere-language en"
            )
        if args.prompt:
            print("warning: recognize_cohere_api does not expose prompt", file=sys.stderr)
        if args.show_all:
            print("warning: recognize_cohere_api returns text only in this package", file=sys.stderr)
        return recognizer.recognize_cohere_api(
            audio,
            language=language,
            model=args.model or "cohere-transcribe-03-2026",
        )

    raise RecognitionScriptError(f"unsupported engine: {args.engine}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        audio_path, grammar = validate_paths(args)
    except RecognitionScriptError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 64

    try:
        sr, UnknownValueError, RequestError, SetupError = load_speech_recognition()
    except ImportError as exc:
        print(
            "ImportError: could not import SpeechRecognition from the active Python "
            f"environment: {exc}. Install the package and required base runtime "
            "dependencies before recognition.",
            file=sys.stderr,
        )
        return 4

    try:
        audio = sr.AudioData.from_file(str(audio_path))
        if args.engine == "inspect":
            print_result(audio_metadata(audio, audio_path))
            return 0

        result = recognize_with_engine(sr, audio, args, grammar)
    except UnknownValueError as exc:
        print(
            "UnknownValueError: the selected engine ran but could not understand "
            f"the audio ({exc}). Try clearer audio, a matching --language, or "
            "--show-all where supported.",
            file=sys.stderr,
        )
        return 3
    except RequestError as exc:
        print(
            "RequestError: recognition request/setup failed: "
            f"{exc}. Check network access, credentials, optional extras, and local models.",
            file=sys.stderr,
        )
        return 2
    except SetupError as exc:
        print(
            "SetupError: recognizer setup failed: "
            f"{exc}. Install the selected engine extra and prepare required local models.",
            file=sys.stderr,
        )
        return 2
    except ImportError as exc:
        print(
            "ImportError: missing optional dependency for the selected engine: "
            f"{exc}. Install the matching SpeechRecognition extra before retrying.",
            file=sys.stderr,
        )
        return 4
    except Exception as exc:  # noqa: BLE001 - command-line helper must fail actionably.
        print(
            f"{type(exc).__name__}: {exc}. Verify the audio file, arguments, "
            "credentials, installed optional extras, and selected engine setup.",
            file=sys.stderr,
        )
        return 1

    print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
