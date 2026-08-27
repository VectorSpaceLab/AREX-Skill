#!/usr/bin/env python3
"""PocketSphinx keyword and grammar workflow template.

Imports PocketSphinx only through ``Recognizer.recognize_sphinx`` after the user
explicitly runs recognition. The script depends on user-provided audio and
optional grammar paths, not on repository example files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class TemplateArgumentError(RuntimeError):
    """User-fixable command-line validation error."""


def keyword_entry(text: str) -> tuple[str, float]:
    """Parse a PocketSphinx keyword entry in ``word:sensitivity`` form."""
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
            f"sensitivity must be in [0, 1], got {sensitivity}"
        )
    return keyword, sensitivity


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run SpeechRecognition's PocketSphinx recognizer with optional "
            "keyword or grammar constraints."
        )
    )
    parser.add_argument(
        "audio_path",
        help="Path to a user-supplied WAV, AIFF/AIFF-C, or native FLAC audio file.",
    )
    parser.add_argument(
        "--language",
        default="en-US",
        help="PocketSphinx language code or installed language data name. Default: en-US.",
    )
    parser.add_argument(
        "--keyword",
        action="append",
        type=keyword_entry,
        default=[],
        metavar="WORD:SENSITIVITY",
        help=(
            "Keyword entry for constrained Sphinx recognition, for example "
            "--keyword yes:0.9. Repeat for multiple keywords."
        ),
    )
    parser.add_argument(
        "--grammar",
        help=(
            "Path to a PocketSphinx JSGF or FSG grammar. If --keyword is also "
            "provided, SpeechRecognition ignores the grammar."
        ),
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Print a compact decoder summary instead of only the best transcript.",
    )
    return parser.parse_args(argv)


def validate_paths(args: argparse.Namespace) -> tuple[Path, str | None]:
    audio_path = Path(args.audio_path).expanduser()
    if not audio_path.is_file():
        raise TemplateArgumentError(f"audio file does not exist: {audio_path}")

    grammar = None
    if args.grammar:
        grammar_path = Path(args.grammar).expanduser()
        if not grammar_path.is_file():
            raise TemplateArgumentError(f"grammar file does not exist: {grammar_path}")
        grammar = str(grammar_path)
        if args.keyword:
            print(
                "warning: SpeechRecognition ignores --grammar when --keyword entries are provided",
                file=sys.stderr,
            )

    return audio_path, grammar


def summarize_decoder(decoder: Any) -> dict[str, Any]:
    """Create a stable, JSON-serializable summary of a PocketSphinx decoder."""
    summary: dict[str, Any] = {"decoder_type": type(decoder).__name__}

    try:
        hypothesis = decoder.hyp()
    except Exception as exc:  # noqa: BLE001 - PocketSphinx versions vary.
        summary["hypothesis_error"] = f"{type(exc).__name__}: {exc}"
    else:
        if hypothesis is None:
            summary["hypothesis"] = None
        else:
            summary["hypothesis"] = getattr(hypothesis, "hypstr", str(hypothesis))
            for attr in ("best_score", "prob"):
                if hasattr(hypothesis, attr):
                    summary[attr] = getattr(hypothesis, attr)

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
    except Exception:  # noqa: BLE001 - decoder.seg() is optional for summaries.
        pass

    return summary


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        audio_path, grammar = validate_paths(args)
    except TemplateArgumentError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 64

    try:
        import speech_recognition as sr
        from speech_recognition.exceptions import RequestError, SetupError, UnknownValueError
    except ImportError as exc:
        print(
            "ImportError: could not import SpeechRecognition from the active Python "
            f"environment: {exc}. Install SpeechRecognition before running recognition.",
            file=sys.stderr,
        )
        return 4

    try:
        audio = sr.AudioData.from_file(str(audio_path))
        recognizer = sr.Recognizer()
        result = recognizer.recognize_sphinx(
            audio,
            language=args.language,
            keyword_entries=args.keyword or None,
            grammar=grammar,
            show_all=args.show_all,
        )
    except UnknownValueError as exc:
        print(
            "UnknownValueError: PocketSphinx ran but produced no hypothesis "
            f"({exc}). Check audio clarity, --language, keywords, or grammar coverage.",
            file=sys.stderr,
        )
        return 3
    except RequestError as exc:
        print(
            "RequestError: PocketSphinx setup/request failed: "
            f"{exc}. Install SpeechRecognition[pocketsphinx] and matching language data.",
            file=sys.stderr,
        )
        return 2
    except SetupError as exc:
        print(
            "SetupError: PocketSphinx setup failed: "
            f"{exc}. Install the pocketsphinx extra and verify local model data.",
            file=sys.stderr,
        )
        return 2
    except ImportError as exc:
        print(
            "ImportError: missing PocketSphinx optional dependency: "
            f"{exc}. Install SpeechRecognition[pocketsphinx] before retrying.",
            file=sys.stderr,
        )
        return 4
    except Exception as exc:  # noqa: BLE001 - keep CLI failures actionable.
        print(
            f"{type(exc).__name__}: {exc}. Verify the audio path, grammar file, "
            "keyword sensitivities, and PocketSphinx installation.",
            file=sys.stderr,
        )
        return 1

    if args.show_all:
        print(json.dumps(summarize_decoder(result), indent=2, sort_keys=True, default=str))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
