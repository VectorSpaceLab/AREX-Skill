#!/usr/bin/env python3
"""Safely add offline observation/prediction trajectories to OpenCDA YAML dumps.

The input is a directory containing one or more frame-YAML sequences.  Each
sequence is grouped by its immediate parent directory and ordered by filename.
Results are written as YAML to a separate, explicitly named output tree unless
--in-place is supplied.  No network, CARLA server, or OpenCDA import is used.
"""

from __future__ import print_function

import argparse
import os
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by an environment error
    yaml = None


REQUIRED_VEHICLE_FIELDS = ("location", "center", "angle", "speed")


def _positive_horizon(value):
    """Parse a non-negative whole-second horizon for argparse."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError("horizon must be a non-negative integer")
    if parsed < 0:
        raise argparse.ArgumentTypeError("horizon must be a non-negative integer")
    return parsed


def _load_frame(path):
    """Load and validate the outer frame mapping with a safe YAML loader."""
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        raise ValueError("invalid YAML in {}: {}".format(path, exc))
    if not isinstance(value, dict):
        raise ValueError("{} must contain a YAML mapping".format(path))
    vehicles = value.get("vehicles")
    if not isinstance(vehicles, dict):
        raise ValueError("{} must contain a mapping at vehicles".format(path))
    return value


def _find_vehicle_key(vehicles, vehicle_id):
    """Find an integer/string YAML key without conflating unrelated ids."""
    candidates = [vehicle_id, str(vehicle_id)]
    try:
        candidates.append(int(vehicle_id))
    except (TypeError, ValueError):
        pass
    for candidate in candidates:
        if candidate in vehicles:
            return candidate
    return None


def _trajectory_tuple(vehicle_id, vehicle):
    """Convert one source record to OpenCDA's seven-value trajectory tuple."""
    if not isinstance(vehicle, dict):
        raise ValueError("vehicle {} is not a mapping".format(vehicle_id))
    missing = [key for key in REQUIRED_VEHICLE_FIELDS if key not in vehicle]
    if missing:
        raise ValueError(
            "vehicle {} is missing required field(s): {}".format(
                vehicle_id, ", ".join(missing)))

    location = vehicle["location"]
    center = vehicle["center"]
    angle = vehicle["angle"]
    if not isinstance(location, (list, tuple)) or len(location) < 3:
        raise ValueError("vehicle {} has an invalid location".format(vehicle_id))
    if not isinstance(center, (list, tuple)) or len(center) < 3:
        raise ValueError("vehicle {} has an invalid center".format(vehicle_id))
    if not isinstance(angle, (list, tuple)) or len(angle) < 3:
        raise ValueError("vehicle {} has an invalid angle".format(vehicle_id))

    return [
        location[0] + center[0],
        location[1] + center[1],
        location[2] + center[2],
        angle[0],
        angle[1],
        angle[2],
        vehicle["speed"],
    ]


def _extract_trajectory(vehicle_id, frames):
    """Extract a vehicle until its first missing frame, without padding."""
    trajectory = []
    for frame in frames:
        vehicles = frame.get("vehicles", {})
        key = _find_vehicle_key(vehicles, vehicle_id)
        if key is None:
            break
        trajectory.append(_trajectory_tuple(vehicle_id, vehicles[key]))
    return trajectory


def _future_frames(frames, index, seconds):
    """Return the following whole 10 Hz window, excluding the current frame."""
    start = index + 1
    stop = min(start + seconds * 10, len(frames))
    return frames[start:stop]


def _past_frames(frames, index, seconds):
    """Return the preceding whole 10 Hz window, excluding the current frame."""
    start = max(0, index - seconds * 10)
    return frames[start:index]


def _augment_frame(frames, index, past_seconds, future_seconds):
    """Return one augmented frame after validating its vehicle records."""
    current = frames[index]
    vehicles = current["vehicles"]
    for vehicle_id, vehicle in vehicles.items():
        # Validate the current record even when both horizons are zero.
        _trajectory_tuple(vehicle_id, vehicle)
        future = _future_frames(frames, index, future_seconds)
        past = _past_frames(frames, index, past_seconds)
        vehicle["predictions"] = _extract_trajectory(vehicle_id, future)
        vehicle["observations"] = _extract_trajectory(vehicle_id, past)
    return current


def _discover_groups(input_root):
    """Group YAML frames by parent directory in stable lexical order."""
    paths = sorted(set(input_root.rglob("*.yaml")) |
                   set(input_root.rglob("*.yml")))
    if not paths:
        raise ValueError("no .yaml or .yml frame files found under {}".format(
            input_root))
    groups = {}
    for path in paths:
        groups.setdefault(path.parent, []).append(path)
    return [(parent, sorted(group)) for parent, group in sorted(groups.items())]


def _resolve_roots(args, parser):
    input_root = Path(args.input_root).expanduser().resolve()
    if not input_root.is_dir():
        parser.error("--input-root is not a directory: {}".format(input_root))

    if args.in_place and args.output_root:
        parser.error("use --output-root or --in-place, not both")
    if not args.in_place and not args.output_root:
        parser.error("--output-root is required unless --in-place is explicit")

    output_root = input_root if args.in_place else \
        Path(args.output_root).expanduser().resolve()
    if output_root != input_root:
        if input_root in output_root.parents or output_root in input_root.parents:
            parser.error("input and output roots must not contain one another")
    return input_root, output_root


def _serialize(path, data):
    """Serialize through a same-directory temporary file and replace atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=".prediction-", suffix=".yaml", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            yaml.safe_dump(data, stream, default_flow_style=False,
                           sort_keys=False, allow_unicode=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, str(path))
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def generate_prediction_yaml(input_root, output_root, past_seconds=1,
                             future_seconds=8, overwrite=False, dry_run=False):
    """Augment all frame groups and write them to an explicit output root.

    ``output_root == input_root`` is allowed only when the caller has already
    explicitly selected --in-place at the CLI boundary.  This function itself
    does not infer or authorize source mutation.
    """
    groups = _discover_groups(input_root)
    prepared = []
    for parent, paths in groups:
        frames = [_load_frame(path) for path in paths]
        augmented = [
            _augment_frame(frames, index, past_seconds, future_seconds)
            for index in range(len(frames))
        ]
        for path, frame in zip(paths, augmented):
            prepared.append((path.relative_to(input_root), frame))

    targets = [output_root / relative for relative, _ in prepared]
    if not overwrite and output_root != input_root:
        existing = [str(path) for path in targets if path.exists()]
        if existing:
            raise FileExistsError(
                "output already contains {} file(s); use --overwrite or a new "
                "output root (first: {})".format(len(existing), existing[0]))

    if dry_run:
        return len(prepared)

    for target, (_, frame) in zip(targets, prepared):
        _serialize(target, frame)
    return len(prepared)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Add 10 Hz OpenCDA observations/predictions without network access.")
    parser.add_argument(
        "--input-root", required=True,
        help="root containing dumped frame YAML files")
    parser.add_argument(
        "--output-root",
        help="separate root for augmented YAML files (required unless --in-place)")
    parser.add_argument(
        "--in-place", action="store_true",
        help="explicitly allow replacing input YAML files")
    parser.add_argument(
        "--overwrite", action="store_true",
        help="allow replacing existing files in a separate output root")
    parser.add_argument(
        "--past-seconds", type=_positive_horizon, default=1,
        help="past 10 Hz window in seconds (default: 1)")
    parser.add_argument(
        "--future-seconds", type=_positive_horizon, default=8,
        help="future 10 Hz window in seconds (default: 8)")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="validate and count outputs without writing files")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if yaml is None:
        parser.error("PyYAML is required; install it in the offline environment")
    input_root, output_root = _resolve_roots(args, parser)
    try:
        count = generate_prediction_yaml(
            input_root=input_root,
            output_root=output_root,
            past_seconds=args.past_seconds,
            future_seconds=args.future_seconds,
            # --in-place is itself the explicit input-overwrite approval.
            overwrite=args.overwrite or args.in_place,
            dry_run=args.dry_run,
        )
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2

    action = "validated" if args.dry_run else "wrote"
    print("{} {} augmented YAML frame(s) under {}".format(
        action, count, output_root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
