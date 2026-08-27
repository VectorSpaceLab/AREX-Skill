#!/usr/bin/env python3
"""Run T-Rex2 embedding-based detection from a base64 embedding text file.

This command adapts the T-Rex2 embedding-inference example into a reusable CLI
that uses the public ``trex.TRex2APIWrapper`` API. Dry-run mode validates the
target image and embedding text, prints a compact converted-payload summary, and
makes no network call. Live mode requires a token and writes only the requested
output JSON and optional visualization image.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import math
import os
import sys
from pathlib import Path
from typing import Any


JSONDict = dict[str, Any]


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Run T-Rex2 detection from a base64 visual embedding file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--token",
        help="DeepDataSpace T-Rex2 API token. If omitted, T_REX_API_TOKEN is used in live mode.",
    )
    parser.add_argument("--target-image", required=True, help="Target image to detect on.")
    parser.add_argument(
        "--embedding-file",
        required=True,
        help="Text file containing the base64 embedding string.",
    )
    parser.add_argument("--output-json", required=True, help="Where to write live detection JSON.")
    parser.add_argument(
        "--visualization-output",
        help="Optional annotated image output. Only written in live mode.",
    )
    parser.add_argument(
        "--box-threshold",
        type=float,
        default=0.3,
        help="Score threshold used only for optional visualization filtering.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate files/schema and print payload summary without a network call or output writes.",
    )
    return parser


def parser_error(parser: argparse.ArgumentParser, message: str) -> None:
    """Raise an argparse-style error with a clear message."""
    parser.error(message)


def resolve_existing_file(raw_path: str, parser: argparse.ArgumentParser, label: str) -> Path:
    """Resolve and validate an existing file path."""
    if not isinstance(raw_path, str) or not raw_path.strip():
        parser_error(parser, f"{label} must be a non-empty path string")
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    if not path.is_file():
        parser_error(parser, f"{label} file not found: {path}")
    return path


def validate_image_file(raw_path: str, parser: argparse.ArgumentParser, label: str) -> Path:
    """Validate that a path exists and can be opened as an image."""
    path = resolve_existing_file(raw_path, parser, label)
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - depends on runtime install
        parser_error(parser, f"Pillow is required to validate {label}: {exc}")

    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as exc:
        parser_error(parser, f"{label} is not a readable image: {path} ({exc})")
    return path


def read_embedding_file(raw_path: str, parser: argparse.ArgumentParser) -> str:
    """Read and lightly validate a base64 embedding text file."""
    path = resolve_existing_file(raw_path, parser, "--embedding-file")
    try:
        raw_text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        parser_error(parser, "--embedding-file must be a text file containing base64, not binary data")
    except OSError as exc:
        parser_error(parser, f"could not read --embedding-file {path}: {exc}")

    embedding = "".join(raw_text.split())
    if not embedding:
        parser_error(parser, "--embedding-file is empty")

    padded = embedding + ("=" * ((4 - len(embedding) % 4) % 4))
    try:
        base64.b64decode(padded, validate=True)
    except (binascii.Error, ValueError) as exc:
        parser_error(
            parser,
            "--embedding-file must contain the base64 embedding text expected by "
            f"TRex2APIWrapper, not a URL, JSON wrapper, or binary checkpoint ({exc})",
        )
    return embedding


def load_trex_wrapper(parser: argparse.ArgumentParser):
    """Import and return the public T-Rex2 wrapper class."""
    try:
        from trex import TRex2APIWrapper
    except Exception as exc:  # pragma: no cover - depends on user's environment
        parser_error(
            parser,
            "could not import 'trex.TRex2APIWrapper'. Install the T-Rex package before "
            f"running this script. Import error: {exc}",
        )
    return TRex2APIWrapper


def summarize_embedding_payload(payload: JSONDict, embedding: str) -> JSONDict:
    """Return a compact summary without target image or embedding contents."""
    prompt = payload.get("prompt", {})
    return {
        "dry_run": True,
        "network_call": False,
        "model": payload.get("model"),
        "targets": payload.get("targets"),
        "target_image_data_uri_chars": len(payload.get("image", "")),
        "prompt_type": prompt.get("type") if isinstance(prompt, dict) else None,
        "embedding_chars": len(embedding),
    }


def ensure_finite_threshold(value: float, parser: argparse.ArgumentParser) -> None:
    """Validate the score threshold."""
    if not math.isfinite(value):
        parser_error(parser, "--box-threshold must be a finite number")


def detections_for_visualization(
    detections: JSONDict,
    threshold: float,
    parser: argparse.ArgumentParser,
) -> JSONDict:
    """Convert postprocess output lists to NumPy arrays and filter by score."""
    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover - depends on runtime install
        parser_error(parser, f"NumPy is required for visualization output: {exc}")

    try:
        scores = np.asarray(detections.get("scores", []), dtype=float)
        labels = np.asarray(detections.get("labels", []))
        boxes = np.asarray(detections.get("boxes", []), dtype=float)
    except Exception as exc:
        parser_error(parser, f"detections could not be converted to arrays: {exc}")

    if boxes.size == 0:
        boxes = boxes.reshape((0, 4))
    if boxes.ndim != 2 or boxes.shape[1] != 4:
        parser_error(parser, "detections['boxes'] must have shape (N, 4)")
    if not (len(scores) == len(labels) == len(boxes)):
        parser_error(parser, "detections scores, labels, and boxes must have equal lengths")

    mask = scores > threshold
    return {"scores": scores[mask], "labels": labels[mask], "boxes": boxes[mask]}


def render_visualization(
    target_image: Path,
    detections: JSONDict,
    output_path: str,
    threshold: float,
    parser: argparse.ArgumentParser,
) -> None:
    """Render detections through ``trex.visualize`` after NumPy conversion."""
    try:
        from PIL import Image
        from trex import visualize
    except Exception as exc:  # pragma: no cover - depends on user's environment
        parser_error(parser, f"could not import visualization dependencies: {exc}")

    target = detections_for_visualization(detections, threshold, parser)
    output = Path(output_path).expanduser()
    if output.parent != Path("."):
        output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(target_image) as image:
            rendered = visualize(image.convert("RGB"), target, draw_score=True)
            rendered.save(output)
    except Exception as exc:
        parser_error(parser, f"failed to write visualization {output}: {exc}")


def write_json(path: str, payload: JSONDict, parser: argparse.ArgumentParser) -> None:
    """Write a JSON file, creating parent directories when needed."""
    output = Path(path).expanduser()
    if output.parent != Path("."):
        output.parent.mkdir(parents=True, exist_ok=True)
    try:
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        parser_error(parser, f"failed to write --output-json {output}: {exc}")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    ensure_finite_threshold(args.box_threshold, parser)

    target_image = validate_image_file(args.target_image, parser, "--target-image")
    embedding = read_embedding_file(args.embedding_file, parser)
    TRex2APIWrapper = load_trex_wrapper(parser)

    if args.dry_run:
        wrapper = TRex2APIWrapper(args.token or os.environ.get("T_REX_API_TOKEN") or "dry-run-token")
        payload = wrapper.convert_embedding_prompt(str(target_image), embedding)
        print(json.dumps(summarize_embedding_payload(payload, embedding), indent=2))
        return 0

    token = args.token or os.environ.get("T_REX_API_TOKEN")
    if not token:
        parser_error(parser, "live mode requires --token or T_REX_API_TOKEN; use --dry-run for offline validation")

    wrapper = TRex2APIWrapper(token)
    try:
        detections = wrapper.embedding_inference(str(target_image), embedding)
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        raise SystemExit(f"T-Rex2 embedding inference API call failed: {exc}") from exc

    output_payload: JSONDict = {
        "schema_version": 1,
        "workflow": "embedding_inference",
        "return_type": ["bbox"],
        "detections": detections,
    }
    write_json(args.output_json, output_payload, parser)

    if args.visualization_output:
        render_visualization(target_image, detections, args.visualization_output, args.box_threshold, parser)

    print(f"Wrote detections to {args.output_json}")
    if args.visualization_output:
        print(f"Wrote visualization to {args.visualization_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
