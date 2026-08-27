#!/usr/bin/env python3
"""Statically validate a TransFuser HybridAgent TEAM_CONFIG directory.

This tool uses only the Python standard library. It does not import CARLA or
PyTorch, allocate CUDA memory, deserialize checkpoint pickles, run inference,
launch a server, modify files, or download anything.
"""

from __future__ import print_function

import argparse
import json
import os
import sys
from pathlib import Path


BACKBONES = (
    "transFuser",
    "late_fusion",
    "geometric_fusion",
    "latentTF",
)
CORE_SENSOR_IDS = (
    "rgb_front",
    "rgb_left",
    "rgb_right",
    "imu",
    "gps",
    "speed",
)
BOOLISH_FIELDS = (
    "sync_batch_norm",
    "use_point_pillars",
    "use_target_point_image",
    "use_velocity",
)
STRING_FIELDS = (
    "image_architecture",
    "lidar_architecture",
)
RUNTIME_DEFAULTS = {
    "backbone": "transFuser",
    "image_architecture": "resnet34",
    "lidar_architecture": "resnet18",
    "use_velocity": True,
    "sync_batch_norm": False,
    "use_point_pillars": False,
    "n_layer": 8,
    "use_target_point_image": False,
}
TRAINING_DEFAULTS_THAT_DIFFER = {
    "image_architecture": "regnety_032",
    "lidar_architecture": "regnety_032",
    "use_velocity": 0,
    "n_layer": 4,
    "use_target_point_image": 1,
}


def _is_boolish(value):
    return isinstance(value, bool) or (type(value) is int and value in (0, 1))


def _as_bool(value):
    if _is_boolish(value):
        return bool(value)
    return None


def _checkpoint_container(path):
    """Identify a container signature without deserializing checkpoint data."""
    try:
        with path.open("rb") as stream:
            header = stream.read(8)
    except OSError as exc:
        return "unreadable: {}".format(exc)

    if header.startswith(b"PK\x03\x04"):
        return "zip-based torch archive"
    if header.startswith(b"\x80"):
        return "pickle/legacy torch archive"
    if not header:
        return "empty"
    return "unknown"


def validate(team_config):
    errors = []
    warnings = []
    notes = []
    checkpoint_records = []
    parsed_args = None

    path = Path(team_config).expanduser()
    display_path = str(path)

    if not path.exists():
        errors.append("TEAM_CONFIG does not exist: {}".format(display_path))
        return _result(path, parsed_args, checkpoint_records, errors, warnings, notes)
    if not path.is_dir():
        errors.append(
            "TEAM_CONFIG must be a directory containing args.txt and .pth files, not: {}".format(
                display_path
            )
        )
        return _result(path, parsed_args, checkpoint_records, errors, warnings, notes)

    args_path = path / "args.txt"
    if not args_path.exists():
        errors.append("missing required JSON file: args.txt")
    elif not args_path.is_file():
        errors.append("args.txt exists but is not a regular file")
    else:
        if args_path.is_symlink():
            warnings.append("args.txt is a symbolic link; verify its provenance")
        try:
            with args_path.open("r", encoding="utf-8") as stream:
                parsed_args = json.load(stream)
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append("cannot parse args.txt as UTF-8 JSON: {}".format(exc))
        else:
            if not isinstance(parsed_args, dict):
                errors.append("args.txt top level must be a JSON object")
                parsed_args = None

    if parsed_args is not None:
        _validate_args(parsed_args, errors, warnings, notes)

    try:
        entries = sorted(path.iterdir(), key=lambda item: item.name)
    except OSError as exc:
        errors.append("cannot list TEAM_CONFIG: {}".format(exc))
        entries = []

    for candidate in entries:
        if not candidate.name.endswith(".pth"):
            continue
        if not candidate.is_file():
            errors.append("checkpoint candidate is not a regular file: {}".format(candidate.name))
            continue
        try:
            size = candidate.stat().st_size
        except OSError as exc:
            errors.append("cannot stat checkpoint {}: {}".format(candidate.name, exc))
            continue

        container = _checkpoint_container(candidate)
        record = {
            "name": candidate.name,
            "size_bytes": size,
            "container": container,
            "symlink": candidate.is_symlink(),
        }
        checkpoint_records.append(record)

        if size <= 0:
            errors.append("checkpoint is empty: {}".format(candidate.name))
        if container.startswith("unreadable"):
            errors.append("checkpoint {} is {}".format(candidate.name, container))
        elif container == "empty":
            # Already covered by the size check; keep one actionable error.
            pass
        elif container == "unknown":
            warnings.append(
                "checkpoint {} has an unknown static container signature".format(
                    candidate.name
                )
            )
        if candidate.is_symlink():
            warnings.append(
                "checkpoint {} is a symbolic link; verify its target and provenance".format(
                    candidate.name
                )
            )
        if candidate.name.lower().startswith("optimizer"):
            errors.append(
                "{} looks like an optimizer checkpoint; the agent loads every .pth file as a model".format(
                    candidate.name
                )
            )

    if not checkpoint_records:
        errors.append("no regular .pth checkpoint files found")
    elif len(checkpoint_records) > 1:
        notes.append(
            "{} .pth files form an ensemble and are all placed on one CUDA device".format(
                len(checkpoint_records)
            )
        )

    notes.append(
        "checkpoint contents were not deserialized; state-dict keys and tensor shapes remain unverified"
    )
    notes.append(
        "CARLA 0.9.10.1 Python API/server and CUDA inference remain external runtime checks"
    )

    return _result(path, parsed_args, checkpoint_records, errors, warnings, notes)


def _validate_args(parsed_args, errors, warnings, notes):
    for field in BOOLISH_FIELDS:
        if field in parsed_args and not _is_boolish(parsed_args[field]):
            errors.append("{} must be a JSON boolean or integer 0/1".format(field))

    for field in STRING_FIELDS:
        if field in parsed_args:
            value = parsed_args[field]
            if not isinstance(value, str) or not value.strip():
                errors.append("{} must be a non-empty string".format(field))

    if "n_layer" in parsed_args:
        value = parsed_args["n_layer"]
        if type(value) is not int or value <= 0:
            errors.append("n_layer must be a positive integer")

    raw_backbone = parsed_args.get("backbone", RUNTIME_DEFAULTS["backbone"])
    if not isinstance(raw_backbone, str):
        errors.append("backbone must be a string")
        backbone = RUNTIME_DEFAULTS["backbone"]
    else:
        backbone = raw_backbone
        if backbone not in BACKBONES:
            errors.append(
                "unsupported backbone {!r}; expected one of {}".format(
                    backbone, ", ".join(BACKBONES)
                )
            )

    for field in RUNTIME_DEFAULTS:
        if field not in parsed_args:
            default = RUNTIME_DEFAULTS[field]
            if field in TRAINING_DEFAULTS_THAT_DIFFER:
                warnings.append(
                    "{} is absent: runtime fallback {!r} differs from observed training default {!r}".format(
                        field, default, TRAINING_DEFAULTS_THAT_DIFFER[field]
                    )
                )
            else:
                warnings.append(
                    "{} is absent: runtime fallback is {!r}; restore original training metadata when possible".format(
                        field, default
                    )
                )

    velocity = _as_bool(parsed_args.get("use_velocity", RUNTIME_DEFAULTS["use_velocity"]))
    point_pillars = _as_bool(
        parsed_args.get("use_point_pillars", RUNTIME_DEFAULTS["use_point_pillars"])
    )

    if backbone != "transFuser" and velocity is True:
        warnings.append(
            "use_velocity is enabled for {}; training help documents it for transFuser".format(
                backbone
            )
        )
    if backbone == "latentTF" and point_pillars is True:
        warnings.append(
            "latentTF omits physical LiDAR but use_point_pillars is enabled; reconcile this with checkpoint provenance"
        )

    if backbone == "latentTF":
        notes.append("latentTF expects no physical lidar sensor and uses a dummy zero BEV tensor")
    else:
        notes.append("{} requires the lowercase lidar sensor payload".format(backbone))


def _result(path, parsed_args, checkpoints, errors, warnings, notes):
    backbone = None
    if isinstance(parsed_args, dict):
        candidate = parsed_args.get("backbone", RUNTIME_DEFAULTS["backbone"])
        if isinstance(candidate, str):
            backbone = candidate

    expected_sensor_ids = list(CORE_SENSOR_IDS)
    if backbone != "latentTF":
        expected_sensor_ids.append("lidar")

    return {
        "valid": not errors,
        "team_config": str(path),
        "backbone": backbone,
        "expected_sensor_ids": expected_sensor_ids,
        "optional_sensor": "rgb_back when SAVE_PATH is non-empty before agent import",
        "checkpoint_count": len(checkpoints),
        "checkpoints": checkpoints,
        "errors": errors,
        "warnings": warnings,
        "notes": notes,
        "safety": {
            "carla_imported": False,
            "torch_imported": False,
            "checkpoint_deserialized": False,
            "cuda_allocated": False,
            "inference_run": False,
            "files_modified": False,
        },
    }


def _print_human(result):
    status = "OK" if result["valid"] else "FAILED"
    print("TransFuser agent config: {}".format(status))
    print("TEAM_CONFIG: {}".format(result["team_config"]))
    print("Backbone: {}".format(result["backbone"] or "unknown"))
    print("Checkpoints: {}".format(result["checkpoint_count"]))
    print("Expected sensors: {}".format(", ".join(result["expected_sensor_ids"])))

    for record in result["checkpoints"]:
        print(
            "  checkpoint: {name} ({size_bytes} bytes; {container})".format(
                **record
            )
        )
    for message in result["errors"]:
        print("ERROR: {}".format(message))
    for message in result["warnings"]:
        print("WARNING: {}".format(message))
    for message in result["notes"]:
        print("NOTE: {}".format(message))


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Statically validate a TransFuser HybridAgent TEAM_CONFIG directory "
            "without importing CARLA/PyTorch or deserializing checkpoints."
        )
    )
    parser.add_argument(
        "team_config",
        help="directory containing args.txt and one or more model .pth files",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="emit one JSON result object",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return a failure exit status when warnings are present",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    options = parser.parse_args(argv)
    result = validate(options.team_config)

    if options.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_human(result)

    if not result["valid"]:
        return 1
    if options.strict and result["warnings"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
