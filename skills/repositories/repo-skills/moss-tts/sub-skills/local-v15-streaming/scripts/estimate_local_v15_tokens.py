#!/usr/bin/env python3
"""Estimate MOSS-TTS Local Transformer v1.5 frame and duration-token budgets.

This utility intentionally imports only the Python standard library. It does not
load torch, transformers, the TTS model, or the codec.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from typing import Any

FRAME_RATE_HZ = 12.5
RVQ_LAYERS = 12
DEFAULT_HARD_CAP_MARGIN = 1.25

# Ratios distilled from the v1.5 streaming helper. Values estimate the prompt
# duration-control field from text length; they are not tokenizer counts.
TOKENS_PER_CHAR = {
    "zh": 3.098411951313033,
    "en": 0.8673376262755219,
    "fr": 0.9,
    "ja": 2.2,
    "ko": 1.8,
}

LANGUAGE_ALIASES = {
    "zh": "zh",
    "zh-cn": "zh",
    "zh-tw": "zh",
    "cmn": "zh",
    "yue": "zh",
    "chinese": "zh",
    "cantonese": "zh",
    "mandarin": "zh",
    "en": "en",
    "en-us": "en",
    "en-gb": "en",
    "english": "en",
    "fr": "fr",
    "french": "fr",
    "ja": "ja",
    "japanese": "ja",
    "ko": "ko",
    "korean": "ko",
}

CJK_RE = re.compile(r"[\u3400-\u9fff]")
LATIN_RE = re.compile(r"[A-Za-z]")


def count_cjk(text: str) -> int:
    return len(CJK_RE.findall(text or ""))


def count_latin(text: str) -> int:
    return len(LATIN_RE.findall(text or ""))


def normalize_language(language: str, text: str) -> str:
    """Return a compact language key used by the duration heuristic."""

    raw = (language or "").strip().lower().replace("_", "-")
    if raw:
        # Accept common tags such as zh-Hans, en_US, fr-FR.
        if raw in LANGUAGE_ALIASES:
            return LANGUAGE_ALIASES[raw]
        primary = raw.split("-", 1)[0]
        if primary in LANGUAGE_ALIASES:
            return LANGUAGE_ALIASES[primary]
        if raw.startswith("zh"):
            return "zh"
        if raw.startswith("en"):
            return "en"
        if raw.startswith("fr"):
            return "fr"
        if raw.startswith("ja"):
            return "ja"
        if raw.startswith("ko"):
            return "ko"

    cjk = count_cjk(text)
    latin = count_latin(text)
    if cjk > 0 and cjk >= latin:
        return "zh"
    return "en"


def estimate_tokens_from_text(text: str, language: str) -> int:
    """Estimate duration-control tokens/frames from text and language."""

    if not text:
        return 0
    key = normalize_language(language, text)
    ratio = TOKENS_PER_CHAR.get(key, TOKENS_PER_CHAR["en"])
    return max(1, int(round(len(text) * float(ratio))))


def frames_from_seconds(seconds: float | None) -> int | None:
    if seconds is None:
        return None
    if seconds <= 0:
        return 0
    return int(math.ceil(float(seconds) * FRAME_RATE_HZ))


def seconds_from_frames(frames: int) -> float:
    return float(frames) / FRAME_RATE_HZ


def build_estimate(text: str, language: str, seconds: float | None) -> dict[str, Any]:
    normalized_language = normalize_language(language, text)
    ratio = TOKENS_PER_CHAR.get(normalized_language, TOKENS_PER_CHAR["en"])
    text_tokens = estimate_tokens_from_text(text, language)
    duration_frames = frames_from_seconds(seconds)

    # Duration control should use the explicit desired duration when supplied;
    # otherwise use the text heuristic.
    suggested_tokens_control = duration_frames if duration_frames is not None else text_tokens

    # max_new_frames is a hard cap. Keep it above the intended duration/control
    # value so generation is less likely to be cut off before the model emits EOS.
    cap_basis = suggested_tokens_control or text_tokens or duration_frames or 0
    suggested_max_new_frames = int(math.ceil(cap_basis * DEFAULT_HARD_CAP_MARGIN)) if cap_basis > 0 else 0

    result: dict[str, Any] = {
        "model_family": "MOSS-TTS-Local-Transformer-v1.5",
        "frame_rate_hz": FRAME_RATE_HZ,
        "rvq_layers": RVQ_LAYERS,
        "language": {
            "input": language,
            "normalized": normalized_language,
            "tokens_per_character": ratio,
        },
        "text": {
            "characters": len(text or ""),
            "cjk_characters": count_cjk(text),
            "latin_characters": count_latin(text),
            "estimated_duration_tokens": text_tokens,
            "estimated_seconds_from_text_tokens": seconds_from_frames(text_tokens) if text_tokens else 0.0,
        },
        "duration": {
            "input_seconds": seconds,
            "frames_from_seconds": duration_frames,
            "rvq_code_values_for_seconds": None if duration_frames is None else int(duration_frames * RVQ_LAYERS),
        },
        "recommendations": {
            "tokens_control_value": int(suggested_tokens_control or 0),
            "max_new_frames": int(suggested_max_new_frames),
            "ui_max_new_tokens": int(suggested_max_new_frames),
            "hard_cap_margin": DEFAULT_HARD_CAP_MARGIN,
        },
        "notes": [
            "tokens_control_value is the duration-control prompt hint, not a hard cap.",
            "max_new_frames is the hard streaming cap; the browser labels the same value max_new_tokens.",
            "At 12.5 frames/sec, 125 frames is about 10 seconds.",
            "Each frame contains 12 RVQ layer values; rvq_code_values_for_seconds equals frames * 12.",
        ],
    }
    return result


def print_plain(estimate: dict[str, Any]) -> None:
    language = estimate["language"]
    text = estimate["text"]
    duration = estimate["duration"]
    rec = estimate["recommendations"]

    print("MOSS-TTS Local v1.5 budget estimate")
    print(f"  language: {language['normalized']} (input={language['input']!r}, ratio={language['tokens_per_character']})")
    print(f"  text characters: {text['characters']} (CJK={text['cjk_characters']}, Latin={text['latin_characters']})")
    print(f"  estimated duration tokens from text: {text['estimated_duration_tokens']}")
    print(f"  estimated seconds from text tokens: {text['estimated_seconds_from_text_tokens']:.2f}")
    if duration["input_seconds"] is not None:
        print(f"  requested seconds: {duration['input_seconds']}")
        print(f"  frames from seconds: {duration['frames_from_seconds']}")
        print(f"  RVQ code values for seconds: {duration['rvq_code_values_for_seconds']}")
    print("Recommendations:")
    print(f"  tokens_control_value: {rec['tokens_control_value']}")
    print(f"  max_new_frames: {rec['max_new_frames']}")
    print(f"  ui_max_new_tokens: {rec['ui_max_new_tokens']}")
    print(f"  hard cap margin: {rec['hard_cap_margin']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate MOSS-TTS Local v1.5 duration tokens and frame caps without loading the model."
    )
    parser.add_argument("--text", default="", help="Text to synthesize or continue.")
    parser.add_argument("--language", default="", help="Optional language tag such as Chinese, English, zh, en, fr, ja, ko.")
    parser.add_argument("--seconds", type=float, default=None, help="Optional desired output duration in seconds.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()
    if args.seconds is not None and args.seconds < 0:
        parser.error("--seconds must be non-negative")
    if not args.text and args.seconds is None:
        parser.error("provide --text, --seconds, or both")
    return args


def main() -> None:
    args = parse_args()
    estimate = build_estimate(args.text, args.language, args.seconds)
    if args.json:
        print(json.dumps(estimate, ensure_ascii=False, indent=2))
    else:
        print_plain(estimate)


if __name__ == "__main__":
    main()
