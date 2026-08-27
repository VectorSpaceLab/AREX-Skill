#!/usr/bin/env python3
"""Render safe local previews for X-AnyLabeling XLABEL annotations.

The script intentionally never installs dependencies. It imports cv2/numpy only
after argparse has handled --help, then exits with a clear message if they are
not available.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Iterable, Optional

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".tif",
    ".tiff",
    ".heic",
    ".heif",
}

SUPPORTED_SHAPE_TYPES = {
    "polygon",
    "rectangle",
    "rotation",
    "quadrilateral",
    "point",
    "line",
    "linestrip",
    "circle",
    "cuboid",
}

FALSE_TOKENS = {"", "0", "false", "no", "none", "off", "omit", "omitted"}
TRUE_TOKENS = {"1", "true", "yes", "on"}


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render image previews from X-AnyLabeling XLABEL JSON files. "
            "No dependency installation is attempted."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--images",
        required=True,
        help="Image file or image directory. Directories are scanned recursively.",
    )
    parser.add_argument(
        "--labels",
        required=True,
        help=(
            "Label JSON file or label directory. For a directory, each image "
            "uses <image_stem>.json."
        ),
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Directory where preview images are written.",
    )
    parser.add_argument(
        "--classes",
        nargs="*",
        default=None,
        help=(
            "Optional class filter. Pass class names, comma-separated values, "
            "or a one-label-per-line classes.txt file. Omit to draw all labels."
        ),
    )
    parser.add_argument(
        "--shape-types",
        nargs="*",
        default=None,
        help=(
            "Optional shape-type filter. Values can be space- or comma-separated. "
            f"Supported: {', '.join(sorted(SUPPORTED_SHAPE_TYPES))}."
        ),
    )
    parser.add_argument(
        "--save-video",
        nargs="?",
        const="preview.mp4",
        default=None,
        help=(
            "Optionally write an MP4 from preview frames. Omit or pass false/no/0 "
            "to disable; pass true or a filename/path to enable."
        ),
    )
    parser.add_argument(
        "--video-fps",
        type=float,
        default=10.0,
        help="Frame rate for --save-video.",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.28,
        help="Fill opacity for closed shapes, from 0.0 to 1.0.",
    )
    parser.add_argument(
        "--line-width",
        type=int,
        default=2,
        help="Outline thickness in pixels.",
    )
    return parser.parse_args(argv)


def require_dependencies():
    missing = []
    try:
        import cv2  # type: ignore
    except ImportError:
        cv2 = None
        missing.append("opencv-python (cv2)")
    try:
        import numpy as np  # type: ignore
    except ImportError:
        np = None
        missing.append("numpy")
    if missing:
        raise RuntimeError(
            "Missing preview dependency/dependencies: "
            + ", ".join(missing)
            + ". Install them in your chosen Python environment; this script "
            "does not auto-install packages."
        )
    return cv2, np


def natural_key(path: Path):
    parts = re.split(r"(\d+)", str(path).lower())
    return [int(p) if p.isdigit() else p for p in parts]


def split_values(values: Optional[Iterable[str]]) -> Optional[list[str]]:
    if values is None:
        return None
    result: list[str] = []
    for value in values:
        for item in str(value).split(","):
            item = item.strip()
            if item:
                result.append(item)
    return result


def load_classes(values: Optional[list[str]]) -> Optional[set[str]]:
    items = split_values(values)
    if items is None:
        return None
    if len(items) == 1:
        maybe_path = Path(items[0]).expanduser()
        if maybe_path.is_file():
            with maybe_path.open("r", encoding="utf-8") as f:
                return {line.strip() for line in f if line.strip()}
    return set(items)


def load_shape_types(values: Optional[list[str]]) -> Optional[set[str]]:
    items = split_values(values)
    if items is None:
        return None
    normalized = {item.lower() for item in items}
    unknown = sorted(normalized - SUPPORTED_SHAPE_TYPES)
    if unknown:
        raise ValueError(
            "Unsupported --shape-types value(s): "
            + ", ".join(unknown)
            + ". Supported values: "
            + ", ".join(sorted(SUPPORTED_SHAPE_TYPES))
        )
    return normalized


def collect_images(images_path: Path) -> tuple[list[Path], Optional[Path]]:
    if images_path.is_file():
        if images_path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError(f"Unsupported image extension: {images_path}")
        return [images_path], images_path.parent
    if images_path.is_dir():
        images = [
            path
            for path in images_path.rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        ]
        return sorted(images, key=natural_key), images_path
    raise FileNotFoundError(f"--images path does not exist: {images_path}")


def resolve_label_file(image_path: Path, labels_path: Path, image_count: int) -> Path:
    if labels_path.is_file():
        if image_count != 1:
            raise ValueError(
                "--labels may be a single JSON file only when --images is a single image"
            )
        return labels_path
    if labels_path.is_dir():
        return labels_path / f"{image_path.stem}.json"
    raise FileNotFoundError(f"--labels path does not exist: {labels_path}")


def imread_unicode(cv2, np, path: Path):
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
    except OSError as exc:
        raise OSError(f"failed to read image bytes: {path}: {exc}") from exc
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"failed to decode image: {path}")
    return image


def imwrite_unicode(cv2, path: Path, image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ext = path.suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}:
        ext = ".jpg"
    ok, buffer = cv2.imencode(ext, image)
    if not ok:
        raise ValueError(f"failed to encode preview image: {path}")
    buffer.tofile(str(path))


def color_for(label: str, index: int) -> tuple[int, int, int]:
    seed = sum((i + 1) * ord(ch) for i, ch in enumerate(label or str(index)))
    # BGR colors kept bright enough for dark/light images.
    return (
        80 + (seed * 37) % 176,
        80 + (seed * 57) % 176,
        80 + (seed * 97) % 176,
    )


def to_points(np, raw_points) -> Optional[object]:
    if not isinstance(raw_points, list):
        return None
    points = []
    for point in raw_points:
        if (
            not isinstance(point, (list, tuple))
            or len(point) < 2
            or not isinstance(point[0], (int, float))
            or not isinstance(point[1], (int, float))
        ):
            return None
        points.append([int(round(float(point[0]))), int(round(float(point[1])))])
    if not points:
        return None
    return np.array(points, dtype=np.int32)


def rectangle_points_from_any(np, pts):
    if len(pts) == 2:
        x1, y1 = pts[0]
        x2, y2 = pts[1]
        xmin, xmax = sorted([int(x1), int(x2)])
        ymin, ymax = sorted([int(y1), int(y2)])
        return np.array([[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]], dtype=np.int32)
    if len(pts) >= 4:
        x_min = int(min(p[0] for p in pts))
        x_max = int(max(p[0] for p in pts))
        y_min = int(min(p[1] for p in pts))
        y_max = int(max(p[1] for p in pts))
        return np.array([[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]], dtype=np.int32)
    return None


def draw_dashed_line(cv2, image, p1, p2, color, thickness=1, dash=8, gap=6):
    x1, y1 = int(p1[0]), int(p1[1])
    x2, y2 = int(p2[0]), int(p2[1])
    length = math.hypot(x2 - x1, y2 - y1)
    if length <= 0:
        return
    dx = (x2 - x1) / length
    dy = (y2 - y1) / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        start_pt = (int(round(x1 + dx * pos)), int(round(y1 + dy * pos)))
        end_pt = (int(round(x1 + dx * end)), int(round(y1 + dy * end)))
        cv2.line(image, start_pt, end_pt, color, thickness, cv2.LINE_AA)
        pos += dash + gap


def draw_label(cv2, image, text: str, point, color) -> None:
    if not text:
        return
    x, y = int(point[0]), int(point[1])
    h, w = image.shape[:2]
    x = max(0, min(w - 1, x))
    y = max(14, min(h - 1, y))
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.45
    thickness = 1
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)
    x2 = min(w - 1, x + tw + 6)
    y1 = max(0, y - th - baseline - 6)
    cv2.rectangle(image, (x, y1), (x2, y + baseline), color, -1)
    cv2.putText(image, text, (x + 3, y - 4), font, scale, (0, 0, 0), thickness, cv2.LINE_AA)


def summarize_top_fields(payload: dict) -> str:
    parts: list[str] = []
    if payload.get("checked") is True:
        parts.append("checked")
    else:
        parts.append("unchecked")
    flags = payload.get("flags")
    if isinstance(flags, dict):
        active = [str(k) for k, v in flags.items() if v is True]
        if active:
            parts.append("flags=" + ",".join(active[:6]) + ("…" if len(active) > 6 else ""))
    vqa = payload.get("vqaData")
    if isinstance(vqa, dict) and vqa:
        parts.append("vqa=" + ",".join(list(map(str, vqa.keys()))[:4]) + ("…" if len(vqa) > 4 else ""))
    chat = payload.get("chat_history")
    if isinstance(chat, list) and chat:
        parts.append(f"chat={len(chat)} msgs")
    return " | ".join(parts)


def draw_banner(cv2, image, text: str) -> None:
    if not text:
        return
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.5
    thickness = 1
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)
    cv2.rectangle(image, (0, 0), (min(image.shape[1] - 1, tw + 12), th + baseline + 10), (255, 255, 255), -1)
    cv2.putText(image, text, (6, th + 4), font, scale, (20, 20, 20), thickness, cv2.LINE_AA)


def draw_shapes(cv2, np, image, payload: dict, class_filter: Optional[set[str]], shape_filter: Optional[set[str]], alpha: float, line_width: int) -> tuple[int, list[str]]:
    warnings: list[str] = []
    shapes = payload.get("shapes", [])
    if not isinstance(shapes, list):
        return 0, ["top-level 'shapes' is not a list"]

    fill_alpha = max(0.0, min(1.0, float(alpha)))

    def blend_fill(draw_func) -> None:
        if fill_alpha <= 0:
            return
        layer = image.copy()
        draw_func(layer)
        cv2.addWeighted(layer, fill_alpha, image, 1.0 - fill_alpha, 0, dst=image)

    drawn = 0
    skipped_labels: set[str] = set()

    for idx, shape in enumerate(shapes):
        if not isinstance(shape, dict):
            warnings.append(f"shape[{idx}] is not an object")
            continue
        label = str(shape.get("label") or "")
        shape_type = str(shape.get("shape_type") or "polygon").lower()
        if shape_type not in SUPPORTED_SHAPE_TYPES:
            warnings.append(f"shape[{idx}] has unsupported shape_type={shape_type!r}")
            continue
        if shape_filter is not None and shape_type not in shape_filter:
            continue
        if class_filter is not None and label not in class_filter:
            if label:
                skipped_labels.add(label)
            continue

        pts = to_points(np, shape.get("points"))
        if pts is None:
            warnings.append(f"shape[{idx}] has invalid points")
            continue
        color = color_for(label, idx)
        label_text = label or f"shape[{idx}]"
        if shape.get("group_id") is not None:
            label_text += f" g={shape.get('group_id')}"
        if shape.get("locked") is True:
            label_text += " lock"

        try:
            if shape_type == "rectangle":
                rect = rectangle_points_from_any(np, pts)
                if rect is None:
                    warnings.append(f"shape[{idx}] rectangle needs 2 or 4 points")
                    continue
                blend_fill(lambda layer, poly=rect.reshape((-1, 1, 2)): cv2.fillPoly(layer, [poly], color))
                cv2.polylines(image, [rect.reshape((-1, 1, 2))], True, color, line_width, cv2.LINE_AA)
                draw_label(cv2, image, label_text, rect[0], color)
            elif shape_type in {"polygon", "rotation", "quadrilateral"}:
                required = 3 if shape_type == "polygon" else 4
                if len(pts) < required:
                    warnings.append(f"shape[{idx}] {shape_type} needs at least {required} points")
                    continue
                poly = pts.reshape((-1, 1, 2))
                blend_fill(lambda layer, poly=poly: cv2.fillPoly(layer, [poly], color))
                cv2.polylines(image, [poly], True, color, line_width, cv2.LINE_AA)
                draw_label(cv2, image, label_text, pts[0], color)
            elif shape_type == "point":
                if len(pts) != 1:
                    warnings.append(f"shape[{idx}] point needs exactly 1 point")
                    continue
                cv2.circle(image, tuple(pts[0]), max(3, line_width + 3), color, -1, cv2.LINE_AA)
                draw_label(cv2, image, label_text, pts[0], color)
            elif shape_type == "line":
                if len(pts) < 2:
                    warnings.append(f"shape[{idx}] line needs 2 points")
                    continue
                cv2.line(image, tuple(pts[0]), tuple(pts[1]), color, line_width, cv2.LINE_AA)
                draw_label(cv2, image, label_text, pts[0], color)
            elif shape_type == "linestrip":
                if len(pts) < 2:
                    warnings.append(f"shape[{idx}] linestrip needs at least 2 points")
                    continue
                cv2.polylines(image, [pts.reshape((-1, 1, 2))], False, color, line_width, cv2.LINE_AA)
                draw_label(cv2, image, label_text, pts[0], color)
            elif shape_type == "circle":
                if len(pts) != 2:
                    warnings.append(f"shape[{idx}] circle needs exactly 2 points")
                    continue
                radius = int(round(math.hypot(int(pts[0][0]) - int(pts[1][0]), int(pts[0][1]) - int(pts[1][1]))))
                blend_fill(lambda layer, center=tuple(pts[0]), radius=radius: cv2.circle(layer, center, radius, color, -1, cv2.LINE_AA))
                cv2.circle(image, tuple(pts[0]), radius, color, line_width, cv2.LINE_AA)
                draw_label(cv2, image, label_text, pts[0], color)
            elif shape_type == "cuboid":
                if len(pts) != 8:
                    warnings.append(f"shape[{idx}] cuboid needs exactly 8 points")
                    continue
                front = pts[:4]
                back = pts[4:8]
                cv2.polylines(image, [front.reshape((-1, 1, 2))], True, color, line_width, cv2.LINE_AA)
                for a, b in zip(back, list(back[1:]) + [back[0]]):
                    draw_dashed_line(cv2, image, a, b, color, max(1, line_width))
                for a, b in zip(front, back):
                    cv2.line(image, tuple(a), tuple(b), color, line_width, cv2.LINE_AA)
                cv2.line(image, tuple(front[0]), tuple(front[1]), (0, 165, 255), line_width + 1, cv2.LINE_AA)
                draw_label(cv2, image, label_text, front[0], color)
            drawn += 1
        except Exception as exc:  # defensive per-shape isolation
            warnings.append(f"shape[{idx}] draw failed: {exc}")

    if skipped_labels:
        warnings.append(
            "skipped labels not in --classes: " + ", ".join(sorted(skipped_labels))
        )
    return drawn, warnings


def output_path_for(image_path: Path, images_root: Optional[Path], output_dir: Path) -> Path:
    if images_root and images_root.is_dir():
        try:
            relative = image_path.relative_to(images_root)
        except ValueError:
            relative = Path(image_path.name)
    else:
        relative = Path(image_path.name)
    return output_dir / relative.with_suffix(".preview.jpg")


def resolve_video_path(save_video: Optional[str], output_dir: Path) -> Optional[Path]:
    if save_video is None:
        return None
    token = str(save_video).strip()
    if token.lower() in FALSE_TOKENS:
        return None
    if token.lower() in TRUE_TOKENS:
        token = "preview.mp4"
    path = Path(token).expanduser()
    if not path.is_absolute():
        path = output_dir / path
    return path


def write_video(cv2, preview_paths: list[Path], video_path: Path, fps: float) -> None:
    if not preview_paths:
        raise ValueError("no preview frames available for --save-video")
    first = cv2.imread(str(preview_paths[0]))
    if first is None:
        raise ValueError(f"failed to read first preview frame: {preview_paths[0]}")
    height, width = first.shape[:2]
    video_path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(video_path), fourcc, float(fps), (width, height))
    if not writer.isOpened():
        raise ValueError(f"failed to open VideoWriter for {video_path}")
    try:
        for frame_path in preview_paths:
            frame = cv2.imread(str(frame_path))
            if frame is None:
                print(f"warning: skip unreadable preview frame for video: {frame_path}", file=sys.stderr)
                continue
            if frame.shape[:2] != (height, width):
                frame = cv2.resize(frame, (width, height))
            writer.write(frame)
    finally:
        writer.release()


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        cv2, np = require_dependencies()
        images_arg = Path(args.images).expanduser()
        labels_arg = Path(args.labels).expanduser()
        output_dir = Path(args.output).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)
        class_filter = load_classes(args.classes)
        shape_filter = load_shape_types(args.shape_types)
        image_paths, images_root = collect_images(images_arg)
        if not image_paths:
            raise ValueError(f"no supported images found under {images_arg}")
        video_path = resolve_video_path(args.save_video, output_dir)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    preview_paths: list[Path] = []
    errors = 0
    total_drawn = 0

    for image_path in image_paths:
        label_path = None
        try:
            label_path = resolve_label_file(image_path, labels_arg, len(image_paths))
            image = imread_unicode(cv2, np, image_path)
            payload = {}
            if label_path.exists():
                with label_path.open("r", encoding="utf-8") as f:
                    payload = json.load(f)
                if not isinstance(payload, dict):
                    raise ValueError("label payload must be a JSON object")
                drawn, warnings = draw_shapes(
                    cv2,
                    np,
                    image,
                    payload,
                    class_filter,
                    shape_filter,
                    args.alpha,
                    max(1, int(args.line_width)),
                )
                total_drawn += drawn
                for warning in warnings:
                    print(f"warning: {label_path}: {warning}", file=sys.stderr)
            else:
                print(f"warning: missing label for {image_path}: expected {label_path}", file=sys.stderr)
            draw_banner(cv2, image, summarize_top_fields(payload))
            preview_path = output_path_for(image_path, images_root, output_dir)
            imwrite_unicode(cv2, preview_path, image)
            preview_paths.append(preview_path)
        except Exception as exc:
            errors += 1
            location = f"{image_path}"
            if label_path is not None:
                location += f" (label {label_path})"
            print(f"error: {location}: {exc}", file=sys.stderr)

    if video_path is not None:
        try:
            write_video(cv2, preview_paths, video_path, args.video_fps)
            print(f"wrote video preview: {video_path}")
        except Exception as exc:
            errors += 1
            print(f"error: video preview failed: {exc}", file=sys.stderr)

    print(
        f"wrote {len(preview_paths)} preview image(s) to {output_dir}; "
        f"drawn shape count: {total_drawn}; error count: {errors}"
    )
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
