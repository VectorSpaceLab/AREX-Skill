#!/usr/bin/env python3
"""Smoke-write ordinary tensorboardX logging and count event records."""

from __future__ import annotations

import argparse
from pathlib import Path
import struct
import tempfile



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write a small tensorboardX scalar log and report event-file counts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--logdir",
        default=None,
        help="Directory that will receive the event files; a new temp directory is created when omitted.",
    )
    parser.add_argument(
        "--export-json",
        dest="export_json",
        default=None,
        help="Optional path for SummaryWriter.export_scalars_to_json().",
    )
    return parser


def make_logdir(logdir: str | None) -> Path:
    if logdir:
        path = Path(logdir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    return Path(tempfile.mkdtemp(prefix="tensorboardx-logging-"))


def count_tfrecord_records(event_file: Path) -> int:
    total = 0
    with event_file.open("rb") as handle:
        while True:
            header = handle.read(8)
            if not header:
                break
            if len(header) != 8:
                break
            (length,) = struct.unpack("Q", header)
            length_crc = handle.read(4)
            payload = handle.read(length)
            payload_crc = handle.read(4)
            if len(length_crc) != 4 or len(payload) != length or len(payload_crc) != 4:
                break
            total += 1
    return total


def count_event_records(logdir: Path):
    event_files = sorted(logdir.rglob("events.out.tfevents.*"))
    record_count = sum(count_tfrecord_records(event_file) for event_file in event_files)
    return event_files, record_count


def main() -> int:
    args = build_parser().parse_args()
    logdir = make_logdir(args.logdir)

    export_json = Path(args.export_json) if args.export_json else None
    if export_json is not None:
        export_json.parent.mkdir(parents=True, exist_ok=True)

    from tensorboardX import SummaryWriter

    with SummaryWriter(logdir=str(logdir)) as writer:
        with writer.use_metadata(global_step=7):
            writer.add_scalar("smoke/default_step", 1.0)

        writer.add_scalar("smoke/loss", 0.25, global_step=1)
        writer.add_scalar("smoke/accuracy", 0.9, global_step=1)
        writer.add_scalars("smoke/group", {"train": 0.24, "val": 0.31}, global_step=1)
        writer.add_custom_scalars(
            {
                "smoke": {
                    "loss_vs_accuracy": ["Multiline", ["smoke/loss", "smoke/accuracy"]],
                }
            }
        )
        writer.add_text("smoke/note", "tensorboardX logging-core smoke", global_step=1)

        if export_json is not None:
            writer.export_scalars_to_json(str(export_json))

    event_files, record_count = count_event_records(logdir)
    print(f"logdir={logdir}")
    print(f"event_files={len(event_files)}")
    print(f"event_records={record_count}")
    if export_json is not None:
        print(f"json_export={export_json}")

    return 0 if event_files else 1


if __name__ == "__main__":
    raise SystemExit(main())
