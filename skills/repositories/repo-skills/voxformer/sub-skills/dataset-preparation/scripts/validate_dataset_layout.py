#!/usr/bin/env python3
"""Read-only structural checker for VoxFormer SemanticKITTI artifacts.

The checker never creates or modifies files below --root.  --self-test uses a
private temporary directory and is the deterministic synthetic-fixture check.
It validates names and consumer-facing shapes, not semantic correctness.
"""

from __future__ import print_function

import argparse
import json
import math
import re
import shutil
import sys
import tempfile
from pathlib import Path

try:
    import numpy as np
except ImportError:  # The layout/name checks remain usable without NumPy.
    np = None

FRAME_RE = re.compile(r"^(\d{6})$")
SEQUENCES = tuple("{:02d}".format(i) for i in range(22))
PACKED_BYTES = 256 * 256 * 32 // 8
LABEL_BYTES = 256 * 256 * 32 * 2


class Finding(object):
    def __init__(self, severity, code, message):
        self.severity = severity
        self.code = code
        self.message = message

    def as_dict(self):
        return {"severity": self.severity, "code": self.code,
                "message": self.message}


def add(findings, severity, code, message):
    findings.append(Finding(severity, code, message))


def file_names(directory, pattern=None):
    if not directory.is_dir():
        return []
    values = [item for item in directory.iterdir() if item.is_file()]
    if pattern is not None:
        values = [item for item in values if pattern(item.name)]
    return sorted(values, key=lambda item: item.name)


def frame_from_name(name, suffix):
    if not name.endswith(suffix):
        return None
    stem = name[:-len(suffix)] if suffix else name
    match = FRAME_RE.match(stem)
    return match.group(1) if match else None


def check_matrix_file(path, key, findings):
    if not path.is_file():
        add(findings, "error", "missing-calibration",
            "missing calibration file: {}".format(path.relative_to(path.parents[3])
                                                    if len(path.parents) > 3 else path))
        return
    found = None
    try:
        for line in path.read_text().splitlines():
            if ":" not in line:
                continue
            name, values = line.split(":", 1)
            if name.strip() == key:
                found = [float(value) for value in values.split()]
                break
    except (OSError, ValueError):
        found = None
    if found is None or len(found) != 12 or not all(math.isfinite(v) for v in found):
        add(findings, "error", "invalid-calibration",
            "{} in {} must contain 12 finite numbers".format(key, path.name))


def check_poses(path, image_frames, findings):
    if not path.is_file():
        add(findings, "error", "missing-poses", "missing poses.txt")
        return
    rows = []
    try:
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            values = [float(value) for value in line.split()]
            if len(values) != 12 or not all(math.isfinite(v) for v in values):
                add(findings, "error", "invalid-pose-row",
                    "poses.txt line {} must contain 12 finite numbers".format(line_number))
            else:
                rows.append(values)
    except (OSError, ValueError):
        add(findings, "error", "invalid-poses", "poses.txt is not readable numeric text")
        return
    for frame in image_frames:
        if int(frame) >= len(rows):
            add(findings, "error", "pose-frame-mismatch",
                "poses.txt has {} rows but image frame {} is requested".format(len(rows), frame))


def check_npy(path, expected_shape, findings):
    if np is None:
        add(findings, "warning", "numpy-unavailable",
            "cannot inspect {} shape without NumPy".format(path.name))
        return
    try:
        array = np.load(str(path), mmap_mode="r", allow_pickle=False)
        if tuple(array.shape) != tuple(expected_shape):
            add(findings, "error", "label-shape",
                "{} has shape {}, expected {}".format(
                    path.name, tuple(array.shape), tuple(expected_shape)))
    except Exception as exc:
        add(findings, "error", "label-read",
            "cannot read {} as a NumPy array: {}".format(path.name, exc))


def check_packed(path, findings):
    try:
        size = path.stat().st_size
    except OSError as exc:
        add(findings, "error", "artifact-stat", "cannot stat {}: {}".format(path.name, exc))
        return
    if size != PACKED_BYTES:
        add(findings, "error", "packed-size",
            "{} is {} bytes; expected {} packed bytes for (256,256,32)".format(
                path.name, size, PACKED_BYTES))


def check_raw_voxels(voxels, findings, require_raw):
    raw_labels = file_names(voxels, lambda name: name.endswith(".label"))
    if not raw_labels:
        if require_raw:
            add(findings, "error", "missing-raw-labels",
                "raw voxels directory has no .label files")
        else:
            add(findings, "warning", "raw-labels-unchecked",
                "no raw .label files; use --require-raw-voxels for conversion preflight")
        return
    for label in raw_labels:
        frame = label.name[:-len(".label")]
        if not FRAME_RE.match(frame):
            add(findings, "error", "raw-frame-name",
                "raw label has non-six-digit frame name: {}".format(label.name))
            continue
        for extension, expected in ((".invalid", PACKED_BYTES),
                                    (".occluded", PACKED_BYTES),
                                    (".bin", PACKED_BYTES)):
            companion = voxels / (frame + extension)
            if not companion.is_file():
                add(findings, "error", "missing-raw-companion",
                    "{} is missing {}".format(label.name, companion.name))
            elif require_raw:
                size = companion.stat().st_size
                if size != expected:
                    add(findings, "error", "raw-size",
                        "{} is {} bytes; expected {}".format(companion.name, size, expected))
        if require_raw and label.stat().st_size != LABEL_BYTES:
            add(findings, "error", "raw-label-size",
                "{} is {} bytes; expected {} uint16 voxels".format(
                    label.name, label.stat().st_size, LABEL_BYTES))


def check_sequence(dataset, sequence, stage, depthmodel, nsweep, query_tag,
                   findings, require_raw, require_velodyne):
    base = dataset / "sequences" / sequence
    if not base.is_dir():
        add(findings, "error", "missing-sequence", "missing sequence directory {}".format(sequence))
        return

    calib = base / "calib.txt"
    check_matrix_file(calib, "P2", findings)
    check_matrix_file(calib, "Tr", findings)

    image_dir = base / "image_2"
    if not image_dir.is_dir():
        add(findings, "error", "missing-images", "missing image_2 for sequence {}".format(sequence))
        image_frames = []
    else:
        image_frames = []
        for item in file_names(image_dir):
            if item.suffix.lower() != ".png":
                continue
            frame = frame_from_name(item.name, ".png")
            if frame is None:
                add(findings, "error", "image-frame-name",
                    "image name is not six digits: {}".format(item.name))
            else:
                image_frames.append(frame)
        if not image_frames:
            add(findings, "error", "empty-images", "image_2 has no six-digit .png frames")

    check_poses(base / "poses.txt", image_frames, findings)

    velodyne = base / "velodyne"
    if not velodyne.is_dir():
        severity = "error" if require_velodyne else "warning"
        add(findings, severity, "missing-velodyne",
            "missing velodyne source directory for sequence {}".format(sequence))

    voxels = base / "voxels"
    if not voxels.is_dir():
        severity = "error" if require_raw else "warning"
        add(findings, severity, "missing-voxels",
            "missing raw voxels directory for sequence {}".format(sequence))
    else:
        check_raw_voxels(voxels, findings, require_raw)

    label_root = dataset / "labels" / sequence
    generated_root = dataset / ("sequences_{}_sweep{}".format(depthmodel, nsweep)) / sequence

    if stage in ("stage1", "both"):
        pseudo_dir = generated_root / "voxels"
        pseudo = file_names(pseudo_dir, lambda name: name.endswith(".pseudo"))
        if not pseudo:
            add(findings, "error", "missing-pseudo",
                "stage 1 has no .pseudo files under {}".format(pseudo_dir))
        for item in pseudo:
            frame = frame_from_name(item.name, ".pseudo")
            if frame is None:
                add(findings, "error", "pseudo-frame-name",
                    "pseudo file has non-six-digit frame name: {}".format(item.name))
                continue
            check_packed(item, findings)
            if frame not in image_frames:
                add(findings, "error", "pseudo-image-mismatch",
                    "pseudo frame {} has no matching image_2 frame".format(frame))
            target = label_root / (frame + "_1_2.npy")
            if not target.is_file():
                add(findings, "error", "missing-stage1-label", "missing {}".format(target.name))
            else:
                check_npy(target, (128, 128, 16), findings)

    if stage in ("stage2", "both"):
        query_dir = generated_root / "queries"
        suffix = "." + query_tag
        queries = file_names(query_dir, lambda name: name.endswith(suffix))
        if not queries:
            add(findings, "error", "missing-queries",
                "stage 2 has no *{} files under {}".format(suffix, query_dir))
        for item in queries:
            frame = frame_from_name(item.name, suffix)
            if frame is None:
                add(findings, "error", "query-frame-name",
                    "query file has non-six-digit frame name: {}".format(item.name))
                continue
            check_packed(item, findings)
            if frame not in image_frames:
                add(findings, "error", "query-image-mismatch",
                    "query frame {} has no matching image_2 frame".format(frame))
            target = label_root / (frame + "_1_1.npy")
            if not target.is_file():
                add(findings, "error", "missing-stage2-label", "missing {}".format(target.name))
            else:
                check_npy(target, (256, 256, 32), findings)


def validate(root, sequences, stage, depthmodel, nsweep, query_tag,
             require_raw=False, require_velodyne=False):
    findings = []
    root = Path(root)
    dataset = root / "dataset"
    if not root.is_dir():
        add(findings, "error", "missing-root", "root is not a directory")
        return findings
    if not dataset.is_dir():
        add(findings, "error", "missing-dataset", "root has no dataset/ directory")
        return findings
    for sequence in sequences:
        check_sequence(dataset, sequence, stage, depthmodel, nsweep, query_tag,
                       findings, require_raw, require_velodyne)
    return findings


def write_fixture(root):
    dataset = root / "dataset"
    seq = dataset / "sequences" / "08"
    (seq / "image_2").mkdir(parents=True)
    (seq / "image_3").mkdir()
    (seq / "velodyne").mkdir()
    (seq / "voxels").mkdir()
    (dataset / "labels" / "08").mkdir(parents=True)
    generated = dataset / "sequences_msnet3d_sweep10" / "08"
    (generated / "voxels").mkdir(parents=True)
    (generated / "queries").mkdir()
    (seq / "calib.txt").write_text(
        "P2: 1 0 0 0 0 1 0 0 0 0 1 0\n"
        "Tr: 1 0 0 0 0 1 0 0 0 0 1 0\n")
    (seq / "poses.txt").write_text("1 0 0 0 0 1 0 0 0 0 1 0\n")
    (seq / "image_2" / "000000.png").write_bytes(b"fixture")
    for extension in (".bin", ".label", ".occluded", ".invalid"):
        size = LABEL_BYTES if extension == ".label" else PACKED_BYTES
        (seq / "voxels" / ("000000" + extension)).write_bytes(b"\0" * size)
    (seq / "velodyne" / "000000.bin").write_bytes(b"\0" * 16)
    (generated / "voxels" / "000000.pseudo").write_bytes(b"\0" * PACKED_BYTES)
    (generated / "queries" / "000000.query_iou5203_pre7712_rec6153").write_bytes(
        b"\0" * PACKED_BYTES)
    if np is None:
        raise RuntimeError("--self-test requires NumPy to create deterministic labels")
    np.save(str(dataset / "labels" / "08" / "000000_1_1.npy"),
            np.zeros((256, 256, 32), dtype=np.uint8))
    np.save(str(dataset / "labels" / "08" / "000000_1_2.npy"),
            np.zeros((128, 128, 16), dtype=np.uint8))


def self_test():
    with tempfile.TemporaryDirectory(prefix="voxformer-layout-") as temp:
        root = Path(temp)
        write_fixture(root)
        good = validate(root, ["08"], "both", "msnet3d", 10,
                        "query_iou5203_pre7712_rec6153", True, True)
        assert not [item for item in good if item.severity == "error"], good
        shutil.rmtree(str(root / "dataset" / "labels" / "08"))
        query = (root / "dataset" / "sequences_msnet3d_sweep10" / "08" /
                 "queries" / "000000.query_iou5203_pre7712_rec6153")
        query.unlink()
        bad = validate(root, ["08"], "stage2", "msnet3d", 10,
                       "query_iou5203_pre7712_rec6153", False, False)
        codes = {item.code for item in bad if item.severity == "error"}
        assert "missing-queries" in codes
        query.write_bytes(b"\0" * PACKED_BYTES)
        bad_with_query = validate(root, ["08"], "stage2", "msnet3d", 10,
                                  "query_iou5203_pre7712_rec6153", False, False)
        codes_with_query = {item.code for item in bad_with_query
                            if item.severity == "error"}
        assert "missing-stage2-label" in codes_with_query
    print("self-test: PASS (valid and deliberately incomplete fixtures)")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="Read-only VoxFormer SemanticKITTI layout and artifact checker")
    parser.add_argument("--root", help="user data root containing dataset/")
    parser.add_argument("--sequence", action="append", dest="sequences",
                        choices=SEQUENCES, help="sequence ID; repeat (default: 00..21)")
    parser.add_argument("--stage", choices=("stage1", "stage2", "both"),
                        default="both", help="consumer contract to validate")
    parser.add_argument("--depthmodel", default="msnet3d",
                        help="generated directory model token (default: msnet3d)")
    parser.add_argument("--nsweep", type=int, default=10,
                        help="generated directory sweep length (default: 10)")
    parser.add_argument("--query-tag", default="query_iou5203_pre7712_rec6153",
                        help="stage-2 query suffix without the leading dot")
    parser.add_argument("--require-raw-voxels", action="store_true",
                        help="make raw .label/.invalid/.occluded/.bin checks errors")
    parser.add_argument("--require-velodyne", action="store_true",
                        help="make missing source velodyne directories errors")
    parser.add_argument("--strict", action="store_true",
                        help="treat warnings as errors")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="emit deterministic JSON findings")
    parser.add_argument("--self-test", action="store_true",
                        help="run deterministic temporary valid/invalid fixture checks")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.root:
        parser.error("--root is required unless --self-test is used")
    sequences = tuple(args.sequences) if args.sequences else SEQUENCES
    findings = validate(args.root, sequences, args.stage, args.depthmodel,
                        args.nsweep, args.query_tag, args.require_raw_voxels,
                        args.require_velodyne)
    if args.strict:
        for item in findings:
            if item.severity == "warning":
                item.severity = "error"
    if args.as_json:
        print(json.dumps({"ok": not any(item.severity == "error" for item in findings),
                          "findings": [item.as_dict() for item in findings]},
                         sort_keys=True, indent=2))
    else:
        if not findings:
            print("PASS: requested layout contract has no findings")
        for item in findings:
            print("{} [{}] {}".format(item.severity.upper(), item.code, item.message))
        errors = sum(item.severity == "error" for item in findings)
        warnings = sum(item.severity == "warning" for item in findings)
        print("Summary: {} error(s), {} warning(s)".format(errors, warnings))
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
