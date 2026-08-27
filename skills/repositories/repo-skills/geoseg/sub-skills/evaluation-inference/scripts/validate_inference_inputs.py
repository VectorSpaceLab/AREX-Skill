#!/usr/bin/env python3
"""Dependency-free preflight checks for GeoSeg inference inputs.

The helper only reads paths and parses literal string assignments from a Python
config with :mod:`ast`. It deliberately does not import GeoSeg, torch, CUDA,
OpenCV, or any config module; it does not download data, create output
folders, load checkpoints, or run inference.
"""

import argparse
import ast
import os
import sys
from pathlib import Path

# Match the three extensions used by the inference entry points.  The source
# glob is case-sensitive, so this helper intentionally does not broaden it.
IMAGE_SUFFIXES = {".tif", ".png", ".jpg"}
UAVID_DATASETS = {"pv", "landcoverai", "uavid"}
HUGE_DATASETS = UAVID_DATASETS | {"building"}


class Report:
    """Collect errors and warnings while keeping output readable in a shell."""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def ok(self, message):
        print("[OK] " + message)

    def warn(self, message):
        self.warnings.append(message)
        print("[WARN] " + message)

    def error(self, message):
        self.errors.append(message)
        print("[ERROR] " + message)


def parse_args(argv=None):
    """Parse arguments without touching the filesystem or importing packages."""
    parser = argparse.ArgumentParser(
        description=(
            "Run a safe, dependency-free GeoSeg inference preflight. Checks "
            "mode-specific input layout, config syntax/checkpoint fields, and "
            "output safety; never runs inference."
        ),
        epilog=(
            "This is a preflight only: it does not test CUDA, model compatibility, "
            "or the original checkout entry point."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=("tile", "uavid", "huge"),
        help="Inference route whose input layout should be checked.",
    )
    parser.add_argument(
        "--image-path",
        required=True,
        type=Path,
        help="Existing tile root, UAVid sequence root, or flat image folder.",
    )
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Existing Python config file; it is parsed as syntax only.",
    )
    parser.add_argument(
        "--output-path",
        required=True,
        type=Path,
        help="Output directory to check without creating or modifying it.",
    )
    parser.add_argument(
        "--dataset",
        choices=sorted(HUGE_DATASETS),
        help="Output mapping for UAVid/huge routes; ignored for tile mode.",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        help="Optional explicit checkpoint; otherwise infer from literal config fields.",
    )
    parser.add_argument(
        "--mask-path",
        type=Path,
        help="Optional tile mask directory; otherwise use <image-path>/masks_1024.",
    )
    parser.add_argument(
        "--check-padding",
        action="store_true",
        help="Run pure-Python bottom/right padding and crop assertions.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return status 2 when warnings remain (errors always return 1).",
    )
    return parser.parse_args(argv)


def image_files(path):
    """Return first-level source-compatible image files in sorted order."""
    if not path.is_dir():
        return []
    return sorted(
        child
        for child in path.iterdir()
        if child.is_file() and child.suffix in IMAGE_SUFFIXES
    )


def nearest_existing_parent(path):
    current = path
    while not current.exists() and current != current.parent:
        current = current.parent
    return current


def check_input_root(path, mode, report):
    if not path.exists():
        report.error("{} input does not exist: {}".format(mode, path))
        return False
    if not path.is_dir():
        report.error("{} input is not a directory: {}".format(mode, path))
        return False
    report.ok("{} input directory exists: {}".format(mode, path))
    return True


def check_output(path, input_path, report):
    """Check output safety without creating the requested output directory."""
    try:
        if path.resolve() == input_path.resolve():
            report.error("output path must be distinct from input path: {}".format(path))
    except OSError as exc:
        report.error("cannot resolve input/output paths: {}".format(exc))

    if path.exists() and path.is_file():
        report.error("output path is a file: {}".format(path))
        return
    if path.exists() and not path.is_dir():
        report.error("output path is not a directory: {}".format(path))
        return

    parent = path if path.exists() else nearest_existing_parent(path.parent)
    if not parent.is_dir():
        report.error("cannot find an existing output parent: {}".format(path))
        return
    if not os.access(str(parent), os.W_OK):
        report.error("output location is not writable: {}".format(parent))
        return
    if path.exists() and not os.access(str(path), os.W_OK):
        report.error("existing output directory is not writable: {}".format(path))
        return
    if path.exists() and any(path.iterdir()):
        report.warn("output directory is non-empty; a rerun may overwrite masks: {}".format(path))
    else:
        report.ok("output directory is available without creating it: {}".format(path))


def literal_string(node, names):
    """Resolve only harmless string literals, names, and ``str.format`` calls."""
    try:
        value = ast.literal_eval(node)
        return value if isinstance(value, str) else None
    except (ValueError, TypeError, SyntaxError):
        pass

    if isinstance(node, ast.Name):
        value = names.get(node.id)
        return value if isinstance(value, str) else None

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "format"
    ):
        template = literal_string(node.func.value, names)
        if template is None or node.keywords:
            return None
        values = []
        for arg in node.args:
            value = literal_string(arg, names)
            if value is None:
                return None
            values.append(value)
        try:
            return template.format(*values)
        except (IndexError, KeyError, ValueError):
            return None
    return None


def config_values(path, report):
    """Parse a config's literal checkpoint fields without executing it."""
    if not path.exists():
        report.error("config file does not exist: {}".format(path))
        return {}
    if not path.is_file():
        report.error("config path is not a file: {}".format(path))
        return {}
    if path.suffix != ".py":
        report.warn("config does not have a .py suffix: {}".format(path))
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        report.error("config cannot be parsed as Python syntax: {}".format(exc))
        return {}

    report.ok("config is readable and valid Python syntax: {}".format(path))
    names = {}
    for statement in tree.body:
        target = None
        value_node = None
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target, value_node = statement.targets[0], statement.value
        elif isinstance(statement, ast.AnnAssign):
            target, value_node = statement.target, statement.value
        if isinstance(target, ast.Name) and value_node is not None:
            value = literal_string(value_node, names)
            if value is not None:
                names[target.id] = value

    values = {key: names.get(key) for key in ("weights_path", "test_weights_name")}
    if values["weights_path"]:
        report.ok("config declares weights_path={}".format(values["weights_path"]))
    else:
        report.warn("could not resolve a literal config weights_path")
    if values["test_weights_name"]:
        report.ok("config declares test_weights_name={}".format(values["test_weights_name"]))
    else:
        report.warn("could not resolve a literal config test_weights_name")
    return values


def check_checkpoint(args, values, report):
    checkpoint = args.checkpoint
    if checkpoint is None and values.get("weights_path") and values.get("test_weights_name"):
        checkpoint = Path(values["weights_path"]) / (values["test_weights_name"] + ".ckpt")
        report.ok("inferred checkpoint path: {}".format(checkpoint))
    elif checkpoint is not None:
        report.ok("using explicit checkpoint path: {}".format(checkpoint))
    else:
        report.warn("checkpoint path could not be inferred; pass --checkpoint explicitly")
        return

    if checkpoint.is_file():
        report.ok("checkpoint exists: {}".format(checkpoint))
    else:
        report.error("checkpoint does not exist: {}".format(checkpoint))


def check_tile(args, report):
    root = args.image_path
    image_dir = root / "images_1024"
    mask_dir = args.mask_path or (root / "masks_1024")
    if not image_dir.is_dir():
        report.warn("expected tile image directory is absent: {}".format(image_dir))
        image_dir = root
    if not mask_dir.is_dir():
        report.warn("expected tile mask directory is absent: {}".format(mask_dir))

    images = image_files(image_dir)
    masks = image_files(mask_dir)
    if images:
        report.ok("found {} tile image files under {}".format(len(images), image_dir))
    else:
        report.warn("no supported .tif/.png/.jpg tile images found under {}".format(image_dir))
    if masks:
        report.ok("found {} tile mask files under {}".format(len(masks), mask_dir))
    else:
        report.warn("no supported .tif/.png/.jpg tile masks found under {}".format(mask_dir))

    if images and masks:
        image_stems = {path.stem for path in images}
        mask_stems = {path.stem for path in masks}
        if image_stems == mask_stems:
            report.ok("tile image/mask stems match")
        else:
            report.error(
                "tile stems do not match (missing images={}, missing masks={})".format(
                    sorted(mask_stems - image_stems)[:5],
                    sorted(image_stems - mask_stems)[:5],
                )
            )


def check_uavid(args, report):
    root = args.image_path
    sequences = sorted(path for path in root.iterdir() if path.is_dir())
    if not sequences:
        report.error("UAVid input has no sequence directories: {}".format(root))
        return
    nonempty = 0
    for sequence in sequences:
        images_dir = sequence / "Images"
        if not images_dir.is_dir():
            report.warn("sequence has no Images directory: {}".format(sequence))
            continue
        files = image_files(images_dir)
        if files:
            nonempty += 1
            report.ok("{}: {} Images files".format(sequence.name, len(files)))
        else:
            report.warn("sequence Images directory is empty: {}".format(images_dir))
    if nonempty == 0:
        report.error("no UAVid sequence contains supported Images files")


def check_huge(args, report):
    root = args.image_path
    files = image_files(root)
    if files:
        report.ok("found {} first-level huge-image files".format(len(files)))
    else:
        report.error("no supported .tif/.png/.jpg files found directly under {}".format(root))
    nested = [path for path in root.iterdir() if path.is_dir()]
    if nested:
        report.warn(
            "nested directories are ignored by huge-image inference: {}".format(
                [path.name for path in nested[:5]]
            )
        )


def padding_case(height, width, patch_height, patch_width):
    padded_height = height + ((patch_height - height % patch_height) % patch_height)
    padded_width = width + ((patch_width - width % patch_width) % patch_width)
    restored = (
        padded_height - (padded_height - height),
        padded_width - (padded_width - width),
    )
    crop_offset = (padded_height - height, padded_width - width)
    return (padded_height, padded_width), restored, crop_offset


def check_padding(report):
    cases = ((5, 7, 3, 4), (6, 8, 3, 4), (1025, 2049, 512, 512))
    for height, width, patch_height, patch_width in cases:
        padded, restored, crop_offset = padding_case(
            height, width, patch_height, patch_width
        )
        if restored != (height, width) or crop_offset[0] >= padded[0] or crop_offset[1] >= padded[1]:
            report.error(
                "padding self-test failed for {}x{} with patch {}x{}".format(
                    height, width, patch_height, patch_width
                )
            )
        else:
            report.ok(
                "padding {}x{} -> {}x{} -> {}x{} (bottom/right crop)".format(
                    height, width, padded[0], padded[1], restored[0], restored[1]
                )
            )


def main(argv=None):
    args = parse_args(argv)
    report = Report()

    input_exists = check_input_root(args.image_path, args.mode, report)
    values = config_values(args.config, report)
    check_output(args.output_path, args.image_path, report)
    check_checkpoint(args, values, report)

    if args.mode == "tile":
        if args.dataset:
            report.warn("--dataset is ignored for tile evaluation; use the matching config")
        if input_exists:
            check_tile(args, report)
        if args.mask_path and not args.mask_path.is_dir():
            report.error("explicit mask path is not a directory: {}".format(args.mask_path))
    elif args.mode == "uavid":
        if args.mask_path:
            report.warn("--mask-path is ignored for UAVid inference")
        if args.dataset is None:
            report.warn("UAVid source default is dataset=uavid; pass it explicitly to record the mapping")
        elif args.dataset not in UAVID_DATASETS:
            report.error("invalid UAVid output mapping: {}".format(args.dataset))
        if input_exists:
            check_uavid(args, report)
    else:
        if args.mask_path:
            report.warn("--mask-path is ignored for huge-image inference")
        if args.dataset is None:
            report.warn("huge-image source default is dataset=pv; pass it explicitly to record the mapping")
        if input_exists:
            check_huge(args, report)

    if args.check_padding:
        check_padding(report)

    print("\nSummary: {} error(s), {} warning(s)".format(len(report.errors), len(report.warnings)))
    if report.errors:
        return 1
    if args.strict and report.warnings:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
