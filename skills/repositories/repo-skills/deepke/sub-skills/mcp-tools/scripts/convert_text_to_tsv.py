#!/usr/bin/env python3
"""Convert one event-extraction input sentence to DeepKE-style raw JSONL and TSV files.

This standalone helper mirrors the pure conversion behavior used by the local
DeepKE MCP event-extraction wrapper. It does not import DeepKE, launch the MCP
server, call models, or mutate an existing DeepKE checkout unless you explicitly
choose output paths inside one.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

SEPARATOR = "\x02"


def stable_text_id(text: str) -> str:
    """Return the MD5 id format used by the source conversion helper."""

    return hashlib.md5(text.encode("utf-8")).hexdigest()


def separated_chars(text: str) -> str:
    """Join Unicode code points with the DeepKE TSV separator."""

    return SEPARATOR.join(text)


def separated_fill(text: str, fill: str = "O") -> str:
    """Return one BIO placeholder label per character."""

    return SEPARATOR.join([fill] * len(text))


def validate_sentence(text: str) -> str:
    """Validate the single-sentence TSV input constraints."""

    if not text:
        raise ValueError("input text must not be empty")
    if any(ch in text for ch in "\r\n\t"):
        raise ValueError("input text must be one sentence without tab or newline characters")
    return text


def write_raw_jsonl(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"text": text, "id": stable_text_id(text)}
    path.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")


def write_trigger_tsv(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = f"{separated_chars(text)}\t{separated_fill(text)}\t0\n"
    path.write_text("text_a\tlabel\tindex\n" + line, encoding="utf-8")


def write_role_tsv(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = f"{separated_chars(text)}\t{separated_fill(text)}\t{separated_fill(text)}\t0\n"
    path.write_text("text_a\tlabel\ttrigger_tag\tindex\n" + line, encoding="utf-8")


def convert_text(text: str, raw_path: Path, role_tsv_path: Path, trigger_tsv_path: Path) -> None:
    text = validate_sentence(text)
    write_raw_jsonl(text, raw_path)
    write_role_tsv(text, role_tsv_path)
    write_trigger_tsv(text, trigger_tsv_path)


def resolve_outputs(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    out_dir = args.output_dir
    raw_path = args.raw_out or (out_dir / f"{args.stem}_raw.jsonl")
    role_path = args.role_tsv or (out_dir / f"{args.stem}_role.tsv")
    trigger_path = args.trigger_tsv or (out_dir / f"{args.stem}_trigger.tsv")
    return raw_path, role_path, trigger_path


def ensure_can_write(paths: Iterable[Path], overwrite: bool) -> None:
    if overwrite:
        return
    existing = [str(path) for path in paths if path.exists()]
    if existing:
        joined = ", ".join(existing)
        raise FileExistsError(f"refusing to overwrite existing file(s): {joined}; pass --overwrite")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write raw JSONL, role TSV, and trigger TSV files for one DeepKE EE input sentence."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="single input sentence")
    source.add_argument("--text-file", type=Path, help="UTF-8 file containing exactly one input sentence")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd(), help="directory for default output files")
    parser.add_argument("--stem", default="input", help="filename stem used with --output-dir")
    parser.add_argument("--raw-out", type=Path, help="explicit raw JSONL output path")
    parser.add_argument("--role-tsv", type=Path, help="explicit role TSV output path")
    parser.add_argument("--trigger-tsv", type=Path, help="explicit trigger TSV output path")
    parser.add_argument("--overwrite", action="store_true", help="allow replacing existing output files")
    parser.add_argument("--quiet", action="store_true", help="suppress success summary")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    text = args.text if args.text is not None else args.text_file.read_text(encoding="utf-8").strip()
    raw_path, role_path, trigger_path = resolve_outputs(args)
    ensure_can_write((raw_path, role_path, trigger_path), args.overwrite)
    convert_text(text, raw_path, role_path, trigger_path)
    if not args.quiet:
        print("wrote DeepKE EE conversion files:")
        print(f"- raw_jsonl: {raw_path}")
        print(f"- role_tsv: {role_path}")
        print(f"- trigger_tsv: {trigger_path}")
        print(f"- text_id: {stable_text_id(validate_sentence(text))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
