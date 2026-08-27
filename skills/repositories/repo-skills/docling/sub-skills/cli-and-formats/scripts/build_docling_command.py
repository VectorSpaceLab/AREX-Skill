#!/usr/bin/env python3
"""Build a safe Docling local conversion command.

The script prints a shell-quoted command; it does not execute Docling.
"""

from __future__ import annotations

import argparse
import shlex
from collections.abc import Sequence

INPUT_FORMATS = (
    "docx",
    "pptx",
    "html",
    "image",
    "pdf",
    "asciidoc",
    "md",
    "csv",
    "xlsx",
    "xml_uspto",
    "xml_jats",
    "xml_xbrl",
    "xml_doclang",
    "mets_gbs",
    "json_docling",
    "audio",
    "vtt",
    "latex",
    "email",
    "epub",
)

OUTPUT_FORMATS = (
    "md",
    "json",
    "yaml",
    "html",
    "html_split_page",
    "text",
    "doctags",
    "vtt",
    "doclang",
)

IMAGE_EXPORT_MODES = ("placeholder", "embedded", "referenced")
HTML_IMAGE_FETCH_MODES = ("none", "local", "remote", "all")
PIPELINES = ("legacy", "standard", "vlm", "asr")
DEVICES = ("auto", "cpu", "cuda", "mps", "xpu")


def _add_repeated(command: list[str], flag: str, values: Sequence[str] | None) -> None:
    for value in values or ():
        command.extend([flag, value])


def _add_bool_pair(
    command: list[str], enabled: bool | None, positive: str, negative: str
) -> None:
    if enabled is True:
        command.append(positive)
    elif enabled is False:
        command.append(negative)


def build_command(args: argparse.Namespace) -> list[str]:
    command = ["docling"]
    command.extend(args.source)

    _add_repeated(command, "--from", args.from_format)
    _add_repeated(command, "--to", args.to)

    if args.output:
        command.extend(["--output", args.output])
    if args.image_export_mode:
        command.extend(["--image-export-mode", args.image_export_mode])
    if args.html_image_fetch:
        command.extend(["--html-image-fetch", args.html_image_fetch])
    if args.headers:
        command.extend(["--headers", args.headers])
    if args.html_image_headers:
        command.extend(["--html-image-headers", args.html_image_headers])
    if args.pipeline:
        command.extend(["--pipeline", args.pipeline])
    if args.vlm_model:
        command.extend(["--vlm-model", args.vlm_model])
    if args.asr_model:
        command.extend(["--asr-model", args.asr_model])
    if args.ocr_lang:
        command.extend(["--ocr-lang", args.ocr_lang])
    if args.ocr_engine:
        command.extend(["--ocr-engine", args.ocr_engine])
    if args.pdf_password:
        command.extend(["--pdf-password", args.pdf_password])
    if args.document_timeout is not None:
        command.extend(["--document-timeout", str(args.document_timeout)])
    if args.num_threads is not None:
        command.extend(["--num-threads", str(args.num_threads)])
    if args.device:
        command.extend(["--device", args.device])
    if args.artifacts_path:
        command.extend(["--artifacts-path", args.artifacts_path])

    _add_bool_pair(command, args.ocr, "--ocr", "--no-ocr")
    _add_bool_pair(command, args.force_ocr, "--force-ocr", "--no-force-ocr")
    _add_bool_pair(command, args.tables, "--tables", "--no-tables")

    if args.enable_remote_services:
        command.append("--enable-remote-services")
    if args.abort_on_error:
        command.append("--abort-on-error")
    if args.verbose:
        command.append("-" + "v" * args.verbose)

    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print a shell-safe local `docling` conversion command. The command "
            "is not executed."
        )
    )
    parser.add_argument(
        "source",
        nargs="+",
        help="One or more local files, directories, or URL sources.",
    )
    parser.add_argument(
        "--output",
        help="Output directory to pass as `--output`.",
    )
    parser.add_argument(
        "--to",
        action="append",
        choices=OUTPUT_FORMATS,
        help="Repeatable Docling output format. Defaults to Docling's md behavior if omitted.",
    )
    parser.add_argument(
        "--from",
        dest="from_format",
        action="append",
        choices=INPUT_FORMATS,
        help="Repeatable Docling input format allow-list for source filtering.",
    )
    parser.add_argument(
        "--image-export-mode",
        choices=IMAGE_EXPORT_MODES,
        help="Image mode for Markdown/JSON/YAML/HTML outputs.",
    )
    parser.add_argument(
        "--html-image-fetch",
        choices=HTML_IMAGE_FETCH_MODES,
        help="Whether HTML/EPUB conversion may fetch referenced image resources.",
    )
    parser.add_argument(
        "--headers",
        help="JSON HTTP headers for URL source fetching.",
    )
    parser.add_argument(
        "--html-image-headers",
        help="JSON HTTP headers for remote HTML/EPUB image-resource fetching.",
    )
    parser.add_argument(
        "--pipeline",
        choices=PIPELINES,
        help="Local processing pipeline.",
    )
    parser.add_argument(
        "--vlm-model",
        help="VLM preset for `--pipeline vlm`.",
    )
    parser.add_argument(
        "--asr-model",
        help="ASR model preset for audio/video work.",
    )
    parser.add_argument(
        "--ocr",
        dest="ocr",
        action="store_true",
        default=None,
        help="Add `--ocr`.",
    )
    parser.add_argument(
        "--no-ocr",
        dest="ocr",
        action="store_false",
        help="Add `--no-ocr`.",
    )
    parser.add_argument(
        "--force-ocr",
        dest="force_ocr",
        action="store_true",
        default=None,
        help="Add `--force-ocr`.",
    )
    parser.add_argument(
        "--no-force-ocr",
        dest="force_ocr",
        action="store_false",
        help="Add `--no-force-ocr`.",
    )
    parser.add_argument(
        "--tables",
        dest="tables",
        action="store_true",
        default=None,
        help="Add `--tables`.",
    )
    parser.add_argument(
        "--no-tables",
        dest="tables",
        action="store_false",
        help="Add `--no-tables`.",
    )
    parser.add_argument(
        "--ocr-lang",
        help="Comma- or semicolon-separated OCR languages to pass through.",
    )
    parser.add_argument(
        "--ocr-engine",
        help="OCR engine name to pass through.",
    )
    parser.add_argument(
        "--pdf-password",
        help="Password for protected PDF documents.",
    )
    parser.add_argument(
        "--document-timeout",
        type=float,
        help="Per-document timeout in seconds.",
    )
    parser.add_argument(
        "--num-threads",
        type=int,
        help="Number of local threads.",
    )
    parser.add_argument(
        "--device",
        choices=DEVICES,
        help="Accelerator device.",
    )
    parser.add_argument(
        "--artifacts-path",
        help="Model artifacts directory to pass through.",
    )
    parser.add_argument(
        "--enable-remote-services",
        action="store_true",
        help="Allow pipeline internals that call remote services.",
    )
    parser.add_argument(
        "--abort-on-error",
        action="store_true",
        help="Abort local batch conversion on the first error.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Add CLI verbosity; repeat for debug.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    command = build_command(args)
    print(shlex.join(command))


if __name__ == "__main__":
    main()
