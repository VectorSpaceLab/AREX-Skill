#!/usr/bin/env python3
"""Safe tensorflow-yolov3 training configuration checker.

This helper validates paths, class names, anchors, annotation rows, multi-scale
input sizes, and optional checkpoint prefixes without importing TensorFlow or
running training. It is intentionally standalone so it can run before the legacy
TF1 environment is ready.
"""
from __future__ import print_function

import argparse
import ast
import glob
import json
import os
from pathlib import Path
import re
import sys

CONFIG_ASSIGNMENT = re.compile(r"^\s*__C\.(YOLO|TRAIN|TEST)\.([A-Z0-9_]+)\s*=\s*(.+?)\s*(?:#.*)?$")

BUILTIN_DEFAULTS = {
    "YOLO.CLASSES": "./data/classes/coco.names",
    "YOLO.ANCHORS": "./data/anchors/basline_anchors.txt",
    "YOLO.STRIDES": [8, 16, 32],
    "YOLO.ANCHOR_PER_SCALE": 3,
    "YOLO.IOU_LOSS_THRESH": 0.5,
    "YOLO.MOVING_AVE_DECAY": 0.9995,
    "YOLO.UPSAMPLE_METHOD": "resize",
    "TRAIN.ANNOT_PATH": "./data/dataset/voc_train.txt",
    "TEST.ANNOT_PATH": "./data/dataset/voc_test.txt",
    "TRAIN.BATCH_SIZE": 6,
    "TRAIN.INPUT_SIZE": [320, 352, 384, 416, 448, 480, 512, 544, 576, 608],
    "TRAIN.DATA_AUG": True,
    "TRAIN.LEARN_RATE_INIT": 1e-4,
    "TRAIN.LEARN_RATE_END": 1e-6,
    "TRAIN.WARMUP_EPOCHS": 2,
    "TRAIN.FISRT_STAGE_EPOCHS": 20,
    "TRAIN.SECOND_STAGE_EPOCHS": 30,
    "TRAIN.INITIAL_WEIGHT": "./checkpoint/yolov3_coco_demo.ckpt",
}


class Reporter(object):
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.notes = []

    def error(self, message):
        self.errors.append(message)
        print("[ERROR] " + message)

    def warn(self, message):
        self.warnings.append(message)
        print("[WARN]  " + message)

    def ok(self, message):
        self.notes.append(message)
        print("[OK]    " + message)


def parse_literal(text):
    text = text.strip()
    try:
        return ast.literal_eval(text)
    except Exception:
        if text in ("True", "False"):
            return text == "True"
        return text


def load_config(config_py):
    values = dict(BUILTIN_DEFAULTS)
    config_path = Path(config_py)
    if not config_path.exists():
        return values, False
    for line in config_path.read_text(encoding="utf-8").splitlines():
        match = CONFIG_ASSIGNMENT.match(line)
        if not match:
            continue
        section, field, raw_value = match.groups()
        values[section + "." + field] = parse_literal(raw_value)
    return values, True


def resolve_path(repo_root, value):
    if value is None or str(value).strip() == "":
        return None
    path = Path(str(value)).expanduser()
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def display_path(path, repo_root):
    if path is None:
        return "<unset>"
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except Exception:
        return str(path)


def coerce_int(value, name, reporter):
    try:
        ivalue = int(value)
    except Exception:
        reporter.error("{} must be an integer, got {!r}".format(name, value))
        return None
    return ivalue


def coerce_float(value, name, reporter):
    try:
        fvalue = float(value)
    except Exception:
        reporter.error("{} must be a float, got {!r}".format(name, value))
        return None
    return fvalue


def parse_input_sizes(value, reporter):
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("["):
            value = parse_literal(text)
        else:
            value = [chunk.strip() for chunk in text.split(",") if chunk.strip()]
    elif isinstance(value, int):
        value = [value]
    elif isinstance(value, tuple):
        value = list(value)
    elif not isinstance(value, list):
        reporter.error("TRAIN.INPUT_SIZE must be an int/list or comma-separated string, got {!r}".format(value))
        return []

    sizes = []
    for item in value:
        try:
            size = int(item)
        except Exception:
            reporter.error("TRAIN.INPUT_SIZE contains a non-integer entry: {!r}".format(item))
            continue
        sizes.append(size)
        if size <= 0:
            reporter.error("TRAIN.INPUT_SIZE entry {} must be positive".format(size))
        if size % 32 != 0:
            reporter.error("TRAIN.INPUT_SIZE entry {} is not divisible by 32, but YOLOv3 strides include 32".format(size))
    if not sizes:
        reporter.error("TRAIN.INPUT_SIZE is empty")
    return sizes


def read_class_names(classes_path, reporter, repo_root):
    if classes_path is None:
        reporter.error("YOLO.CLASSES path is unset")
        return []
    if not classes_path.exists():
        reporter.error("YOLO.CLASSES file not found: {}".format(display_path(classes_path, repo_root)))
        return []
    names = [line.strip() for line in classes_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not names:
        reporter.error("YOLO.CLASSES is empty: {}".format(display_path(classes_path, repo_root)))
        return []
    duplicates = sorted(set(name for name in names if names.count(name) > 1))
    if duplicates:
        reporter.warn("YOLO.CLASSES contains duplicate class names: {}".format(", ".join(duplicates[:10])))
    reporter.ok("Read {} classes from {}".format(len(names), display_path(classes_path, repo_root)))
    return names


def validate_anchors(anchors_path, anchor_per_scale, reporter, repo_root):
    if anchors_path is None:
        reporter.error("YOLO.ANCHORS path is unset")
        return []
    if not anchors_path.exists():
        reporter.error("YOLO.ANCHORS file not found: {}".format(display_path(anchors_path, repo_root)))
        return []
    text = anchors_path.read_text(encoding="utf-8").strip()
    raw_parts = [part.strip() for part in text.replace("\n", ",").split(",") if part.strip()]
    values = []
    for part in raw_parts:
        try:
            values.append(float(part))
        except Exception:
            reporter.error("YOLO.ANCHORS contains a non-float value {!r}".format(part))
    expected = 3 * int(anchor_per_scale or 0) * 2
    if expected <= 0:
        reporter.error("YOLO.ANCHOR_PER_SCALE must be positive, got {!r}".format(anchor_per_scale))
    elif len(values) != expected:
        reporter.error("YOLO.ANCHORS must contain {} floats for shape (3, {}, 2), found {}".format(expected, anchor_per_scale, len(values)))
    if any(v <= 0 for v in values):
        reporter.error("YOLO.ANCHORS values must all be positive")
    if values and len(values) == expected and all(v > 0 for v in values):
        reporter.ok("Anchor file has shape (3, {}, 2): {}".format(anchor_per_scale, display_path(anchors_path, repo_root)))
    return values


def image_size_with_pillow(path):
    try:
        from PIL import Image
    except Exception as exc:
        raise RuntimeError("Pillow is not installed: {}".format(exc))
    with Image.open(str(path)) as img:
        return img.size


def parse_box_token(token):
    pieces = token.split(",")
    if len(pieces) != 5:
        raise ValueError("expected x_min,y_min,x_max,y_max,class_id")
    nums = [float(piece) for piece in pieces]
    # The repo converts all five values through int(float(...)); mirror that
    # behavior for class-id and coordinate diagnostics while warning separately
    # about non-integral class ids.
    return nums


def validate_annotation_file(label, annot_path, repo_root, class_count, args, reporter):
    if annot_path is None:
        reporter.error("{} annotation path is unset".format(label))
        return {"rows": 0, "boxes": 0}
    if not annot_path.exists():
        reporter.error("{} annotation file not found: {}".format(label, display_path(annot_path, repo_root)))
        return {"rows": 0, "boxes": 0}

    rows = 0
    rows_with_boxes = 0
    boxes = 0
    invalid_boxes = 0
    checked_images = 0
    missing_images = 0
    dimension_checks = 0
    lines = annot_path.read_text(encoding="utf-8").splitlines()
    max_lines = args.max_annotation_lines
    if max_lines and max_lines > 0:
        lines_to_check = lines[:max_lines]
    else:
        lines_to_check = lines

    for line_number, raw_line in enumerate(lines_to_check, 1):
        line = raw_line.strip()
        if not line:
            continue
        rows += 1
        if line.startswith("#"):
            reporter.error("{}:{} starts with '#'; Dataset.load_annotations does not skip comments".format(display_path(annot_path, repo_root), line_number))
            continue
        parts = line.split()
        if len(parts) < 2:
            reporter.warn("{}:{} has no boxes and will be filtered out by Dataset.load_annotations".format(display_path(annot_path, repo_root), line_number))
            continue
        rows_with_boxes += 1
        image_ref = parts[0]
        image_path = Path(image_ref).expanduser()
        if not image_path.is_absolute():
            image_path = (repo_root / image_path).resolve()
        image_width = image_height = None
        if not args.no_check_images:
            checked_images += 1
            if not image_path.exists():
                missing_images += 1
                reporter.error("{}:{} image path does not exist from training cwd: {}".format(display_path(annot_path, repo_root), line_number, image_ref))
            elif args.check_image_dimensions:
                try:
                    image_width, image_height = image_size_with_pillow(image_path)
                    dimension_checks += 1
                except Exception as exc:
                    reporter.warn("{}:{} could not inspect image dimensions for {}: {}".format(display_path(annot_path, repo_root), line_number, image_ref, exc))
        for token in parts[1:]:
            boxes += 1
            try:
                x1, y1, x2, y2, class_id_float = parse_box_token(token)
            except Exception as exc:
                invalid_boxes += 1
                reporter.error("{}:{} malformed box {!r}: {}".format(display_path(annot_path, repo_root), line_number, token, exc))
                continue
            class_id = int(class_id_float)
            if class_id_float != class_id:
                reporter.warn("{}:{} class id {} will be truncated to {} by int(float(...))".format(display_path(annot_path, repo_root), line_number, class_id_float, class_id))
            if x2 <= x1 or y2 <= y1:
                invalid_boxes += 1
                reporter.error("{}:{} invalid box coordinates {}; require x_max > x_min and y_max > y_min".format(display_path(annot_path, repo_root), line_number, token))
            if class_count > 0 and (class_id < 0 or class_id >= class_count):
                invalid_boxes += 1
                reporter.error("{}:{} class id {} is outside YOLO.CLASSES range [0, {}]".format(display_path(annot_path, repo_root), line_number, class_id, class_count - 1))
            if image_width is not None and image_height is not None:
                if x1 < 0 or y1 < 0 or x2 > image_width or y2 > image_height:
                    reporter.warn("{}:{} box {} exceeds image bounds {}x{}; README says x_max < width and y_max < height, and the loader later clips boxes".format(display_path(annot_path, repo_root), line_number, token, image_width, image_height))
    if rows == 0:
        reporter.error("{} annotation file has no non-empty rows: {}".format(label, display_path(annot_path, repo_root)))
    if rows_with_boxes == 0:
        reporter.error("{} annotation file has no usable rows with boxes: {}".format(label, display_path(annot_path, repo_root)))
    if boxes == 0:
        reporter.error("{} annotation file has no boxes: {}".format(label, display_path(annot_path, repo_root)))
    if invalid_boxes == 0 and rows_with_boxes > 0:
        reporter.ok("{} annotation file format checked: {} rows with boxes, {} boxes".format(label, rows_with_boxes, boxes))
    if args.no_check_images:
        reporter.warn("{} image existence checks were disabled".format(label))
    elif missing_images == 0 and checked_images > 0:
        reporter.ok("{} image paths exist for {} checked rows".format(label, checked_images))
    if args.check_image_dimensions and dimension_checks > 0:
        reporter.ok("{} image dimension checks completed for {} rows".format(label, dimension_checks))
    if max_lines and max_lines > 0 and len(lines) > max_lines:
        reporter.warn("{} validation stopped after --max-annotation-lines {}; file has {} lines".format(label, max_lines, len(lines)))
    return {"rows": rows, "rows_with_boxes": rows_with_boxes, "boxes": boxes, "missing_images": missing_images, "invalid_boxes": invalid_boxes}


def checkpoint_artifacts(prefix_path):
    if prefix_path is None:
        return {"present": False, "index": False, "data": [], "meta": False, "direct": False}
    direct = prefix_path.exists()
    index = Path(str(prefix_path) + ".index").exists()
    data = sorted(glob.glob(str(prefix_path) + ".data-*"))
    meta = Path(str(prefix_path) + ".meta").exists()
    return {"present": bool(direct or (index and data)), "index": index, "data": data, "meta": meta, "direct": direct}


def validate_checkpoint(initial_weight, repo_root, require_checkpoint, reporter):
    if not initial_weight:
        if require_checkpoint:
            reporter.error("TRAIN.INITIAL_WEIGHT is unset but --require-checkpoint was requested")
        else:
            reporter.warn("TRAIN.INITIAL_WEIGHT is unset; train.py will train from scratch")
        return
    prefix_path = resolve_path(repo_root, initial_weight)
    artifacts = checkpoint_artifacts(prefix_path)
    if artifacts["present"]:
        if artifacts["index"] and artifacts["data"]:
            reporter.ok("Checkpoint prefix is restorable by tf.train.Saver: {}".format(display_path(prefix_path, repo_root)))
        else:
            reporter.warn("Checkpoint path exists but does not look like a complete TF checkpoint prefix: {}".format(display_path(prefix_path, repo_root)))
        if not artifacts["meta"]:
            reporter.warn("Checkpoint .meta file is absent for {}; Saver.restore can still use .index/.data, but conversion scripts may need .meta for source checkpoints".format(display_path(prefix_path, repo_root)))
    else:
        message = "Initial checkpoint prefix not found: {}".format(display_path(prefix_path, repo_root))
        if require_checkpoint:
            reporter.error(message + " (required by --require-checkpoint)")
        else:
            reporter.warn(message + "; train.py catches restore failure, sets first-stage epochs to 0, and trains from scratch")


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Validate tensorflow-yolov3 training config paths/classes/annotations/checkpoint without running training."
    )
    parser.add_argument("--repo-root", default=".", help="Repository/training working directory; relative annotation image paths are resolved from here.")
    parser.add_argument("--config-py", default="./core/config.py", help="Config file to parse for __C.YOLO, __C.TRAIN, and __C.TEST assignments.")
    parser.add_argument("--classes", default=None, help="Override cfg.YOLO.CLASSES.")
    parser.add_argument("--anchors", default=None, help="Override cfg.YOLO.ANCHORS.")
    parser.add_argument("--train-annot", default=None, help="Override cfg.TRAIN.ANNOT_PATH.")
    parser.add_argument("--test-annot", default=None, help="Override cfg.TEST.ANNOT_PATH.")
    parser.add_argument("--initial-weight", default=None, help="Override cfg.TRAIN.INITIAL_WEIGHT checkpoint prefix.")
    parser.add_argument("--input-sizes", default=None, help="Override cfg.TRAIN.INPUT_SIZE as int/list/comma-separated values.")
    parser.add_argument("--batch-size", default=None, help="Override cfg.TRAIN.BATCH_SIZE.")
    parser.add_argument("--first-stage-epochs", default=None, help="Override cfg.TRAIN.FISRT_STAGE_EPOCHS (misspelled in repo config).")
    parser.add_argument("--second-stage-epochs", default=None, help="Override cfg.TRAIN.SECOND_STAGE_EPOCHS.")
    parser.add_argument("--require-checkpoint", action="store_true", help="Fail if TRAIN.INITIAL_WEIGHT checkpoint prefix is absent; use for COCO-initialized training.")
    parser.add_argument("--no-check-images", action="store_true", help="Skip annotation image existence checks.")
    parser.add_argument("--check-image-dimensions", action="store_true", help="Use Pillow, if available, to warn when boxes exceed image dimensions.")
    parser.add_argument("--max-annotation-lines", type=int, default=0, help="Check only the first N non-empty annotation lines per file; 0 checks all lines.")
    parser.add_argument("--strict-warnings", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--json", action="store_true", help="Print a final machine-readable summary JSON object.")
    return parser


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
    reporter = Reporter()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        reporter.error("--repo-root does not exist: {}".format(repo_root))
    config_py = resolve_path(repo_root, args.config_py)
    config, config_found = load_config(config_py)
    if config_found:
        reporter.ok("Parsed config assignments from {}".format(display_path(config_py, repo_root)))
    else:
        reporter.warn("Config file not found; using built-in defaults: {}".format(display_path(config_py, repo_root)))

    classes_value = args.classes if args.classes is not None else config.get("YOLO.CLASSES")
    anchors_value = args.anchors if args.anchors is not None else config.get("YOLO.ANCHORS")
    train_annot_value = args.train_annot if args.train_annot is not None else config.get("TRAIN.ANNOT_PATH")
    test_annot_value = args.test_annot if args.test_annot is not None else config.get("TEST.ANNOT_PATH")
    initial_weight = args.initial_weight if args.initial_weight is not None else config.get("TRAIN.INITIAL_WEIGHT")
    input_sizes_value = args.input_sizes if args.input_sizes is not None else config.get("TRAIN.INPUT_SIZE")
    batch_size_value = args.batch_size if args.batch_size is not None else config.get("TRAIN.BATCH_SIZE")
    first_stage_value = args.first_stage_epochs if args.first_stage_epochs is not None else config.get("TRAIN.FISRT_STAGE_EPOCHS")
    second_stage_value = args.second_stage_epochs if args.second_stage_epochs is not None else config.get("TRAIN.SECOND_STAGE_EPOCHS")
    anchor_per_scale = config.get("YOLO.ANCHOR_PER_SCALE", 3)

    classes_path = resolve_path(repo_root, classes_value)
    anchors_path = resolve_path(repo_root, anchors_value)
    train_annot_path = resolve_path(repo_root, train_annot_value)
    test_annot_path = resolve_path(repo_root, test_annot_value)

    batch_size = coerce_int(batch_size_value, "TRAIN.BATCH_SIZE", reporter)
    if batch_size is not None:
        if batch_size <= 0:
            reporter.error("TRAIN.BATCH_SIZE must be positive")
        else:
            reporter.ok("TRAIN.BATCH_SIZE = {}".format(batch_size))
    first_stage = coerce_int(first_stage_value, "TRAIN.FISRT_STAGE_EPOCHS", reporter)
    second_stage = coerce_int(second_stage_value, "TRAIN.SECOND_STAGE_EPOCHS", reporter)
    if first_stage is not None and first_stage < 0:
        reporter.error("TRAIN.FISRT_STAGE_EPOCHS must be non-negative")
    if second_stage is not None and second_stage < 0:
        reporter.error("TRAIN.SECOND_STAGE_EPOCHS must be non-negative")
    if first_stage == 0:
        reporter.warn("First-stage frozen-head training is disabled (TRAIN.FISRT_STAGE_EPOCHS = 0)")
    if first_stage == 0 and second_stage == 0:
        reporter.error("Both training stages have zero epochs")

    lr_init = coerce_float(config.get("TRAIN.LEARN_RATE_INIT"), "TRAIN.LEARN_RATE_INIT", reporter)
    lr_end = coerce_float(config.get("TRAIN.LEARN_RATE_END"), "TRAIN.LEARN_RATE_END", reporter)
    if lr_init is not None and lr_init <= 0:
        reporter.error("TRAIN.LEARN_RATE_INIT must be positive")
    if lr_end is not None and lr_end <= 0:
        reporter.error("TRAIN.LEARN_RATE_END must be positive")
    if lr_init is not None and lr_end is not None and lr_end > lr_init:
        reporter.warn("TRAIN.LEARN_RATE_END is greater than TRAIN.LEARN_RATE_INIT; cosine decay will increase late in training")

    input_sizes = parse_input_sizes(input_sizes_value, reporter)
    if input_sizes:
        reporter.ok("TRAIN.INPUT_SIZE candidates: {}".format(", ".join(str(size) for size in input_sizes)))

    class_names = read_class_names(classes_path, reporter, repo_root)
    validate_anchors(anchors_path, anchor_per_scale, reporter, repo_root)
    train_stats = validate_annotation_file("train", train_annot_path, repo_root, len(class_names), args, reporter)
    test_stats = validate_annotation_file("test", test_annot_path, repo_root, len(class_names), args, reporter)
    validate_checkpoint(initial_weight, repo_root, args.require_checkpoint, reporter)

    if train_stats.get("rows_with_boxes", 0) and batch_size:
        batches = (train_stats["rows_with_boxes"] + batch_size - 1) // batch_size
        reporter.ok("Estimated train Dataset.__len__ = ceil({}/{}) = {} batch(es)".format(train_stats["rows_with_boxes"], batch_size, batches))

    if "TRAIN.FIRST_STAGE_EPOCHS" in config:
        reporter.warn("Config contains TRAIN.FIRST_STAGE_EPOCHS, but train.py reads the misspelled TRAIN.FISRT_STAGE_EPOCHS")

    status = "ok"
    if reporter.errors or (args.strict_warnings and reporter.warnings):
        status = "failed"
    summary = {
        "status": status,
        "errors": reporter.errors,
        "warnings": reporter.warnings,
        "class_count": len(class_names),
        "input_sizes": input_sizes,
        "train_annotation": train_stats,
        "test_annotation": test_stats,
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    if status == "failed":
        print("Result: FAILED ({} error(s), {} warning(s))".format(len(reporter.errors), len(reporter.warnings)))
        return 1
    print("Result: OK ({} warning(s))".format(len(reporter.warnings)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
