#!/usr/bin/env python3
"""Inspect TensorBoard event files and print scalar summary values.

The helper is intentionally tiny: it accepts a file, directory, or glob pattern,
then prints matching scalar tags one row at a time.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import sys
from pathlib import Path


def _expand_event_inputs(raw_path):
    raw_path = str(raw_path)
    if any(ch in raw_path for ch in "*?[]"):
        return sorted(glob.glob(raw_path))

    path = Path(raw_path)
    if path.is_dir():
        return sorted(
            str(child) for child in path.iterdir()
            if child.name.startswith("events.out.tfevents"))

    return [raw_path]


def _get_summary_iterator(tf_module):
    compat_v1 = getattr(tf_module, "compat", None)
    if compat_v1 is not None:
        compat_v1 = getattr(compat_v1, "v1", None)
        if compat_v1 is not None:
            train = getattr(compat_v1, "train", None)
            if train is not None and hasattr(train, "summary_iterator"):
                return train.summary_iterator

    train = getattr(tf_module, "train", None)
    if train is not None and hasattr(train, "summary_iterator"):
        return train.summary_iterator

    raise RuntimeError("TensorFlow summary_iterator is unavailable in this environment.")


def _format_time(wall_time):
    try:
        return dt.datetime.utcfromtimestamp(float(wall_time)).isoformat() + "Z"
    except Exception:  # pragma: no cover - best effort formatting
        return str(wall_time)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Read TensorBoard event files and print scalar summary values.")
    parser.add_argument(
        "--event-file",
        required=True,
        help="Event file path, event directory, or glob pattern.")
    parser.add_argument(
        "--tag",
        action="append",
        default=[],
        help=(
            "Scalar tag to keep. Repeat the option or separate tags with commas. "
            "If omitted, every scalar tag is printed."))
    parser.add_argument(
        "--limit-events",
        type=int,
        default=0,
        help="Stop after this many events have been read across all files.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    try:
        import tensorflow as tf  # pylint: disable=import-error
    except Exception as exc:  # pragma: no cover - environment-dependent
        print("TensorFlow is required to read event files: {}".format(exc),
              file=sys.stderr)
        return 2

    event_files = _expand_event_inputs(args.event_file)
    if not event_files:
        print("No event files matched: {}".format(args.event_file),
              file=sys.stderr)
        return 2

    requested_tags = set()
    for item in args.tag:
        for part in item.split(","):
            part = part.strip()
            if part:
                requested_tags.add(part)

    summary_iterator = _get_summary_iterator(tf)
    events_seen = 0
    values_seen = 0

    for event_file in event_files:
        for event in summary_iterator(event_file):
            events_seen += 1
            summary = getattr(event, "summary", None)
            values = getattr(summary, "value", []) if summary is not None else []

            for value in values:
                tag = getattr(value, "tag", None)
                if not tag:
                    continue
                if requested_tags and tag not in requested_tags:
                    continue
                simple_value = getattr(value, "simple_value", None)
                if simple_value is None:
                    continue
                values_seen += 1
                print(
                    "event_file={}\tstep={}\ttime={}\ttag={}\tvalue={}".
                    format(event_file, getattr(event, "step", 0),
                           _format_time(getattr(event, "wall_time", 0.0)), tag,
                           simple_value))

            if args.limit_events and events_seen >= args.limit_events:
                return 0

    if values_seen == 0:
        print("No matching scalar values found.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
