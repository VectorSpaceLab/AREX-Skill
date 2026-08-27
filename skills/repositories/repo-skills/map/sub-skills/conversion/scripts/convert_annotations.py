#!/usr/bin/env python3
"""Safe annotation/result converters for the mAP evaluator text format.

The original repository shipped small one-off converters that assumed a fixed
checkout layout and moved source files into backup folders. This bundled helper
keeps the same format conventions while requiring explicit input and output
paths. It reads source annotations/results and writes evaluator-ready .txt files;
it never renames, moves, or deletes source files.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
    ".webp",
}


class ConversionError(Exception):
    """Raised for user-fixable conversion errors."""


def format_number(value: object) -> str:
    """Format numeric coordinates/confidences without unnecessary .0 suffixes."""
    if isinstance(value, str):
        value = value.strip()
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:g}"


def parse_float(token: str, source: str) -> float:
    try:
        return float(token)
    except Exception as exc:  # noqa: BLE001 - keep a clear CLI error
        raise ConversionError(f"{source}: expected a numeric value, got {token!r}") from exc


def parse_class_id(token: str, classes: Sequence[str], source: str) -> str:
    value = parse_float(token, source)
    if not value.is_integer():
        raise ConversionError(f"{source}: class id {token!r} is not an integer index")
    idx = int(value)
    if idx < 0 or idx >= len(classes):
        raise ConversionError(
            f"{source}: class id {idx} is outside class_list range 0..{len(classes) - 1}"
        )
    return classes[idx]


def load_class_list(path: Path) -> List[str]:
    if not path.exists():
        raise ConversionError(f"class list not found: {path}")
    classes = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    if not classes:
        raise ConversionError(f"class list is empty: {path}")
    for idx, name in enumerate(classes, start=1):
        if not name:
            raise ConversionError(
                f"class list contains an empty class name at line {idx}; blank lines shift class ids"
            )
        if any(ch.isspace() for ch in name):
            raise ConversionError(
                f"class list line {idx} contains whitespace; evaluator class names must be single tokens"
            )
    return classes


def collect_files(input_path: Path, suffixes: Sequence[str], label: str) -> List[Path]:
    if not input_path.exists():
        raise ConversionError(f"{label} input path not found: {input_path}")
    suffixes_lower = tuple(s.lower() for s in suffixes)
    if input_path.is_file():
        if input_path.suffix.lower() not in suffixes_lower:
            raise ConversionError(
                f"{label} input file must have one of {', '.join(suffixes)}: {input_path}"
            )
        return [input_path]
    files = sorted(p for p in input_path.iterdir() if p.is_file() and p.suffix.lower() in suffixes_lower)
    if not files:
        raise ConversionError(
            f"no {', '.join(suffixes)} files found in {label} input directory: {input_path}"
        )
    return files


def write_output(path: Path, lines: Iterable[str], overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise ConversionError(f"refusing to overwrite existing output {path}; pass --overwrite if intentional")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(line if line.endswith("\n") else line + "\n" for line in lines)
    path.write_text(text, encoding="utf-8")


def voc_xml_to_gt(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    files = collect_files(Path(args.input), [".xml"], "VOC XML ground-truth")
    count = 0
    for xml_path in files:
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError as exc:
            raise ConversionError(f"{xml_path}: invalid XML: {exc}") from exc
        rows: List[str] = []
        for obj_idx, obj in enumerate(root.findall("object"), start=1):
            source = f"{xml_path}: object #{obj_idx}"
            name = (obj.findtext("name") or "").strip()
            if not name:
                raise ConversionError(f"{source}: missing object/name")
            if any(ch.isspace() for ch in name):
                raise ConversionError(f"{source}: class name {name!r} contains whitespace")
            bndbox = obj.find("bndbox")
            if bndbox is None:
                raise ConversionError(f"{source}: missing bndbox")
            coords = []
            for tag in ("xmin", "ymin", "xmax", "ymax"):
                value = (bndbox.findtext(tag) or "").strip()
                if not value:
                    raise ConversionError(f"{source}: missing bndbox/{tag}")
                coords.append(format_number(value))
            row = f"{name} {' '.join(coords)}"
            difficult = (obj.findtext("difficult") or "").strip().lower()
            if not args.drop_difficult and difficult in {"1", "true", "yes", "difficult"}:
                row += " difficult"
            rows.append(row)
        write_output(output_dir / f"{xml_path.stem}.txt", rows, args.overwrite)
        count += 1
    print(f"Converted {count} VOC XML file(s) to ground-truth text in {output_dir}")
    return 0


def parse_positive_int(token: str, source: str) -> int:
    value = parse_float(token, source)
    if not value.is_integer():
        raise ConversionError(f"{source}: expected a whole positive integer, got {token!r}")
    integer = int(value)
    if integer <= 0:
        raise ConversionError(f"{source}: expected a positive integer, got {integer}")
    return integer


def load_image_size_file(path: Optional[str]) -> Dict[str, Tuple[int, int]]:
    if not path:
        return {}
    size_path = Path(path)
    if not size_path.exists():
        raise ConversionError(f"image size file not found: {size_path}")
    result: Dict[str, Tuple[int, int]] = {}
    for line_no, raw in enumerate(size_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = re.split(r"[\s,]+", line)
        if len(parts) != 3:
            raise ConversionError(
                f"{size_path}:{line_no}: expected '<image_id> <width> <height>'"
            )
        image_id, width_s, height_s = parts
        width = parse_positive_int(width_s, f"{size_path}:{line_no} width")
        height = parse_positive_int(height_s, f"{size_path}:{line_no} height")
        result[image_id] = (width, height)
        result[Path(image_id).stem] = (width, height)
    return result


def jpeg_size(path: Path) -> Optional[Tuple[int, int]]:
    with path.open("rb") as fh:
        if fh.read(2) != b"\xff\xd8":
            return None
        while True:
            marker_prefix = fh.read(1)
            if not marker_prefix:
                return None
            if marker_prefix != b"\xff":
                continue
            marker = fh.read(1)
            while marker == b"\xff":
                marker = fh.read(1)
            if marker in {b"\xd8", b"\xd9"}:
                continue
            length_bytes = fh.read(2)
            if len(length_bytes) != 2:
                return None
            length = struct.unpack(">H", length_bytes)[0]
            if length < 2:
                return None
            if marker and marker[0] in {
                0xC0,
                0xC1,
                0xC2,
                0xC3,
                0xC5,
                0xC6,
                0xC7,
                0xC9,
                0xCA,
                0xCB,
                0xCD,
                0xCE,
                0xCF,
            }:
                data = fh.read(5)
                if len(data) != 5:
                    return None
                height, width = struct.unpack(">HH", data[1:5])
                return int(width), int(height)
            fh.seek(length - 2, 1)


def stdlib_image_size(path: Path) -> Optional[Tuple[int, int]]:
    try:
        with path.open("rb") as fh:
            header = fh.read(32)
        if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
            width, height = struct.unpack(">II", header[16:24])
            return int(width), int(height)
        if header[:6] in {b"GIF87a", b"GIF89a"} and len(header) >= 10:
            width, height = struct.unpack("<HH", header[6:10])
            return int(width), int(height)
        if header.startswith(b"\xff\xd8"):
            return jpeg_size(path)
    except Exception:
        return None
    return None


def optional_library_image_size(path: Path) -> Optional[Tuple[int, int]]:
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as image:
            width, height = image.size
            return int(width), int(height)
    except Exception:
        pass
    try:
        import cv2  # type: ignore

        image = cv2.imread(str(path))
        if image is not None:
            height, width = image.shape[:2]
            return int(width), int(height)
    except Exception:
        pass
    return None


def read_image_size(path: Path) -> Tuple[int, int]:
    size = stdlib_image_size(path) or optional_library_image_size(path)
    if size is None:
        raise ConversionError(
            f"could not read dimensions for image {path}; provide --image-size or --image-size-file, "
            "or install Pillow/OpenCV for this image type"
        )
    width, height = size
    if width <= 0 or height <= 0:
        raise ConversionError(f"invalid dimensions for image {path}: {width}x{height}")
    return width, height


def find_image_for_stem(image_dir: Path, stem: str) -> Optional[Path]:
    if not image_dir.exists():
        raise ConversionError(f"image directory not found: {image_dir}")
    matches = sorted(
        p
        for p in image_dir.iterdir()
        if p.is_file() and p.stem == stem and p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not matches:
        return None
    if len(matches) > 1:
        raise ConversionError(f"multiple images match label stem {stem!r}: {matches}")
    return matches[0]


def yolo_size_for_file(label_path: Path, args: argparse.Namespace, sizes: Dict[str, Tuple[int, int]]) -> Tuple[int, int]:
    if label_path.name in sizes:
        return sizes[label_path.name]
    if label_path.stem in sizes:
        return sizes[label_path.stem]
    if args.image_size:
        width, height = args.image_size
        if width <= 0 or height <= 0:
            raise ConversionError("--image-size width and height must be positive")
        return int(width), int(height)
    if args.image_dir:
        image = find_image_for_stem(Path(args.image_dir), label_path.stem)
        if image is None:
            raise ConversionError(
                f"image not found for YOLO label file {label_path.name}; provide --image-size, "
                "--image-size-file, or a matching image in --image-dir"
            )
        return read_image_size(image)
    raise ConversionError(
        "YOLO ground-truth conversion needs image dimensions; pass --image-size, "
        "--image-size-file, or --image-dir"
    )


def yolo_box_to_voc(
    x_c_n: str,
    y_c_n: str,
    width_n: str,
    height_n: str,
    img_width: int,
    img_height: int,
    source: str,
) -> Tuple[int, int, int, int]:
    x_c = parse_float(x_c_n, source) * img_width
    y_c = parse_float(y_c_n, source) * img_height
    width = parse_float(width_n, source) * img_width
    height = parse_float(height_n, source) * img_height
    if width < 0 or height < 0:
        raise ConversionError(f"{source}: YOLO width and height must be non-negative")
    half_width = width / 2.0
    half_height = height / 2.0
    # Match the legacy converter: VOC coordinates are 1-based and int-truncated.
    left = int(x_c - half_width) + 1
    top = int(y_c - half_height) + 1
    right = int(x_c + half_width) + 1
    bottom = int(y_c + half_height) + 1
    return left, top, right, bottom


def yolo_gt_to_text(args: argparse.Namespace) -> int:
    classes = load_class_list(Path(args.class_list))
    sizes = load_image_size_file(args.image_size_file)
    files = collect_files(Path(args.input), [".txt"], "YOLO ground-truth")
    output_dir = Path(args.output_dir)
    count = 0
    for label_path in files:
        img_width, img_height = yolo_size_for_file(label_path, args, sizes)
        rows: List[str] = []
        for line_no, raw in enumerate(label_path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw.strip()
            if not line:
                continue
            parts = line.split()
            source = f"{label_path}:{line_no}"
            if len(parts) != 5:
                raise ConversionError(
                    f"{source}: expected 'class_id x_center y_center width height', got {len(parts)} fields"
                )
            class_name = parse_class_id(parts[0], classes, source)
            left, top, right, bottom = yolo_box_to_voc(*parts[1:], img_width, img_height, source)
            rows.append(f"{class_name} {left} {top} {right} {bottom}")
        write_output(output_dir / f"{label_path.stem}.txt", rows, args.overwrite)
        count += 1
    print(f"Converted {count} YOLO ground-truth file(s) to evaluator text in {output_dir}")
    return 0


def darkflow_json_to_dr(args: argparse.Namespace) -> int:
    files = collect_files(Path(args.input), [".json"], "darkflow JSON detection-results")
    output_dir = Path(args.output_dir)
    count = 0
    for json_path in files:
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConversionError(f"{json_path}: invalid JSON: {exc}") from exc
        if not isinstance(data, list):
            raise ConversionError(f"{json_path}: expected a JSON list of detection objects")
        rows: List[str] = []
        for obj_idx, obj in enumerate(data, start=1):
            source = f"{json_path}: object #{obj_idx}"
            if not isinstance(obj, dict):
                raise ConversionError(f"{source}: expected an object")
            try:
                label = str(obj["label"]).strip()
                confidence = format_number(obj["confidence"])
                top_left = obj["topleft"]
                bottom_right = obj["bottomright"]
                left = format_number(top_left["x"])
                top = format_number(top_left["y"])
                right = format_number(bottom_right["x"])
                bottom = format_number(bottom_right["y"])
            except KeyError as exc:
                raise ConversionError(f"{source}: missing key {exc.args[0]!r}") from exc
            except TypeError as exc:
                raise ConversionError(f"{source}: malformed topleft/bottomright object") from exc
            if not label or any(ch.isspace() for ch in label):
                raise ConversionError(f"{source}: label must be a non-empty single token")
            rows.append(f"{label} {confidence} {left} {top} {right} {bottom}")
        write_output(output_dir / f"{json_path.stem}.txt", rows, args.overwrite)
        count += 1
    print(f"Converted {count} darkflow JSON file(s) to detection-results text in {output_dir}")
    return 0


def image_stem_from_path(image_path: str) -> str:
    normalized = image_path.replace("\\", "/").rstrip("/")
    name = normalized.rsplit("/", 1)[-1]
    return Path(name).stem


def parse_darknet_detection(line: str, source: str) -> Optional[str]:
    match = re.match(r"^\s*(?P<class>[^:]+):\s*(?P<confidence>-?\d+(?:\.\d+)?)%\s*\((?P<bbox>.*)\)\s*$", line)
    if not match:
        return None
    class_name = match.group("class").strip()
    if not class_name or any(ch.isspace() for ch in class_name):
        raise ConversionError(f"{source}: class name must be a non-empty single token")
    bbox_text = match.group("bbox")
    values: Dict[str, int] = {}
    for key in ("left_x", "top_y", "width", "height"):
        key_match = re.search(rf"{key}\s*:\s*(-?\d+)", bbox_text)
        if not key_match:
            raise ConversionError(f"{source}: missing {key} in darknet bbox")
        values[key] = int(key_match.group(1))
    left = values["left_x"]
    top = values["top_y"]
    right = left + values["width"]
    bottom = top + values["height"]
    confidence = parse_float(match.group("confidence"), source) / 100.0
    return f"{class_name} {format_number(confidence)} {left} {top} {right} {bottom}"


def darknet_result_to_dr(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.exists():
        raise ConversionError(f"darknet result input not found: {input_path}")
    output_dir = Path(args.output_dir)
    image_ext = args.image_ext if args.image_ext.startswith(".") else f".{args.image_ext}"
    section_re = re.compile(r"Enter Image Path:\s*(.*?)" + re.escape(image_ext), re.IGNORECASE)
    outputs: Dict[str, List[str]] = {}
    current_stem: Optional[str] = None
    saw_section = False
    for line_no, raw in enumerate(input_path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        source = f"{input_path}:{line_no}"
        section = section_re.search(raw)
        if section:
            image_path = section.group(1) + image_ext
            current_stem = image_stem_from_path(image_path)
            if not current_stem:
                raise ConversionError(f"{source}: could not derive image name from {image_path!r}")
            outputs.setdefault(current_stem, [])
            saw_section = True
            continue
        if current_stem is None:
            continue
        parsed = parse_darknet_detection(raw, source)
        if parsed is not None:
            outputs[current_stem].append(parsed)
            continue
        stripped = raw.strip()
        # Ignore benign log lines, but fail on bbox-like malformed detection rows.
        if stripped and "%" in stripped and ":" in stripped:
            raise ConversionError(f"{source}: unsupported darknet detection row: {stripped!r}")
    if not saw_section:
        raise ConversionError(
            f"no darknet image sections found in {input_path}; expected lines containing 'Enter Image Path:'"
        )
    for stem, rows in outputs.items():
        write_output(output_dir / f"{stem}.txt", rows, args.overwrite)
    print(f"Converted {len(outputs)} darknet result section(s) to detection-results text in {output_dir}")
    return 0


def safe_path_component(component: str) -> str:
    cleaned = component.replace(":", "_").strip()
    if cleaned in {"", ".", ".."}:
        raise ConversionError(f"unsafe empty/path-traversal component in image path {component!r}")
    return cleaned


def with_txt_suffix(name: str) -> str:
    p = Path(name)
    if p.suffix:
        return p.with_suffix(".txt").name
    return p.name + ".txt"


def keras_output_path(output_dir: Path, image_path: str, recursive: bool, root: Optional[str]) -> Path:
    normalized = image_path.replace("\\", "/")
    if recursive:
        rel = normalized
        if root:
            root_norm = root.replace("\\", "/").rstrip("/")
            if rel == root_norm:
                raise ConversionError(f"image path {image_path!r} equals --keras-root and has no file name")
            if not rel.startswith(root_norm + "/"):
                raise ConversionError(f"image path {image_path!r} is not under --keras-root {root!r}")
            rel = rel[len(root_norm) + 1 :]
        rel = rel.lstrip("/")
        parts = [safe_path_component(part) for part in rel.split("/") if part not in {"", "."}]
        if not parts:
            raise ConversionError(f"could not derive recursive output path from image path {image_path!r}")
        parts[-1] = with_txt_suffix(parts[-1])
        return output_dir.joinpath(*parts)
    flat = normalized.lstrip("/").replace("/", "__")
    if not flat:
        raise ConversionError(f"could not derive flat output file name from image path {image_path!r}")
    return output_dir / safe_path_component(with_txt_suffix(flat))


def parse_keras_box(
    token: str,
    classes: Sequence[str],
    is_gt: bool,
    source: str,
) -> str:
    fields = token.split(",")
    expected = 5 if is_gt else 6
    if len(fields) != expected:
        raise ConversionError(
            f"{source}: expected {expected} comma-separated values per bbox, got {len(fields)} in {token!r}"
        )
    x_min, y_min, x_max, y_max = (format_number(parse_float(v, source)) for v in fields[:4])
    class_name = parse_class_id(fields[4], classes, source)
    if is_gt:
        return f"{class_name} {x_min} {y_min} {x_max} {y_max}"
    score = format_number(parse_float(fields[5], source))
    return f"{class_name} {score} {x_min} {y_min} {x_max} {y_max}"


def keras_yolo3_to_text(args: argparse.Namespace) -> int:
    classes = load_class_list(Path(args.class_list))
    annotation_path = Path(args.gt or args.dr)
    if not annotation_path.exists():
        raise ConversionError(f"keras-yolo3 annotation file not found: {annotation_path}")
    is_gt = bool(args.gt)
    output_dir = Path(args.output_dir)
    outputs: Dict[Path, List[str]] = {}
    for line_no, raw in enumerate(annotation_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        image_path = parts[0]
        destination = keras_output_path(output_dir, image_path, args.recursive, args.keras_root)
        rows = outputs.setdefault(destination, [])
        for bbox_no, bbox in enumerate(parts[1:], start=1):
            rows.append(parse_keras_box(bbox, classes, is_gt, f"{annotation_path}:{line_no}: bbox #{bbox_no}"))
    if not outputs:
        raise ConversionError(f"keras-yolo3 annotation file has no rows: {annotation_path}")
    for path, rows in outputs.items():
        write_output(path, rows, args.overwrite)
    target = "ground-truth" if is_gt else "detection-results"
    print(f"Converted {len(outputs)} keras-yolo3 image annotation(s) to {target} text in {output_dir}")
    return 0


def add_common_io(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", required=True, help="input file or non-recursive directory to read")
    parser.add_argument("--output-dir", required=True, help="directory where evaluator .txt files will be written")
    parser.add_argument("--overwrite", action="store_true", help="allow overwriting existing output .txt files")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert VOC XML, YOLO, darkflow JSON, darknet result text, or keras-yolo3 annotations into mAP evaluator text files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_xml = subparsers.add_parser("voc-xml-gt", help="convert PASCAL VOC XML files to ground-truth text")
    add_common_io(p_xml)
    p_xml.add_argument(
        "--drop-difficult",
        action="store_true",
        help="do not append the evaluator's optional 'difficult' token for VOC difficult objects",
    )
    p_xml.set_defaults(func=voc_xml_to_gt)

    p_yolo_gt = subparsers.add_parser("yolo-gt", help="convert YOLO normalized label files to ground-truth text")
    add_common_io(p_yolo_gt)
    p_yolo_gt.add_argument("--class-list", required=True, help="newline-delimited zero-based class-name list")
    p_yolo_gt.add_argument("--image-dir", help="directory containing images with stems matching label files")
    p_yolo_gt.add_argument("--image-size", nargs=2, type=int, metavar=("WIDTH", "HEIGHT"), help="use one image size for all labels")
    p_yolo_gt.add_argument(
        "--image-size-file",
        help="text/CSV rows '<image_id> <width> <height>'; image_id may be a stem or file name",
    )
    p_yolo_gt.set_defaults(func=yolo_gt_to_text)

    p_darkflow = subparsers.add_parser("darkflow-json-dr", help="convert darkflow JSON result files to detection-results text")
    add_common_io(p_darkflow)
    p_darkflow.set_defaults(func=darkflow_json_to_dr)

    p_darknet = subparsers.add_parser("darknet-result-dr", help="convert darknet result.txt output to detection-results text")
    add_common_io(p_darknet)
    p_darknet.add_argument("--image-ext", default=".jpg", help="image extension used in 'Enter Image Path' sections, default: .jpg")
    p_darknet.set_defaults(func=darknet_result_to_dr)

    p_keras = subparsers.add_parser("keras-yolo3", help="convert keras-yolo3 annotation files to evaluator text")
    group = p_keras.add_mutually_exclusive_group(required=True)
    group.add_argument("--gt", help="keras-yolo3 ground-truth annotation file")
    group.add_argument("--dr", help="keras-yolo3 detection-results annotation file")
    p_keras.add_argument("--class-list", required=True, help="newline-delimited zero-based class-name list")
    p_keras.add_argument("--output-dir", required=True, help="directory where evaluator .txt files will be written")
    p_keras.add_argument("--recursive", action="store_true", help="preserve nested image-path directories under output-dir")
    p_keras.add_argument("--keras-root", help="root prefix to strip when --recursive is used")
    p_keras.add_argument("--overwrite", action="store_true", help="allow overwriting existing output .txt files")
    p_keras.set_defaults(func=keras_yolo3_to_text)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ConversionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
