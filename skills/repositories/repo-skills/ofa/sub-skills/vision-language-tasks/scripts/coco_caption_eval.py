#!/usr/bin/env python3
"""Evaluate COCO caption predictions with pycocotools / pycocoevalcap.

This is an adapted, safer version of the repo's caption evaluation helper.
It keeps the same basic data expectations but provides explicit CLI arguments
and clearer dependency failure messages.

Example:
  python coco_caption_eval.py --predictions test_predict.json \
    --labels test_caption_coco_format.json --output metrics.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def evaluate_on_coco_caption(predictions: Path, labels: Path) -> dict:
    try:
        from pycocotools.coco import COCO
        from pycocoevalcap.eval import COCOEvalCap
    except Exception as exc:  # pragma: no cover - helper diagnostics
        raise RuntimeError(
            "missing optional dependency: pycocotools/pycocoevalcap are required for COCO caption evaluation"
        ) from exc

    coco = COCO(str(labels))
    coco_res = coco.loadRes(str(predictions))
    coco_eval = COCOEvalCap(coco, coco_res)
    coco_eval.params["image_id"] = coco_res.getImgIds()
    try:
        coco_eval.evaluate()
    except Exception as exc:  # pragma: no cover - helper diagnostics
        raise RuntimeError(
            "COCO caption evaluation failed; check that Java 1.8 is installed for SPICE and that the result file is valid COCO output"
        ) from exc
    return coco_eval.eval


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path, help="COCO-format predictions JSON file.")
    parser.add_argument("--labels", required=True, type=Path, help="Ground-truth COCO annotations JSON file.")
    parser.add_argument("--output", default=None, type=Path, help="Optional JSON file for metrics.")
    args = parser.parse_args()

    try:
        metrics = evaluate_on_coco_caption(args.predictions, args.labels)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output is not None:
        args.output.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
