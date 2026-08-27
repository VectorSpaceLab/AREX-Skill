#!/usr/bin/env python
"""Validate ShapeNetPart layouts used by pointnet2 part_seg workflows.

The validator is intentionally TensorFlow-free and repository-free. It encodes
schema facts from part_seg/part_dataset.py and part_seg/part_dataset_all_normal.py
so a future agent can diagnose data problems before launching legacy training.
"""
from __future__ import print_function

import argparse
import io
import json
import os
import sys

SEG_CLASSES = {
    "Earphone": [16, 17, 18],
    "Motorbike": [30, 31, 32, 33, 34, 35],
    "Rocket": [41, 42, 43],
    "Car": [8, 9, 10, 11],
    "Laptop": [28, 29],
    "Cap": [6, 7],
    "Skateboard": [44, 45, 46],
    "Mug": [36, 37],
    "Guitar": [19, 20, 21],
    "Bag": [4, 5],
    "Lamp": [24, 25, 26, 27],
    "Table": [47, 48, 49],
    "Airplane": [0, 1, 2, 3],
    "Pistol": [38, 39, 40],
    "Chair": [12, 13, 14, 15],
    "Knife": [22, 23],
}

SPLIT_FILES = {
    "train": "shuffled_train_file_list.json",
    "val": "shuffled_val_file_list.json",
    "test": "shuffled_test_file_list.json",
}


class Report(object):
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.category_counts = {}
        self.checked_files = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def add(self, msg):
        self.info.append(msg)

    def as_dict(self):
        return {
            "ok": not self.errors,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "categoryCounts": self.category_counts,
            "checkedFiles": self.checked_files,
        }


def read_category_file(root, report):
    catfile = os.path.join(root, "synsetoffset2category.txt")
    categories = []
    if not os.path.isfile(catfile):
        report.error("missing synsetoffset2category.txt at %s" % catfile)
        return categories
    try:
        with io.open(catfile, "r", encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                parts = stripped.split()
                if len(parts) < 2:
                    report.error("bad category line %d in synsetoffset2category.txt: %r" % (lineno, stripped))
                    continue
                categories.append((parts[0], parts[1]))
    except Exception as exc:
        report.error("failed reading synsetoffset2category.txt: %s" % exc)
    names = [name for name, _synset in categories]
    duplicates = sorted(set([name for name in names if names.count(name) > 1]))
    if duplicates:
        report.error("duplicate category names in synsetoffset2category.txt: %s" % ", ".join(duplicates))
    return categories


def split_tokens(root, split, report):
    needed = []
    if split == "trainval":
        needed = ["train", "val"]
    else:
        needed = [split]
    ids = set()
    split_dir = os.path.join(root, "train_test_split")
    if not os.path.isdir(split_dir):
        report.error("missing train_test_split directory at %s" % split_dir)
        return ids
    for key in needed:
        path = os.path.join(split_dir, SPLIT_FILES[key])
        if not os.path.isfile(path):
            report.error("missing split JSON %s" % path)
            continue
        try:
            with io.open(path, "r", encoding="utf-8") as handle:
                entries = json.load(handle)
        except Exception as exc:
            report.error("failed reading %s: %s" % (path, exc))
            continue
        if not isinstance(entries, list):
            report.error("split JSON %s must contain a list of path strings" % path)
            continue
        bad_entries = 0
        for entry in entries:
            if not isinstance(entry, str if sys.version_info[0] >= 3 else basestring):  # noqa: F821 on py3 branch only
                bad_entries += 1
                continue
            parts = entry.split("/")
            if len(parts) < 3 or not parts[2]:
                bad_entries += 1
                continue
            ids.add(parts[2])
        if bad_entries:
            report.warn("%s had %d entries that do not match loader parsing d.split('/')[2]" % (path, bad_entries))
    report.add("loaded %d unique shape ids for split %s" % (len(ids), split))
    return ids


def parse_class_choices(raw_values):
    if not raw_values:
        return None
    values = []
    for raw in raw_values:
        for part in raw.split(","):
            item = part.strip()
            if item:
                values.append(item)
    return values or None


def first_nonempty_lines(path, max_lines):
    lines = []
    with io.open(path, "r", encoding="utf-8", errors="ignore") if sys.version_info[0] >= 3 else io.open(path, "r") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
                if len(lines) >= max_lines:
                    break
    return lines


def is_float(value):
    try:
        float(value)
        return True
    except Exception:
        return False


def int_label(value):
    try:
        as_float = float(value)
        as_int = int(as_float)
        if abs(as_float - as_int) > 1e-6:
            return None
        return as_int
    except Exception:
        return None


def validate_normal_file(path, category, args, report):
    rel = os.path.relpath(path, args.root)
    try:
        lines = first_nonempty_lines(path, args.max_lines_per_file)
    except Exception as exc:
        report.error("%s: failed to read normal sample: %s" % (rel, exc))
        return
    if not lines:
        report.error("%s: empty sample file" % rel)
        return
    expected_labels = set(SEG_CLASSES.get(category, []))
    for idx, line in enumerate(lines, 1):
        fields = line.split()
        if len(fields) < 7:
            report.error("%s line %d: expected at least 7 columns (xyz normal label), got %d" % (rel, idx, len(fields)))
            continue
        if not all(is_float(v) for v in fields[:6]):
            report.error("%s line %d: first six columns must be numeric xyz+normal values" % (rel, idx))
        label = int_label(fields[-1])
        if label is None:
            report.error("%s line %d: last column must be an integer part label" % (rel, idx))
        elif args.strict_labels and expected_labels and label not in expected_labels:
            report.error("%s line %d: label %s is outside expected range for %s: %s" % (rel, idx, label, category, sorted(expected_labels)))
    report.checked_files.append(rel)


def validate_legacy_pair(points_path, seg_path, category, args, report):
    rel_points = os.path.relpath(points_path, args.root)
    rel_seg = os.path.relpath(seg_path, args.root)
    try:
        point_lines = first_nonempty_lines(points_path, args.max_lines_per_file)
    except Exception as exc:
        report.error("%s: failed to read .pts file: %s" % (rel_points, exc))
        point_lines = []
    try:
        seg_lines = first_nonempty_lines(seg_path, args.max_lines_per_file)
    except Exception as exc:
        report.error("%s: failed to read .seg file: %s" % (rel_seg, exc))
        seg_lines = []
    if not point_lines:
        report.error("%s: empty .pts file" % rel_points)
    if not seg_lines:
        report.error("%s: empty .seg file" % rel_seg)
    for idx, line in enumerate(point_lines, 1):
        fields = line.split()
        if len(fields) < 3 or not all(is_float(v) for v in fields[:3]):
            report.error("%s line %d: expected at least three numeric XYZ columns" % (rel_points, idx))
    for idx, line in enumerate(seg_lines, 1):
        fields = line.split()
        if not fields:
            continue
        label = int_label(fields[0])
        if label is None:
            report.error("%s line %d: expected integer segmentation label" % (rel_seg, idx))
        elif args.strict_labels and label < 1:
            report.error("%s line %d: legacy on-disk labels should be one-based before loader subtracts 1" % (rel_seg, idx))
    report.checked_files.extend([rel_points, rel_seg])


def choose_files_by_split(filenames, split_ids, suffix):
    chosen = []
    for name in sorted(filenames):
        if not name.endswith(suffix):
            continue
        token = os.path.splitext(os.path.basename(name))[0]
        if token in split_ids:
            chosen.append(name)
    return chosen


def validate_normal(root, categories, split_ids, args, report):
    for category, synset in categories:
        dir_path = os.path.join(root, synset)
        if not os.path.isdir(dir_path):
            report.error("%s: missing normal category directory %s" % (category, dir_path))
            report.category_counts[category] = 0
            continue
        try:
            names = os.listdir(dir_path)
        except Exception as exc:
            report.error("%s: cannot list %s: %s" % (category, dir_path, exc))
            report.category_counts[category] = 0
            continue
        chosen = choose_files_by_split(names, split_ids, ".txt")
        report.category_counts[category] = len(chosen)
        if not chosen:
            msg = "%s: selected split has 0 normal .txt samples in %s" % (category, dir_path)
            if args.allow_empty_split:
                report.warn(msg)
            else:
                report.error(msg)
            continue
        for name in chosen[: args.max_samples_per_category]:
            validate_normal_file(os.path.join(dir_path, name), category, args, report)


def validate_legacy(root, categories, split_ids, args, report):
    for category, synset in categories:
        cat_dir = os.path.join(root, synset)
        points_dir = os.path.join(cat_dir, "points")
        seg_dir = os.path.join(cat_dir, "points_label")
        if not os.path.isdir(points_dir):
            report.error("%s: missing legacy points directory %s" % (category, points_dir))
            report.category_counts[category] = 0
            continue
        if not os.path.isdir(seg_dir):
            report.error("%s: missing legacy points_label directory %s" % (category, seg_dir))
            report.category_counts[category] = 0
            continue
        try:
            point_names = os.listdir(points_dir)
        except Exception as exc:
            report.error("%s: cannot list %s: %s" % (category, points_dir, exc))
            report.category_counts[category] = 0
            continue
        chosen = choose_files_by_split(point_names, split_ids, ".pts")
        report.category_counts[category] = len(chosen)
        if not chosen:
            msg = "%s: selected split has 0 legacy .pts samples in %s" % (category, points_dir)
            if args.allow_empty_split:
                report.warn(msg)
            else:
                report.error(msg)
            continue
        for name in chosen[: args.max_samples_per_category]:
            token = os.path.splitext(os.path.basename(name))[0]
            seg_path = os.path.join(seg_dir, token + ".seg")
            if not os.path.isfile(seg_path):
                report.error("%s: missing segmentation file for %s: %s" % (category, token, seg_path))
                continue
            validate_legacy_pair(os.path.join(points_dir, name), seg_path, category, args, report)


def filter_categories(categories, choices, report):
    if not choices:
        return categories
    available = dict(categories)
    selected = []
    for choice in choices:
        if choice not in available:
            report.error("requested category %s is not present in synsetoffset2category.txt" % choice)
        else:
            selected.append((choice, available[choice]))
    return selected


def build_parser():
    parser = argparse.ArgumentParser(description="Validate pointnet2 ShapeNetPart dataset layout.")
    parser.add_argument("root", help="ShapeNetPart dataset root to validate.")
    parser.add_argument("--format", choices=["normal", "legacy-points"], default="normal", help="Loader layout to validate.")
    parser.add_argument("--split", choices=["train", "val", "trainval", "test"], default="trainval", help="Dataset split to validate using source loader semantics.")
    parser.add_argument("--class-choice", action="append", help="Category name(s) to validate; may be repeated or comma-separated.")
    parser.add_argument("--allow-empty-split", action="store_true", help="Report empty selected category splits as warnings instead of errors.")
    parser.add_argument("--strict-labels", action="store_true", help="Check sampled labels against known category ranges when possible.")
    parser.add_argument("--require-16-categories", action="store_true", help="Require the official 16 ShapeNetPart categories.")
    parser.add_argument("--max-samples-per-category", type=int, default=3, help="Maximum files to inspect per selected category.")
    parser.add_argument("--max-lines-per-file", type=int, default=5, help="Maximum non-empty lines to inspect per sampled file.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON report.")
    return parser


def run(args):
    report = Report()
    args.root = os.path.abspath(args.root)
    if args.max_samples_per_category <= 0:
        report.error("--max-samples-per-category must be positive")
        return report
    if args.max_lines_per_file <= 0:
        report.error("--max-lines-per-file must be positive")
        return report
    if not os.path.isdir(args.root):
        report.error("dataset root is not a directory: %s" % args.root)
        return report

    categories = read_category_file(args.root, report)
    choices = parse_class_choices(args.class_choice)
    categories = filter_categories(categories, choices, report)
    if args.require_16_categories and len(categories) != 16:
        report.error("expected 16 categories, found %d after filtering" % len(categories))
    unknown_seg_categories = [name for name, _synset in categories if name not in SEG_CLASSES]
    if unknown_seg_categories and args.format == "normal":
        report.warn("categories without built-in seg_classes label ranges: %s" % ", ".join(unknown_seg_categories))

    split_ids = split_tokens(args.root, args.split, report)
    if categories and split_ids:
        if args.format == "normal":
            validate_normal(args.root, categories, split_ids, args, report)
        else:
            validate_legacy(args.root, categories, split_ids, args, report)
    return report


def print_text(report):
    status = "OK" if not report.errors else "ERROR"
    print("ShapeNetPart layout validation: %s" % status)
    for msg in report.info:
        print("info: %s" % msg)
    for category in sorted(report.category_counts):
        print("category %s: %d selected sample(s)" % (category, report.category_counts[category]))
    for rel in report.checked_files:
        print("checked: %s" % rel)
    for msg in report.warnings:
        print("warning: %s" % msg)
    for msg in report.errors:
        print("error: %s" % msg)


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    report = run(args)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if not report.errors else 2


if __name__ == "__main__":
    sys.exit(main())
