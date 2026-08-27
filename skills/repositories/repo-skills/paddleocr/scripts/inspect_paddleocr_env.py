#!/usr/bin/env python3
"""Inspect the public PaddleOCR surface without touching the source checkout.

This helper is intentionally read-only. It imports the installed package,
prints a compact summary, and can optionally run safe CLI help checks.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


def _run(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, check=False, text=True, capture_output=True)
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def _safe_version(dist_name: str) -> str | None:
    try:
        return version(dist_name)
    except PackageNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the installed PaddleOCR package and safe CLI entry points."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable summary.",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Also run safe PaddleOCR CLI help/version checks.",
    )
    parser.add_argument(
        "--mcp-help",
        action="store_true",
        help="Also try the PaddleOCR MCP server help check when installed.",
    )
    args = parser.parse_args()

    summary: dict[str, Any] = {}

    paddleocr = import_module("paddleocr")
    summary["paddleocr_version"] = getattr(paddleocr, "__version__", None)
    summary["paddleocr_file"] = str(Path(getattr(paddleocr, "__file__", "")))
    summary["paddleocr_all"] = list(getattr(paddleocr, "__all__", []))
    summary["paddlex_version"] = _safe_version("paddlex")
    summary["paddle_version"] = _safe_version("paddle")

    try:
        from paddleocr import doc2md_supported_formats

        summary["doc2md_supported_formats"] = doc2md_supported_formats()
    except Exception as exc:  # pragma: no cover - best-effort reporting
        summary["doc2md_supported_formats_error"] = f"{type(exc).__name__}: {exc}"

    if args.cli:
        summary["cli_checks"] = [
            _run([sys.executable, "-m", "paddleocr", "--version"]),
            _run([sys.executable, "-m", "paddleocr", "--help"]),
            _run([sys.executable, "-m", "paddleocr", "doc2md", "--formats"]),
            _run([sys.executable, "-m", "paddleocr", "api", "--help"]),
        ]

    if args.mcp_help:
        try:
            import_module("paddleocr_mcp")
        except Exception as exc:
            summary["mcp_help"] = {
                "skipped": True,
                "reason": f"{type(exc).__name__}: {exc}",
            }
        else:
            summary["mcp_help"] = _run([sys.executable, "-m", "paddleocr_mcp", "--help"])

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"paddleocr version: {summary['paddleocr_version']}")
        print(f"paddleocr module: {summary['paddleocr_file']}")
        if summary.get("paddlex_version"):
            print(f"paddlex version: {summary['paddlex_version']}")
        if summary.get("paddle_version"):
            print(f"paddle version: {summary['paddle_version']}")
        if "doc2md_supported_formats" in summary:
            formats = ", ".join(f".{item}" for item in summary["doc2md_supported_formats"])
            print(f"doc2md formats: {formats}")
        if args.cli:
            print("CLI checks:")
            for item in summary["cli_checks"]:
                print(f"- {item['command']}: rc={item['returncode']}")
        if args.mcp_help and "mcp_help" in summary:
            print(f"MCP help: {summary['mcp_help']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
