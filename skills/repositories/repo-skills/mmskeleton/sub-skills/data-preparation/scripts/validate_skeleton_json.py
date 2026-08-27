#!/usr/bin/env python3
"""Read-only validator for MMSkeleton skeleton JSON samples."""

from __future__ import print_function

import argparse
import json
import math
import os
import sys


SUPPORTED_CHANNELS = set(("x", "y", "score", "visibility"))
INFO_KEYS = ("resolution", "num_frame", "num_keypoints", "keypoint_channels")
ANNOTATION_KEYS = ("frame_index", "id", "person_id", "keypoints")


class IssueCollector(object):
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, path, location, message):
        self.errors.append("ERROR {}: {}: {}".format(path, location, message))

    def warning(self, path, location, message):
        self.warnings.append("WARNING {}: {}: {}".format(path, location, message))


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def is_finite_number(value):
    if not is_number(value):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        # Keep malformed numeric values on the normal validation-error path;
        # an oversized integer or non-finite numeric subclass must not escape
        # as an uncaught conversion exception.
        return False


def load_json(path, issues, label):
    try:
        with open(path, "r") as handle:
            return json.load(handle)
    except OSError as exc:
        issues.error(path, label, "cannot read JSON: {}".format(exc))
    except (TypeError, ValueError) as exc:
        issues.error(path, label, "invalid JSON: {}".format(exc))
    return None


def category_keys(sample_path, info):
    candidates = []
    video_name = info.get("video_name") if isinstance(info, dict) else None
    if isinstance(video_name, str) and video_name:
        candidates.append(video_name)
    basename = os.path.basename(sample_path)
    candidates.append(basename)
    if basename.lower().endswith(".json"):
        candidates.append(basename[:-5])
    stem = os.path.splitext(basename)[0]
    candidates.append(stem)
    result = []
    for candidate in candidates:
        if candidate not in result:
            result.append(candidate)
    return result


def validate_category_file(path, issues):
    root = load_json(path, issues, "category annotations")
    if root is None:
        return None
    if not isinstance(root, dict):
        issues.error(path, "root", "must be a JSON object")
        return None
    if "categories" not in root:
        issues.error(path, "root.categories", "required key is missing")
        categories = None
    else:
        categories = root["categories"]
        if not isinstance(categories, list) or not categories:
            issues.error(path, "root.categories", "must be a non-empty list")
            categories = None
        elif any(not isinstance(item, str) or not item for item in categories):
            issues.error(path, "root.categories", "every category must be a non-empty string")
        elif len(set(categories)) != len(categories):
            issues.error(path, "root.categories", "category names must be unique")
    if "annotations" not in root:
        issues.error(path, "root.annotations", "required key is missing")
        mapping = None
    else:
        mapping = root["annotations"]
        if not isinstance(mapping, dict):
            issues.error(path, "root.annotations", "must be an object keyed by video/file name")
            mapping = None
    valid_mapping = {}
    if mapping is not None:
        for name, entry in sorted(mapping.items()):
            location = "root.annotations[{}]".format(json.dumps(name))
            if not isinstance(name, str) or not name:
                issues.error(path, location, "mapping keys must be non-empty strings")
                continue
            if not isinstance(entry, dict) or "category_id" not in entry:
                issues.error(path, location, "must contain a category_id")
                continue
            category_id = entry["category_id"]
            if not is_integer(category_id):
                issues.error(path, location + ".category_id", "must be an integer")
                continue
            if categories is not None and not (0 <= category_id < len(categories)):
                issues.error(path, location + ".category_id", "{} is outside category range [0, {})".format(category_id, len(categories)))
                continue
            valid_mapping[name] = {"category_id": category_id}
    if categories is None or mapping is None:
        return None
    return {"categories": categories, "annotations": valid_mapping}


def validate_sample(path, category_data, num_track, issues):
    root = load_json(path, issues, "sample")
    if root is None:
        return False
    if not isinstance(root, dict):
        issues.error(path, "root", "must be a JSON object")
        return False

    for key in ("info", "annotations", "category_id"):
        if key not in root:
            issues.error(path, "root", "required key '{}' is missing".format(key))
    info = root.get("info")
    annotations = root.get("annotations")
    category_id = root.get("category_id")
    if not isinstance(info, dict):
        issues.error(path, "info", "must be an object")
        info = {}
    if not isinstance(annotations, list):
        issues.error(path, "annotations", "must be a list")
        annotations = []
    if not is_integer(category_id):
        issues.error(path, "category_id", "must be an integer; use -1 for intentionally missing labels")
        category_id = None
    elif category_id < -1:
        issues.error(path, "category_id", "must be -1 or a non-negative class index")

    for key in INFO_KEYS:
        if key not in info:
            issues.error(path, "info", "required key '{}' is missing".format(key))

    resolution = info.get("resolution")
    if not isinstance(resolution, list) or len(resolution) != 2:
        issues.error(path, "info.resolution", "must be [width, height]")
        resolution = None
    elif any(not is_finite_number(value) or float(value) <= 0 for value in resolution):
        issues.error(path, "info.resolution", "width and height must be finite positive numbers")

    num_frame = info.get("num_frame")
    if not is_integer(num_frame) or num_frame <= 0:
        issues.error(path, "info.num_frame", "must be a positive integer")
        num_frame = None

    num_keypoints = info.get("num_keypoints")
    if not is_integer(num_keypoints) or num_keypoints <= 0:
        issues.error(path, "info.num_keypoints", "must be a positive integer; -1 is not loadable")
        num_keypoints = None

    channels = info.get("keypoint_channels")
    if not isinstance(channels, list) or not channels:
        issues.error(path, "info.keypoint_channels", "must be a non-empty list of channel names")
        channels = None
    else:
        if any(not isinstance(channel, str) or not channel for channel in channels):
            issues.error(path, "info.keypoint_channels", "every channel name must be a non-empty string")
        hashable_channels = [channel for channel in channels if isinstance(channel, str)]
        if len(set(hashable_channels)) != len(hashable_channels):
            issues.error(path, "info.keypoint_channels", "channel names must be unique")
        unsupported = [channel for channel in hashable_channels if channel not in SUPPORTED_CHANNELS]
        if unsupported:
            issues.error(path, "info.keypoint_channels", "unsupported channel name(s) {}; use x, y, score, or visibility".format(", ".join(repr(item) for item in unsupported)))
        if "x" not in channels or "y" not in channels:
            issues.error(path, "info.keypoint_channels", "x and y channels are required for the documented 2-D skeleton contract")

    if isinstance(info.get("version"), bool) or ("version" in info and not isinstance(info["version"], str)):
        issues.error(path, "info.version", "when present, must be a string")
    if "video_name" in info and not isinstance(info["video_name"], str):
        issues.error(path, "info.video_name", "when present, must be a string")

    seen = set()
    for index, annotation in enumerate(annotations):
        location = "annotations[{}]".format(index)
        if not isinstance(annotation, dict):
            issues.error(path, location, "must be an object")
            continue
        for key in ANNOTATION_KEYS:
            if key not in annotation:
                issues.error(path, location, "required key '{}' is missing".format(key))
        frame_index = annotation.get("frame_index")
        identifier = annotation.get("id")
        person_id = annotation.get("person_id")
        if not is_integer(frame_index):
            issues.error(path, location + ".frame_index", "must be a non-negative integer")
        elif frame_index < 0 or (num_frame is not None and frame_index >= num_frame):
            issues.error(path, location + ".frame_index", "{} is outside valid frame range [0, {})".format(frame_index, num_frame or 0))
        if not is_integer(identifier) or identifier < 0:
            issues.error(path, location + ".id", "must be a non-negative integer")
        if person_id is not None and (not is_integer(person_id) or person_id < 0):
            issues.error(path, location + ".person_id", "must be null or a non-negative integer")
        effective_person = person_id if person_id is not None else identifier
        if is_integer(effective_person) and effective_person >= 0:
            if num_track is not None and effective_person >= num_track:
                issues.error(path, location + ".person_id", "effective person slot {} is outside configured range [0, {})".format(effective_person, num_track))
            if is_integer(frame_index) and frame_index >= 0:
                pair = (frame_index, effective_person)
                if pair in seen:
                    issues.error(path, location, "duplicate annotation for frame {} and effective person slot {}; loader would overwrite data".format(frame_index, effective_person))
                seen.add(pair)

        keypoints = annotation.get("keypoints")
        if not isinstance(keypoints, list):
            issues.error(path, location + ".keypoints", "must be a list of joint rows")
            continue
        if num_keypoints is not None and len(keypoints) != num_keypoints:
            issues.error(path, location + ".keypoints", "contains {} joints, expected {} from info.num_keypoints".format(len(keypoints), num_keypoints))
        expected_channels = len(channels) if channels is not None else None
        for joint_index, point in enumerate(keypoints):
            point_location = "{}.keypoints[{}]".format(location, joint_index)
            if not isinstance(point, list):
                issues.error(path, point_location, "must be a numeric list")
                continue
            if expected_channels is not None and len(point) != expected_channels:
                issues.error(path, point_location, "contains {} values, expected {} for keypoint_channels".format(len(point), expected_channels))
            for channel_index, value in enumerate(point):
                if not is_finite_number(value):
                    issues.error(path, "{}[{}]".format(point_location, channel_index), "must be a finite number")

    if category_data is not None and category_id is not None:
        matches = []
        mapping = category_data["annotations"]
        for key in category_keys(path, info):
            if key in mapping:
                matches.append((key, mapping[key]["category_id"]))
        if matches:
            expected = matches[0][1]
            if any(item[1] != expected for item in matches[1:]):
                issues.error(path, "category_id", "category mapping keys resolve to conflicting IDs: {}".format(matches))
            if category_id != expected:
                issues.error(path, "category_id", "sample label {} disagrees with category mapping label {} for {}".format(category_id, expected, matches[0][0]))
        elif category_id != -1:
            issues.error(path, "category_id", "no category mapping entry matched; missing category must be -1 when a mapping file is supplied")

    return True


def collect_inputs(input_path, issues):
    if os.path.isfile(input_path):
        return [input_path]
    if os.path.isdir(input_path):
        files = [os.path.join(input_path, name) for name in sorted(os.listdir(input_path)) if name.lower().endswith(".json")]
        if not files:
            issues.error(input_path, "input", "directory contains no .json files")
        return files
    issues.error(input_path, "input", "is neither a readable JSON file nor a directory")
    return []


def build_parser():
    parser = argparse.ArgumentParser(
        description="Validate MMSkeleton skeleton JSON without modifying input files.")
    parser.add_argument("--input", required=True, metavar="FILE_OR_DIRECTORY", help="one skeleton JSON file or a directory of JSON files")
    parser.add_argument("--category-annotations", metavar="FILE", help="optional category mapping JSON to cross-check labels")
    parser.add_argument("--num-track", type=int, metavar="M", help="optional exclusive upper bound for effective person slots")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    issues = IssueCollector()
    if args.num_track is not None and args.num_track <= 0:
        issues.error("<arguments>", "--num-track", "must be a positive integer")
    category_data = None
    if args.category_annotations:
        category_data = validate_category_file(args.category_annotations, issues)
    files = collect_inputs(args.input, issues)
    if args.category_annotations and os.path.isdir(args.input):
        category_real = os.path.realpath(args.category_annotations)
        files = [path for path in files if os.path.realpath(path) != category_real]
    checked = 0
    for path in files:
        if validate_sample(path, category_data, args.num_track, issues):
            checked += 1
    for line in issues.warnings + issues.errors:
        print(line, file=sys.stderr if line.startswith("ERROR") else sys.stdout)
    if issues.errors:
        print("Validation failed: {} file(s) checked, {} error(s).".format(checked, len(issues.errors)), file=sys.stderr)
        return 1
    print("Validation passed: {} file(s) checked.".format(checked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
