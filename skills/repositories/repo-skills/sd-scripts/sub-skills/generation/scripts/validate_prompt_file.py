#!/usr/bin/env python3
"""Validate sd-scripts generation prompt-file conventions without loading models."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

GEN_IMG_OPTIONS = {
    "n": "text",
    "w": "int",
    "h": "int",
    "s": "int",
    "d": "seeds",
    "l": "float",
    "t": "float",
    "nl": "float",
    "am": "floats",
    "ow": "int",
    "oh": "int",
    "nw": "int",
    "nh": "int",
    "ct": "int",
    "cl": "int",
    "c": "text",
    "f": "text",
    "glt": "float",
    "glr": "float",
    "gls": "float",
    "gle": "int",
    "dsd1": "int",
    "dst1": "int",
    "dsd2": "int",
    "dst2": "int",
    "dsr": "float",
}

ANIMA_LLLITE_EXTRA = {
    "cn": "path",
    "mk": "path",
}

TEXT_OPTIONS = {"n", "c", "f"}
OPTION_RE = re.compile(r"(?<!\S)--([A-Za-z][A-Za-z0-9_]*)\b")
INT_RE = re.compile(r"^[+-]?\d+$")
FLOAT_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
SEEDS_RE = re.compile(r"^[+-]?\d+(?:,[+-]?\d+)*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt_file", type=Path, help="UTF-8 prompt file to validate")
    parser.add_argument(
        "--family",
        choices=("gen-img", "anima-lllite", "minimal"),
        default="gen-img",
        help="Prompt option dialect to validate",
    )
    parser.add_argument(
        "--images-per-prompt",
        type=int,
        default=None,
        help="Warn if a --d seed list length differs from this value",
    )
    parser.add_argument(
        "--expected-networks",
        type=int,
        default=None,
        help="Warn if --am multiplier count differs from the loaded network count",
    )
    parser.add_argument(
        "--allow-unknown-options",
        action="store_true",
        help="Do not fail on unknown per-line --options",
    )
    return parser.parse_args()


def option_table(family: str) -> dict[str, str]:
    options = dict(GEN_IMG_OPTIONS)
    if family == "anima-lllite":
        options.update(ANIMA_LLLITE_EXTRA)
    elif family == "minimal":
        options = {
            "w": "int",
            "h": "int",
            "s": "int",
            "d": "seeds",
            "n": "text",
            "g": "float",
            "m": "floats",
            "c": "float",
        }
    return options


def next_non_text_value(line: str, start: int, matches: list[re.Match[str]]) -> tuple[str, int]:
    end = len(line)
    for match in matches:
        if match.start() > start:
            end = match.start()
            break
    return line[start:end].strip(), end


def validate_scalar(kind: str, value: str) -> str | None:
    if kind == "int" and not INT_RE.match(value):
        return f"expected integer, got {value!r}"
    if kind == "float" and not FLOAT_RE.match(value):
        return f"expected number, got {value!r}"
    if kind == "seeds" and not SEEDS_RE.match(value):
        return f"expected comma-separated integer seeds, got {value!r}"
    if kind == "floats":
        parts = [part.strip() for part in value.split(",")]
        if not parts or any(not part for part in parts):
            return f"expected comma-separated numbers, got {value!r}"
        for part in parts:
            if not FLOAT_RE.match(part):
                return f"expected comma-separated numbers, got {value!r}"
    if kind == "path" and not value:
        return "expected a path value"
    return None


def validate_line(
    line: str,
    line_number: int,
    options: dict[str, str],
    allow_unknown: bool,
    images_per_prompt: int | None,
    expected_networks: int | None,
) -> list[str]:
    messages: list[str] = []
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return messages

    matches = list(OPTION_RE.finditer(line))
    if stripped.startswith("--"):
        messages.append("line starts with an option; add positive prompt text before prompt options")

    for index, match in enumerate(matches):
        name = match.group(1)
        kind = options.get(name)
        if kind is None:
            if not allow_unknown:
                messages.append(f"unknown option --{name}")
            continue

        value_start = match.end()
        value, _ = next_non_text_value(line, value_start, matches[index + 1 :])
        if not value:
            messages.append(f"--{name} is missing a value")
            continue

        if name not in TEXT_OPTIONS:
            first_token = value.split()[0]
            problem = validate_scalar(kind, first_token)
            if problem:
                messages.append(f"--{name}: {problem}")
            if kind in {"int", "float", "seeds", "floats", "path"} and len(value.split()) > 1:
                messages.append(f"--{name} value {first_token!r} is followed by extra text {value[len(first_token):].strip()!r}")

        if name == "d" and images_per_prompt and value:
            seeds = value.split()[0].split(",")
            if len(seeds) not in {1, images_per_prompt}:
                messages.append(
                    f"--d provides {len(seeds)} seeds but --images-per-prompt is {images_per_prompt}"
                )

        if name in {"am", "m"} and expected_networks and value:
            multipliers = value.split()[0].split(",")
            if len(multipliers) not in {1, expected_networks}:
                messages.append(
                    f"--{name} provides {len(multipliers)} multipliers but expected {expected_networks} networks"
                )

    if "--n" in line and not re.search(r"(?<!\S)--n\b\s+\S", line):
        messages.append("--n is present but has no negative prompt text")

    if re.search(r"\S--[A-Za-z]", line):
        messages.append("option appears without leading whitespace; write 'prompt --n negative', not 'prompt--n negative'")

    return [f"line {line_number}: {message}" for message in messages]


def main() -> int:
    args = parse_args()
    if args.images_per_prompt is not None and args.images_per_prompt < 1:
        print("--images-per-prompt must be positive", file=sys.stderr)
        return 2
    if args.expected_networks is not None and args.expected_networks < 1:
        print("--expected-networks must be positive", file=sys.stderr)
        return 2
    if not args.prompt_file.is_file():
        print(f"prompt file not found: {args.prompt_file}", file=sys.stderr)
        return 2

    options = option_table(args.family)
    try:
        lines = args.prompt_file.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as error:
        print(f"failed to read UTF-8 prompt file: {error}", file=sys.stderr)
        return 2

    diagnostics: list[str] = []
    non_empty = 0
    for line_number, line in enumerate(lines, 1):
        if line.strip() and not line.lstrip().startswith("#"):
            non_empty += 1
        diagnostics.extend(
            validate_line(
                line,
                line_number,
                options,
                args.allow_unknown_options,
                args.images_per_prompt,
                args.expected_networks,
            )
        )

    if diagnostics:
        print("Prompt file validation failed:")
        for diagnostic in diagnostics:
            print(f"- {diagnostic}")
        return 1

    print(f"OK: {args.prompt_file} contains {non_empty} prompt line(s) for {args.family}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
