#!/usr/bin/env python3
"""Smoke-test Sparrow OCR response post-processing without PaddleOCR.

This script uses a small Paddle-style JSON fixture and a self-contained copy of
Sparrow OCR's response-shaping logic. It intentionally does not import
paddleocr, paddlepaddle, FastAPI, or the Sparrow source package, so it is safe
for quick bbox/response contract checks before model weights are available.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List


PADDLE_STYLE_FIXTURE: Dict[str, Any] = {
    "res": {
        "rec_texts": [
            "Invoice Number: 12345",
            "low confidence noise",
            "  Total: $42.50  ",
            "   ",
        ],
        "rec_scores": [0.95, 0.29, 0.7749, 0.88],
        "rec_boxes": [
            [80.2, 40.9, 300.7, 70.4],
            [1, 1, 2, 2],
            [120, 260, 300, 292],
            [5, 5, 9, 9],
        ],
    }
}


def extract_text_from_json(result_json: Dict[str, Any], include_bbox: bool = False) -> Dict[str, Any]:
    """Extract simple text and optional bbox regions from Paddle-style JSON.

    Mirrors the Sparrow OCR post-processing contract: read OCR payload from
    result_json["res"], keep non-empty text with score > 0.3, join kept text
    with spaces, average all rec_scores, and emit bbox dictionaries when
    requested.
    """

    ocr_data = result_json.get("res", {})
    rec_texts: List[str] = ocr_data.get("rec_texts", [])
    rec_scores: List[float] = ocr_data.get("rec_scores", [])
    rec_boxes: List[List[float]] = ocr_data.get("rec_boxes", []) if include_bbox else []

    clean_texts: List[str] = []
    text_regions: List[Dict[str, Any]] = []

    for i, (text, score) in enumerate(zip(rec_texts, rec_scores)):
        if text and text.strip() and score > 0.3:
            clean_text = text.strip()
            clean_texts.append(clean_text)

            if include_bbox and i < len(rec_boxes):
                box = rec_boxes[i]
                if len(box) >= 4:
                    x1, y1, x2, y2 = box[:4]
                    text_regions.append(
                        {
                            "text": clean_text,
                            "bbox": {
                                "x1": int(x1),
                                "y1": int(y1),
                                "x2": int(x2),
                                "y2": int(y2),
                                "width": int(x2 - x1),
                                "height": int(y2 - y1),
                            },
                            "confidence": round(float(score), 3),
                        }
                    )

    simple_output: Dict[str, Any] = {
        "extracted_text": " ".join(clean_texts),
        "text_count": len(clean_texts),
        "avg_confidence": round(sum(rec_scores) / len(rec_scores), 2) if rec_scores else 0,
    }

    if include_bbox:
        simple_output["text_regions"] = text_regions

    return simple_output


def build_endpoint_like_response(include_bbox: bool = True) -> List[Dict[str, Any]]:
    """Create a minimal endpoint-like list response from the fixture."""

    page = extract_text_from_json(PADDLE_STYLE_FIXTURE, include_bbox=include_bbox)
    page["processing_info"] = {
        "processing_time_seconds": 0.01,
        "experimental_features_used": False,
        "worker_pid": 0,
    }
    return [page]


def assert_contract() -> Dict[str, Any]:
    """Assert the expected OCR response contract and return the bbox result."""

    no_bbox = extract_text_from_json(PADDLE_STYLE_FIXTURE, include_bbox=False)
    assert no_bbox == {
        "extracted_text": "Invoice Number: 12345 Total: $42.50",
        "text_count": 2,
        "avg_confidence": 0.72,
    }, no_bbox
    assert "text_regions" not in no_bbox

    with_bbox = extract_text_from_json(PADDLE_STYLE_FIXTURE, include_bbox=True)
    assert with_bbox["extracted_text"] == "Invoice Number: 12345 Total: $42.50"
    assert with_bbox["text_count"] == 2
    assert with_bbox["avg_confidence"] == 0.72
    assert len(with_bbox["text_regions"]) == 2

    first_region = with_bbox["text_regions"][0]
    assert first_region == {
        "text": "Invoice Number: 12345",
        "bbox": {"x1": 80, "y1": 40, "x2": 300, "y2": 70, "width": 220, "height": 29},
        "confidence": 0.95,
    }, first_region

    second_region = with_bbox["text_regions"][1]
    assert second_region["bbox"] == {"x1": 120, "y1": 260, "x2": 300, "y2": 292, "width": 180, "height": 32}
    assert second_region["confidence"] == 0.775

    endpoint_like = build_endpoint_like_response(include_bbox=True)
    assert isinstance(endpoint_like, list) and endpoint_like
    assert "processing_info" in endpoint_like[0]
    assert endpoint_like[0]["processing_info"]["experimental_features_used"] is False

    return with_bbox


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate Sparrow OCR Paddle-style JSON post-processing without importing PaddleOCR."
    )
    parser.add_argument(
        "--dump-json",
        action="store_true",
        help="Print the endpoint-like fixture response after assertions pass.",
    )
    parser.add_argument(
        "--no-bbox",
        action="store_true",
        help="Dump the no-bbox response shape instead of the endpoint-like bbox shape.",
    )
    args = parser.parse_args()

    assert_contract()

    if args.dump_json:
        payload: Any
        if args.no_bbox:
            payload = extract_text_from_json(PADDLE_STYLE_FIXTURE, include_bbox=False)
        else:
            payload = build_endpoint_like_response(include_bbox=True)
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("OK: Sparrow OCR response post-processing fixture passed without PaddleOCR imports.")


if __name__ == "__main__":
    main()
