#!/usr/bin/env python3
"""Safe single-document OCR helper for installed docTR.

The script imports docTR only after argparse has handled --help, so help works
in environments where docTR is not installed yet.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

IMAGE_SUFFIXES = {".jpeg", ".jpg", ".png", ".tif", ".tiff", ".bmp"}
PDF_SUFFIXES = {".pdf"}
SUPPORTED_SUFFIXES = IMAGE_SUFFIXES | PDF_SUFFIXES


class UserError(RuntimeError):
    """An expected user-facing command failure."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run docTR OCR on one PDF or image and write json/txt/xml output.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input_path", help="Path to one input PDF or image")
    parser.add_argument("-o", "--output", default="doctr_ocr.json", help="Output file path")
    parser.add_argument("-f", "--format", choices=("json", "txt", "xml"), default="json", help="Output format")
    parser.add_argument(
        "--det-arch",
        "--detection",
        dest="det_arch",
        default="db_resnet50",
        help="Detection architecture name",
    )
    parser.add_argument(
        "--reco-arch",
        "--recognition",
        dest="reco_arch",
        default="crnn_vgg16_bn",
        help="Recognition architecture name",
    )
    parser.add_argument(
        "--pretrained",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Load trained OCR weights; --no-pretrained avoids intentional weight/backbone downloads",
    )
    parser.add_argument(
        "--assume-straight-pages",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Assume pages contain only straight text elements",
    )
    parser.add_argument("--straighten-pages", action="store_true", help="Attempt to straighten skewed pages")
    parser.add_argument(
        "--preserve-aspect-ratio",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Preserve aspect ratio during page resizing",
    )
    parser.add_argument("--symmetric-pad", action="store_true", help="Apply symmetric padding")
    parser.add_argument("--det-bs", type=int, default=2, help="Detection batch size")
    parser.add_argument("--reco-bs", type=int, default=128, help="Recognition batch size")
    parser.add_argument("--detect-orientation", action="store_true", help="Add page orientation prediction")
    parser.add_argument("--detect-language", action="store_true", help="Add language prediction")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing output files")
    return parser


def fail(message: str, exit_code: int = 1) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return exit_code


def validate_input(path: Path) -> Path:
    path = path.expanduser()
    if not path.exists():
        raise UserError(f"input file does not exist: {path}")
    if path.is_dir():
        raise UserError("doctr_quick_ocr.py expects one file; use doctr_batch_ocr.py for directories")
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        suffixes = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise UserError(f"unsupported input suffix {path.suffix!r}; supported suffixes: {suffixes}")
    return path


def prepare_output(path: Path, overwrite: bool) -> Path:
    path = path.expanduser()
    if path.exists() and path.is_dir():
        raise UserError(f"output path is a directory, expected a file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise UserError(f"output already exists: {path} (pass --overwrite to replace it)")
    return path


def write_text(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise UserError(f"output already exists: {path} (pass --overwrite to replace it)")
    path.write_text(content, encoding="utf-8")


def write_json_or_text(result: Any, output_path: Path, fmt: str, overwrite: bool) -> list[Path]:
    if fmt == "json":
        write_text(output_path, json.dumps(result.export(), indent=2, ensure_ascii=False), overwrite)
        return [output_path]
    if fmt == "txt":
        write_text(output_path, result.render(), overwrite)
        return [output_path]
    raise AssertionError(f"unexpected non-text format: {fmt}")


def write_xml(result: Any, output_path: Path, overwrite: bool) -> list[Path]:
    if not hasattr(result, "export_as_xml"):
        raise UserError("the OCR result object does not expose export_as_xml()")
    xml_pages = result.export_as_xml()
    if not xml_pages:
        raise UserError("export_as_xml() returned no pages")

    outputs: list[Path] = []
    stem_path = output_path.with_suffix("")
    for index, (_xml_bytes, xml_tree) in enumerate(xml_pages, start=1):
        page_path = output_path if len(xml_pages) == 1 else stem_path.with_name(f"{stem_path.name}_page{index}").with_suffix(".xml")
        if page_path.exists() and not overwrite:
            raise UserError(f"output already exists: {page_path} (pass --overwrite to replace it)")
        page_path.parent.mkdir(parents=True, exist_ok=True)
        xml_tree.write(page_path, encoding="utf-8", xml_declaration=True)
        outputs.append(page_path)
    return outputs


def load_document(DocumentFile: Any, input_path: Path) -> Any:
    try:
        if input_path.suffix.lower() in PDF_SUFFIXES:
            return DocumentFile.from_pdf(str(input_path))
        return DocumentFile.from_images(str(input_path))
    except FileNotFoundError as exc:
        raise UserError(f"input file not found: {input_path}") from exc
    except ValueError as exc:
        raise UserError(f"input could not be read as a valid image or PDF: {input_path}; {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - report user-facing loader failures cleanly
        raise UserError(f"failed to load input {input_path}: {exc}") from exc


def run(args: argparse.Namespace) -> int:
    input_path = validate_input(Path(args.input_path))
    output_path = prepare_output(Path(args.output), args.overwrite)

    try:
        from doctr.io import DocumentFile
        from doctr.models import ocr_predictor
    except Exception as exc:  # noqa: BLE001 - import diagnostics for CLI users
        raise UserError(
            "could not import docTR OCR APIs; install python-doctr and its runtime dependencies in this Python environment"
        ) from exc

    try:
        model = ocr_predictor(
            det_arch=args.det_arch,
            reco_arch=args.reco_arch,
            pretrained=args.pretrained,
            pretrained_backbone=args.pretrained,
            assume_straight_pages=args.assume_straight_pages,
            preserve_aspect_ratio=args.preserve_aspect_ratio,
            symmetric_pad=args.symmetric_pad,
            detect_orientation=args.detect_orientation,
            straighten_pages=args.straighten_pages,
            detect_language=args.detect_language,
            det_bs=args.det_bs,
            reco_bs=args.reco_bs,
        )
    except Exception as exc:  # noqa: BLE001
        hint = ""
        if args.pretrained:
            hint = " If this happened while loading weights, retry with --no-pretrained to isolate cache/network issues."
        raise UserError(f"failed to create OCR predictor: {exc}.{hint}") from exc

    doc = load_document(DocumentFile, input_path)

    try:
        result = model(doc)
    except Exception as exc:  # noqa: BLE001
        raise UserError(f"OCR inference failed: {exc}") from exc

    try:
        if args.format == "xml":
            outputs = write_xml(result, output_path, args.overwrite)
        else:
            outputs = write_json_or_text(result, output_path, args.format, args.overwrite)
    except OSError as exc:
        raise UserError(f"failed to write output: {exc}") from exc

    print(
        json.dumps(
            {
                "ok": True,
                "input": str(input_path),
                "outputs": [str(path) for path in outputs],
                "format": args.format,
                "pretrained": args.pretrained,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except UserError as exc:
        return fail(str(exc))
    except KeyboardInterrupt:
        return fail("interrupted", 130)


if __name__ == "__main__":
    raise SystemExit(main())
