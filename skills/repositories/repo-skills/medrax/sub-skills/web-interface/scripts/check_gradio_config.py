#!/usr/bin/env python3
"""Validate MedRAX/Gradio launch values without launching a server.

This helper is intentionally independent of the current working directory. It
only parses arguments and checks environment-variable presence; it does not
import Gradio, read uploads, make network requests, create directories, or
print secret values.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Iterable

KNOWN_TOOLS = {
    "ChestXRayClassifierTool",
    "ChestXRaySegmentationTool",
    "LlavaMedTool",
    "XRayVQATool",
    "ChestXRayReportGeneratorTool",
    "XRayPhraseGroundingTool",
    "ChestXRayGeneratorTool",
    "ImageVisualizerTool",
    "DicomProcessorTool",
}
LOOPBACK_NAMES = {"127.0.0.1", "localhost", "::1", "[::1]"}
BROAD_NAMES = {"0.0.0.0", "::", "[::]"}
ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError("expected true/false, yes/no, or 1/0")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check safe Gradio configuration; never launch or expose files."
    )
    parser.add_argument("--server-name", default="127.0.0.1")
    parser.add_argument("--server-port", type=int, default=8585)
    parser.add_argument("--share", type=parse_bool, default=False)
    parser.add_argument("--temp-dir", default="temp")
    parser.add_argument(
        "--tools",
        action="append",
        default=[],
        help="Selected initializer tool name; repeat for multiple tools.",
    )
    parser.add_argument("--enable-dicom", action="store_true")
    parser.add_argument(
        "--require-env",
        action="append",
        default=[],
        metavar="NAME",
        help="Require a non-empty environment variable; repeat as needed.",
    )
    parser.add_argument(
        "--require-openai",
        action="store_true",
        help="Require OPENAI_API_KEY without printing its value.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat broad binds and share=True as errors rather than warnings.",
    )
    return parser


def validate(args: argparse.Namespace, environ: dict[str, str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    server_name = args.server_name.strip()
    if not server_name or any(ord(char) < 32 for char in server_name):
        errors.append("--server-name must be a non-empty hostname or address")
    if not 1 <= args.server_port <= 65535:
        errors.append("--server-port must be between 1 and 65535")
    if not args.temp_dir.strip() or "\x00" in args.temp_dir:
        errors.append("--temp-dir must be a non-empty path without NUL bytes")

    unknown = sorted(set(args.tools) - KNOWN_TOOLS)
    if unknown:
        errors.append("unknown tool name(s): " + ", ".join(unknown))
    if args.enable_dicom and "DicomProcessorTool" not in args.tools:
        errors.append("--enable-dicom requires DicomProcessorTool in --tools")

    required = list(args.require_env)
    if args.require_openai:
        required.append("OPENAI_API_KEY")
    for name in required:
        if not ENV_NAME.fullmatch(name):
            errors.append(f"invalid environment-variable name: {name!r}")
        elif not environ.get(name, "").strip():
            errors.append(f"required environment variable is missing or empty: {name}")

    if server_name in BROAD_NAMES:
        message = "server binds on all interfaces; review authentication and network boundaries"
        (errors if args.strict else warnings).append(message)
    elif server_name not in LOOPBACK_NAMES:
        warnings.append("server-name is not loopback; review who can reach the interface")
    if args.share:
        message = "share=True can create public exposure; use only with explicit approval"
        (errors if args.strict else warnings).append(message)

    if not args.tools:
        warnings.append("no tools selected; confirm that the initializer's default-all behavior is intended")
    if "DicomProcessorTool" in args.tools and not args.enable_dicom:
        warnings.append("DicomProcessorTool selected but --enable-dicom is not set")
    if "OPENAI_BASE_URL" not in environ:
        warnings.append("OPENAI_BASE_URL is unset; confirm the default model endpoint is intended")

    return errors, warnings


def report(errors: Iterable[str], warnings: Iterable[str]) -> int:
    errors = list(errors)
    warnings = list(warnings)
    for message in warnings:
        print(f"WARNING: {message}")
    for message in errors:
        print(f"ERROR: {message}", file=sys.stderr)
    if errors:
        print(f"Configuration check failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print("Configuration check passed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors, warnings = validate(args, dict(os.environ))
    return report(errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
