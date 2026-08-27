#!/usr/bin/env python3
"""List MMPreTrain model-zoo names without checkpoint downloads."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys


TASKS = [
    "Image Classification",
    "Image Retrieval",
    "Image Caption",
    "Visual Question Answering",
    "Visual Grounding",
    "Text-To-Image Retrieval",
    "Image-To-Text Retrieval",
    "NLVR",
    "null",
]

INFERENCER_ALIASES = {
    "classification": "ImageClassificationInferencer",
    "image-retrieval": "ImageRetrievalInferencer",
    "feature-extraction": "FeatureExtractor",
    "caption": "ImageCaptionInferencer",
    "vqa": "VisualQuestionAnsweringInferencer",
    "grounding": "VisualGroundingInferencer",
    "text-to-image": "TextToImageRetrievalInferencer",
    "image-to-text": "ImageToTextRetrievalInferencer",
    "nlvr": "NLVRInferencer",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List locally registered MMPreTrain model names. No checkpoints are downloaded."
    )
    parser.add_argument(
        "--pattern",
        help="Wildcard/prefix pattern, e.g. 'resnet18' or 'resnet*in1k'.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Wildcard/prefix pattern to exclude. Repeatable.",
    )
    parser.add_argument(
        "--task",
        choices=TASKS,
        help="Exact model-index task filter. Mutually exclusive with --inferencer.",
    )
    parser.add_argument(
        "--inferencer",
        choices=sorted(INFERENCER_ALIASES),
        help="Use an inferencer-specific list_models filter.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Print at most this many names after filtering.",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help="Print only the count after filtering/limit.",
    )
    parser.add_argument(
        "--as-json",
        action="store_true",
        help="Emit JSON with count and model list.",
    )
    return parser


def source_style_exclude(names: list[str], patterns: list[str]) -> list[str]:
    kept = list(names)
    for pattern in patterns:
        kept = [name for name in kept if not fnmatch.fnmatch(name, pattern + "*")]
    return kept


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.task and args.inferencer:
        parser.error("--task and --inferencer are mutually exclusive")
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be non-negative")

    try:
        import mmpretrain.apis as apis
    except Exception as exc:
        print(f"Failed to import mmpretrain.apis: {exc}", file=sys.stderr)
        return 2

    try:
        if args.inferencer:
            class_name = INFERENCER_ALIASES[args.inferencer]
            cls = getattr(apis, class_name)
            names = list(cls.list_models(args.pattern))
            names = source_style_exclude(names, args.exclude)
        else:
            names = list(
                apis.list_models(
                    pattern=args.pattern,
                    exclude_patterns=args.exclude or None,
                    task=args.task,
                )
            )
    except Exception as exc:
        print(f"Failed to list models: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3

    if args.limit is not None:
        names = names[: args.limit]

    if args.as_json:
        print(json.dumps({"count": len(names), "models": names}, indent=2))
    elif args.count:
        print(len(names))
    else:
        for name in names:
            print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
