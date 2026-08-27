#!/usr/bin/env python3
"""Read-only preflight for GradSLAM dataset adapter layouts.

This checker validates names, required metadata files, and paths referenced by
ScanNet sequence metadata. It deliberately does not import GradSLAM, decode
images, download data, or modify the caller's dataset.
"""

from __future__ import print_function

import argparse
import os
import sys
from pathlib import Path


def _parser():
    parser = argparse.ArgumentParser(
        description="Check TUM, ICL-NUIM, or ScanNet paths without modifying them."
    )
    parser.add_argument("--kind", required=True, choices=("tum", "icl", "scannet"))
    parser.add_argument("--basedir", required=True, help="Extracted dataset root")
    parser.add_argument(
        "--seqmetadir",
        help="ScanNet sequence-metadata directory (required for --kind scannet)",
    )
    parser.add_argument(
        "--select",
        action="append",
        default=None,
        metavar="NAME",
        help="Restrict checks to this sequence/trajectory/scene; repeat the option",
    )
    parser.add_argument(
        "--require-poses",
        action="store_true",
        help="Require TUM/ICL pose metadata in addition to RGB/depth metadata",
    )
    parser.add_argument(
        "--require-labels",
        action="store_true",
        help="For ScanNet, require label-filt paths in every metadata row",
    )
    return parser


def _missing_file(path, label):
    if not path.is_file():
        return "%s is missing: %s" % (label, path)
    return None


def _is_tum_name(name):
    parts = name.split("_")
    return len(parts) >= 4 and parts[0] == "rgbd" and parts[1] == "dataset" and parts[2][:-1] == "freiburg"


def _check_tum(root, selected, require_poses):
    errors = []
    all_directories = sorted(p for p in root.iterdir() if p.is_dir())
    invalid = [p.name for p in all_directories if not _is_tum_name(p.name)]
    errors = ["unexpected TUM subdirectory name: %s" % name for name in invalid]
    directories = [p for p in all_directories if _is_tum_name(p.name)]
    if selected:
        wanted = set(selected)
        directories = [p for p in directories if p.name in wanted]
        missing = sorted(wanted.difference(p.name for p in directories))
        errors.extend("selected TUM sequence is missing: %s" % name for name in missing)
    if not directories:
        errors.append("no TUM directories named rgbd_dataset_freiburgX_NAME were found")
        return errors
    for directory in directories:
        for child in ("rgb", "depth"):
            if not (directory / child).is_dir():
                errors.append("%s is missing directory %s" % (directory.name, child))
        for filename in ("rgb.txt", "depth.txt"):
            error = _missing_file(directory / filename, "%s/%s" % (directory.name, filename))
            if error:
                errors.append(error)
        if require_poses:
            error = _missing_file(
                directory / "groundtruth.txt", "%s/groundtruth.txt" % directory.name
            )
            if error:
                errors.append(error)
    return errors


def _check_icl(root, selected, require_poses):
    errors = []
    directories = sorted(
        p
        for p in root.iterdir()
        if p.is_dir() and p.name.startswith("living_room_traj") and p.name.endswith("_frei_png")
    )
    if selected:
        wanted = set(selected)
        directories = [p for p in directories if p.name in wanted]
        missing = sorted(wanted.difference(p.name for p in directories))
        errors.extend("selected ICL trajectory is missing: %s" % name for name in missing)
    if not directories:
        errors.append("no ICL directories named living_room_trajX_frei_png were found")
        return errors
    for directory in directories:
        for child in ("rgb", "depth"):
            if not (directory / child).is_dir():
                errors.append("%s is missing directory %s" % (directory.name, child))
        error = _missing_file(
            directory / "associations.txt", "%s/associations.txt" % directory.name
        )
        if error:
            errors.append(error)
        if require_poses:
            suffix = directory.name[len("living_room_traj") :].split("_")[0]
            error = _missing_file(
                directory / ("livingRoom%sn.gt.sim" % suffix),
                "%s pose file" % directory.name,
            )
            if error:
                errors.append(error)
    return errors


def _check_scannet(root, metadata_root, selected, require_labels):
    errors = []
    if not metadata_root.is_dir():
        return ["ScanNet metadata directory is missing: %s" % metadata_root]
    metadata = sorted(metadata_root.glob("*.txt"))
    if selected:
        wanted = set(selected)
        metadata = [p for p in metadata if p.name.split("-", 1)[0] in wanted]
        found = {p.name.split("-", 1)[0] for p in metadata}
        errors.extend("selected ScanNet scene has no metadata file: %s" % name for name in sorted(wanted - found))
    if not metadata:
        errors.append("no ScanNet metadata .txt files were found")
        return errors

    for meta in metadata:
        scene = meta.name.split("-", 1)[0]
        scene_dir = root / scene
        if not scene_dir.is_dir():
            errors.append("metadata scene directory is missing: %s" % scene_dir)
        try:
            lines = meta.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            errors.append("cannot read %s: %s" % (meta, exc))
            continue
        if not lines:
            errors.append("metadata file is empty: %s" % meta)
            continue
        for line_number, raw in enumerate(lines, 1):
            fields = raw.split()
            prefix = "%s:%d" % (meta.name, line_number)
            if len(fields) < 16:
                errors.append("%s has %d fields; expected at least 16" % (prefix, len(fields)))
                continue
            expected = ((0, "color"), (2, "depth"), (4, "pose"), (6, "label-filt"), (14, "intrinsic_depth"))
            for index, label in expected:
                if fields[index] != label:
                    errors.append("%s field %d is %r, expected %r" % (prefix, index, fields[index], label))
            path_fields = ((1, "color"), (3, "depth"), (5, "pose"), (15, "intrinsic_depth"))
            if require_labels:
                path_fields += ((7, "label-filt"),)
            for index, label in path_fields:
                referenced = root / fields[index]
                if not referenced.is_file():
                    errors.append("%s %s path is missing: %s" % (prefix, label, referenced))
    return errors


def main(argv=None):
    args = _parser().parse_args(argv)
    root = Path(args.basedir).expanduser()
    errors = []
    if not root.is_dir():
        errors.append("dataset root is missing or not a directory: %s" % root)
    else:
        selected = args.select
        if args.kind == "tum":
            errors = _check_tum(root, selected, args.require_poses)
        elif args.kind == "icl":
            errors = _check_icl(root, selected, args.require_poses)
        else:
            if not args.seqmetadir:
                errors.append("--seqmetadir is required for --kind scannet")
            else:
                errors = _check_scannet(
                    root,
                    Path(args.seqmetadir).expanduser(),
                    selected,
                    args.require_labels,
                )
    if errors:
        print("FAIL: %d layout issue(s)" % len(errors))
        for error in errors:
            print("- %s" % error)
        return 1
    print("OK: %s layout preflight passed (paths and metadata names only)" % args.kind)
    return 0


if __name__ == "__main__":
    sys.exit(main())
