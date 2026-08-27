#!/usr/bin/env python3
"""Safe synthetic WhisperX alignment contract checker.

This helper verifies the installed WhisperX aligner with a tiny CPU-only mock
alignment model. It does not load ASR models, download wav2vec2 weights, use
credentials, read audio files, or write outputs.

Example:
    python scripts/check_alignment_contract.py
    python scripts/check_alignment_contract.py --interpolate-method ignore \
        --text "halt mit 4,9 nicht ins parlament" --required-word "4,9" --language de
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a safe CPU-only synthetic WhisperX alignment contract check. "
            "The default verifies that the numeric comma word '4,9' receives "
            "word-level timestamps."
        )
    )
    parser.add_argument(
        "--interpolate-method",
        default="nearest",
        choices=("nearest", "linear", "ignore"),
        help="Timestamp interpolation method passed to whisperx.align.",
    )
    parser.add_argument(
        "--text",
        default="cost 4,9 dollars",
        help="Synthetic transcript text to align.",
    )
    parser.add_argument(
        "--required-word",
        default="4,9",
        help="Word that must appear in word_segments with start/end/score.",
    )
    parser.add_argument(
        "--language",
        default="en",
        help="Alignment metadata language code. Use de for the German comma case.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Synthetic audio duration in seconds.",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=220,
        help="Number of synthetic CTC emission frames.",
    )
    parser.add_argument(
        "--return-char-alignments",
        action="store_true",
        help="Also request and validate non-empty character alignments.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the aligned result as JSON after validation.",
    )
    return parser.parse_args()


@dataclass
class SimpleSentenceSplitter:
    """Minimal sentence splitter used to avoid NLTK data/network access."""

    def span_tokenize(self, text: str) -> Iterable[tuple[int, int]]:
        if not text:
            return []
        return [(0, len(text))]


class MockTorchaudioModel:
    """Torchaudio-style model returning a fixed emission matrix."""

    def __init__(self, emission):
        self.emission = emission

    def __call__(self, waveform, lengths=None):  # noqa: D401 - torchaudio-compatible signature
        return self.emission.unsqueeze(0), None


def _clean_chars_for_alignment(text: str, language: str, dictionary: dict[str, int]) -> list[str]:
    languages_without_spaces = {"ja", "zh"}
    clean_chars: list[str] = []
    leading = len(text) - len(text.lstrip())
    trailing = len(text) - len(text.rstrip())
    for index, char in enumerate(text):
        char_ = char.lower()
        if language not in languages_without_spaces:
            char_ = char_.replace(" ", "|")

        if index < leading:
            continue
        if index > len(text) - trailing - 1:
            continue
        if char_ in dictionary:
            clean_chars.append(char_)
        elif char_ not in (" ", "|"):
            # Unknown non-whitespace characters are intentionally preserved;
            # whisperx.align maps them to a wildcard CTC column.
            clean_chars.append(char_)
    return clean_chars


def _make_dictionary(text: str, language: str) -> dict[str, int]:
    """Create a tiny dictionary that excludes digits/punctuation on purpose."""
    languages_without_spaces = {"ja", "zh"}
    chars: set[str] = set()
    for char in text.lower():
        if char == " " and language not in languages_without_spaces:
            chars.add("|")
        elif char.isalpha():
            chars.add(char)
    # Guarantee at least one known non-blank token for wildcard emissions.
    chars.update({"a", "|"})
    dictionary = {"<pad>": 0}
    for idx, char in enumerate(sorted(chars), start=1):
        dictionary[char] = idx
    return dictionary


def _make_emission(num_frames: int, dictionary: dict[str, int], clean_chars: list[str]):
    import torch

    if num_frames < max(20, len(clean_chars) * 3):
        raise ValueError("--frames is too small for the requested transcript")

    blank_id = dictionary["<pad>"]
    vocab_size = max(dictionary.values()) + 1
    emission = torch.full((num_frames, vocab_size), -8.0, dtype=torch.float32)
    emission[:, blank_id] = 5.0

    fallback_token = dictionary.get("a")
    if fallback_token is None:
        fallback_token = next(v for k, v in dictionary.items() if k != "<pad>")

    if not clean_chars:
        return emission

    step = num_frames / (len(clean_chars) + 1)
    span = max(2, int(step // 2))
    for seq_index, char in enumerate(clean_chars):
        center = int(round((seq_index + 1) * step))
        start = max(0, center - span // 2)
        end = min(num_frames, center + span // 2 + 1)
        token_id = dictionary.get(char, fallback_token)
        emission[start:end, blank_id] = -8.0
        emission[start:end, token_id] = 12.0
    return emission


def _patch_sentence_splitter(alignment_module) -> None:
    splitter = SimpleSentenceSplitter()
    alignment_module.nltk_load = lambda *_args, **_kwargs: splitter


def _validate_result(result: dict, required_word: str, duration: float, require_chars: bool) -> None:
    if "segments" not in result or "word_segments" not in result:
        raise AssertionError(f"result missing aligned keys: {sorted(result)}")
    if not result["segments"]:
        raise AssertionError("expected at least one aligned segment")
    if not result["word_segments"]:
        raise AssertionError("expected non-empty word_segments")

    words = {word["word"]: word for word in result["word_segments"]}
    if required_word not in words:
        raise AssertionError(
            f"required word {required_word!r} not found; got {list(words)}"
        )
    required = words[required_word]
    missing = [key for key in ("start", "end", "score") if key not in required]
    if missing:
        raise AssertionError(f"{required_word!r} missing fields {missing}: {required}")

    start = required["start"]
    end = required["end"]
    score = required["score"]
    if not (isinstance(start, (int, float)) and isinstance(end, (int, float))):
        raise AssertionError(f"timestamps are not numeric: {required}")
    if not (0.0 <= float(start) <= float(end) <= duration + 1e-6):
        raise AssertionError(f"timestamps out of range 0..{duration}: {required}")
    if not isinstance(score, (int, float)) or math.isnan(float(score)):
        raise AssertionError(f"score is not numeric: {required}")

    starts = [float(w["start"]) for w in result["word_segments"] if "start" in w]
    for previous, current in zip(starts, starts[1:]):
        if current < previous:
            raise AssertionError(f"word start timestamps are not monotonic: {starts}")

    for segment in result["segments"]:
        for key in ("start", "end"):
            value = segment.get(key)
            if not isinstance(value, (int, float)) or math.isnan(float(value)):
                raise AssertionError(f"segment {key} is invalid: {segment}")

    if require_chars:
        chars = []
        for segment in result["segments"]:
            chars.extend(segment.get("chars") or [])
        if not chars:
            raise AssertionError("--return-char-alignments requested but no chars were returned")
        timed_chars = [c for c in chars if "start" in c and "end" in c]
        if not timed_chars:
            raise AssertionError("char alignments contain no timed characters")


def main() -> int:
    args = parse_args()
    if args.duration <= 0:
        raise SystemExit("--duration must be positive")
    if args.frames <= 0:
        raise SystemExit("--frames must be positive")

    try:
        import torch
        import whisperx.alignment as alignment_module
    except Exception as exc:  # pragma: no cover - user-facing diagnostic
        print(
            "ERROR: could not import torch and whisperx alignment modules. "
            "Install whisperx with its runtime dependencies before running this checker.",
            file=sys.stderr,
        )
        print(f"Import failure: {exc}", file=sys.stderr)
        return 2

    _patch_sentence_splitter(alignment_module)

    dictionary = _make_dictionary(args.text, args.language)
    clean_chars = _clean_chars_for_alignment(args.text, args.language, dictionary)
    emission = _make_emission(args.frames, dictionary, clean_chars)
    model = MockTorchaudioModel(emission)
    metadata = {"language": args.language, "dictionary": dictionary, "type": "torchaudio"}

    sample_rate = 16000
    audio = torch.zeros(int(args.duration * sample_rate), dtype=torch.float32)
    transcript = [{"text": args.text, "start": 0.0, "end": args.duration}]

    result = alignment_module.align(
        transcript=transcript,
        model=model,
        align_model_metadata=metadata,
        audio=audio,
        device="cpu",
        interpolate_method=args.interpolate_method,
        return_char_alignments=args.return_char_alignments,
    )

    _validate_result(result, args.required_word, args.duration, args.return_char_alignments)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    words = {word["word"]: word for word in result["word_segments"]}
    required = words[args.required_word]
    print(
        "OK: synthetic alignment produced timestamps for "
        f"{args.required_word!r} using interpolate_method={args.interpolate_method!r}: "
        f"start={required['start']}, end={required['end']}, score={required['score']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
