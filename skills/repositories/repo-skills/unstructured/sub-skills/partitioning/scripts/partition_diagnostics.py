#!/usr/bin/env python3
"""Diagnose unstructured partitioning capabilities and optionally preview a partition run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _json_default(value: Any) -> str:
    return str(value)


def _capability_for(spec: str | None, file_path: str | None) -> tuple[bool, list[str]]:
    if spec and file_path:
        raise ValueError("Use either --for or --file, not both.")

    from unstructured.doctor import evaluate_specifier, file_path_to_capability

    if spec:
        result = evaluate_specifier(spec)
    elif file_path:
        result = file_path_to_capability(file_path)
    else:
        raise ValueError("A capability target is required.")
    return result.ready, list(result.messages)


def _doctor_report() -> str:
    from unstructured.doctor import build_report

    return build_report()


def _element_summary(element: Any) -> dict[str, Any]:
    metadata = getattr(element, "metadata", None)
    coordinates = getattr(metadata, "coordinates", None) if metadata is not None else None
    return {
        "type": type(element).__name__,
        "category": getattr(element, "category", None),
        "text_preview": (getattr(element, "text", "") or "")[:160],
        "metadata": {
            "filename": getattr(metadata, "filename", None) if metadata is not None else None,
            "filetype": getattr(metadata, "filetype", None) if metadata is not None else None,
            "page_number": getattr(metadata, "page_number", None) if metadata is not None else None,
            "languages": getattr(metadata, "languages", None) if metadata is not None else None,
            "detection_origin": getattr(metadata, "detection_origin", None) if metadata is not None else None,
            "has_coordinates": coordinates is not None,
            "has_text_as_html": bool(getattr(metadata, "text_as_html", None))
            if metadata is not None
            else False,
        },
    }


def _partition_preview(args: argparse.Namespace) -> tuple[list[Any], list[dict[str, Any]]]:
    from unstructured.partition.auto import partition

    kwargs: dict[str, Any] = {
        "filename": args.partition,
        "strategy": args.strategy,
    }
    if args.content_type:
        kwargs["content_type"] = args.content_type
    if args.encoding:
        kwargs["encoding"] = args.encoding
    if args.languages:
        kwargs["languages"] = args.languages.split(",")
    if args.detect_language_per_element:
        kwargs["detect_language_per_element"] = True
    if args.infer_tables:
        kwargs["skip_infer_table_types"] = []
    if args.request_timeout is not None:
        kwargs["request_timeout"] = args.request_timeout

    elements = partition(**kwargs)
    return elements, [_element_summary(element) for element in elements[: args.limit]]


def _write_tiny_fixture(path: str) -> None:
    target = Path(path)
    target.write_text("Title\n\nThis is a tiny unstructured partitioning fixture.\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run unstructured doctor capability checks and optionally preview local "
            "partition output for a file."
        ),
    )
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--for", dest="for_cap", metavar="TYPE", help="Check a type/family, e.g. pdf, image, docx, audio.")
    target.add_argument("--file", metavar="PATH", help="Infer file type from PATH and check readiness.")
    parser.add_argument("--report", action="store_true", help="Print the full doctor report.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--partition", metavar="PATH", help="Run a local partition preview for PATH.")
    parser.add_argument("--strategy", default="auto", choices=("auto", "fast", "hi_res", "ocr_only"), help="Partition strategy for --partition.")
    parser.add_argument("--content-type", help="Content type override for --partition.")
    parser.add_argument("--encoding", help="Encoding override for --partition.")
    parser.add_argument("--languages", help="Comma-separated language hints, e.g. eng,spa.")
    parser.add_argument("--detect-language-per-element", action="store_true", help="Request per-element language metadata.")
    parser.add_argument("--infer-tables", action="store_true", help="Request table structure inference where supported.")
    parser.add_argument("--request-timeout", type=int, help="Request timeout for URL partitioning.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum preview elements to show.")
    parser.add_argument("--write-tiny-fixture", metavar="PATH", help="Write a tiny text fixture for smoke checks, then exit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.write_tiny_fixture:
        _write_tiny_fixture(args.write_tiny_fixture)
        print(args.write_tiny_fixture)
        return 0

    output: dict[str, Any] = {"ok": True}
    text_sections: list[str] = []

    try:
        if args.report or (not args.for_cap and not args.file and not args.partition):
            report = _doctor_report()
            output["report"] = report
            text_sections.append(report.rstrip())

        if args.for_cap or args.file:
            ready, messages = _capability_for(args.for_cap, args.file)
            output["capability"] = {
                "target": args.for_cap or args.file,
                "ready": ready,
                "messages": messages,
            }
            output["ok"] = output["ok"] and ready
            if messages:
                text_sections.extend(messages)
            text_sections.append(f"ready={str(ready).lower()}")

        if args.partition:
            elements, preview = _partition_preview(args)
            output["partition"] = {
                "path": args.partition,
                "strategy": args.strategy,
                "element_count": len(elements),
                "preview": preview,
            }
            text_sections.append(f"partitioned {len(elements)} element(s) from {args.partition}")
            for item in preview:
                text_sections.append(f"- {item['type']}: {item['text_preview']!r}")

    except Exception as exc:  # noqa: BLE001 - CLI diagnostic should surface any failure plainly.
        output["ok"] = False
        output["error"] = str(exc)
        if args.json:
            print(json.dumps(output, indent=2, default=_json_default))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(output, indent=2, default=_json_default))
    else:
        print("\n".join(section for section in text_sections if section))
    return 0 if output.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
