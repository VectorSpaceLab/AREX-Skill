#!/usr/bin/env python3
"""Run the public PaddleOCR pipeline with safe, explicit arguments.

This helper stays on the public package surface and does not depend on the
original repository checkout.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paddleocr import PaddleOCR


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the PaddleOCR pipeline.")
    parser.add_argument("input", help="Input image, PDF, or URL.")
    parser.add_argument("--lang", default=None, help="OCR language code.")
    parser.add_argument("--ocr-version", default=None, help="OCR family, e.g. PP-OCRv6.")
    parser.add_argument("--model-name", default=None, help="Explicit model name.")
    parser.add_argument("--model-dir", default=None, help="Path to a local model directory.")
    parser.add_argument("--device", default=None, help="Inference device.")
    parser.add_argument("--engine", default=None, help="Inference engine.")
    parser.add_argument("--output", default=None, help="Optional JSON output path.")
    args = parser.parse_args()

    ocr = PaddleOCR(
        lang=args.lang,
        ocr_version=args.ocr_version,
        model_name=args.model_name,
        model_dir=args.model_dir,
        device=args.device,
        engine=args.engine,
    )

    try:
        result = ocr.predict(args.input)
    finally:
        ocr.close()

    payload = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
        print(str(output_path))
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
