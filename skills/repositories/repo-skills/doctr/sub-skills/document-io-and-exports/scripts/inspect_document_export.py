#!/usr/bin/env python3
"""Inspect docTR document loading and export surfaces without running predictors.

This helper is intentionally safe: it can validate DocumentFile page arrays for
user-supplied inputs, then demonstrates Document/Page/KIEDocument exporters on
small synthetic result objects. It does not construct OCR/KIE predictors and does
not download model weights.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np


DocumentFile: Any | None = None
elements: Any | None = None
_FORMATS = ("text", "json", "markdown", "asciidoc", "html", "xml")


def _require_doctr_io() -> tuple[Any, Any]:
    """Import docTR IO lazily so --help works before the package is installed."""
    global DocumentFile, elements
    if DocumentFile is None or elements is None:
        try:
            from doctr.io import DocumentFile as _DocumentFile
            from doctr.io import elements as _elements
        except ModuleNotFoundError as exc:  # pragma: no cover - depends on caller installation
            raise SystemExit(
                "python-doctr or one of its required dependencies is not importable. "
                "Install the docTR package before running this helper."
            ) from exc
        DocumentFile = _DocumentFile
        elements = _elements
    return DocumentFile, elements


def _word(text: str, x0: float, y0: float, x1: float, y1: float) -> elements.Word:
    return elements.Word(text, 0.95, ((x0, y0), (x1, y1)), 0.90, {"value": 0, "confidence": None})


def _prediction(text: str, x0: float, y0: float, x1: float, y1: float) -> elements.Prediction:
    return elements.Prediction(text, 0.93, ((x0, y0), (x1, y1)), 0.88, {"value": 0, "confidence": None})


def _line(text: str, x0: float, y0: float, x1: float, y1: float) -> elements.Line:
    tokens = text.split()
    if not tokens:
        return elements.Line([], ((x0, y0), (x1, y1)), objectness_score=0.0)
    step = (x1 - x0) / len(tokens)
    return elements.Line([
        _word(token, x0 + idx * step, y0, x0 + (idx + 0.85) * step, y1)
        for idx, token in enumerate(tokens)
    ])


def _synthetic_page() -> elements.Page:
    page_img = np.zeros((1000, 800, 3), dtype=np.uint8)
    lines = [
        _line("Quarterly Invoice", 0.20, 0.05, 0.80, 0.09),
        _line("left column first", 0.08, 0.16, 0.45, 0.20),
        _line("left column second", 0.08, 0.22, 0.45, 0.26),
        _line("right column first", 0.55, 0.16, 0.92, 0.20),
        _line("Page 1 of 1", 0.40, 0.94, 0.62, 0.97),
    ]
    layout = [
        elements.LayoutElement("Title", 0.99, ((0.15, 0.04), (0.85, 0.11))),
        elements.LayoutElement("Text", 0.98, ((0.06, 0.14), (0.48, 0.30))),
        elements.LayoutElement("Text", 0.98, ((0.52, 0.14), (0.94, 0.24))),
        elements.LayoutElement("Page-footer", 0.97, ((0.35, 0.92), (0.70, 0.99))),
    ]
    cells = [
        elements.TableCell("Item", 0.97, ((0.08, 0.40), (0.35, 0.45)), 0, 0, 0, 0),
        elements.TableCell("Qty", 0.97, ((0.35, 0.40), (0.50, 0.45)), 0, 0, 1, 1),
        elements.TableCell("Bolt", 0.94, ((0.08, 0.45), (0.35, 0.50)), 1, 1, 0, 0),
        elements.TableCell("12", 0.94, ((0.35, 0.45), (0.50, 0.50)), 1, 1, 1, 1),
    ]
    table = elements.Table(cells=cells, num_rows=2, num_cols=2, geometry=((0.08, 0.40), (0.50, 0.50)))
    return elements.Page(
        page_img,
        [elements.Block(lines=lines)],
        page_idx=0,
        dimensions=(1000, 800),
        orientation={"value": 0.0, "confidence": 1.0},
        language={"value": "en", "confidence": 0.90},
        layout=layout,
        tables=[table],
    )


def _synthetic_document() -> elements.Document:
    return elements.Document([_synthetic_page()])


def _synthetic_kie_document() -> elements.KIEDocument:
    page = np.zeros((1000, 800, 3), dtype=np.uint8)
    predictions = {
        "date": [
            _prediction("2026-01-31", 0.15, 0.18, 0.35, 0.22),
            _prediction("2026-02-29", 0.15, 0.30, 0.35, 0.34),
        ],
        "total": [_prediction("123.45", 0.70, 0.78, 0.86, 0.82)],
        "empty_class": [],
    }
    kie_page = elements.KIEPage(
        page,
        predictions,
        page_idx=0,
        dimensions=(1000, 800),
        orientation={"value": 0.0, "confidence": 1.0},
        language={"value": "en", "confidence": 0.90},
    )
    return elements.KIEDocument([kie_page])


def _formats(selected: str) -> tuple[str, ...]:
    return _FORMATS if selected == "all" else (selected,)


def _export_object(obj: Any, fmt: str) -> Any:
    if fmt == "text":
        return obj.render()
    if fmt == "json":
        return obj.export()
    if fmt == "markdown":
        return obj.export_as_markdown()
    if fmt == "asciidoc":
        return obj.export_as_asciidoc()
    if fmt == "html":
        return obj.export_as_html()
    if fmt == "xml":
        return obj.export_as_xml()
    raise ValueError(f"unsupported demo format: {fmt}")


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _preview(value: Any, limit: int = 900) -> str:
    if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], (bytes, bytearray)):
        text = value[0].decode("utf-8", errors="replace")
    elif isinstance(value, list) and value and isinstance(value[0], tuple) and isinstance(value[0][0], (bytes, bytearray)):
        text = "\n".join(item[0].decode("utf-8", errors="replace") for item in value)
    elif isinstance(value, (dict, list, tuple)):
        text = _json_text(value)
    else:
        text = str(value)
    return text if len(text) <= limit else text[:limit] + "\n... <truncated>"


def _write_export(out_dir: Path, label: str, fmt: str, value: Any) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if fmt == "json":
        path = out_dir / f"{label}.json"
        path.write_text(_json_text(value) + "\n", encoding="utf-8")
        return [path]
    if fmt == "xml":
        xml_items: Iterable[Any]
        if isinstance(value, tuple):
            xml_items = [value]
        else:
            xml_items = value
        for idx, item in enumerate(xml_items, start=1):
            path = out_dir / f"{label}.page-{idx}.hocr.xml"
            path.write_bytes(item[0])
            written.append(path)
        return written
    suffix = {"text": "txt", "markdown": "md", "asciidoc": "adoc", "html": "html"}[fmt]
    path = out_dir / f"{label}.{suffix}"
    path.write_text(str(value) + "\n", encoding="utf-8")
    return [path]


def _shape_report(pages: list[np.ndarray]) -> list[dict[str, Any]]:
    report: list[dict[str, Any]] = []
    for idx, page in enumerate(pages):
        item = {
            "page_index": idx,
            "type": type(page).__name__,
            "shape": tuple(int(dim) for dim in getattr(page, "shape", ())),
            "dtype": str(getattr(page, "dtype", "unknown")),
            "is_uint8_hwc_rgb_candidate": bool(
                isinstance(page, np.ndarray)
                and page.dtype == np.uint8
                and page.ndim == 3
                and page.shape[-1] == 3
            ),
        }
        report.append(item)
    return report


def _load_pages(args: argparse.Namespace) -> list[np.ndarray] | None:
    if not args.url and not args.input:
        return None
    DocumentFileCls, _ = _require_doctr_io()
    if args.url:
        return DocumentFileCls.from_url(args.url)
    inputs = [Path(item) for item in args.input]
    kind = args.kind
    if kind == "auto":
        kind = "pdf" if len(inputs) == 1 and inputs[0].suffix.lower() == ".pdf" else "image"
    if kind == "pdf":
        if len(inputs) != 1:
            raise ValueError("--kind pdf expects exactly one --input path")
        return DocumentFileCls.from_pdf(inputs[0])
    if kind == "image":
        return DocumentFileCls.from_images(inputs if len(inputs) > 1 else inputs[0])
    raise ValueError("--kind url should be provided with --url")


def _print_demo(args: argparse.Namespace) -> None:
    _require_doctr_io()
    doc = _synthetic_document()
    kie_doc = _synthetic_kie_document() if args.include_kie else None
    page = doc.pages[0]

    print("\n=== Synthetic OCR page structure ===")
    print(f"pages={len(doc.pages)} blocks={len(page.blocks)} tables={len(page.tables)} layout_regions={len(page.layout)}")
    print(f"table_grid={page.tables[0].to_grid() if page.tables else []}")
    print("reading_order_items=", [type(item).__name__ for item in page.items_in_reading_order()])

    for fmt in _formats(args.demo_format):
        value = _export_object(doc, fmt)
        label = f"document.{fmt}"
        if args.write_dir:
            paths = _write_export(Path(args.write_dir), "document", fmt, value)
            print(f"wrote {label}: " + ", ".join(str(path) for path in paths))
        else:
            print(f"\n--- {label} ---")
            print(_preview(value))

    if kie_doc is not None:
        print("\n=== Synthetic KIE page structure ===")
        kie_page = kie_doc.pages[0]
        print({class_name: len(preds) for class_name, preds in kie_page.predictions.items()})
        for fmt in _formats(args.demo_format):
            value = _export_object(kie_doc, fmt)
            label = f"kie-document.{fmt}"
            if args.write_dir:
                paths = _write_export(Path(args.write_dir), "kie-document", fmt, value)
                print(f"wrote {label}: " + ", ".join(str(path) for path in paths))
            else:
                print(f"\n--- {label} ---")
                print(_preview(value))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        nargs="*",
        help="PDF/image path(s) to load with DocumentFile. Multiple paths imply image inputs unless --kind is set.",
    )
    parser.add_argument("--url", help="URL to load with DocumentFile.from_url; requires the html extra.")
    parser.add_argument(
        "--kind",
        choices=("auto", "pdf", "image", "url"),
        default="auto",
        help="How to interpret --input. Default infers pdf for a single .pdf path, otherwise image.",
    )
    parser.add_argument(
        "--demo-format",
        choices=("all", *_FORMATS),
        default="all",
        help="Synthetic export format to print or write.",
    )
    parser.add_argument("--include-kie", action="store_true", help="Also demonstrate KIEDocument export behavior.")
    parser.add_argument("--write-dir", help="Optional directory where synthetic exports are written instead of previewed.")
    parser.add_argument(
        "--skip-demo",
        action="store_true",
        help="Only validate DocumentFile input loading; do not build synthetic result objects.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.url and args.input:
        raise SystemExit("Use either --url or --input, not both.")
    if args.kind == "url" and not args.url:
        raise SystemExit("--kind url requires --url.")

    pages = _load_pages(args)
    if pages is not None:
        print("=== DocumentFile loading report ===")
        print(_json_text(_shape_report(pages)))
        if not all(item["is_uint8_hwc_rgb_candidate"] for item in _shape_report(pages)):
            print("WARNING: at least one page does not look like a uint8 HWC 3-channel predictor input.")

    if not args.skip_demo:
        _print_demo(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
