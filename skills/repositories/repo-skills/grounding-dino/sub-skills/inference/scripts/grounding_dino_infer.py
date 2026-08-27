#!/usr/bin/env python3
"""Safe single-image GroundingDINO inference helper.

This script adapts the repository's single-image demo into a portable helper for
agents. It requires caller-provided config, checkpoint, and image paths; it does
not download weights and does not assume a source checkout exists.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Iterable


class UserError(Exception):
    """A deterministic, user-correctable CLI error."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="grounding_dino_infer.py",
        description="Run GroundingDINO single-image open-vocabulary detection.",
    )
    parser.add_argument(
        "--config-file",
        "--config_file",
        "-c",
        dest="config_file",
        required=True,
        help="Path to a GroundingDINO Python config file.",
    )
    parser.add_argument(
        "--checkpoint-path",
        "--checkpoint_path",
        "-p",
        dest="checkpoint_path",
        required=True,
        help="Path to a compatible GroundingDINO checkpoint (.pth).",
    )
    parser.add_argument(
        "--image-path",
        "--image_path",
        "-i",
        dest="image_path",
        required=True,
        help="Path to the input image.",
    )
    parser.add_argument(
        "--text-prompt",
        "--text_prompt",
        "-t",
        dest="text_prompt",
        default=None,
        help="Text prompt, for example 'chair . person . dog .'.",
    )
    parser.add_argument(
        "--classes",
        nargs="+",
        default=None,
        help="Class names converted into a period-separated prompt.",
    )
    parser.add_argument(
        "--output-dir",
        "--output_dir",
        "-o",
        dest="output_dir",
        required=True,
        help="Directory where raw_image.jpg, pred.jpg, and optional JSON are written.",
    )
    parser.add_argument("--box-threshold", "--box_threshold", dest="box_threshold", type=float, default=0.3)
    parser.add_argument("--text-threshold", "--text_threshold", dest="text_threshold", type=float, default=0.25)
    parser.add_argument(
        "--token-spans",
        "--token_spans",
        dest="token_spans",
        default=None,
        help=(
            "Python literal span list, e.g. '[[[9, 10], [11, 14]], [[19, 20], [21, 24]]]'. "
            "When set, text threshold is ignored and box threshold filters phrase logits."
        ),
    )
    parser.add_argument(
        "--device",
        default="cuda",
        help="Torch device to use, for example 'cuda', 'cuda:0', or 'cpu'. Ignored when --cpu-only is set.",
    )
    parser.add_argument("--cpu-only", action="store_true", help="Force CPU inference.")
    parser.add_argument(
        "--remove-combined",
        action="store_true",
        help="For normal prompt mode, restrict phrase extraction between separator tokens such as periods.",
    )
    parser.add_argument(
        "--json-output",
        nargs="?",
        const="detections.json",
        default=None,
        help="Optional JSON path. Use without a value for output-dir/detections.json, or '-' for stdout.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate arguments, paths, image readability, spans, and device, then exit before loading weights.",
    )
    return parser


def normalize_caption(caption: str) -> str:
    result = caption.lower().strip()
    if not result:
        raise UserError("text prompt is empty after stripping whitespace")
    if not result.endswith("."):
        result += "."
    return result


def caption_from_args(args: argparse.Namespace) -> str:
    if args.text_prompt and args.classes:
        raise UserError("use either --text-prompt or --classes, not both")
    if args.classes:
        classes = [item.strip() for item in args.classes if item.strip()]
        if not classes:
            raise UserError("--classes did not contain any non-empty class names")
        return normalize_caption(". ".join(classes))
    if args.text_prompt:
        return normalize_caption(args.text_prompt)
    raise UserError("provide --text-prompt or --classes")


def require_file(path_text: str, label: str) -> Path:
    path = Path(path_text).expanduser()
    if not path.exists():
        raise UserError(f"missing {label}: {path}")
    if not path.is_file():
        raise UserError(f"{label} is not a file: {path}")
    return path


def validate_threshold(value: float, label: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise UserError(f"{label} must be between 0 and 1, got {value}")


def parse_token_spans(value: str | None, caption: str) -> list[list[list[int]]] | None:
    if value is None:
        return None
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError) as exc:
        raise UserError(f"malformed token spans: expected a Python literal list ({exc})") from exc
    if not isinstance(parsed, (list, tuple)) or len(parsed) == 0:
        raise UserError("token spans must be a non-empty list of phrase span groups")

    normalized: list[list[list[int]]] = []
    for phrase_index, phrase_group in enumerate(parsed):
        if not isinstance(phrase_group, (list, tuple)) or len(phrase_group) == 0:
            raise UserError(f"token span group {phrase_index} must be a non-empty list of [start, end] pairs")
        normalized_group: list[list[int]] = []
        phrase_parts: list[str] = []
        for span_index, span in enumerate(phrase_group):
            if not isinstance(span, (list, tuple)) or len(span) != 2:
                raise UserError(f"token span group {phrase_index} item {span_index} must be [start, end]")
            start, end = span
            if not isinstance(start, int) or not isinstance(end, int):
                raise UserError(f"token span group {phrase_index} item {span_index} must contain integer offsets")
            if start < 0 or end > len(caption) or start >= end:
                raise UserError(
                    f"token span group {phrase_index} item {span_index} is outside caption bounds 0..{len(caption)}"
                )
            text = caption[start:end]
            if not text.strip():
                raise UserError(f"token span group {phrase_index} item {span_index} selects only whitespace")
            normalized_group.append([start, end])
            phrase_parts.append(text)
        phrase = " ".join(part.strip() for part in phrase_parts).strip()
        if not phrase:
            raise UserError(f"token span group {phrase_index} did not select visible caption text")
        normalized.append(normalized_group)
    return normalized


def validate_image(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image
    except ModuleNotFoundError as exc:
        raise UserError("Pillow is required to validate and save images; install the GroundingDINO requirements") from exc
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            return image.size
    except Exception as exc:  # noqa: BLE001 - present a deterministic CLI error.
        raise UserError(f"image could not be opened: {path} ({exc})") from exc


def choose_device(args: argparse.Namespace) -> str:
    device = "cpu" if args.cpu_only else args.device
    try:
        import torch
    except ModuleNotFoundError as exc:
        raise UserError("torch is required for GroundingDINO inference") from exc
    if device.startswith("cuda") and not torch.cuda.is_available():
        raise UserError("CUDA device requested but torch.cuda.is_available() is false; use --cpu-only or --device cpu")
    return device


def validate_args(args: argparse.Namespace) -> tuple[Path, Path, Path, Path, str, list[list[list[int]]] | None, str]:
    config_path = require_file(args.config_file, "config")
    checkpoint_path = require_file(args.checkpoint_path, "checkpoint")
    image_path = require_file(args.image_path, "image")
    validate_threshold(args.box_threshold, "box threshold")
    validate_threshold(args.text_threshold, "text threshold")
    caption = caption_from_args(args)
    if args.classes and args.token_spans:
        raise UserError("--token-spans requires explicit --text-prompt offsets; do not combine it with --classes")
    token_spans = parse_token_spans(args.token_spans, caption)
    validate_image(image_path)
    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    if not output_dir.is_dir():
        raise UserError(f"output path is not a directory: {output_dir}")
    device = choose_device(args)
    return config_path, checkpoint_path, image_path, output_dir, caption, token_spans, device


def import_groundingdino_api():
    try:
        from groundingdino.util.inference import load_image, load_model, predict
    except ModuleNotFoundError as exc:
        raise UserError("groundingdino is not importable; install the package before running inference") from exc
    return load_image, load_model, predict


def predict_with_token_spans(model, image, caption: str, token_spans: list[list[list[int]]], box_threshold: float, device: str):
    import torch
    from groundingdino.util.vl_utils import create_positive_map_from_span

    model = model.to(device)
    image = image.to(device)
    with torch.no_grad():
        outputs = model(image[None], captions=[caption])

    logits = outputs["pred_logits"].sigmoid()[0]
    boxes = outputs["pred_boxes"][0]
    tokenized = model.tokenizer(caption)
    positive_maps = create_positive_map_from_span(tokenized, token_span=token_spans).to(logits.device)
    empty_rows = (positive_maps.sum(dim=1) == 0).nonzero(as_tuple=False).flatten().tolist()
    if empty_rows:
        raise UserError(
            "token spans did not align with tokenizer tokens for group(s): "
            + ", ".join(str(index) for index in empty_rows)
        )

    logits_for_phrases = positive_maps @ logits.T
    all_boxes = []
    all_logits = []
    all_phrases: list[str] = []
    for span_group, phrase_logits in zip(token_spans, logits_for_phrases):
        phrase = " ".join(caption[start:end].strip() for start, end in span_group).strip()
        keep = phrase_logits > box_threshold
        selected_boxes = boxes[keep]
        selected_logits = phrase_logits[keep]
        if selected_boxes.numel() == 0:
            continue
        all_boxes.append(selected_boxes)
        all_logits.append(selected_logits)
        all_phrases.extend([phrase] * int(selected_boxes.shape[0]))

    if not all_boxes:
        return boxes.new_zeros((0, 4)).cpu(), logits.new_zeros((0,)).cpu(), []
    return torch.cat(all_boxes, dim=0).cpu(), torch.cat(all_logits, dim=0).cpu(), all_phrases


def cxcywh_to_xyxy_pixels(box: Iterable[float], width: int, height: int) -> list[float]:
    cx, cy, bw, bh = [float(value) for value in box]
    x0 = (cx - bw / 2.0) * width
    y0 = (cy - bh / 2.0) * height
    x1 = (cx + bw / 2.0) * width
    y1 = (cy + bh / 2.0) * height
    return [max(0.0, x0), max(0.0, y0), min(float(width), x1), min(float(height), y1)]


def draw_annotations(image_source, boxes, logits, phrases: list[str], output_path: Path) -> list[dict[str, object]]:
    from PIL import Image, ImageDraw, ImageFont

    image = Image.fromarray(image_source).convert("RGB")
    width, height = image.size
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    records: list[dict[str, object]] = []
    palette = [
        (230, 25, 75),
        (60, 180, 75),
        (255, 225, 25),
        (0, 130, 200),
        (245, 130, 48),
        (145, 30, 180),
        (70, 240, 240),
        (240, 50, 230),
    ]

    for index, (box, logit, phrase) in enumerate(zip(boxes.tolist(), logits.tolist(), phrases)):
        xyxy = cxcywh_to_xyxy_pixels(box, width, height)
        color = palette[index % len(palette)]
        label = f"{phrase} {float(logit):.2f}"
        draw.rectangle(xyxy, outline=color, width=4)
        if hasattr(draw, "textbbox"):
            text_box = draw.textbbox((xyxy[0], xyxy[1]), label, font=font)
        else:
            text_width, text_height = draw.textsize(label, font=font)
            text_box = (xyxy[0], xyxy[1], xyxy[0] + text_width, xyxy[1] + text_height)
        draw.rectangle(text_box, fill=color)
        draw.text((xyxy[0], xyxy[1]), label, fill="white", font=font)
        records.append(
            {
                "phrase": phrase,
                "confidence": float(logit),
                "box_normalized_cxcywh": [float(value) for value in box],
                "box_pixel_xyxy": [float(value) for value in xyxy],
            }
        )

    image.save(output_path)
    return records


def write_json(args: argparse.Namespace, output_dir: Path, payload: dict[str, object]) -> None:
    if args.json_output is None:
        return
    if args.json_output == "-":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    json_path = Path(args.json_output)
    if not json_path.is_absolute():
        json_path = output_dir / json_path
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config_path, checkpoint_path, image_path, output_dir, caption, token_spans, device = validate_args(args)

    if args.validate_only:
        print("validation ok")
        return 0

    load_image, load_model, predict = import_groundingdino_api()
    image_source, image = load_image(str(image_path))
    model = load_model(str(config_path), str(checkpoint_path), device=device)

    raw_path = output_dir / "raw_image.jpg"
    pred_path = output_dir / "pred.jpg"

    from PIL import Image

    Image.fromarray(image_source).save(raw_path)
    if token_spans is not None:
        boxes, logits, phrases = predict_with_token_spans(model, image, caption, token_spans, args.box_threshold, device)
        text_threshold = None
    else:
        boxes, logits, phrases = predict(
            model=model,
            image=image,
            caption=caption,
            box_threshold=args.box_threshold,
            text_threshold=args.text_threshold,
            device=device,
            remove_combined=args.remove_combined,
        )
        text_threshold = args.text_threshold

    records = draw_annotations(image_source, boxes, logits, phrases, pred_path)
    if not records:
        print(
            "warning: no detections; try lower thresholds, add periods between categories, or verify the prompt names visible objects",
            file=sys.stderr,
        )

    payload = {
        "caption": caption,
        "device": device,
        "box_threshold": args.box_threshold,
        "text_threshold": text_threshold,
        "token_spans": token_spans,
        "outputs": {"raw_image": str(raw_path), "annotated_image": str(pred_path)},
        "detections": records,
    }
    write_json(args, output_dir, payload)
    print(f"wrote {raw_path}")
    print(f"wrote {pred_path}")
    print(f"detections: {len(records)}")
    return 0


def main() -> int:
    try:
        return run()
    except UserError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        message = str(exc)
        if "_C" in message or "CUDA_HOME" in message or "CUDA" in message:
            print(
                "error: GroundingDINO runtime failed, likely due to CUDA/custom C++ extension setup: " + message,
                file=sys.stderr,
            )
            return 3
        print(f"error: GroundingDINO runtime failed: {message}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
