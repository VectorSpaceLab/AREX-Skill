#!/usr/bin/env python3
"""Safe OpenMed multimodal intake smoke check.

This helper demonstrates two parser-only contracts without requiring external
OCR binaries, model downloads, or real clinical data:

1. Extract normalized text and source spans from synthetic Markdown.
2. Convert deterministic fake-OCR words into an ExtractedDocument with bounding
   boxes that can later receive de-identification span projections.

Example:
    python document_intake_smoke.py --json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Any

SYNTHETIC_MARKDOWN = """# Synthetic visit note\n\nPatient Alice Example called 555-0100 about a rash.\n"""


def _markdown_document(markdown: str) -> Any:
    """Return an ExtractedDocument using OpenMed's Markdown parser when present."""
    try:
        from openmed.multimodal.documents_markdown import extract_markdown
    except Exception as exc:  # pragma: no cover - only when optional path absent
        raise RuntimeError(
            "Markdown intake is unavailable. Install the document parser dependency "
            "or run the fake OCR-only path. Original error: " + str(exc)
        ) from exc
    return extract_markdown(markdown)


def _fake_ocr_document() -> Any:
    """Return an ExtractedDocument from deterministic fake OCR words."""
    from openmed.multimodal.ocr import FakeOcrEngine, OcrWord

    engine = FakeOcrEngine(
        [
            OcrWord("Patient", (0.0, 0.0, 52.0, 12.0), 0.99),
            OcrWord("Alice", (57.0, 0.0, 92.0, 12.0), 0.98),
            OcrWord("Example", (97.0, 0.0, 150.0, 12.0), 0.97),
            OcrWord("555-0100", (0.0, 18.0, 70.0, 30.0), 0.96),
        ],
        fixture="synthetic",
    )
    result = engine.recognize(image=None, languages=["en"])
    return result.to_document(separator=" ")


def _document_summary(document: Any) -> dict[str, Any]:
    spans = []
    for span in getattr(document, "spans", ()):
        if hasattr(span, "__dataclass_fields__"):
            value = asdict(span)
        else:
            value = {
                "start": getattr(span, "start", None),
                "end": getattr(span, "end", None),
                "page": getattr(span, "page", None),
                "bbox": getattr(span, "bbox", None),
                "metadata": getattr(span, "metadata", {}),
            }
        spans.append(value)
    return {
        "text": getattr(document, "text", ""),
        "span_count": len(spans),
        "first_spans": spans[:4],
        "metadata": dict(getattr(document, "metadata", {}) or {}),
    }


def build_payload(markdown: str) -> dict[str, Any]:
    markdown_doc = _markdown_document(markdown)
    ocr_doc = _fake_ocr_document()
    return {
        "ok": True,
        "markdown": _document_summary(markdown_doc),
        "fake_ocr": _document_summary(ocr_doc),
        "handoff_reminder": (
            "Use the normalized text for de-identification, then project offsets "
            "back through the saved spans before source redaction."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a synthetic OpenMed document-intake smoke check."
    )
    parser.add_argument(
        "--markdown",
        default=SYNTHETIC_MARKDOWN,
        help="Synthetic Markdown text to extract; keep examples PHI-free.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a short text summary.",
    )
    args = parser.parse_args()

    payload = build_payload(args.markdown)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("OpenMed multimodal intake smoke: ok")
        print(f"Markdown text length: {len(payload['markdown']['text'])}")
        print(f"Markdown spans: {payload['markdown']['span_count']}")
        print(f"Fake OCR text: {payload['fake_ocr']['text']}")
        print(f"Fake OCR spans: {payload['fake_ocr']['span_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
