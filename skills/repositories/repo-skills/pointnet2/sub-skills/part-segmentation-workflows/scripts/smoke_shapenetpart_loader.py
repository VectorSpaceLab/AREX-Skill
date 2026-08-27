#!/usr/bin/env python
"""Smoke-check the bundled ShapeNetPart layout validator with tiny fixtures."""
from __future__ import print_function

import argparse
import io
import os
import shutil
import sys
import tempfile

import validate_shapenetpart_layout as validator


def write_text(path, text):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    if sys.version_info[0] < 3 and isinstance(text, str):
        text = text.decode("utf-8")
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def make_normal_fixture(root):
    write_text(
        os.path.join(root, "synsetoffset2category.txt"),
        "Airplane 02691156\nChair 03001627\n",
    )
    split_dir = os.path.join(root, "train_test_split")
    os.makedirs(split_dir)
    write_text(os.path.join(split_dir, "shuffled_train_file_list.json"), "[\"shape_data/02691156/air_train\"]\n")
    write_text(os.path.join(split_dir, "shuffled_val_file_list.json"), "[]\n")
    write_text(os.path.join(split_dir, "shuffled_test_file_list.json"), "[\"shape_data/02691156/air_test\"]\n")
    os.makedirs(os.path.join(root, "02691156"))
    os.makedirs(os.path.join(root, "03001627"))
    sample = "0 0 0 1 0 0 0\n1 0 0 0 1 0 1\n"
    write_text(os.path.join(root, "02691156", "air_train.txt"), sample)
    write_text(os.path.join(root, "02691156", "air_test.txt"), sample)


def make_legacy_fixture(root):
    write_text(os.path.join(root, "synsetoffset2category.txt"), "Airplane 02691156\n")
    split_dir = os.path.join(root, "train_test_split")
    os.makedirs(split_dir)
    write_text(os.path.join(split_dir, "shuffled_train_file_list.json"), "[]\n")
    write_text(os.path.join(split_dir, "shuffled_val_file_list.json"), "[]\n")
    write_text(os.path.join(split_dir, "shuffled_test_file_list.json"), "[\"shape_data/02691156/air_legacy\"]\n")
    points = os.path.join(root, "02691156", "points")
    labels = os.path.join(root, "02691156", "points_label")
    os.makedirs(points)
    os.makedirs(labels)
    write_text(os.path.join(points, "air_legacy.pts"), "0 0 0\n1 0 0\n")
    write_text(os.path.join(labels, "air_legacy.seg"), "1\n2\n")


def run_case(argv, expect_ok):
    parser = validator.build_parser()
    args = parser.parse_args(argv)
    report = validator.run(args)
    ok = not report.errors
    if ok != expect_ok:
        validator.print_text(report)
        raise AssertionError("validator result mismatch for %r: expected ok=%s got ok=%s" % (argv, expect_ok, ok))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run tiny-fixture smoke checks for validate_shapenetpart_layout.py.")
    parser.add_argument("--keep", action="store_true", help="Keep the temporary fixture directory and print its path.")
    args = parser.parse_args(argv)

    tmp = tempfile.mkdtemp(prefix="pointnet2-shapenetpart-smoke-")
    try:
        normal_root = os.path.join(tmp, "normal")
        legacy_root = os.path.join(tmp, "legacy")
        os.makedirs(normal_root)
        os.makedirs(legacy_root)
        make_normal_fixture(normal_root)
        make_legacy_fixture(legacy_root)

        run_case([normal_root, "--format", "normal", "--split", "test", "--class-choice", "Airplane", "--strict-labels"], True)
        run_case([normal_root, "--format", "normal", "--split", "test", "--class-choice", "Chair"], False)
        run_case([legacy_root, "--format", "legacy-points", "--split", "test", "--class-choice", "Airplane", "--strict-labels"], True)

        print("ShapeNetPart validator smoke passed")
        if args.keep:
            print("fixture: %s" % tmp)
            tmp = None
        return 0
    finally:
        if tmp is not None:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    sys.exit(main())
