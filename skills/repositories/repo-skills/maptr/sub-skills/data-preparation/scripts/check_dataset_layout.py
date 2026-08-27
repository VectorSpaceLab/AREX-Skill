#!/usr/bin/env python3
"""CPU-only, read-only MapTR dataset layout checker.

This checks names and lightweight JSON structure only. It deliberately does not
import MapTR, mmcv, nuscenes, av2, torch, or deserialize annotation pickles.
"""

from __future__ import print_function

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


EXIT_ERRORS = 1


class Report(object):
    def __init__(self, dataset, as_json=False):
        self.dataset = dataset
        self.as_json = as_json
        self.checks = []

    def add(self, status, message, path=None):
        item = {"status": status, "message": message}
        if path is not None:
            item["path"] = str(path)
        self.checks.append(item)

    def ok(self, message, path=None):
        self.add("pass", message, path)

    def warn(self, message, path=None):
        self.add("warning", message, path)

    def error(self, message, path=None):
        self.add("error", message, path)

    @property
    def errors(self):
        return [item for item in self.checks if item["status"] == "error"]

    def emit(self):
        if self.as_json:
            print(json.dumps({
                "dataset": self.dataset,
                "checks": self.checks,
                "errors": len(self.errors),
                "warnings": sum(item["status"] == "warning" for item in self.checks),
                "ok": not self.errors,
            }, indent=2, sort_keys=True))
            return
        print("Dataset: {}".format(self.dataset))
        for item in self.checks:
            label = item["status"].upper()
            suffix = " ({})".format(item["path"]) if "path" in item else ""
            print("[{}] {}{}".format(label, item["message"], suffix))
        print("Summary: {} error(s), {} warning(s)".format(
            len(self.errors),
            sum(item["status"] == "warning" for item in self.checks)))


def existing_dir(report, path, label, required=True):
    path = Path(path)
    if path.is_dir():
        report.ok("{} directory exists".format(label), path)
        return True
    if required:
        report.error("{} directory is missing".format(label), path)
    else:
        report.warn("{} directory is missing".format(label), path)
    return False


def existing_file(report, path, label, required=True):
    path = Path(path)
    if path.is_file():
        try:
            nonempty = path.stat().st_size > 0
        except OSError:
            nonempty = False
        if nonempty:
            report.ok("{} file exists and is non-empty".format(label), path)
            return True
        if required:
            report.error("{} file is empty".format(label), path)
        else:
            report.warn("{} file is empty".format(label), path)
        return False
    if required:
        report.error("{} file is missing".format(label), path)
    else:
        report.warn("{} file is missing".format(label), path)
    return False


def check_nuscenes(args, report):
    root = Path(args.root).expanduser().resolve()
    if not existing_dir(report, root, "nuScenes root"):
        return

    for name in ("maps", "samples", "sweeps"):
        existing_dir(report, root / name, "nuScenes {}".format(name))

    releases = ["v1.0-trainval", "v1.0-test", "v1.0-mini"]
    found_releases = [name for name in releases if (root / name).is_dir()]
    if found_releases:
        report.ok("nuScenes release metadata found: {}".format(", ".join(found_releases)))
    else:
        report.error("nuScenes release metadata directory is missing; expected one of {}".format(
            ", ".join(releases)), root)

    if not args.canbus_root:
        report.error("--canbus-root is required for the documented nuScenes layout")
    else:
        canbus_root = Path(args.canbus_root).expanduser().resolve()
        expected = canbus_root / "can_bus"
        if expected.is_dir():
            report.ok("nuScenes CAN bus directory is at the requested parent level", expected)
        else:
            nested = root / "can_bus"
            if nested.is_dir():
                report.error(
                    "CAN bus is nested under the nuScenes root; expected it at the --canbus-root parent level",
                    nested)
            else:
                report.error("nuScenes CAN bus directory is missing under --canbus-root", expected)
        if canbus_root == root:
            report.error("--canbus-root resolves to the nuScenes root; use its parent directory", canbus_root)

    if args.check_annotations:
        expected_names = [
            "nuscenes_infos_temporal_train.pkl",
            "nuscenes_infos_temporal_val.pkl",
        ]
        # The full-release dispatch also attempts a test file when the test
        # metadata is present. It is a warning unless explicitly requested.
        if (root / "v1.0-test").is_dir():
            expected_names.append("nuscenes_infos_temporal_test.pkl")
        for name in expected_names:
            existing_file(report, root / name, "nuScenes {}".format(name))


def check_map_archive(report, archive):
    try:
        with archive.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, UnicodeError, ValueError) as exc:
        report.error("AV2 map archive is not valid JSON: {}".format(exc), archive)
        return False
    if not isinstance(value, dict):
        report.error("AV2 map archive JSON must contain an object", archive)
        return False
    # ArgoverseStaticMap.from_json is later required to validate the full
    # schema. These keys are the three collections consumed by this converter;
    # requiring them catches an empty {} placeholder without claiming semantic
    # validation here.
    required_keys = {"lane_segments", "pedestrian_crossings", "drivable_areas"}
    missing = sorted(required_keys.difference(value))
    if missing:
        report.error(
            "AV2 map archive is missing converter collections: {}".format(", ".join(missing)),
            archive)
        return False
    report.ok("AV2 map archive has valid JSON and converter collection keys", archive)
    return True


def check_av2(args, report):
    root = Path(args.root).expanduser().resolve()
    if not existing_dir(report, root, "Argoverse2 sensor root"):
        return

    split_dirs = {}
    for split in ("train", "val", "test"):
        split_dirs[split] = existing_dir(report, root / split, "AV2 {} split".format(split))

    # The converter receives the parent of all splits and the custom dataset
    # uses the same root when selecting train/val.
    if not any(split_dirs.values()):
        return

    for split, split_exists in split_dirs.items():
        if not split_exists:
            continue
        logs = sorted(path for path in (root / split).iterdir() if path.is_dir())
        if not logs:
            report.error("AV2 {} split has no log directories".format(split), root / split)
            continue
        report.ok("AV2 {} split has {} log director{}".format(
            split, len(logs), "y" if len(logs) == 1 else "ies"), root / split)
        for log in logs:
            existing_dir(report, log / "sensors", "AV2 {} sensors for {}".format(split, log.name))
            map_dir = log / "map"
            if not existing_dir(report, map_dir, "AV2 {} map directory for {}".format(split, log.name)):
                continue
            archives = sorted(map_dir.glob("log_map_archive_*.json"))
            if len(archives) != 1:
                report.error(
                    "AV2 {} log must contain exactly one log_map_archive_*.json (found {})".format(
                        log.name, len(archives)), map_dir)
                continue
            check_map_archive(report, archives[0])

    if args.check_annotations:
        for split in ("train", "val", "test"):
            existing_file(report, root / "av2_map_infos_{}.pkl".format(split),
                          "AV2 {} annotation".format(split))


def run(args):
    report = Report(args.dataset, args.json)
    if args.dataset == "nuscenes":
        check_nuscenes(args, report)
    else:
        check_av2(args, report)
    report.emit()
    return EXIT_ERRORS if report.errors else 0


def make_file(path, content=b"x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(content)


def make_valid_nuscenes(root, parent):
    for name in ("maps", "samples", "sweeps", "v1.0-trainval", "v1.0-test"):
        (root / name).mkdir(parents=True, exist_ok=True)
    (parent / "can_bus").mkdir(parents=True, exist_ok=True)
    for name in (
        "nuscenes_infos_temporal_train.pkl",
        "nuscenes_infos_temporal_val.pkl",
        "nuscenes_infos_temporal_test.pkl",
    ):
        make_file(root / name)


def make_valid_av2(root):
    archive = json.dumps({
        "lane_segments": [],
        "pedestrian_crossings": [],
        "drivable_areas": [],
    }).encode("utf-8")
    for split in ("train", "val", "test"):
        log = root / split / ("log-{}".format(split))
        (log / "sensors").mkdir(parents=True, exist_ok=True)
        (log / "map").mkdir(parents=True, exist_ok=True)
        make_file(log / "map" / "log_map_archive_{}.json".format(split), archive)
        make_file(root / "av2_map_infos_{}.pkl".format(split))


def self_test():
    """Run deterministic tiny fixture checks; never touches the caller's data."""
    with tempfile.TemporaryDirectory(prefix="maptr-layout-") as temporary:
        base = Path(temporary)

        nusc_parent = base / "nusc-parent"
        nusc_root = nusc_parent / "nuscenes"
        make_valid_nuscenes(nusc_root, nusc_parent)
        valid_args = argparse.Namespace(
            dataset="nuscenes", root=str(nusc_root), canbus_root=str(nusc_parent),
            check_annotations=True, json=False)
        valid_report = Report("nuscenes")
        check_nuscenes(valid_args, valid_report)
        assert not valid_report.errors, "valid nuScenes fixture unexpectedly failed"

        wrong = base / "wrong-nusc"
        for name in ("maps", "samples", "sweeps", "v1.0-trainval"):
            (wrong / name).mkdir(parents=True, exist_ok=True)
        (wrong / "can_bus").mkdir(parents=True, exist_ok=True)
        wrong_args = argparse.Namespace(
            dataset="nuscenes", root=str(wrong), canbus_root=str(base),
            check_annotations=True, json=False)
        wrong_report = Report("nuscenes")
        check_nuscenes(wrong_args, wrong_report)
        wrong_text = "\n".join(item["message"] for item in wrong_report.errors)
        assert "CAN bus is nested" in wrong_text, "wrong CAN bus placement was not detected"
        assert "nuscenes_infos_temporal_train.pkl" in wrong_text, "missing temporal pkl was not detected"

        av2_root = base / "sensor"
        make_valid_av2(av2_root)
        av2_args = argparse.Namespace(
            dataset="av2", root=str(av2_root), check_annotations=True, json=False)
        av2_report = Report("av2")
        check_av2(av2_args, av2_report)
        assert not av2_report.errors, "valid AV2 fixture unexpectedly failed"

        difficult = base / "difficult-sensor"
        log = difficult / "train" / "log-a"
        (log / "sensors").mkdir(parents=True, exist_ok=True)
        (log / "map").mkdir(parents=True, exist_ok=True)
        make_file(log / "map" / "log_map_archive_a.json", b"not-json")
        (difficult / "val" / "log-b" / "sensors").mkdir(parents=True, exist_ok=True)
        (difficult / "val" / "log-b" / "map").mkdir(parents=True, exist_ok=True)
        make_file(difficult / "val" / "log-b" / "map" / "log_map_archive_b.json", b"{}")
        difficult_args = argparse.Namespace(
            dataset="av2", root=str(difficult), check_annotations=True, json=False)
        difficult_report = Report("av2")
        check_av2(difficult_args, difficult_report)
        difficult_text = "\n".join(item["message"] for item in difficult_report.errors)
        difficult_paths = "\n".join(item.get("path", "") for item in difficult_report.errors)
        assert "AV2 test split directory is missing" in difficult_text, "missing AV2 split was not detected"
        assert "not valid JSON" in difficult_text, "malformed AV2 archive was not detected"
        assert "missing converter collections" in difficult_text, "empty AV2 archive was not rejected"
        assert "av2_map_infos_train.pkl" in difficult_paths, "missing AV2 annotation pkl was not detected"

    print("self-test: PASS (nuScenes placement/temporal pkl and AV2 split/archive fixtures)")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Read-only CPU preflight for MapTR nuScenes or Argoverse2 "
            "directory layouts and generated annotation filenames."
        )
    )
    parser.add_argument("--dataset", choices=("nuscenes", "av2"),
                        help="dataset layout to check")
    parser.add_argument("--root", help="absolute or relative dataset root")
    parser.add_argument("--canbus-root",
                        help="parent containing can_bus for nuScenes")
    parser.add_argument("--check-annotations", action="store_true",
                        help="require the expected generated pkl filenames")
    parser.add_argument("--json", action="store_true",
                        help="emit a machine-readable report")
    parser.add_argument("--self-test", action="store_true",
                        help="run tiny synthetic fixture checks and exit")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.dataset or not args.root:
        parser.error("--dataset and --root are required unless --self-test is used")
    if args.dataset == "av2" and args.canbus_root:
        parser.error("--canbus-root is only valid for --dataset nuscenes")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
