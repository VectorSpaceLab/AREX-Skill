#!/usr/bin/env python3
"""Smoke-write tiny tensorboardX hparams trials and count event records."""

from __future__ import annotations

import argparse
from pathlib import Path
import struct
import tempfile

TRIALS = [
    (
        "trial-1",
        {"lr": 0.1, "batch_size": 8, "bn": True},
        {"accuracy": 0.82, "loss": 0.44},
    ),
    (
        "trial-2",
        {"lr": 0.01, "batch_size": 16, "bn": False},
        {"accuracy": 0.88, "loss": 0.35},
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write a small tensorboardX hparams log and report event-file counts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--logdir",
        default=None,
        help="Directory that will receive the hparams trial folders; a new temp directory is created when omitted.",
    )
    return parser


def make_logdir(logdir: str | None) -> Path:
    if logdir:
        path = Path(logdir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    return Path(tempfile.mkdtemp(prefix="tensorboardx-hparams-"))


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

    from tensorboardX import SummaryWriter

    with SummaryWriter(logdir=str(logdir)) as writer:
        for index, (trial_name, hparams, metrics) in enumerate(TRIALS, start=1):
            writer.add_hparams(hparams, metrics, name=trial_name, global_step=index)

    event_files, record_count = count_event_records(logdir)
    print(f"logdir={logdir}")
    print(f"event_files={len(event_files)}")
    print(f"event_records={record_count}")

    return 0 if event_files else 1


if __name__ == "__main__":
    raise SystemExit(main())
