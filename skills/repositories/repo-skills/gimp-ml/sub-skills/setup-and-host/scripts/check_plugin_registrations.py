#!/usr/bin/env python3
"""Statically report likely Python-Fu registration points.

The scanner reads source text and tokenizes it where possible. It never imports
or executes a plug-in, starts GIMP, contacts a network, or changes files. It is
intended for Python 2-style source that may not parse under Python 3.
"""

from __future__ import annotations

import argparse
import io
import re
import tokenize
from pathlib import Path
from tokenize import COMMENT, DEDENT, ENCODING, INDENT, NL, NEWLINE, NAME, OP, STRING
from typing import Iterable, List, Optional, Sequence, Tuple

Token = tokenize.TokenInfo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only static scan for register() calls that look like "
            "Python-Fu entry points. No source is imported or executed."
        )
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="file or source tree to scan (default: current directory)",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="also scan files below dot-prefixed directories",
    )
    return parser.parse_args()


def source_files(path: Path, include_hidden: bool) -> Iterable[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() == ".py" else []
    if not path.is_dir():
        return []
    found: List[Path] = []
    try:
        for item in sorted(path.rglob("*.py")):
            if not include_hidden and any(part.startswith(".") for part in item.relative_to(path).parts):
                continue
            if item.is_file():
                found.append(item)
    except OSError:
        return found
    return found


def load_text(path: Path) -> str:
    # tokenize.open handles an encoding cookie; fallback keeps old/binary-ish
    # source inspectable without attempting to compile it.
    try:
        with tokenize.open(str(path)) as handle:
            return handle.read()
    except (SyntaxError, LookupError, UnicodeDecodeError, OSError):
        return path.read_text(encoding="utf-8", errors="replace")


def token_stream(text: str) -> Optional[List[Token]]:
    try:
        return list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (IndentationError, SyntaxError, tokenize.TokenError):
        return None


def significant(tokens: Sequence[Token]) -> List[Token]:
    ignored = {COMMENT, NL, NEWLINE, INDENT, DEDENT, ENCODING}
    return [token for token in tokens if token.type not in ignored]


def call_lines(tokens: Optional[Sequence[Token]], name: str) -> List[int]:
    if tokens is None:
        return []
    result: List[int] = []
    items = significant(tokens)
    for index, token in enumerate(items[:-1]):
        if token.type != NAME or token.string != name:
            continue
        if items[index + 1].type != OP or items[index + 1].string != "(":
            continue
        if index and items[index - 1].type == NAME and items[index - 1].string == "def":
            continue
        result.append(token.start[0])
    return result


def import_flags(text: str) -> Tuple[bool, bool, bool]:
    gimpfu = bool(re.search(r"(?m)^\s*(?:from\s+gimpfu\s+import|import\s+gimpfu)\b", text))
    helper = bool(re.search(r"(?m)^\s*(?:from\s+plugin_utils_g2\s+import|import\s+plugin_utils_g2)\b", text))
    gimp_reference = bool(re.search(r"(?m)^\s*(?:from\s+gimp\s+import|import\s+gimp)\b", text))
    return gimpfu, helper, gimp_reference


def first_procedure_name(lines: Sequence[str], register_line: int) -> str:
    # Look only at the call's opening area. This handles ordinary string first
    # arguments and the newer N_("...") style without evaluating expressions.
    block = "\n".join(lines[register_line : register_line + 45])
    call = re.search(r"\bregister\s*\(", block)
    if call:
        block = block[call.end() :]
    match = re.search(r"\s*['\"]([^'\"]+)['\"]\s*,", block)
    if match:
        return match.group(1)
    match = re.search(r"N_\(\s*['\"]([^'\"]+)['\"]\s*\)", block)
    if match:
        return match.group(1) + " (localized label; procedure name not literal)"
    return "<not a simple literal>"


def menu_path(lines: Sequence[str], register_line: int) -> str:
    block = "\n".join(lines[register_line : register_line + 70])
    match = re.search(r"\bmenu\s*=\s*['\"]([^'\"]+)['\"]", block)
    return match.group(1) if match else "<not found>"


def scan_file(path: Path, display_root: Path) -> None:
    try:
        text = load_text(path)
    except OSError as exc:
        print(f"FILE_ERROR path={path} error={exc}")
        return
    tokens = token_stream(text)
    registers = call_lines(tokens, "register")
    mains = set(call_lines(tokens, "main"))
    gimpfu, helper, gimp_reference = import_flags(text)
    if not registers:
        return

    lines = text.splitlines()
    try:
        relative = path.relative_to(display_root)
    except ValueError:
        relative = path
    for line in registers:
        nearby_main = any(line <= main_line <= line + 100 for main_line in mains)
        likely = (gimpfu or helper or gimp_reference) and nearby_main
        if gimpfu:
            flavor = "gimpfu-import"
        elif helper:
            flavor = "plugin-utils-g2-import"
        elif gimp_reference:
            flavor = "gimp-import"
        else:
            flavor = "no-direct-gimp-import"
        print(f"file: {relative}")
        print(f"  register_line: {line}")
        print(f"  procedure: {first_procedure_name(lines, line - 1)}")
        print(f"  menu: {menu_path(lines, line - 1)}")
        print(f"  flavor: {flavor}")
        print(f"  main_call_nearby: {'yes' if nearby_main else 'no'}")
        print(f"  likely_python_fu_entry: {'yes' if likely else 'review'}")


def main() -> int:
    args = parse_args()
    root = Path(args.path).expanduser()
    print("READ_ONLY registration scan")
    print(f"scan_root: {root}")
    if not root.exists():
        print("scan_status: missing (no changes made)")
        return 0
    if not root.is_file() and not root.is_dir():
        print("scan_status: unsupported-path (no changes made)")
        return 0

    files = list(source_files(root, args.include_hidden))
    print(f"python_files: {len(files)}")
    for path in files:
        scan_file(path, root if root.is_dir() else root.parent)
    print("result: scan complete; findings are static hints, not proof of GIMP loading")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
