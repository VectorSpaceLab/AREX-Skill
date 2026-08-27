#!/usr/bin/env python3
"""Self-contained Presidio image OCR smoke check.

The default smoke path creates an in-memory image, verifies that Tesseract is
available, runs OCR, uses a NoOpNlpEngine plus a deny-list recognizer to avoid
model downloads, and asserts that at least one image bbox is redacted.

Use --use-default-analyzer to exercise Presidio's default AnalyzerEngine path;
that mode needs the documented default spaCy model in the active environment.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_TEXT = "JOHN SMITH\nPHONE 555-123-4567"
DEFAULT_EXPECTED_TOKEN = "JOHN"
DEFAULT_MIN_BBOXES = 1

MISSING_MODEL_HINTS = (
    "en_core_web_lg",
    "can't find model",
    "cannot find model",
    "no module named 'en_core_web_lg'",
    "spacy",
    "download",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-check Presidio image OCR/redaction without reading any source "
            "checkout files. By default this uses a no-download custom analyzer."
        )
    )
    parser.add_argument(
        "--import-only",
        action="store_true",
        help="Only import required Python packages/classes; do not check Tesseract or run OCR.",
    )
    parser.add_argument(
        "--use-default-analyzer",
        action="store_true",
        help=(
            "Use ImageRedactorEngine() with the default AnalyzerEngine. This also "
            "checks that the default analyzer model is installed."
        ),
    )
    parser.add_argument(
        "--text",
        default=DEFAULT_TEXT,
        help="Text to draw into the generated in-memory image.",
    )
    parser.add_argument(
        "--expected-token",
        default=DEFAULT_EXPECTED_TOKEN,
        help="Token expected to appear in raw OCR output before redaction is attempted.",
    )
    parser.add_argument(
        "--min-bboxes",
        type=int,
        default=DEFAULT_MIN_BBOXES,
        help="Minimum number of redaction bboxes expected for a passing smoke run.",
    )
    parser.add_argument(
        "--ocr-threshold",
        type=float,
        default=None,
        help="Optional OCR confidence threshold passed as ocr_kwargs['ocr_threshold'].",
    )
    parser.add_argument(
        "--tesseract-config",
        default="--psm 6",
        help="Tesseract config string forwarded to pytesseract image_to_data.",
    )
    parser.add_argument(
        "--fill",
        default="255,0,0",
        help="Redaction fill as an int like '255' or RGB tuple text like '255,0,0'.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path where the redacted generated image should be written.",
    )
    return parser


def load_runtime_modules():
    """Import runtime dependencies lazily so --help works without packages."""
    modules = {}
    for module_name in [
        "PIL.Image",
        "PIL.ImageDraw",
        "PIL.ImageFont",
        "pytesseract",
        "presidio_analyzer",
        "presidio_analyzer.nlp_engine",
        "presidio_analyzer.recognizer_registry",
        "presidio_image_redactor",
        "presidio_image_redactor.entities",
    ]:
        modules[module_name] = importlib.import_module(module_name)
    return modules


def validate_symbols(modules) -> None:
    """Fail early if expected public classes moved or are missing."""
    required = [
        ("presidio_image_redactor", "DocumentIntelligenceOCR"),
        ("presidio_image_redactor", "DicomImagePiiVerifyEngine"),
        ("presidio_image_redactor", "DicomImageRedactorEngine"),
        ("presidio_image_redactor", "ImageAnalyzerEngine"),
        ("presidio_image_redactor", "ImagePiiVerifyEngine"),
        ("presidio_image_redactor", "ImageRedactorEngine"),
        ("presidio_image_redactor", "TesseractOCR"),
        ("presidio_image_redactor.entities", "ImageRecognizerResult"),
        ("presidio_analyzer", "AnalyzerEngine"),
        ("presidio_analyzer", "PatternRecognizer"),
        ("presidio_analyzer.nlp_engine", "NoOpNlpEngine"),
        ("presidio_analyzer.recognizer_registry", "RecognizerRegistry"),
    ]
    missing = [f"{module}.{symbol}" for module, symbol in required if not hasattr(modules[module], symbol)]
    if missing:
        raise ImportError("Missing expected symbol(s): " + ", ".join(missing))



def print_import_guidance(exc: BaseException) -> int:
    print("Presidio image OCR smoke import failed.", file=sys.stderr)
    print(f"Original error: {exc}", file=sys.stderr)
    print(
        "Install the image package in the active environment, for example: "
        "python -m pip install presidio-image-redactor",
        file=sys.stderr,
    )
    print(
        "If the default analyzer path is used, also install the documented spaCy "
        "model: python -m spacy download en_core_web_lg",
        file=sys.stderr,
    )
    return 1


def check_tesseract(pytesseract_module) -> str:
    try:
        version = pytesseract_module.get_tesseract_version()
    except Exception as exc:  # pragma: no cover - depends on host binary
        print("Tesseract OCR binary was not found or is not runnable.", file=sys.stderr)
        print(f"Original error: {exc}", file=sys.stderr)
        print(
            "Install the Tesseract OCR system binary, ensure 'tesseract' is on PATH, "
            "or set pytesseract.pytesseract.tesseract_cmd in your application before "
            "running Presidio TesseractOCR.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return str(version)


def parse_fill(fill_text: str):
    if "," not in fill_text:
        return int(fill_text)
    parts = [int(part.strip()) for part in fill_text.split(",")]
    if len(parts) != 3:
        raise ValueError("RGB fill must have exactly three comma-separated integers")
    if any(part < 0 or part > 255 for part in parts):
        raise ValueError("Fill values must be in the 0..255 range")
    return tuple(parts)


def create_image(text: str, pil_modules):
    Image = pil_modules["PIL.Image"]
    ImageDraw = pil_modules["PIL.ImageDraw"]
    ImageFont = pil_modules["PIL.ImageFont"]

    image = Image.new("RGB", (900, 260), color="white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", size=48)
    except Exception:
        font = ImageFont.load_default()
    draw.multiline_text((40, 45), text, fill="black", font=font, spacing=18)
    return image


def non_empty_words(ocr_result: dict) -> list[str]:
    return [word for word in ocr_result.get("text", []) if word and not word.isspace()]


def looks_like_missing_default_model(exc: BaseException) -> bool:
    message = str(exc).lower()
    return any(hint.lower() in message for hint in MISSING_MODEL_HINTS)


def build_no_download_redactor(modules):
    presidio_analyzer = modules["presidio_analyzer"]
    nlp_engine_module = modules["presidio_analyzer.nlp_engine"]
    registry_module = modules["presidio_analyzer.recognizer_registry"]
    image_module = modules["presidio_image_redactor"]

    recognizer = presidio_analyzer.PatternRecognizer(
        supported_entity="PERSON",
        deny_list=["JOHN", "SMITH", "JOHN SMITH"],
        supported_language="en",
    )
    registry = registry_module.RecognizerRegistry(
        recognizers=[recognizer],
        supported_languages=["en"],
    )
    nlp_engine = nlp_engine_module.NoOpNlpEngine(
        models=[{"lang_code": "en", "model_name": "no_op"}]
    )
    analyzer = presidio_analyzer.AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["en"],
    )
    image_analyzer = image_module.ImageAnalyzerEngine(analyzer_engine=analyzer)
    return image_module.ImageRedactorEngine(image_analyzer_engine=image_analyzer)


def run_smoke(args: argparse.Namespace, modules) -> int:
    image_module = modules["presidio_image_redactor"]
    pytesseract_module = modules["pytesseract"]

    version = check_tesseract(pytesseract_module)
    print(f"Tesseract OCR available: {version}")

    image = create_image(args.text, modules)
    ocr_kwargs = {"config": args.tesseract_config}
    if args.ocr_threshold is not None:
        ocr_kwargs["ocr_threshold"] = args.ocr_threshold

    raw_ocr_kwargs = {key: value for key, value in ocr_kwargs.items() if key != "ocr_threshold"}
    raw = image_module.TesseractOCR().perform_ocr(image, **raw_ocr_kwargs)
    words = non_empty_words(raw)
    print("OCR words:", words)

    expected_upper = args.expected_token.upper()
    if args.expected_token and not any(expected_upper in word.upper() for word in words):
        print(
            "OCR completed but the expected token was not present. "
            "If raw words are empty or garbled, adjust image quality, Tesseract language "
            "data, --tesseract-config, or --ocr-threshold before tuning analyzer kwargs.",
            file=sys.stderr,
        )
        return 4

    try:
        redactor = image_module.ImageRedactorEngine() if args.use_default_analyzer else build_no_download_redactor(modules)
        redacted, bboxes = redactor.redact_and_return_bbox(
            image,
            fill=parse_fill(args.fill),
            ocr_kwargs=ocr_kwargs,
            entities=["PERSON"],
            score_threshold=0.0,
        )
    except Exception as exc:  # pragma: no cover - depends on optional model state
        if args.use_default_analyzer and looks_like_missing_default_model(exc):
            print("Default AnalyzerEngine model appears to be missing.", file=sys.stderr)
            print(f"Original error: {exc}", file=sys.stderr)
            print(
                "Install the documented default model with: "
                "python -m spacy download en_core_web_lg. "
                "For no-download smoke checks, omit --use-default-analyzer so the script "
                "uses NoOpNlpEngine plus a deny-list recognizer.",
                file=sys.stderr,
            )
            return 3
        raise

    print(f"Detected {len(bboxes)} bbox(es)")
    for bbox in bboxes:
        print(str(bbox))

    if len(bboxes) < args.min_bboxes:
        print(
            "Redaction produced fewer bboxes than expected. If OCR words were present, "
            "check entities, language, score_threshold, allow_list, and custom recognizers.",
            file=sys.stderr,
        )
        return 4

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        redacted.save(args.output)
        print(f"Wrote redacted generated image to {args.output}")

    print("Presidio image OCR smoke passed")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        modules = load_runtime_modules()
        validate_symbols(modules)
    except Exception as exc:
        return print_import_guidance(exc)

    if args.import_only:
        print("Imports passed for Presidio image redactor smoke dependencies and expected public classes")
        return 0

    return run_smoke(args, modules)


if __name__ == "__main__":
    raise SystemExit(main())
