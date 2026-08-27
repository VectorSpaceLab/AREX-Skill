#!/usr/bin/env python3
"""Print a bounded, redacted view of an AlpaSim size-delimited protobuf log."""

from __future__ import annotations

import argparse
import asyncio

from alpasim_grpc.v0.logging_pb2 import LogEntry
from alpasim_utils.logs import async_read_pb_log


def _redact_payloads(entry: LogEntry) -> None:
    """Remove image and video-model bytes before an entry is printed."""
    kind = entry.WhichOneof("log_entry")
    if kind == "driver_camera_image":
        entry.driver_camera_image.camera_image.image_bytes = b"<image data redacted>"
    elif kind == "video_model_session_request":
        request = entry.video_model_session_request
        request.static_world_map.hdmap_parquets = b"<hdmap data redacted>"
        for image in request.initial_frames:
            image.data = b"<image data redacted>"
    elif kind == "video_model_chunk_return":
        response = entry.video_model_chunk_return
        for camera in response.camera_outputs:
            for image in camera.rgb_frames:
                image.data = b"<image data redacted>"
            for image in camera.hdmap_condition_frames:
                image.data = b"<image data redacted>"


async def print_asl(
    file_path: str,
    start: int,
    end: int | None,
    message_types: set[str],
    just_types: bool,
    strict: bool,
) -> int:
    if start < 0 or (end is not None and end < start):
        raise ValueError("require 0 <= start <= end")

    printed = 0
    async for index, entry in _indexed_entries(file_path, strict):
        if end is not None and index >= end:
            break
        if index < start:
            continue
        kind = entry.WhichOneof("log_entry")
        if kind not in message_types:
            continue
        if just_types:
            print(kind)
        else:
            _redact_payloads(entry)
            print(entry)
        printed += 1
    return printed


async def _indexed_entries(file_path: str, strict: bool):
    index = 0
    async for entry in async_read_pb_log(file_path, raise_on_malformed=strict):
        yield index, entry
        index += 1


def main() -> int:
    fields = tuple(field.name for field in LogEntry.DESCRIPTOR.fields)
    parser = argparse.ArgumentParser(
        description="Print a bounded, redacted view of an AlpaSim .asl log."
    )
    parser.add_argument("asl_file", help="Path to the .asl file")
    parser.add_argument(
        "--start", type=int, default=0, help="First message index (default: 0)"
    )
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="Exclusive message index; omit to read to EOF",
    )
    parser.add_argument(
        "--message-types",
        nargs="+",
        choices=fields,
        default=fields,
        metavar="MSG_TYPE",
        help="Oneof fields to print (default: all)",
    )
    parser.add_argument(
        "--just-types", action="store_true", help="Print only oneof field names"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Raise on a truncated size-delimited record instead of stopping",
    )
    args = parser.parse_args()
    printed = asyncio.run(
        print_asl(
            file_path=args.asl_file,
            start=args.start,
            end=args.end,
            message_types=set(args.message_types),
            just_types=args.just_types,
            strict=args.strict,
        )
    )
    if not args.just_types:
        print(f"# printed {printed} matching message(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
