#!/usr/bin/env python3
"""Smoke-check docTR OCR/KIE predictor construction and optional inference.

Defaults avoid pretrained task/backbone downloads. With random weights, successful
inference proves only API wiring and result schema, not OCR quality.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("ocr", "kie"), default="ocr", help="predictor factory to exercise")
    parser.add_argument("--det-arch", default="fast_base", help="detection architecture name")
    parser.add_argument("--reco-arch", default="crnn_vgg16_bn", help="recognition architecture name")
    parser.add_argument("--pretrained", action="store_true", help="load pretrained detector/recognizer weights")
    parser.add_argument(
        "--pretrained-backbone",
        action="store_true",
        help="allow pretrained backbones; may download weights on first use",
    )
    parser.add_argument("--pages", type=int, default=1, help="number of synthetic pages for forward smoke")
    parser.add_argument("--height", type=int, default=96, help="synthetic page height")
    parser.add_argument("--width", type=int, default=128, help="synthetic page width")
    parser.add_argument("--det-bs", type=int, default=2, help="detection/layout batch size")
    parser.add_argument("--reco-bs", type=int, default=128, help="recognition crop batch size")
    parser.add_argument(
        "--no-assume-straight-pages",
        dest="assume_straight_pages",
        action="store_false",
        help="exercise rotated-box/non-straight predictor path",
    )
    parser.set_defaults(assume_straight_pages=True)
    parser.add_argument("--export-as-straight-boxes", action="store_true", help="force straight exported boxes")
    parser.add_argument("--straighten-pages", action="store_true", help="exercise page straightening path")
    parser.add_argument("--preserve-original-coords", action="store_true", help="remap straightened outputs to original coords")
    parser.add_argument("--detect-orientation", action="store_true", help="attach page orientation metadata")
    parser.add_argument("--detect-language", action="store_true", help="attach language metadata from recognized text")
    parser.add_argument("--detect-layout", action="store_true", help="attach layout regions")
    parser.add_argument("--detect-tables", action="store_true", help="OCR only: attach structured page tables")
    parser.add_argument(
        "--layout-arch",
        default="lw_detr_s",
        help="layout architecture when layout/table detection is enabled",
    )
    parser.add_argument(
        "--ignore-region",
        action="append",
        default=[],
        help="layout class to mask before text detection; repeat for multiple classes",
    )
    parser.add_argument(
        "--enable-orientation-helpers",
        action="store_true",
        help="allow pretrained page/crop orientation helper models in non-straight/straightening/orientation modes",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "mps", "auto"),
        default="cpu",
        help="move predictor to this torch device before optional forward",
    )
    parser.add_argument("--skip-forward", action="store_true", help="construct and move predictor but do not run inference")
    return parser


def _select_device(name: str):
    import torch

    if name == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    if name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false")
    if name == "mps" and not (getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available()):
        raise RuntimeError("MPS was requested but torch.backends.mps.is_available() is false")
    return torch.device(name)


def _make_pages(count: int, height: int, width: int):
    import numpy as np

    if count < 1:
        raise ValueError("--pages must be >= 1")
    if height < 8 or width < 8:
        raise ValueError("--height and --width must be >= 8")
    pages = []
    for idx in range(count):
        page = np.full((height, width, 3), 255, dtype=np.uint8)
        # Draw a small deterministic dark rectangle so detector preprocessing sees non-empty content.
        y0 = min(height - 2, 8 + idx)
        x0 = min(width - 2, 8 + idx)
        page[y0 : min(height, y0 + 8), x0 : min(width, x0 + 32)] = 0
        pages.append(page)
    return pages


def _build_predictor(args: argparse.Namespace):
    from doctr.models import kie_predictor, ocr_predictor

    kwargs: dict[str, Any] = {
        "det_arch": args.det_arch,
        "reco_arch": args.reco_arch,
        "pretrained": args.pretrained,
        "pretrained_backbone": args.pretrained_backbone,
        "assume_straight_pages": args.assume_straight_pages,
        "export_as_straight_boxes": args.export_as_straight_boxes,
        "straighten_pages": args.straighten_pages,
        "preserve_original_coords": args.preserve_original_coords,
        "detect_orientation": args.detect_orientation,
        "detect_language": args.detect_language,
        "detect_layout": args.detect_layout,
        "layout_arch": args.layout_arch,
        "det_bs": args.det_bs,
        "reco_bs": args.reco_bs,
    }
    if args.ignore_region:
        kwargs["ignore_regions"] = args.ignore_region

    orientation_path = (not args.assume_straight_pages) or args.straighten_pages or args.detect_orientation
    if orientation_path and not args.enable_orientation_helpers:
        kwargs["disable_page_orientation"] = True
        kwargs["disable_crop_orientation"] = True

    if args.mode == "ocr":
        kwargs["detect_tables"] = args.detect_tables
        return ocr_predictor(**kwargs)
    if args.detect_tables:
        raise ValueError("--detect-tables is supported by OCR mode only, not KIE mode")
    return kie_predictor(**kwargs)


def _summarize_result(result: Any, page_count: int) -> dict[str, Any]:
    from doctr.io.elements import Document, KIEDocument

    if isinstance(result, KIEDocument):
        if len(result.pages) != page_count:
            raise AssertionError(f"page count mismatch: {len(result.pages)} != {page_count}")
        classes = sorted({name for page in result.pages for name in page.predictions.keys()})
        return {
            "result_type": type(result).__name__,
            "pages": len(result.pages),
            "prediction_classes": classes,
            "predictions_per_page": [sum(len(v) for v in page.predictions.values()) for page in result.pages],
            "layout_per_page": [len(page.layout) for page in result.pages],
        }

    if isinstance(result, Document):
        if len(result.pages) != page_count:
            raise AssertionError(f"page count mismatch: {len(result.pages)} != {page_count}")
        return {
            "result_type": type(result).__name__,
            "pages": len(result.pages),
            "blocks_per_page": [len(page.blocks) for page in result.pages],
            "layout_per_page": [len(page.layout) for page in result.pages],
            "tables_per_page": [len(page.tables) for page in result.pages],
        }

    raise AssertionError(f"unexpected result type: {type(result)!r}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        predictor = _build_predictor(args)
        device = _select_device(args.device)
        predictor = predictor.to(device)

        summary: dict[str, Any] = {
            "ok": True,
            "mode": args.mode,
            "predictor_type": type(predictor).__name__,
            "device": str(device),
            "pretrained": args.pretrained,
            "pretrained_backbone": args.pretrained_backbone,
            "forward_ran": False,
        }

        if not args.skip_forward:
            pages = _make_pages(args.pages, args.height, args.width)
            result = predictor(pages)
            summary.update(_summarize_result(result, len(pages)))
            summary["forward_ran"] = True

        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except ModuleNotFoundError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "stage": "import_or_dependency",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "hint": "Install python-doctr with its core dependencies in the active Python environment.",
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
