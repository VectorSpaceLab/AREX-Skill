#!/usr/bin/env python3
"""Run the public PaddleOCR document-parsing pipelines with safe defaults."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paddleocr import PPStructureV3, PaddleOCRVL


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a PaddleOCR document parser.")
    parser.add_argument("input", help="Input image, PDF, or URL.")
    parser.add_argument(
        "--mode",
        choices=["pp-structurev3", "paddleocr-vl"],
        default="pp-structurev3",
        help="Document parsing family to run.",
    )
    parser.add_argument("--device", default=None, help="Inference device.")
    parser.add_argument("--engine", default=None, help="Inference engine.")
    parser.add_argument(
        "--pipeline-version",
        default="v1.6",
        help="PaddleOCR-VL pipeline version.",
    )
    parser.add_argument(
        "--vl-backend",
        default=None,
        help="Optional VL backend for PaddleOCR-VL.",
    )
    parser.add_argument("--output", default=None, help="Optional JSON output path.")
    args = parser.parse_args()

    if args.mode == "pp-structurev3":
        parser_obj = PPStructureV3(device=args.device, engine=args.engine)
        try:
            result = parser_obj.predict(args.input)
        finally:
            parser_obj.close()
    else:
        parser_obj = PaddleOCRVL(
            pipeline_version=args.pipeline_version,
            vl_rec_backend=args.vl_backend,
            device=args.device,
            engine=args.engine,
        )
        try:
            result = parser_obj.predict(args.input)
        finally:
            parser_obj.close()

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
