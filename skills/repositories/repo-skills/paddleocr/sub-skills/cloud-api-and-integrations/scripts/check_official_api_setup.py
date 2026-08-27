#!/usr/bin/env python3
"""Validate hosted PaddleOCR setup without sending a network request by default."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

from paddleocr._api_client.models import (
    Model,
    OCROptions,
    PaddleOCRVLOptions,
    PPStructureV3Options,
    is_ocr_model,
    is_vl_model,
)


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jsonable(item) for item in obj]
    return obj


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check PaddleOCR hosted API setup without calling the service."
    )
    parser.add_argument(
        "--model-type",
        choices=["ocr", "doc_parsing"],
        required=True,
        help="Task family to validate.",
    )
    parser.add_argument(
        "--model",
        choices=[m.value for m in Model],
        default=None,
        help="Optional model name to validate.",
    )
    parser.add_argument("--token", default=None, help="Access token override.")
    parser.add_argument("--base-url", default=None, help="Base URL override.")
    parser.add_argument("--client-platform", default=None, help="Client-Platform header value.")
    parser.add_argument("--page-ranges", default=None, help="Page range string.")
    parser.add_argument("--batch-id", default=None, help="Batch identifier.")
    parser.add_argument(
        "--require-token",
        action="store_true",
        help="Exit non-zero when the token is missing.",
    )
    parser.add_argument(
        "--require-base-url",
        action="store_true",
        help="Exit non-zero when the base URL is missing.",
    )

    # Common OCR / document-parsing toggles used by the public CLI.
    parser.add_argument("--use-doc-orientation-classify", action="store_true")
    parser.add_argument("--use-doc-unwarping", action="store_true")
    parser.add_argument("--use-textline-orientation", action="store_true")
    parser.add_argument("--use-layout-detection", action="store_true")
    parser.add_argument("--use-chart-recognition", action="store_true")
    parser.add_argument("--use-seal-recognition", action="store_true")
    parser.add_argument("--use-table-recognition", action="store_true")
    parser.add_argument("--use-formula-recognition", action="store_true")
    parser.add_argument("--use-ocr-for-image-block", action="store_true")
    parser.add_argument("--format-block-content", action="store_true")
    parser.add_argument("--prettify-markdown", action="store_true")
    parser.add_argument("--show-formula-number", action="store_true")
    parser.add_argument("--restructure-pages", action="store_true")
    parser.add_argument("--merge-tables", action="store_true")
    parser.add_argument("--relevel-titles", action="store_true")
    parser.add_argument("--return-markdown-images", action="store_true")
    parser.add_argument("--text-det-limit-side-len", type=int, default=None)
    parser.add_argument("--text-det-limit-type", default=None)
    parser.add_argument("--text-rec-score-thresh", type=float, default=None)
    parser.add_argument("--top-p", type=float, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--repetition-penalty", type=float, default=None)
    parser.add_argument("--min-pixels", type=int, default=None)
    parser.add_argument("--max-pixels", type=int, default=None)
    parser.add_argument("--max-new-tokens", type=int, default=None)
    args = parser.parse_args()

    token = args.token or os.getenv("PADDLEOCR_ACCESS_TOKEN")
    base_url = args.base_url or os.getenv("PADDLEOCR_BASE_URL")

    if args.require_token and not token:
        parser.error("PADDLEOCR_ACCESS_TOKEN is required for this check")
    if args.require_base_url and not base_url:
        parser.error("PADDLEOCR_BASE_URL is required for this check")

    model = Model(args.model) if args.model else None

    if args.model_type == "ocr":
        if model is not None and not is_ocr_model(model):
            parser.error(f"{model.value!r} is not a valid OCR model")
        options = OCROptions(
            use_doc_orientation_classify=args.use_doc_orientation_classify,
            use_doc_unwarping=args.use_doc_unwarping,
            use_textline_orientation=args.use_textline_orientation,
            text_det_limit_side_len=args.text_det_limit_side_len,
            text_det_limit_type=args.text_det_limit_type,
            text_rec_score_thresh=args.text_rec_score_thresh,
        )
    else:
        if model is None:
            model = Model.PADDLE_OCR_VL_16
        if is_vl_model(model):
            options = PaddleOCRVLOptions(
                use_doc_orientation_classify=args.use_doc_orientation_classify,
                use_doc_unwarping=args.use_doc_unwarping,
                use_layout_detection=args.use_layout_detection,
                use_chart_recognition=args.use_chart_recognition,
                use_seal_recognition=args.use_seal_recognition,
                use_ocr_for_image_block=args.use_ocr_for_image_block,
                format_block_content=args.format_block_content,
                prettify_markdown=args.prettify_markdown,
                show_formula_number=args.show_formula_number,
                restructure_pages=args.restructure_pages,
                merge_tables=args.merge_tables,
                relevel_titles=args.relevel_titles,
                return_markdown_images=args.return_markdown_images,
                top_p=args.top_p,
                temperature=args.temperature,
                repetition_penalty=args.repetition_penalty,
                min_pixels=args.min_pixels,
                max_pixels=args.max_pixels,
                max_new_tokens=args.max_new_tokens,
            )
        else:
            options = PPStructureV3Options(
                use_doc_orientation_classify=args.use_doc_orientation_classify,
                use_doc_unwarping=args.use_doc_unwarping,
                use_textline_orientation=args.use_textline_orientation,
                use_seal_recognition=args.use_seal_recognition,
                use_table_recognition=args.use_table_recognition,
                use_formula_recognition=args.use_formula_recognition,
                use_chart_recognition=args.use_chart_recognition,
                layout_threshold=None,
                layout_nms=None,
                layout_unclip_ratio=None,
                layout_merge_bboxes_mode=None,
                text_det_limit_side_len=args.text_det_limit_side_len,
                text_det_limit_type=args.text_det_limit_type,
                text_rec_score_thresh=args.text_rec_score_thresh,
                format_block_content=args.format_block_content,
                prettify_markdown=args.prettify_markdown,
                show_formula_number=args.show_formula_number,
                return_markdown_images=args.return_markdown_images,
            )

    summary = {
        "token_present": bool(token),
        "base_url": base_url,
        "client_platform": args.client_platform,
        "model_type": args.model_type,
        "model": model.value if model else None,
        "page_ranges": args.page_ranges,
        "batch_id": args.batch_id,
        "payload": options.to_payload(),
    }

    print(json.dumps(_jsonable(summary), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
