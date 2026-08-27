#!/usr/bin/env python3
"""Safely validate MarkItDown Azure cloud integration configuration.

This script performs local import and argument validation only. It does not
construct Azure clients, resolve custom analyzers, read input files, or call
Azure services.
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from dataclasses import dataclass
from typing import Iterable, Sequence
from urllib.parse import urlparse


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate MarkItDown Azure cloud integration configuration without network calls."
    )
    parser.add_argument(
        "--mode",
        choices=("docintel", "cu"),
        required=True,
        help="Cloud integration to validate: docintel or cu.",
    )
    parser.add_argument(
        "--endpoint",
        required=True,
        help="Azure service endpoint URL. Use a placeholder for dry documentation checks.",
    )
    parser.add_argument(
        "--analyzer",
        help="Content Understanding analyzer ID. Valid only with --mode cu.",
    )
    parser.add_argument(
        "--file-types",
        help="Comma-separated file type values to route to the selected cloud converter.",
    )
    parser.add_argument(
        "--filename",
        help="Optional filename used only to check CLI cloud-mode requirements.",
    )
    parser.add_argument(
        "--use-docintel",
        action="store_true",
        help="Validate the equivalent MarkItDown CLI flag combination.",
    )
    parser.add_argument(
        "--use-cu",
        action="store_true",
        help="Validate the equivalent MarkItDown CLI flag combination.",
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        default=True,
        help="Keep validation local. This is the default and this script never calls Azure.",
    )
    return parser.parse_args(argv)


def import_module(name: str) -> CheckResult:
    try:
        importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - report local import diagnostics only.
        return CheckResult(name, False, f"import failed: {exc}")
    return CheckResult(name, True, "import ok")


def check_converter_imports(mode: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    try:
        if mode == "docintel":
            from markitdown.converters import (  # noqa: F401
                DocumentIntelligenceConverter,
                DocumentIntelligenceFileType,
            )

            results.append(
                CheckResult(
                    "markitdown DocumentIntelligenceConverter",
                    True,
                    "converter class import ok",
                )
            )
        else:
            from markitdown.converters import (  # noqa: F401
                ContentUnderstandingConverter,
                ContentUnderstandingFileType,
            )

            results.append(
                CheckResult(
                    "markitdown ContentUnderstandingConverter",
                    True,
                    "converter class import ok",
                )
            )
    except Exception as exc:  # noqa: BLE001 - report local import diagnostics only.
        results.append(CheckResult("markitdown converter import", False, str(exc)))
    return results


def check_optional_sdk_imports(mode: str) -> list[CheckResult]:
    if mode == "docintel":
        return [
            import_module("azure.ai.documentintelligence"),
            import_module("azure.identity"),
        ]
    return [
        import_module("azure.ai.contentunderstanding"),
        import_module("azure.identity"),
    ]


def validate_endpoint(endpoint: str) -> CheckResult:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        return CheckResult(
            "endpoint",
            False,
            "endpoint should be an absolute URL such as https://<resource>.cognitiveservices.azure.com/",
        )
    if parsed.scheme != "https":
        return CheckResult(
            "endpoint",
            True,
            "URL parses, but https is strongly preferred for real Azure calls",
        )
    return CheckResult("endpoint", True, "URL parses as an https endpoint")


def supported_file_types(mode: str) -> set[str]:
    if mode == "docintel":
        return {"docx", "pptx", "xlsx", "html", "pdf", "jpeg", "png", "bmp", "tiff"}
    return {
        "pdf",
        "docx",
        "pptx",
        "xlsx",
        "html",
        "txt",
        "md",
        "rtf",
        "xml",
        "eml",
        "msg",
        "jpeg",
        "png",
        "bmp",
        "tiff",
        "heif",
        "mp4",
        "m4v",
        "mov",
        "avi",
        "mkv",
        "webm",
        "flv",
        "wmv",
        "wav",
        "mp3",
        "m4a",
        "flac",
        "ogg",
        "aac",
        "wma",
    }


def split_file_types(raw: str | None) -> list[str]:
    if raw is None:
        return []
    return [part.strip().lower() for part in raw.split(",") if part.strip()]


def validate_file_types(mode: str, raw: str | None) -> CheckResult:
    values = split_file_types(raw)
    if not values:
        return CheckResult("file types", True, "no file-type restriction supplied")
    allowed = supported_file_types(mode)
    unknown = sorted(set(values) - allowed)
    if unknown:
        return CheckResult(
            "file types",
            False,
            f"unsupported for {mode}: {', '.join(unknown)}; allowed: {', '.join(sorted(allowed))}",
        )
    return CheckResult("file types", True, f"validated: {', '.join(values)}")


def validate_cli_combination(args: argparse.Namespace) -> CheckResult:
    if args.use_docintel and args.use_cu:
        return CheckResult(
            "cli flags",
            False,
            "--use-docintel and --use-cu are mutually exclusive in the MarkItDown CLI",
        )
    if args.mode == "docintel" and args.use_cu:
        return CheckResult("cli flags", False, "--mode docintel conflicts with --use-cu")
    if args.mode == "cu" and args.use_docintel:
        return CheckResult("cli flags", False, "--mode cu conflicts with --use-docintel")
    if args.analyzer and args.mode != "cu":
        return CheckResult("cli flags", False, "--analyzer is valid only with --mode cu")
    if (args.use_docintel or args.use_cu) and not args.filename:
        return CheckResult(
            "cli flags",
            False,
            "MarkItDown cloud CLI modes require a filename argument",
        )
    return CheckResult("cli flags", True, "argument combination is locally consistent")


def credential_hint() -> CheckResult:
    if os.environ.get("AZURE_API_KEY"):
        return CheckResult(
            "credentials",
            True,
            "AZURE_API_KEY is present; value was not read or printed",
        )
    return CheckResult(
        "credentials",
        True,
        "AZURE_API_KEY is not set; converter may use Azure Identity defaults for real calls",
    )


def print_results(results: Iterable[CheckResult]) -> bool:
    ok = True
    for result in results:
        status = "OK" if result.ok else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")
        ok = ok and result.ok
    return ok


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    results: list[CheckResult] = []
    results.extend(check_converter_imports(args.mode))
    results.extend(check_optional_sdk_imports(args.mode))
    results.append(validate_endpoint(args.endpoint))
    results.append(validate_file_types(args.mode, args.file_types))
    results.append(validate_cli_combination(args))
    results.append(credential_hint())
    results.append(
        CheckResult(
            "network",
            True,
            "no Azure clients were constructed and no network calls were made",
        )
    )

    return 0 if print_results(results) else 2


if __name__ == "__main__":
    sys.exit(main())
