#!/usr/bin/env python3
"""Inspect and validate a TransFuser leaderboard result JSON, without CARLA."""

from __future__ import print_function

import argparse
import json
import math
from pathlib import Path
import sys

INFRACTION_KEYS = (
    "collisions_pedestrian", "collisions_vehicle", "collisions_layout",
    "red_light", "stop_infraction", "outside_route_lanes", "route_dev",
    "route_timeout", "vehicle_blocked",
)
SCORE_KEYS = ("score_route", "score_penalty", "score_composed")
REQUIRED_RECORD_KEYS = ("route_id", "index", "status", "infractions", "scores", "meta")


def number(value, label, errors):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        errors.append("{} must be a finite number".format(label))
        return None
    return float(value)


def validate(data, strict=False):
    errors, warnings = [], []
    if not isinstance(data, dict):
        return ["top-level JSON must be an object"], [], {}
    checkpoint = data.get("_checkpoint")
    if not isinstance(checkpoint, dict):
        return ["missing _checkpoint object"], [], {}
    progress = checkpoint.get("progress")
    if not (isinstance(progress, list) and len(progress) == 2 and all(isinstance(x, int) and not isinstance(x, bool) for x in progress)):
        errors.append("_checkpoint.progress must be [completed_or_next_index, total] integers")
        progress = [None, None]
    elif progress[0] < 0 or progress[1] < 0 or progress[0] > progress[1]:
        errors.append("_checkpoint.progress must satisfy 0 <= progress[0] <= progress[1]")

    records = checkpoint.get("records")
    if not isinstance(records, list):
        errors.append("_checkpoint.records must be an array")
        records = []
    for i, record in enumerate(records):
        label = "record[{}]".format(i)
        if not isinstance(record, dict):
            errors.append("{} must be an object".format(label))
            continue
        for key in REQUIRED_RECORD_KEYS:
            if key not in record:
                errors.append("{} missing {}".format(label, key))
        scores = record.get("scores", {})
        if not isinstance(scores, dict):
            errors.append("{}.scores must be an object".format(label))
        else:
            for key in SCORE_KEYS:
                if key not in scores:
                    errors.append("{}.scores missing {}".format(label, key))
                else:
                    number(scores[key], "{}.scores.{}".format(label, key), errors)
            if isinstance(scores.get("score_route"), (int, float)) and not isinstance(scores.get("score_route"), bool):
                if not 0 <= float(scores["score_route"]) <= 100:
                    errors.append("{}.scores.score_route must be in [0, 100]".format(label))
        infractions = record.get("infractions", {})
        if not isinstance(infractions, dict):
            errors.append("{}.infractions must be an object".format(label))
        else:
            for key in INFRACTION_KEYS:
                if key not in infractions:
                    errors.append("{}.infractions missing {}".format(label, key))
                elif not isinstance(infractions[key], list):
                    errors.append("{}.infractions.{} must be an array".format(label, key))
        meta = record.get("meta", {})
        if not isinstance(meta, dict):
            errors.append("{}.meta must be an object".format(label))
        else:
            for key in ("duration_system", "duration_game", "route_length"):
                if key not in meta:
                    errors.append("{}.meta missing {}".format(label, key))
                else:
                    number(meta[key], "{}.meta.{}".format(label, key), errors)
        status = record.get("status")
        if not isinstance(status, str):
            errors.append("{}.status must be a string".format(label))
        elif status != "Completed":
            warnings.append("{} has status {!r}".format(label, status))

    global_record = checkpoint.get("global_record")
    if not isinstance(global_record, dict):
        errors.append("_checkpoint.global_record must be an object")
    labels, values = data.get("labels"), data.get("values")
    if not isinstance(labels, list) or not isinstance(values, list):
        errors.append("labels and values must both be arrays")
    elif len(labels) != len(values):
        errors.append("labels and values must have equal lengths")

    if progress[0] is not None and progress[1] is not None:
        if progress[0] != len(records):
            warnings.append("progress[0]={} differs from record count {}".format(progress[0], len(records)))
        if strict and progress[0] != progress[1]:
            errors.append("strict mode requires completed progress to equal total")
    if strict:
        for i, record in enumerate(records):
            if isinstance(record, dict) and record.get("status") != "Completed":
                errors.append("strict mode rejects record[{}] status {!r}".format(i, record.get("status")))
        if progress[1] is not None and len(records) != progress[1]:
            errors.append("strict mode requires record count to equal total")

    report = {
        "progress": progress,
        "record_count": len(records),
        "statuses": {},
        "entry_status": data.get("entry_status"),
        "eligible": data.get("eligible"),
        "sensors": data.get("sensors", []),
        "labels": labels if isinstance(labels, list) else [],
        "values": values if isinstance(values, list) else [],
    }
    for record in records:
        if isinstance(record, dict):
            status = record.get("status")
            report["statuses"][status] = report["statuses"].get(status, 0) + 1
    return errors, warnings, report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate and summarize a result JSON; never run CARLA.")
    parser.add_argument("file", type=Path)
    parser.add_argument("--records", action="store_true", help="Print one compact line per route")
    parser.add_argument("--strict", action="store_true", help="Require all records completed and progress complete")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        with args.file.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        print("ERROR: cannot read JSON: {}".format(exc), file=sys.stderr)
        return 2
    errors, warnings, report = validate(data, strict=args.strict)
    report["errors"] = errors
    report["warnings"] = warnings
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("file: {}".format(args.file))
        print("progress: {}/{}".format(*report["progress"]))
        print("records: {}".format(report["record_count"]))
        print("entry_status: {}".format(report["entry_status"]))
        print("eligible: {}".format(report["eligible"]))
        print("statuses: {}".format(json.dumps(report["statuses"], sort_keys=True)))
        if args.records:
            for record in data.get("_checkpoint", {}).get("records", []):
                if isinstance(record, dict):
                    scores = record.get("scores", {})
                    try:
                        completion = float(scores.get("score_route", 0))
                        composed = float(scores.get("score_composed", 0))
                        score_text = "completion={:.3f}\tscore={:.3f}".format(completion, composed)
                    except (TypeError, ValueError):
                        score_text = "scores=invalid"
                    print("{}\t{}\t{}".format(record.get("route_id"), record.get("status"), score_text))
        for warning in warnings:
            print("WARNING: {}".format(warning), file=sys.stderr)
        for error in errors:
            print("ERROR: {}".format(error), file=sys.stderr)
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
