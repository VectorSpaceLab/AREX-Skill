#!/usr/bin/env python3
"""Guarded Marker conversion template.

This template runs conversion only when given an existing input path. It is safe to
import and safe to inspect with --help; model initialization happens inside main.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


CONVERTERS = {
    "pdf": "marker.converters.pdf.PdfConverter",
    "table": "marker.converters.table.TableConverter",
    "ocr": "marker.converters.ocr.OCRConverter",
}


RENDERED_OUTPUT_FORMATS = {"markdown", "json", "html", "chunks"}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert one document with Marker's Python API.")
    parser.add_argument("input_path", help="Existing document path to convert.")
    parser.add_argument("--output-dir", default="marker_output", help="Directory where output files are written.")
    parser.add_argument("--output-format", choices=sorted(RENDERED_OUTPUT_FORMATS), default="markdown")
    parser.add_argument("--converter", choices=sorted(CONVERTERS), default="pdf", help="Conversion pipeline to use.")
    parser.add_argument("--page-range", help="Zero-based page range such as '0,5-10'.")
    parser.add_argument("--disable-image-extraction", action="store_true", help="Do not save extracted images for Markdown/HTML output.")
    parser.add_argument("--disable-multiprocessing", action="store_true", help="Use single-worker PDF text extraction.")
    parser.add_argument("--force-layout-block", help="Example for table conversion: Table.")
    parser.add_argument("--force-ocr", action="store_true", help="Force OCR for all pages.")
    parser.add_argument("--strip-existing-ocr", action="store_true", help="Strip existing OCR text before OCR.")
    parser.add_argument("--keep-chars", action="store_true", help="Keep OCR character boxes where supported.")
    parser.add_argument("--torch-device", choices=("cpu", "cuda", "mps"), help="Set TORCH_DEVICE before importing Marker.")
    return parser.parse_args(argv)


def import_converter(class_path: str):
    module_name, class_name = class_path.rsplit(".", 1)
    module = __import__(module_name, fromlist=[class_name])
    return getattr(module, class_name)


def build_options(args: argparse.Namespace) -> dict[str, object]:
    options: dict[str, object] = {"output_format": args.output_format}
    if args.page_range:
        options["page_range"] = args.page_range
    if args.disable_image_extraction:
        options["disable_image_extraction"] = True
    if args.disable_multiprocessing:
        options["disable_multiprocessing"] = True
    if args.force_layout_block:
        options["force_layout_block"] = args.force_layout_block
    if args.force_ocr:
        options["force_ocr"] = True
    if args.strip_existing_ocr:
        options["strip_existing_ocr"] = True
    if args.keep_chars:
        options["keep_chars"] = True
    return options


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    input_path = Path(args.input_path).expanduser()
    if not input_path.is_file():
        print(f"Input path is not a file: {input_path}", file=sys.stderr)
        return 2

    if args.torch_device:
        os.environ["TORCH_DEVICE"] = args.torch_device

    from marker.config.parser import ConfigParser
    from marker.models import create_model_dict
    from marker.output import save_output, text_from_rendered

    converter_cls = import_converter(CONVERTERS[args.converter])
    config_parser = ConfigParser(build_options(args))
    converter = converter_cls(
        artifact_dict=create_model_dict(),
        config=config_parser.generate_config_dict(),
        processor_list=config_parser.get_processors(),
        renderer=None if args.converter == "ocr" else config_parser.get_renderer(),
        llm_service=config_parser.get_llm_service(),
    )

    rendered = converter(str(input_path))
    text, extension, images = text_from_rendered(rendered)
    output_dir = Path(args.output_dir).expanduser() / input_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    save_output(rendered, str(output_dir), input_path.stem)

    print(f"Wrote {extension} output under {output_dir}")
    print(f"Extracted images: {len(images)}")
    if getattr(converter, "page_count", None) is not None:
        print(f"Converted pages: {converter.page_count}")
    print(f"Text characters: {len(text)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
