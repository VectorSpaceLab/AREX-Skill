#!/usr/bin/env python3
"""Safe batch OCR helper for installed docTR.

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
        description="Run docTR OCR over one file or a directory and write txt/json/xml outputs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input_path", help="Path to a supported file or directory")
    parser.add_argument("--output-dir", default="doctr_ocr_output", help="Directory for result files and manifest.json")
    parser.add_argument("-f", "--format", choices=("txt", "json", "xml"), default="txt", help="Output format")
    parser.add_argument("--detection", default="fast_base", help="Detection model factory name")
    parser.add_argument("--bin-thresh", type=float, default=0.3, help="Binarization threshold for compatible detection models")
    parser.add_argument("--box-thresh", type=float, default=0.1, help="Box threshold for compatible detection models")
    parser.add_argument("--recognition", default="crnn_vgg16_bn", help="Recognition architecture name")
    parser.add_argument(
        "--pretrained",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Load trained OCR weights; --no-pretrained avoids intentional weight/backbone downloads",
    )
    parser.add_argument("--recursive", action="store_true", help="Recurse into subdirectories when input_path is a directory")
    parser.add_argument("--max-files", type=int, default=0, help="Maximum files to process; 0 means no limit")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing output files")
    parser.add_argument("--stop-on-error", action="store_true", help="Stop at the first per-file processing error")
    return parser


def fail(message: str, exit_code: int = 1) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return exit_code


def is_supported_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES


def discover_files(input_path: Path, recursive: bool, max_files: int) -> tuple[Path, list[Path]]:
    input_path = input_path.expanduser()
    if max_files < 0:
        raise UserError("--max-files must be >= 0")
    if not input_path.exists():
        raise UserError(f"input path does not exist: {input_path}")
    if input_path.is_file():
        if not is_supported_file(input_path):
            suffixes = ", ".join(sorted(SUPPORTED_SUFFIXES))
            raise UserError(f"unsupported input suffix {input_path.suffix!r}; supported suffixes: {suffixes}")
        return input_path.parent, [input_path]
    if not input_path.is_dir():
        raise UserError(f"input path is neither a file nor a directory: {input_path}")

    iterator = input_path.rglob("*") if recursive else input_path.iterdir()
    files = sorted(path for path in iterator if is_supported_file(path))
    if max_files:
        files = files[:max_files]
    if not files:
        raise UserError("no supported PDF/image files found")
    return input_path, files


def safe_output_stem(root: Path, file_path: Path) -> str:
    try:
        rel = file_path.relative_to(root)
    except ValueError:
        rel = file_path.name  # type: ignore[assignment]
    if isinstance(rel, Path):
        parts = rel.with_suffix("").parts
    else:
        parts = (Path(rel).stem,)
    cleaned = [part.replace(" ", "_") for part in parts if part not in (".", "")]
    return "__".join(cleaned) or file_path.stem


def load_document(DocumentFile: Any, file_path: Path) -> Any:
    try:
        if file_path.suffix.lower() in PDF_SUFFIXES:
            return DocumentFile.from_pdf(str(file_path))
        return DocumentFile.from_images([str(file_path)])
    except FileNotFoundError as exc:
        raise UserError(f"input file not found: {file_path}") from exc
    except ValueError as exc:
        raise UserError(f"input could not be read as a valid image or PDF: {file_path}; {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        raise UserError(f"failed to load input {file_path}: {exc}") from exc


def check_write_target(path: Path, overwrite: bool) -> None:
    if path.exists() and path.is_dir():
        raise UserError(f"output path is a directory: {path}")
    if path.exists() and not overwrite:
        raise UserError(f"output already exists: {path} (pass --overwrite to replace it)")


def write_result(result: Any, output_dir: Path, stem: str, fmt: str, overwrite: bool) -> list[Path]:
    outputs: list[Path] = []
    if fmt == "json":
        path = output_dir / f"{stem}.json"
        check_write_target(path, overwrite)
        path.write_text(json.dumps(result.export(), indent=2, ensure_ascii=False), encoding="utf-8")
        return [path]
    if fmt == "txt":
        path = output_dir / f"{stem}.txt"
        check_write_target(path, overwrite)
        path.write_text(result.render(), encoding="utf-8")
        return [path]
    if fmt != "xml":
        raise AssertionError(f"unexpected format: {fmt}")

    if not hasattr(result, "export_as_xml"):
        raise UserError("the OCR result object does not expose export_as_xml()")
    xml_pages = result.export_as_xml()
    if not xml_pages:
        raise UserError("export_as_xml() returned no pages")
    for index, (_xml_bytes, xml_tree) in enumerate(xml_pages, start=1):
        suffix = "xml" if len(xml_pages) == 1 else f"page{index}.xml"
        path = output_dir / f"{stem}.{suffix}"
        check_write_target(path, overwrite)
        xml_tree.write(path, encoding="utf-8", xml_declaration=True)
        outputs.append(path)
    return outputs


def build_model(args: argparse.Namespace) -> Any:
    try:
        from doctr.models import detection, ocr_predictor
    except Exception as exc:  # noqa: BLE001
        raise UserError(
            "could not import docTR model APIs; install python-doctr and its runtime dependencies in this Python environment"
        ) from exc

    try:
        detection_factory = getattr(detection, args.detection)
    except AttributeError as exc:
        raise UserError(f"unknown detection model factory: {args.detection}") from exc

    try:
        detection_model = detection_factory(
            pretrained=args.pretrained,
            bin_thresh=args.bin_thresh,
            box_thresh=args.box_thresh,
        )
    except TypeError:
        detection_model = detection_factory(pretrained=args.pretrained)
    except Exception as exc:  # noqa: BLE001
        hint = ""
        if args.pretrained:
            hint = " Retry with --no-pretrained to isolate cache/network issues."
        raise UserError(f"failed to create detection model {args.detection!r}: {exc}.{hint}") from exc

    try:
        return ocr_predictor(
            detection_model,
            args.recognition,
            pretrained=args.pretrained,
            pretrained_backbone=args.pretrained,
        )
    except Exception as exc:  # noqa: BLE001
        hint = ""
        if args.pretrained:
            hint = " Retry with --no-pretrained to isolate cache/network issues."
        raise UserError(f"failed to create OCR predictor: {exc}.{hint}") from exc


def process_one(model: Any, DocumentFile: Any, root: Path, file_path: Path, output_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    item: dict[str, Any] = {"input": str(file_path), "status": "pending", "outputs": [], "error": None}
    try:
        doc = load_document(DocumentFile, file_path)
        result = model(doc)
        outputs = write_result(result, output_dir, safe_output_stem(root, file_path), args.format, args.overwrite)
        item.update({"status": "ok", "outputs": [str(path) for path in outputs]})
    except Exception as exc:  # noqa: BLE001 - per-file manifest error capture
        item.update({"status": "error", "error": str(exc)})
        if args.stop_on_error:
            raise
    return item


def run(args: argparse.Namespace) -> int:
    root, files = discover_files(Path(args.input_path), args.recursive, args.max_files)
    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    if not output_dir.is_dir():
        raise UserError(f"output path is not a directory: {output_dir}")

    manifest_path = output_dir / "manifest.json"
    if manifest_path.exists() and not args.overwrite:
        raise UserError(f"manifest already exists: {manifest_path} (pass --overwrite to replace it)")

    try:
        from doctr.io import DocumentFile
    except Exception as exc:  # noqa: BLE001
        raise UserError(
            "could not import docTR document APIs; install python-doctr and its runtime dependencies in this Python environment"
        ) from exc

    model = build_model(args)
    manifest: dict[str, Any] = {
        "ok": True,
        "input": str(Path(args.input_path).expanduser()),
        "output_dir": str(output_dir),
        "format": args.format,
        "pretrained": args.pretrained,
        "count": len(files),
        "items": [],
    }

    for index, file_path in enumerate(files, start=1):
        print(f"[{index}/{len(files)}] {file_path}", file=sys.stderr)
        try:
            item = process_one(model, DocumentFile, root, file_path, output_dir, args)
        except Exception as exc:  # noqa: BLE001
            item = {"input": str(file_path), "status": "error", "outputs": [], "error": str(exc)}
            manifest["items"].append(item)
            manifest["ok"] = False
            break
        manifest["items"].append(item)
        if item["status"] != "ok":
            manifest["ok"] = False

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": manifest["ok"], "manifest": str(manifest_path), "count": len(manifest["items"])}))
    return 0 if manifest["ok"] else 1


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
