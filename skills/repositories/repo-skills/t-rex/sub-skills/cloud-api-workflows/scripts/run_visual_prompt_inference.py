#!/usr/bin/env python3
"""Run T-Rex2 visual-prompt detection from a prompt JSON file.

This command adapts the interactive and generic T-Rex2 API examples into a
self-contained CLI that uses the public ``trex.TRex2APIWrapper`` API. Dry-run
mode validates inputs and prints a compact converted-payload summary without
making a network call. Live mode requires a token and writes only the requested
output JSON and optional visualization image.
"""

from __future__ import annotations

import argparse
import copy
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
        description="Run T-Rex2 visual-prompt detection with local image paths and prompt JSON.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--token",
        help="DeepDataSpace T-Rex2 API token. If omitted, T_REX_API_TOKEN is used in live mode.",
    )
    parser.add_argument("--target-image", required=True, help="Target image to detect on.")
    parser.add_argument(
        "--prompt-json",
        required=True,
        help="JSON prompt file: list of objects with image and interactions fields.",
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


def resolve_existing_file(
    raw_path: str,
    parser: argparse.ArgumentParser,
    label: str,
    base_dir: Path | None = None,
) -> Path:
    """Resolve a file path, trying prompt-relative paths before cwd paths."""
    if not isinstance(raw_path, str) or not raw_path.strip():
        parser_error(parser, f"{label} must be a non-empty path string")

    original = Path(raw_path).expanduser()
    candidates: list[Path] = []
    if original.is_absolute():
        candidates.append(original)
    else:
        if base_dir is not None:
            candidates.append(base_dir / original)
        candidates.append(Path.cwd() / original)

    seen: set[Path] = set()
    unique_candidates: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_candidates.append(resolved)

    for candidate in unique_candidates:
        if candidate.is_file():
            return candidate

    tried = ", ".join(str(candidate) for candidate in unique_candidates)
    parser_error(parser, f"{label} file not found for {raw_path!r}; tried: {tried}")
    raise AssertionError("unreachable")


def validate_image_file(
    raw_path: str,
    parser: argparse.ArgumentParser,
    label: str,
    base_dir: Path | None = None,
) -> Path:
    """Validate that a path exists and can be opened as an image."""
    path = resolve_existing_file(raw_path, parser, label, base_dir=base_dir)
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


def numeric_sequence(
    value: Any,
    length: int,
    parser: argparse.ArgumentParser,
    label: str,
) -> list[float]:
    """Validate a numeric coordinate sequence."""
    if not isinstance(value, list) or len(value) != length:
        parser_error(parser, f"{label} must be a list of {length} numbers")
    numbers: list[float] = []
    for index, item in enumerate(value):
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            parser_error(parser, f"{label}[{index}] must be a number")
        number = float(item)
        if not math.isfinite(number):
            parser_error(parser, f"{label}[{index}] must be finite")
        numbers.append(number)
    return numbers


def validate_interaction(
    interaction: Any,
    parser: argparse.ArgumentParser,
    label: str,
) -> JSONDict:
    """Validate one prompt interaction and return a sanitized dict."""
    if not isinstance(interaction, dict):
        parser_error(parser, f"{label} must be an object")

    prompt_type = interaction.get("type")
    category_id = interaction.get("category_id")
    if isinstance(category_id, bool) or not isinstance(category_id, int):
        parser_error(parser, f"{label}.category_id must be an integer")

    if prompt_type == "rect":
        rect = numeric_sequence(interaction.get("rect"), 4, parser, f"{label}.rect")
        if rect[0] >= rect[2] or rect[1] >= rect[3]:
            parser_error(parser, f"{label}.rect must satisfy x1 < x2 and y1 < y2")
        return {"type": "rect", "category_id": category_id, "rect": rect}

    if prompt_type == "point":
        point = numeric_sequence(interaction.get("point"), 2, parser, f"{label}.point")
        return {"type": "point", "category_id": category_id, "point": point}

    parser_error(parser, f"{label}.type must be 'rect' or 'point'")
    raise AssertionError("unreachable")


def load_prompt_json(prompt_json: str, parser: argparse.ArgumentParser) -> list[JSONDict]:
    """Load and validate the visual prompt JSON file."""
    prompt_path = resolve_existing_file(prompt_json, parser, "--prompt-json")
    try:
        data = json.loads(prompt_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        parser_error(
            parser,
            f"--prompt-json is malformed JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
        )
    except OSError as exc:
        parser_error(parser, f"could not read --prompt-json {prompt_path}: {exc}")

    if not isinstance(data, list) or not data:
        parser_error(parser, "--prompt-json must contain a non-empty list of prompt objects")

    prompts: list[JSONDict] = []
    for prompt_index, prompt in enumerate(data):
        prompt_label = f"prompt[{prompt_index}]"
        if not isinstance(prompt, dict):
            parser_error(parser, f"{prompt_label} must be an object")

        image_path = validate_image_file(
            prompt.get("image"), parser, f"{prompt_label}.image", base_dir=prompt_path.parent
        )

        interactions = prompt.get("interactions")
        if not isinstance(interactions, list) or not interactions:
            parser_error(parser, f"{prompt_label}.interactions must be a non-empty list")

        sanitized_interactions = [
            validate_interaction(interaction, parser, f"{prompt_label}.interactions[{i}]")
            for i, interaction in enumerate(interactions)
        ]
        prompts.append({"image": str(image_path), "interactions": sanitized_interactions})

    return prompts


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


def summarize_visual_payload(payload: JSONDict) -> JSONDict:
    """Return a compact summary without base64 image contents."""
    prompt = payload.get("prompt", {})
    visual_images = prompt.get("visual_images", []) if isinstance(prompt, dict) else []
    prompt_summaries: list[JSONDict] = []
    total_interactions = 0
    for index, item in enumerate(visual_images):
        interactions = item.get("interactions", []) if isinstance(item, dict) else []
        total_interactions += len(interactions)
        prompt_summaries.append(
            {
                "index": index,
                "image_data_uri_chars": len(item.get("image", "")) if isinstance(item, dict) else 0,
                "interactions": len(interactions),
                "interaction_types": sorted(
                    {interaction.get("type") for interaction in interactions if isinstance(interaction, dict)}
                ),
                "category_ids": sorted(
                    {
                        interaction.get("category_id")
                        for interaction in interactions
                        if isinstance(interaction, dict) and "category_id" in interaction
                    }
                ),
            }
        )

    return {
        "dry_run": True,
        "network_call": False,
        "model": payload.get("model"),
        "targets": payload.get("targets"),
        "target_image_data_uri_chars": len(payload.get("image", "")),
        "prompt_type": prompt.get("type") if isinstance(prompt, dict) else None,
        "prompt_images": len(visual_images),
        "total_interactions": total_interactions,
        "prompt_summaries": prompt_summaries,
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
    prompts = load_prompt_json(args.prompt_json, parser)
    TRex2APIWrapper = load_trex_wrapper(parser)

    if args.dry_run:
        wrapper = TRex2APIWrapper(args.token or os.environ.get("T_REX_API_TOKEN") or "dry-run-token")
        payload = wrapper.convert_visual_prompt(str(target_image), copy.deepcopy(prompts), return_type=["bbox"])
        print(json.dumps(summarize_visual_payload(payload), indent=2))
        return 0

    token = args.token or os.environ.get("T_REX_API_TOKEN")
    if not token:
        parser_error(parser, "live mode requires --token or T_REX_API_TOKEN; use --dry-run for offline validation")

    wrapper = TRex2APIWrapper(token)
    try:
        detections, _ = wrapper.visual_prompt_inference(
            str(target_image), copy.deepcopy(prompts), return_type=["bbox"]
        )
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        raise SystemExit(f"T-Rex2 visual prompt API call failed: {exc}") from exc

    output_payload: JSONDict = {
        "schema_version": 1,
        "workflow": "visual_prompt_inference",
        "return_type": ["bbox"],
        "prompt_images": len(prompts),
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
