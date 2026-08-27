#!/usr/bin/env python3
"""Lightweight Viseron detection-config snippet checker.

The checker intentionally avoids importing Viseron, OpenCV, ML frameworks, or
service SDKs. It validates common YAML/JSON mistakes in detector snippets:
label confidence/range fields, mask/zone polygon coordinate counts, and
motion-overlap settings.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MOTION_COMPONENTS = {"background_subtractor", "mog2", "mqtt"}
OBJECT_DETECTOR_KEY = "object_detector"
MOTION_DETECTOR_KEY = "motion_detector"
POST_PROCESSOR_KEYS = {
    "face_recognition",
    "image_classification",
    "license_plate_recognition",
}
RANGE_0_1_KEYS = {
    "confidence",
    "min_confidence",
    "iou",
    "suppression",
    "height_min",
    "height_max",
    "width_min",
    "width_max",
    "motion_overlap_threshold",
    "area",
    "alpha",
    "learning_rate",
    "det_prob_threshold",
    "similarity_threshold",
}
BOOL_KEYS = {
    "trigger_event_recording",
    "trigger_recorder",
    "store",
    "require_motion",
    "require_motion_overlap",
    "scan_on_motion_only",
    "recorder_keepalive",
    "detect_shadows",
    "half_precision",
    "save_faces",
    "save_unknown_faces",
    "save_plates",
    "train",
}


@dataclass
class Issue:
    """One validation issue."""

    severity: str
    path: str
    message: str


def format_path(parts: list[str]) -> str:
    """Return a readable dotted path."""
    if not parts:
        return "<root>"
    rendered = []
    for part in parts:
        if part.startswith("["):
            rendered[-1] = rendered[-1] + part if rendered else part
        else:
            rendered.append(part)
    return ".".join(rendered)


def add(issues: list[Issue], severity: str, path: list[str], message: str) -> None:
    """Append an issue, suppressing duplicates from recursive checks."""
    issue = Issue(severity, format_path(path), message)
    if issue not in issues:
        issues.append(issue)


def is_number(value: Any) -> bool:
    """Return whether value is a real number but not a boolean."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def load_config(path: str | None) -> tuple[Any, str]:
    """Load YAML or JSON from a path or stdin."""
    if path in (None, "-"):
        text = sys.stdin.read()
        source = "<stdin>"
    else:
        source = path
        text = Path(path).read_text(encoding="utf-8")

    # JSON first for deterministic errors on JSON snippets.
    try:
        return json.loads(text), source
    except json.JSONDecodeError as json_error:
        json_exc = json_error

    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit(
            "Input is not valid JSON and PyYAML is not installed, so YAML cannot "
            f"be parsed. JSON error was: {json_exc}"
        ) from exc

    data = yaml.safe_load(text)
    return data, source


def collect_motion_cameras(config: Any) -> set[str]:
    """Collect cameras that appear to have a configured motion detector."""
    cameras: set[str] = set()
    if not isinstance(config, dict):
        return cameras

    for component, body in config.items():
        if component not in MOTION_COMPONENTS or not isinstance(body, dict):
            continue
        motion = body.get(MOTION_DETECTOR_KEY)
        if not isinstance(motion, dict):
            continue
        motion_cameras = motion.get("cameras")
        if isinstance(motion_cameras, dict):
            cameras.update(str(camera) for camera in motion_cameras)
    return cameras


def validate_range_value(
    key: str, value: Any, path: list[str], issues: list[Issue]
) -> None:
    """Validate common 0..1 numeric settings."""
    if key not in RANGE_0_1_KEYS:
        return
    if value is None:
        return
    if not is_number(value):
        add(issues, "error", path, f"{key!r} must be numeric")
        return
    if not 0 <= float(value) <= 1:
        add(issues, "error", path, f"{key!r} must be between 0 and 1")


def validate_bool_value(
    key: str, value: Any, path: list[str], issues: list[Issue]
) -> None:
    """Validate common boolean settings."""
    if key in BOOL_KEYS and not isinstance(value, bool):
        add(issues, "error", path, f"{key!r} must be true or false")


def validate_min_max(label: dict[str, Any], path: list[str], issues: list[Issue]) -> None:
    """Validate relative width/height min/max filters."""
    for axis in ("width", "height"):
        min_key = f"{axis}_min"
        max_key = f"{axis}_max"
        if min_key not in label or max_key not in label:
            continue
        min_value = label[min_key]
        max_value = label[max_key]
        if is_number(min_value) and is_number(max_value) and min_value >= max_value:
            add(
                issues,
                "error",
                path + [min_key],
                f"{min_key} must be smaller than {max_key}",
            )


def validate_label(
    label: Any,
    path: list[str],
    issues: list[Issue],
    *,
    camera: str | None,
    motion_cameras: set[str],
) -> None:
    """Validate an object-detector label mapping or post-processor label string."""
    if isinstance(label, str):
        if not label:
            add(issues, "error", path, "label string must not be empty")
        return

    if not isinstance(label, dict):
        add(issues, "error", path, "label entries must be strings or mappings")
        return

    if "label" in label and (not isinstance(label["label"], str) or not label["label"]):
        add(issues, "error", path + ["label"], "object label must be a non-empty string")

    for key, value in label.items():
        validate_range_value(key, value, path + [key], issues)
        validate_bool_value(key, value, path + [key], issues)

    validate_min_max(label, path, issues)

    if "trigger_recorder" in label:
        add(
            issues,
            "warning",
            path + ["trigger_recorder"],
            "deprecated; use trigger_event_recording instead",
        )

    if label.get("motion_overlap_threshold") is not None and not label.get(
        "require_motion_overlap", False
    ):
        add(
            issues,
            "warning",
            path + ["motion_overlap_threshold"],
            "has no effect unless require_motion_overlap is true",
        )

    if label.get("require_motion_overlap") or label.get("require_motion"):
        if camera is None:
            add(
                issues,
                "warning",
                path,
                "motion requirement present but camera context is unknown in this snippet",
            )
        elif camera not in motion_cameras:
            add(
                issues,
                "warning",
                path,
                "motion requirement is configured but no same-camera motion detector was found in the snippet",
            )


def validate_labels(
    labels: Any,
    path: list[str],
    issues: list[Issue],
    *,
    camera: str | None,
    motion_cameras: set[str],
) -> None:
    """Validate a labels list."""
    if labels is None:
        return
    if not isinstance(labels, list):
        add(issues, "error", path, "labels must be a list")
        return
    for index, label in enumerate(labels):
        validate_label(
            label,
            path + [f"[{index}]"],
            issues,
            camera=camera,
            motion_cameras=motion_cameras,
        )


def validate_coordinates(coords: Any, path: list[str], issues: list[Issue]) -> None:
    """Validate a polygon coordinates list."""
    if not isinstance(coords, list):
        add(issues, "error", path, "coordinates must be a list of points")
        return
    if len(coords) < 3:
        add(issues, "error", path, "polygon must contain at least three points")
    for index, point in enumerate(coords):
        point_path = path + [f"[{index}]"]
        if not isinstance(point, dict):
            add(issues, "error", point_path, "point must be a mapping with x and y")
            continue
        for axis in ("x", "y"):
            if axis not in point:
                add(issues, "error", point_path + [axis], f"missing {axis!r}")
            elif not is_number(point[axis]):
                add(issues, "error", point_path + [axis], f"{axis!r} must be numeric")


def validate_polygon_list(polygons: Any, path: list[str], issues: list[Issue]) -> None:
    """Validate mask entries."""
    if polygons is None:
        return
    if not isinstance(polygons, list):
        add(issues, "error", path, "mask must be a list")
        return
    for index, polygon in enumerate(polygons):
        poly_path = path + [f"[{index}]"]
        if not isinstance(polygon, dict):
            add(issues, "error", poly_path, "mask entry must be a mapping")
            continue
        if "coordinates" not in polygon:
            add(issues, "error", poly_path, "mask entry missing coordinates")
            continue
        validate_coordinates(polygon["coordinates"], poly_path + ["coordinates"], issues)


def validate_camera_config(
    camera_config: Any,
    path: list[str],
    issues: list[Issue],
    *,
    camera: str,
    motion_cameras: set[str],
) -> None:
    """Validate detector/post-processor per-camera options."""
    if camera_config is None:
        return
    if not isinstance(camera_config, dict):
        add(issues, "error", path, "camera config must be a mapping or null")
        return

    if camera_config.get("scan_on_motion_only") is True and camera not in motion_cameras:
        add(
            issues,
            "warning",
            path + ["scan_on_motion_only"],
            "true but no same-camera motion detector was found in the snippet",
        )

    if "labels" in camera_config:
        validate_labels(
            camera_config["labels"],
            path + ["labels"],
            issues,
            camera=camera,
            motion_cameras=motion_cameras,
        )
    if "mask" in camera_config:
        validate_polygon_list(camera_config["mask"], path + ["mask"], issues)
    if "zones" in camera_config:
        validate_zones(
            camera_config["zones"],
            path + ["zones"],
            issues,
            camera=camera,
            motion_cameras=motion_cameras,
        )

    for key, value in camera_config.items():
        validate_range_value(key, value, path + [key], issues)
        validate_bool_value(key, value, path + [key], issues)


def validate_zones(
    zones: Any,
    path: list[str],
    issues: list[Issue],
    *,
    camera: str,
    motion_cameras: set[str],
) -> None:
    """Validate object-detector zones."""
    if zones is None:
        return
    if not isinstance(zones, list):
        add(issues, "error", path, "zones must be a list")
        return

    seen_names: set[str] = set()
    for index, zone in enumerate(zones):
        zone_path = path + [f"[{index}]"]
        if not isinstance(zone, dict):
            add(issues, "error", zone_path, "zone must be a mapping")
            continue
        name = zone.get("name")
        if not isinstance(name, str) or not name:
            add(issues, "error", zone_path + ["name"], "zone name must be a non-empty string")
        elif name in seen_names:
            add(issues, "error", zone_path + ["name"], "zone name must be unique per camera")
        else:
            seen_names.add(name)
        if "coordinates" not in zone:
            add(issues, "error", zone_path, "zone missing coordinates")
        else:
            validate_coordinates(zone["coordinates"], zone_path + ["coordinates"], issues)
        if "labels" not in zone:
            add(issues, "warning", zone_path, "zone has no labels; it will not detect objects")
        else:
            validate_labels(
                zone["labels"],
                zone_path + ["labels"],
                issues,
                camera=camera,
                motion_cameras=motion_cameras,
            )


def validate_domain_cameras(
    domain_config: Any,
    path: list[str],
    issues: list[Issue],
    *,
    motion_cameras: set[str],
) -> None:
    """Validate a domain config containing cameras."""
    if not isinstance(domain_config, dict):
        add(issues, "error", path, "domain config must be a mapping")
        return

    for key, value in domain_config.items():
        validate_range_value(key, value, path + [key], issues)
        validate_bool_value(key, value, path + [key], issues)

    if "labels" in domain_config:
        validate_labels(
            domain_config["labels"],
            path + ["labels"],
            issues,
            camera=None,
            motion_cameras=motion_cameras,
        )

    cameras = domain_config.get("cameras")
    if cameras is None:
        return
    if not isinstance(cameras, dict):
        add(issues, "error", path + ["cameras"], "cameras must be a mapping")
        return
    for camera, camera_config in cameras.items():
        validate_camera_config(
            camera_config,
            path + ["cameras", str(camera)],
            issues,
            camera=str(camera),
            motion_cameras=motion_cameras,
        )


def walk(node: Any, path: list[str], issues: list[Issue], motion_cameras: set[str]) -> None:
    """Recursively find detector domains and validate common scalar settings."""
    if isinstance(node, dict):
        # Domain-level validation when a mapping directly contains cameras.
        key = path[-1] if path else ""
        if key in {OBJECT_DETECTOR_KEY, MOTION_DETECTOR_KEY, *POST_PROCESSOR_KEYS}:
            validate_domain_cameras(node, path, issues, motion_cameras=motion_cameras)

        for child_key, child_value in node.items():
            child_path = path + [str(child_key)]
            validate_range_value(str(child_key), child_value, child_path, issues)
            validate_bool_value(str(child_key), child_value, child_path, issues)
            walk(child_value, child_path, issues, motion_cameras)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            walk(item, path + [f"[{index}]"], issues, motion_cameras)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate common Viseron detection YAML/JSON snippet mistakes without "
            "importing Viseron or heavy ML packages."
        )
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="-",
        help="YAML/JSON snippet path, or '-' / omitted for stdin.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human-readable text.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the checker."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    config, source = load_config(args.path)
    issues: list[Issue] = []

    if config is None:
        add(issues, "error", [], "configuration is empty")
    elif not isinstance(config, dict):
        add(issues, "error", [], "top-level snippet should be a mapping")
    else:
        motion_cameras = collect_motion_cameras(config)
        walk(config, [], issues, motion_cameras)

    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]
    failed = bool(errors or (args.strict and warnings))

    if args.json:
        print(
            json.dumps(
                {
                    "source": source,
                    "ok": not failed,
                    "errors": [issue.__dict__ for issue in errors],
                    "warnings": [issue.__dict__ for issue in warnings],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        if not issues:
            print(f"OK: {source}: no detection snippet issues found")
        else:
            for issue in issues:
                print(f"{issue.severity.upper()}: {issue.path}: {issue.message}")
            if failed:
                print(f"FAILED: {source}: {len(errors)} error(s), {len(warnings)} warning(s)")
            else:
                print(f"OK: {source}: {len(warnings)} warning(s), no errors")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
