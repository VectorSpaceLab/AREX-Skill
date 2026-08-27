#!/usr/bin/env python3
"""Safe smoke helper for the MarkItDown core conversion API."""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-test the installed markitdown package and convert a small input."
    )
    parser.add_argument(
        "--check-import",
        action="store_true",
        help="Only import markitdown and print the installed version/API status.",
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        help="Optional local file to convert. If omitted, converts a tiny in-memory HTML sample.",
    )
    parser.add_argument(
        "--extension",
        help="Optional extension hint, with or without a leading dot, such as html or .pdf.",
    )
    parser.add_argument("--mime-type", help="Optional MIME type hint, such as text/html.")
    parser.add_argument("--charset", help="Optional charset hint, such as utf-8.")
    parser.add_argument(
        "--keep-data-uris",
        action="store_true",
        help="Preserve embedded data URIs instead of allowing MarkItDown to truncate them.",
    )
    return parser


def _normalize_extension(extension: str | None) -> str | None:
    if extension is None:
        return None
    extension = extension.strip()
    if not extension:
        return None
    return extension if extension.startswith(".") else f".{extension}"


def _print_error(message: str, detail: BaseException | None = None) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    if detail is not None:
        print(f"DETAIL: {type(detail).__name__}: {detail}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        from markitdown import (
            __version__,
            FileConversionException,
            MarkItDown,
            MissingDependencyException,
            StreamInfo,
            UnsupportedFormatException,
        )
    except Exception as exc:  # pragma: no cover - diagnostic path
        return _print_error(
            "Could not import markitdown. Install the package first, for example `pip install markitdown` or an editable repo install.",
            exc,
        )

    print(f"markitdown import OK: {__version__}")
    if args.check_import:
        return 0

    extension = _normalize_extension(args.extension)
    stream_info = StreamInfo(
        extension=extension,
        mimetype=args.mime_type,
        charset=args.charset,
    )

    try:
        md = MarkItDown()
        if args.input_file is None:
            sample = b"<html><body><h1>MarkItDown smoke</h1><p>conversion ok</p></body></html>"
            if extension is None and args.mime_type is None and args.charset is None:
                stream_info = StreamInfo(
                    extension=".html", mimetype="text/html", charset="utf-8"
                )
            result = md.convert_stream(
                io.BytesIO(sample),
                stream_info=stream_info,
                keep_data_uris=args.keep_data_uris,
            )
        else:
            if not args.input_file.exists():
                return _print_error(f"Input file does not exist: {args.input_file}")
            if not args.input_file.is_file():
                return _print_error(f"Input path is not a regular file: {args.input_file}")
            result = md.convert_local(
                args.input_file,
                stream_info=stream_info,
                keep_data_uris=args.keep_data_uris,
            )
    except MissingDependencyException as exc:
        return _print_error(
            "A converter recognized the input, but an optional dependency is missing. Install the relevant extra, such as `markitdown[pdf]`, `markitdown[docx]`, or `markitdown[all]`.",
            exc,
        )
    except UnsupportedFormatException as exc:
        return _print_error(
            "No converter accepted the input. Check the file type and provide --extension, --mime-type, or --charset hints for streams or ambiguous files.",
            exc,
        )
    except FileConversionException as exc:
        print(
            "ERROR: A converter accepted the input but conversion failed.",
            file=sys.stderr,
        )
        attempts = exc.attempts or []
        if attempts:
            print("Failed converter attempts:", file=sys.stderr)
            for attempt in attempts:
                converter_name = type(attempt.converter).__name__
                if attempt.exc_info is None:
                    print(f"- {converter_name}: no exception info", file=sys.stderr)
                else:
                    exc_type, exc_value, _ = attempt.exc_info
                    print(
                        f"- {converter_name}: {exc_type.__name__}: {exc_value}",
                        file=sys.stderr,
                    )
        else:
            print(f"DETAIL: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        return _print_error(
            "I/O failed while reading the input. Check path permissions and file availability.",
            exc,
        )
    except Exception as exc:  # pragma: no cover - diagnostic path
        return _print_error("Unexpected conversion failure.", exc)

    print("conversion OK")
    if result.title:
        print(f"title: {result.title}")
    print("--- markdown ---")
    print(result.markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
