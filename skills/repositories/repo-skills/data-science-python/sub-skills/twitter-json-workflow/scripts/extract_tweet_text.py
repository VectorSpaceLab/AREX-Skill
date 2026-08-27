#!/usr/bin/env python3
"""Extract tweet text from Twitter/X JSONL archives.

The script is stdlib-only and designed for portable line-oriented text export.
It prefers extended_tweet.full_text, then full_text, then text, unless the user
supplies an explicit field order with --field.
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_FIELDS = ["extended_tweet.full_text", "full_text", "text"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract tweet text from JSONL archives without third-party JSONL dependencies."
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        default=["-"],
        help="Input JSONL files, or - for standard input.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        help="Output path, or - for standard output.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "jsonl"],
        default="text",
        help="Write plain text lines or structured JSONL rows.",
    )
    parser.add_argument(
        "--field",
        action="append",
        dest="fields",
        help="Dotted field path to try for tweet text. Repeat to set precedence.",
    )
    parser.add_argument(
        "--on-error",
        choices=["warn", "skip", "stop"],
        default="warn",
        help="How to handle malformed JSON lines.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Input encoding for JSONL files.",
    )
    return parser.parse_args()


def resolve_path(record, path):
    if not path:
        return None
    value = record
    for part in path.split("."):
        if isinstance(value, dict):
            if part not in value:
                return None
            value = value[part]
        elif isinstance(value, list):
            if not part.isdigit():
                return None
            index = int(part)
            if index < 0 or index >= len(value):
                return None
            value = value[index]
        else:
            return None
    return value


def coerce_text(value):
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8", "replace")
    if isinstance(value, str):
        text = value
    elif isinstance(value, (int, float, bool)):
        text = str(value)
    else:
        try:
            text = json.dumps(value, ensure_ascii=False)
        except TypeError:
            text = str(value)
    text = text.strip()
    return text or None


def extract_text(record, fields):
    for field in fields:
        text = coerce_text(resolve_path(record, field))
        if text:
            return text, field
    return None, None


def normalize_text(text):
    return text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ").strip()


def format_jsonl_row(record, text, field, source, line_no):
    row = {
        "text": text,
        "text_field": field,
        "source_file": source,
        "source_line": line_no,
    }
    tweet_id = record.get("id_str") or record.get("id")
    if tweet_id is not None:
        row["tweet_id"] = tweet_id
    for key in ("created_at", "lang"):
        if key in record and record[key] is not None:
            row[key] = record[key]
    return row


def report_error(args, source, line_no, message):
    if args.on_error == "skip":
        return
    text = f"{source}:{line_no}: {message}"
    if args.on_error == "warn":
        print(text, file=sys.stderr)
        return
    raise SystemExit(text)


def main():
    args = parse_args()
    fields = args.fields if args.fields else DEFAULT_FIELDS
    stats = {"records": 0, "written": 0, "blank": 0, "malformed": 0, "empty": 0}

    if args.output == "-":
        out = sys.stdout
        close_output = False
    else:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        out = open(output_path, "w", encoding="utf-8", newline="\n")
        close_output = True

    try:
        for source in args.inputs:
            if source == "-":
                handle = sys.stdin
                close_input = False
            else:
                handle = open(Path(source).expanduser(), encoding=args.encoding, errors="replace")
                close_input = True
            try:
                for line_no, raw in enumerate(handle, 1):
                    if not raw.strip():
                        stats["blank"] += 1
                        continue
                    try:
                        record = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        stats["malformed"] += 1
                        report_error(args, source, line_no, f"malformed JSON ({exc.msg})")
                        continue
                    if not isinstance(record, dict):
                        stats["malformed"] += 1
                        report_error(args, source, line_no, "JSON value is not an object")
                        continue
                    stats["records"] += 1
                    text, field = extract_text(record, fields)
                    if text is None:
                        stats["empty"] += 1
                        continue
                    if args.format == "text":
                        out.write(normalize_text(text) + "\n")
                    else:
                        out.write(
                            json.dumps(
                                format_jsonl_row(record, text, field, source, line_no),
                                ensure_ascii=False,
                            )
                            + "\n"
                        )
                    stats["written"] += 1
            finally:
                if close_input:
                    handle.close()
        print(
            f"processed {stats['records']} records; wrote {stats['written']} rows; "
            f"skipped {stats['empty']} empty, {stats['blank']} blank, {stats['malformed']} malformed",
            file=sys.stderr,
        )
        return 0
    finally:
        if close_output:
            out.close()


if __name__ == "__main__":
    raise SystemExit(main())
