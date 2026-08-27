#!/usr/bin/env python3
"""Render T-Rex2 detection JSON to an annotated image.

This helper wraps the public ``trex.visualize`` function with validation and
score conversion. It accepts either raw postprocess output
``{"scores": ..., "labels": ..., "boxes": ...}`` or output from the bundled
cloud API scripts where detections are nested under a ``detections`` key.

Examples:
  python render_detections.py --demo-fixture --output-image /tmp/trex_demo.jpg
  python render_detections.py --image target.jpg --detections-json detections.json \
      --output-image annotated.jpg --box-threshold 0.3 --draw-score
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any


JSONDict = dict[str, Any]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render T-Rex2 detections with trex.visualize.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--image", help="Input image to annotate. Required unless --demo-fixture is used.")
    parser.add_argument(
        "--detections-json",
        help="Detection JSON file. Accepts raw scores/labels/boxes or a top-level detections object. Required unless --demo-fixture is used.",
    )
    parser.add_argument("--output-image", required=True, help="Where to write the annotated output image.")
    parser.add_argument("--box-threshold", type=float, default=0.3, help="Keep boxes with score > threshold.")
    parser.add_argument("--return-point", action="store_true", help="Draw center points instead of rectangles.")
    parser.add_argument("--draw-width", type=float, default=6.0, help="Rectangle line width or point radius.")
    parser.add_argument("--draw-score", action="store_true", help="Draw score text next to each box.")
    parser.add_argument("--no-draw-label", action="store_true", help="Do not draw label text.")
    parser.add_argument(
        "--overwrite-colors-json",
        help="Optional JSON mapping string labels to RGB lists, e.g. {\"1\": [255, 0, 0]}.",
    )
    parser.add_argument(
        "--agnostic-random-color",
        action="store_true",
        help="Use a fresh random color for each box instead of per-label colors.",
    )
    parser.add_argument(
        "--demo-fixture",
        action="store_true",
        help="Ignore --image/--detections-json and render a tiny built-in fixture for smoke testing.",
    )
    parser.add_argument(
        "--print-summary",
        action="store_true",
        help="Print a compact summary of filtered detections after rendering.",
    )
    return parser


def parser_error(parser: argparse.ArgumentParser, message: str) -> None:
    parser.error(message)


def resolve_file(raw_path: str | None, parser: argparse.ArgumentParser, label: str) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip():
        parser_error(parser, f"{label} is required")
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    if not path.is_file():
        parser_error(parser, f"{label} file not found: {path}")
    return path


def load_json_file(raw_path: str, parser: argparse.ArgumentParser, label: str) -> JSONDict:
    path = resolve_file(raw_path, parser, label)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        parser_error(parser, f"{label} is malformed JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except OSError as exc:
        parser_error(parser, f"could not read {label} {path}: {exc}")
    if not isinstance(data, dict):
        parser_error(parser, f"{label} must contain a JSON object")
    return data


def extract_detections(data: JSONDict, parser: argparse.ArgumentParser) -> JSONDict:
    detections = data.get("detections", data)
    if not isinstance(detections, dict):
        parser_error(parser, "detections must be a JSON object")
    missing = [key for key in ("scores", "labels", "boxes") if key not in detections]
    if missing:
        parser_error(parser, f"detections missing required keys: {', '.join(missing)}")
    return detections


def validate_thresholds(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if not math.isfinite(args.box_threshold):
        parser_error(parser, "--box-threshold must be finite")
    if not math.isfinite(args.draw_width) or args.draw_width < 0:
        parser_error(parser, "--draw-width must be a finite non-negative number")


def coerce_and_filter(detections: JSONDict, threshold: float, parser: argparse.ArgumentParser) -> JSONDict:
    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover - depends on user environment
        parser_error(parser, f"NumPy is required for rendering because trex.visualize expects scalar .item(): {exc}")

    try:
        scores = np.asarray(detections["scores"], dtype=float)
        labels = np.asarray(detections["labels"])
        boxes = np.asarray(detections["boxes"], dtype=float)
    except Exception as exc:
        parser_error(parser, f"could not convert detections to arrays: {exc}")

    if scores.ndim != 1:
        parser_error(parser, "detections['scores'] must be a 1-D list/array")
    if labels.ndim != 1:
        parser_error(parser, "detections['labels'] must be a 1-D list/array")
    if boxes.size == 0:
        boxes = boxes.reshape((0, 4))
    if boxes.ndim != 2 or boxes.shape[1] != 4:
        parser_error(parser, "detections['boxes'] must have shape (N, 4)")
    if not (len(scores) == len(labels) == len(boxes)):
        parser_error(parser, "detections scores, labels, and boxes must have equal lengths")
    if not np.all(np.isfinite(scores)) or not np.all(np.isfinite(boxes)):
        parser_error(parser, "scores and boxes must be finite numbers")

    if len(boxes):
        invalid = (boxes[:, 0] >= boxes[:, 2]) | (boxes[:, 1] >= boxes[:, 3])
        if bool(np.any(invalid)):
            bad_indices = np.where(invalid)[0].tolist()
            parser_error(parser, f"boxes must satisfy x1 < x2 and y1 < y2; invalid indices: {bad_indices}")

    mask = scores > threshold
    return {"scores": scores[mask], "labels": labels[mask], "boxes": boxes[mask]}


def load_colors(raw_path: str | None, labels: Any, parser: argparse.ArgumentParser) -> dict[str, tuple[int, int, int]] | None:
    if raw_path is None:
        return None
    data = load_json_file(raw_path, parser, "--overwrite-colors-json")
    colors: dict[str, tuple[int, int, int]] = {}
    for key, value in data.items():
        if not isinstance(key, str):
            parser_error(parser, "color mapping keys must be strings")
        if not isinstance(value, list) or len(value) != 3:
            parser_error(parser, f"color mapping for label {key!r} must be an RGB list of three integers")
        rgb: list[int] = []
        for item in value:
            if isinstance(item, bool) or not isinstance(item, int) or not 0 <= item <= 255:
                parser_error(parser, f"color mapping for label {key!r} must contain integers in [0, 255]")
            rgb.append(item)
        colors[key] = tuple(rgb)  # type: ignore[arg-type]

    missing = sorted({str(label) for label in labels} - set(colors))
    if missing:
        parser_error(parser, f"color mapping missing labels after filtering: {missing}")
    return colors


def demo_fixture() -> tuple[Path, JSONDict, tempfile.TemporaryDirectory[str]]:
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Pillow is required for --demo-fixture: {exc}") from exc

    tempdir = tempfile.TemporaryDirectory(prefix="trex-render-fixture-")
    image_path = Path(tempdir.name) / "fixture.jpg"
    Image.new("RGB", (64, 48), color="white").save(image_path)
    detections = {"scores": [0.95], "labels": [1], "boxes": [[8, 8, 40, 32]]}
    return image_path, detections, tempdir


def write_output(image_path: Path, target: JSONDict, args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    try:
        from PIL import Image
        from trex import visualize
    except Exception as exc:  # pragma: no cover - depends on user environment
        parser_error(parser, f"could not import rendering dependencies (Pillow and trex): {exc}")

    output = Path(args.output_image).expanduser()
    if not output.is_absolute():
        output = Path.cwd() / output
    if output.parent != Path("."):
        output.parent.mkdir(parents=True, exist_ok=True)

    colors = load_colors(args.overwrite_colors_json, target["labels"], parser)
    try:
        with Image.open(image_path) as image:
            rendered = visualize(
                image.convert("RGB"),
                target,
                return_point=args.return_point,
                draw_width=args.draw_width,
                overwrite_color=colors,
                agnostic_random_color=args.agnostic_random_color,
                draw_score=args.draw_score,
                draw_label=not args.no_draw_label,
            )
            rendered.save(output)
    except Exception as exc:
        parser_error(parser, f"failed to render or save output image {output}: {exc}")


def summarize(target: JSONDict) -> JSONDict:
    return {
        "kept_detections": int(len(target["scores"])),
        "labels": [str(label) for label in target["labels"].tolist()],
        "boxes": target["boxes"].astype(float).tolist(),
        "scores": target["scores"].astype(float).tolist(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_thresholds(args, parser)

    fixture_tmp: tempfile.TemporaryDirectory[str] | None = None
    if args.demo_fixture:
        try:
            image_path, detections, fixture_tmp = demo_fixture()
        except RuntimeError as exc:
            parser_error(parser, str(exc))
    else:
        image_path = resolve_file(args.image, parser, "--image")
        detections = extract_detections(load_json_file(args.detections_json, parser, "--detections-json"), parser)

    target = coerce_and_filter(detections, args.box_threshold, parser)
    write_output(image_path, target, args, parser)

    if args.print_summary:
        print(json.dumps(summarize(target), indent=2))

    if fixture_tmp is not None:
        fixture_tmp.cleanup()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
