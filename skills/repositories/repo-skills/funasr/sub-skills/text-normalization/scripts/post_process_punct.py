#!/usr/bin/env python3
"""Standalone punctuation cleanup helper for FunASR text normalization.

The `align` command preserves the tested FunTextProcessing behavior that moves
spaces around punctuation in a normalized candidate so they match the original
input text. The script intentionally does not import Pynini or run the full
ITN/TN stack by default.
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import re
import string
import sys
from pathlib import Path
from typing import Iterable, List, Sequence
from unicodedata import category

SPACE_DUP = re.compile(r" +")


def post_process_punctuation(text: str) -> str:
    """Normalize common quote variants and tighten common punctuation spacing."""
    text = (
        text.replace("( ", "(")
        .replace(" )", ")")
        .replace("{ ", "{")
        .replace(" }", "}")
        .replace("[ ", "[")
        .replace(" ]", "]")
        .replace("”", '"')
        .replace("’", "'")
        .replace("»", '"')
        .replace("«", '"')
        .replace("\\", "")
        .replace("„", '"')
        .replace("´", "'")
        .replace("“", '"')
        .replace("‘", "'")
        .replace("`", "'")
        .replace("- -", "--")
    )
    text = SPACE_DUP.sub(" ", text)
    for punct in "!,.:;?":
        text = text.replace(f" {punct}", punct)
    return SPACE_DUP.sub(" ", text).strip()


def post_process_punct(input_text: str, normalized_text: str, add_unicode_punct: bool = False) -> str:
    """Align spaces around punctuation in `normalized_text` with `input_text`.

    This is useful after a normalizer or detokenizer shifts an apostrophe,
    quote, comma, or other punctuation mark away from the spacing used by the
    original input.
    """
    if "``" in input_text and "``" not in normalized_text:
        input_text = input_text.replace("``", '"')

    input_chars = list(input_text)
    normalized_chars = list(normalized_text)
    punct_marks = [char for char in string.punctuation if char in input_chars]

    if add_unicode_punct:
        punct_marks.extend(
            char
            for char in dict.fromkeys(input_chars)
            if char not in string.punctuation and category(char).startswith("P")
        )

    for punct in punct_marks:
        try:
            counts_match = input_chars.count(punct) == normalized_chars.count(punct)
            idx_in = 0
            idx_out = 0
            while punct in input_chars[idx_in:]:
                idx_out = normalized_chars.index(punct, idx_out)
                idx_in = input_chars.index(punct, idx_in)

                def is_valid_alignment() -> bool:
                    """Allow partial alignment when nearby chars prove this mark corresponds."""
                    return (
                        idx_out > 0
                        and idx_in > 0
                        and normalized_chars[idx_out - 1] == input_chars[idx_in - 1]
                    ) or (
                        idx_out < len(normalized_chars) - 1
                        and idx_in < len(input_chars) - 1
                        and normalized_chars[idx_out + 1] == input_chars[idx_in + 1]
                    )

                if not counts_match and not is_valid_alignment():
                    idx_in += 1
                    continue

                if idx_in > 0 and idx_out > 0:
                    if normalized_chars[idx_out - 1] == " " and input_chars[idx_in - 1] != " ":
                        normalized_chars[idx_out - 1] = ""
                    elif normalized_chars[idx_out - 1] != " " and input_chars[idx_in - 1] == " ":
                        normalized_chars[idx_out - 1] += " "

                if idx_in < len(input_chars) - 1 and idx_out < len(normalized_chars) - 1:
                    if normalized_chars[idx_out + 1] == " " and input_chars[idx_in + 1] != " ":
                        normalized_chars[idx_out + 1] = ""
                    elif normalized_chars[idx_out + 1] != " " and input_chars[idx_in + 1] == " ":
                        normalized_chars[idx_out] = normalized_chars[idx_out] + " "

                idx_out += 1
                idx_in += 1
        except Exception as exc:  # Keep helper best-effort like the upstream behavior.
            logging.debug("Skipping punctuation alignment for %r: %s", punct, exc)

    return SPACE_DUP.sub(" ", "".join(normalized_chars))


def _read_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _write_lines(lines: Sequence[str], output_file: Path | None) -> None:
    payload = "\n".join(lines)
    if output_file:
        output_file.write_text(payload + ("\n" if lines else ""), encoding="utf-8")
    else:
        for line in lines:
            print(line)


def _pair_inputs(args: argparse.Namespace) -> tuple[List[str], List[str]]:
    if args.input_file:
        inputs = _read_lines(args.input_file)
    else:
        inputs = [args.input_text]

    if args.normalized_file:
        normalized = _read_lines(args.normalized_file)
    else:
        normalized = [args.normalized_text]

    if len(inputs) != len(normalized):
        raise ValueError(
            f"input and normalized sources must have the same number of lines; "
            f"got {len(inputs)} and {len(normalized)}"
        )
    return inputs, normalized


def cmd_align(args: argparse.Namespace) -> int:
    try:
        inputs, normalized = _pair_inputs(args)
    except OSError as exc:
        print(f"error: could not read input file: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    cleaned = [
        post_process_punct(src, cand, add_unicode_punct=args.unicode_punct)
        for src, cand in zip(inputs, normalized)
    ]
    _write_lines(cleaned, args.output_file)
    return 0


def cmd_simple(args: argparse.Namespace) -> int:
    try:
        lines = _read_lines(args.input_file) if args.input_file else [args.text]
    except OSError as exc:
        print(f"error: could not read input file: {exc}", file=sys.stderr)
        return 2
    _write_lines([post_process_punctuation(line) for line in lines], args.output_file)
    return 0


def _find_spec(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def cmd_check_full_stack(args: argparse.Namespace) -> int:
    required = {
        "fun_text_processing": "FunTextProcessing package modules from FunASR",
        "pynini": "Pynini finite-state runtime for full ITN/TN grammars",
        "regex": "regex helper imported by the full TN path",
        "joblib": "parallel batch helper imported by the full TN path",
        "tqdm": "progress helper imported by the full TN path",
    }
    optional = {
        "nemo.collections.common.tokenizers.moses_tokenizers": (
            "optional Moses detokenizer used by full TN punct_post_process"
        ),
    }

    missing_required: List[str] = []
    print("Full FunTextProcessing ITN/TN dependency check:")
    for module_name, purpose in required.items():
        ok = _find_spec(module_name)
        print(f"  [{'ok' if ok else 'missing'}] {module_name} - {purpose}")
        if not ok:
            missing_required.append(module_name)

    for module_name, purpose in optional.items():
        ok = _find_spec(module_name)
        print(f"  [{'ok' if ok else 'missing optional'}] {module_name} - {purpose}")

    if missing_required:
        print("\nMissing required full-stack package(s): " + ", ".join(missing_required))
        if "pynini" in missing_required:
            print(
                "Install a compatible Pynini build before using semantic ITN/TN; "
                "pynini==2.1.5 is the version expected by this FunTextProcessing code line."
            )
        print(
            "The standalone punctuation helper remains usable: "
            "post_process_punct.py align --input ... --normalized ..."
        )
        return 1 if args.strict else 0

    print("\nRequired full-stack imports are discoverable. Grammar/cache creation still needs a runtime smoke for the selected language.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Standalone FunASR punctuation post-processing helper.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    align = subparsers.add_parser(
        "align",
        help="align punctuation spacing in normalized text with original input",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    input_group = align.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input", dest="input_text", help="original input text")
    input_group.add_argument("--input-file", type=Path, help="UTF-8 file of original lines")
    normalized_group = align.add_mutually_exclusive_group(required=True)
    normalized_group.add_argument("--normalized", dest="normalized_text", help="normalized candidate text")
    normalized_group.add_argument("--normalized-file", type=Path, help="UTF-8 file of normalized candidate lines")
    align.add_argument("--output-file", type=Path, help="write cleaned lines to this UTF-8 file")
    align.add_argument("--unicode-punct", action="store_true", help="also align non-ASCII Unicode punctuation present in the input")
    align.set_defaults(func=cmd_align)

    simple = subparsers.add_parser(
        "simple",
        help="normalize common quote variants and tighten common punctuation spacing",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    simple_group = simple.add_mutually_exclusive_group(required=True)
    simple_group.add_argument("--text", help="text to clean")
    simple_group.add_argument("--input-file", type=Path, help="UTF-8 file of lines to clean")
    simple.add_argument("--output-file", type=Path, help="write cleaned lines to this UTF-8 file")
    simple.set_defaults(func=cmd_simple)

    check = subparsers.add_parser(
        "check-full-stack",
        help="report optional full ITN/TN dependency readiness without importing heavy grammars",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    check.add_argument("--strict", action="store_true", help="exit non-zero when required full-stack packages are missing")
    check.set_defaults(func=cmd_check_full_stack)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
