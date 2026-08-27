#!/usr/bin/env python3
"""Read-only cfg/names inspector for this pytorch-yolo-v3 Darknet implementation."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

SUPPORTED_CREATE_MODULES = {
    "net",
    "convolutional",
    "upsample",
    "route",
    "shortcut",
    "maxpool",
    "yolo",
}
KNOWN_UNSUPPORTED = {"region", "reorg"}


class ConfigError(Exception):
    """Raised for cfg or names files that cannot be inspected."""


def resolve_path(repo_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path


def parse_cfg(cfg_path: Path) -> List[Dict[str, str]]:
    if not cfg_path.is_file():
        raise ConfigError(f"cfg file not found: {cfg_path}")

    blocks: List[Dict[str, str]] = []
    block: Optional[Dict[str, str]] = None

    with cfg_path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("["):
                if not line.endswith("]"):
                    raise ConfigError(f"line {line_no}: malformed block header {line!r}")
                if block is not None:
                    blocks.append(block)
                block = {"type": line[1:-1].strip(), "__line__": str(line_no)}
                continue
            if block is None:
                raise ConfigError(f"line {line_no}: key/value appears before first block")
            if "=" not in line:
                raise ConfigError(f"line {line_no}: expected key=value, got {line!r}")
            key, value = line.split("=", 1)
            block[key.strip()] = value.strip()

    if block is not None:
        blocks.append(block)
    if not blocks:
        raise ConfigError("cfg file contains no blocks")
    if blocks[0].get("type") != "net":
        raise ConfigError("first cfg block should be [net]")
    return blocks


def parse_int(block: Dict[str, str], key: str) -> Optional[int]:
    value = block.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def split_int_list(value: Optional[str]) -> List[int]:
    if not value:
        return []
    result: List[int] = []
    for piece in value.split(","):
        piece = piece.strip()
        if not piece:
            continue
        result.append(int(piece))
    return result


def count_names(names_path: Path) -> int:
    if not names_path.is_file():
        raise ConfigError(f"names file not found: {names_path}")
    count = 0
    with names_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if line and not line.startswith("#"):
                count += 1
    return count


def expected_detection_filters(block: Dict[str, str]) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    classes = parse_int(block, "classes")
    coords = parse_int(block, "coords")
    if coords is None:
        coords = 4

    mask_values = split_int_list(block.get("mask"))
    if mask_values:
        anchors_per_head = len(mask_values)
    else:
        anchors_per_head = parse_int(block, "num")

    if classes is None or anchors_per_head is None:
        return classes, anchors_per_head, None
    return classes, anchors_per_head, (classes + coords + 1) * anchors_per_head


def validate_resolution(net: Dict[str, str]) -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    errors: List[str] = []
    dims = {}
    for key in ("width", "height"):
        value = parse_int(net, key)
        dims[key] = value
        if value is None:
            errors.append(f"[net] {key} is missing or not an integer")
        elif value <= 32:
            errors.append(f"[net] {key}={value} is not greater than 32")
        elif value % 32 != 0:
            errors.append(f"[net] {key}={value} is not a multiple of 32")
    if dims.get("width") and dims.get("height") and dims["width"] != dims["height"]:
        warnings.append(
            "[net] width and height differ; this implementation commonly uses height as the YOLO input dimension"
        )
    return warnings, errors


def detection_reports(blocks: List[Dict[str, str]]) -> Tuple[List[str], List[int], List[str]]:
    lines: List[str] = []
    class_values: List[int] = []
    errors: List[str] = []

    for index, block in enumerate(blocks):
        block_type = block.get("type")
        if block_type not in {"yolo", "region"}:
            continue

        classes, anchors_per_head, expected_filters = expected_detection_filters(block)
        if classes is not None:
            class_values.append(classes)

        previous = blocks[index - 1] if index > 0 else {}
        previous_filters = parse_int(previous, "filters") if previous.get("type") == "convolutional" else None

        label = f"block {index} [{block_type}]"
        lines.append(
            f"  {label}: classes={classes if classes is not None else 'unknown'}, "
            f"anchors_per_head={anchors_per_head if anchors_per_head is not None else 'unknown'}, "
            f"expected_prev_filters={expected_filters if expected_filters is not None else 'unknown'}, "
            f"actual_prev_filters={previous_filters if previous_filters is not None else 'unknown'}"
        )

        if previous.get("type") != "convolutional":
            errors.append(f"{label} is not immediately preceded by a convolutional block")
        elif expected_filters is not None and previous_filters != expected_filters:
            errors.append(
                f"{label} expects previous convolution filters={expected_filters}, got {previous_filters}"
            )

    return lines, class_values, errors


def print_block_counts(blocks: List[Dict[str, str]]) -> None:
    counts = Counter(block.get("type", "<missing>") for block in blocks)
    print("block_types:")
    for block_type, count in sorted(counts.items()):
        print(f"  {block_type}: {count}")


def build_model(repo_root: Path, cfg_path: Path) -> int:
    darknet_py = repo_root / "darknet.py"
    if not darknet_py.is_file():
        print(f"ERROR: cannot build model because darknet.py was not found under repo root: {repo_root}")
        return 2

    sys.path.insert(0, str(repo_root))
    try:
        from darknet import Darknet  # type: ignore

        model = Darknet(str(cfg_path))
        module_list = model.get_module_list() if hasattr(model, "get_module_list") else model.module_list
        print(f"build_model: ok; Darknet constructed modules={len(module_list)}")
        return 0
    except AssertionError as exc:
        print(
            "ERROR: Darknet construction raised AssertionError. For unsupported cfg blocks, "
            "this repo prints 'Something I dunno' before the assertion."
        )
        if str(exc):
            print(f"       assertion detail: {exc}")
        return 2
    except Exception as exc:  # pragma: no cover - environment-specific import/runtime errors
        print(f"ERROR: Darknet construction failed: {type(exc).__name__}: {exc}")
        return 2


def unique_sorted(values: Iterable[int]) -> List[int]:
    return sorted(set(values))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect cfg/names compatibility for this pytorch-yolo-v3 Darknet implementation without downloads or inference."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to a local user checkout/source tree containing darknet.py, cfg/, and data/ (default: current directory).",
    )
    parser.add_argument("--cfg", required=True, help="Cfg path, absolute or relative to --repo-root.")
    parser.add_argument("--names", help="Optional names file path, absolute or relative to --repo-root.")
    parser.add_argument(
        "--build-model",
        action="store_true",
        help="Instantiate Darknet(cfgfile) after static checks. This imports repo code but never downloads or loads weights.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).expanduser().resolve()
    cfg_path = resolve_path(repo_root, args.cfg).resolve()

    print(f"repo_root: {repo_root}")
    print(f"cfg: {cfg_path}")

    try:
        blocks = parse_cfg(cfg_path)
    except ConfigError as exc:
        print(f"ERROR: {exc}")
        return 2

    print(f"blocks: {len(blocks)}")
    print(f"modules_if_constructible: {max(len(blocks) - 1, 0)}")
    print_block_counts(blocks)

    net = blocks[0]
    print("net:")
    for key in ("batch", "subdivisions", "width", "height", "channels"):
        if key in net:
            print(f"  {key}: {net[key]}")

    warnings, errors = validate_resolution(net)

    unsupported = sorted({block.get("type", "") for block in blocks} - SUPPORTED_CREATE_MODULES)
    if unsupported:
        if any(item in KNOWN_UNSUPPORTED for item in unsupported):
            errors.append(
                "unsupported block types for create_modules: "
                + ", ".join(unsupported)
                + "; parse_cfg can read them, but create_modules prints 'Something I dunno' and raises AssertionError"
            )
        else:
            errors.append("unsupported block types for create_modules: " + ", ".join(unsupported))

    report_lines, class_values, detection_errors = detection_reports(blocks)
    if report_lines:
        print("detection_blocks:")
        for line in report_lines:
            print(line)
    else:
        warnings.append("no yolo or region detection blocks found")
    errors.extend(detection_errors)

    unique_classes = unique_sorted(class_values)
    if unique_classes:
        print("class_values: " + ", ".join(str(value) for value in unique_classes))
        if len(unique_classes) > 1:
            errors.append("detection blocks do not agree on classes: " + ", ".join(map(str, unique_classes)))

    if args.names:
        names_path = resolve_path(repo_root, args.names).resolve()
        print(f"names: {names_path}")
        try:
            names_count = count_names(names_path)
            print(f"names_count: {names_count}")
            if len(unique_classes) == 1 and names_count != unique_classes[0]:
                errors.append(f"names_count={names_count} does not match cfg classes={unique_classes[0]}")
        except ConfigError as exc:
            errors.append(str(exc))

    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"  WARNING: {warning}")

    if errors:
        print("errors:")
        for error in errors:
            print(f"  ERROR: {error}")

    exit_code = 2 if errors else 0

    if args.build_model:
        if unsupported:
            print("build_model: skipped because unsupported block types are present")
            exit_code = 2
        else:
            build_exit = build_model(repo_root, cfg_path)
            exit_code = max(exit_code, build_exit)
    else:
        print("build_model: not requested")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
