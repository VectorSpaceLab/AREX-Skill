#!/usr/bin/env python3
"""Safely inspect a conventional BVH file without importing project code.

The optional round-trip writes a new text BVH from the parsed hierarchy and
motion rows. It is a structural test, not a pose-conversion implementation.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


_NUM = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
_ROOT_OR_JOINT = re.compile(r"^\s*(ROOT|JOINT)\s+(\S+)")
_FRAMES = re.compile(r"^\s*Frames\s*:\s*(\d+)\s*$", re.IGNORECASE)
_FRAME_TIME = re.compile(r"^\s*Frame\s+Time\s*:\s*(%s)\s*$" % _NUM, re.IGNORECASE)
_OFFSET = re.compile(r"^\s*OFFSET\s+(\S+)\s+(\S+)\s+(\S+)\s*$", re.IGNORECASE)
_CHANNELS = re.compile(r"^\s*CHANNELS\s+(\d+)\s*(.*)$", re.IGNORECASE)


class BVHInspectionError(Exception):
    """Raised for an unreadable BVH structure."""


class ParsedBVH:
    def __init__(self) -> None:
        self.joints: List[Dict[str, Any]] = []
        self.stack: List[Tuple[str, Optional[int]]] = []
        self.pending: Optional[Tuple[str, Optional[int]]] = None
        self.frames_declared: Optional[int] = None
        self.frame_time: Optional[float] = None
        self.motion_rows: List[List[float]] = []
        self.motion_started = False
        self.in_motion = False
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def current_joint(self) -> Optional[int]:
        for kind, index in reversed(self.stack):
            if kind == "joint":
                return index
        return None

    def parent_joint(self) -> int:
        parent = self.current_joint()
        return -1 if parent is None else parent

    def parse(self, path: Path) -> None:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            raise BVHInspectionError(f"cannot read {path}: {exc}") from exc
        except UnicodeDecodeError as exc:
            raise BVHInspectionError(f"{path} is not UTF-8 text: {exc}") from exc

        for line_number, raw in enumerate(text.splitlines(), start=1):
            line = raw.strip()
            if not line:
                continue
            upper = line.upper()
            if upper == "HIERARCHY":
                if self.joints:
                    self.errors.append(f"line {line_number}: duplicate HIERARCHY")
                continue
            if upper == "MOTION":
                self.in_motion = True
                continue
            if self.in_motion:
                self._motion_line(line, line_number)
            else:
                self._hierarchy_line(line, line_number)

        if self.stack:
            self.errors.append("hierarchy has unclosed blocks")
        if self.pending is not None:
            self.errors.append("hierarchy ends with an unclosed declaration")

    def _hierarchy_line(self, line: str, line_number: int) -> None:
        match = _ROOT_OR_JOINT.match(line)
        if match:
            kind, name = match.groups()
            if kind == "ROOT" and self.joints:
                self.errors.append(f"line {line_number}: more than one ROOT")
            if any(j["name"] == name for j in self.joints):
                self.errors.append(f"line {line_number}: duplicate joint name {name!r}")
            index = len(self.joints)
            self.joints.append({
                "kind": kind,
                "name": name,
                "parent": self.parent_joint(),
                "offset": None,
                "channels": [],
                "end_sites": [],
            })
            self.pending = ("joint", index)
            return

        if upper_line_starts(line, "END SITE"):
            parent = self.current_joint()
            if parent is None:
                self.errors.append(f"line {line_number}: End Site has no parent joint")
            self.pending = ("end", parent)
            return

        if line == "{":
            if self.pending is None:
                self.errors.append(f"line {line_number}: unexpected '{{'" )
            else:
                self.stack.append(self.pending)
                self.pending = None
            return

        if line == "}":
            if not self.stack:
                self.errors.append(f"line {line_number}: unexpected '}}'")
            else:
                self.stack.pop()
            return

        match = _OFFSET.match(line)
        if match:
            try:
                values = [float(value) for value in match.groups()]
            except ValueError:
                self.errors.append(f"line {line_number}: non-numeric OFFSET")
                return
            if not all(math.isfinite(value) for value in values):
                self.errors.append(f"line {line_number}: non-finite OFFSET")
            if not self.stack:
                self.errors.append(f"line {line_number}: OFFSET outside a block")
                return
            kind, index = self.stack[-1]
            if kind == "joint" and index is not None:
                if self.joints[index]["offset"] is not None:
                    self.errors.append(f"line {line_number}: duplicate OFFSET for {self.joints[index]['name']!r}")
                self.joints[index]["offset"] = values
            elif kind == "end" and index is not None:
                self.joints[index]["end_sites"].append(values)
            return

        match = _CHANNELS.match(line)
        if match:
            count = int(match.group(1))
            names = match.group(2).split()
            joint = self.current_joint()
            if joint is None:
                self.errors.append(f"line {line_number}: CHANNELS outside a joint")
                return
            if len(names) != count:
                self.errors.append(
                    f"line {line_number}: CHANNELS declares {count} names but has {len(names)}"
                )
            self.joints[joint]["channels"] = names
            return

        if line.upper().startswith("HIERARCHY"):
            return
        self.warnings.append(f"line {line_number}: unrecognized hierarchy line {line!r}")

    def _motion_line(self, line: str, line_number: int) -> None:
        match = _FRAMES.match(line)
        if match:
            self.frames_declared = int(match.group(1))
            return
        match = _FRAME_TIME.match(line)
        if match:
            self.frame_time = float(match.group(1))
            self.motion_started = True
            return
        if not self.motion_started:
            self.errors.append(f"line {line_number}: motion data/header before Frame Time")
            return
        values = line.split()
        try:
            row = [float(value) for value in values]
        except ValueError:
            self.errors.append(f"line {line_number}: non-numeric motion row")
            return
        self.motion_rows.append(row)

    @property
    def expected_channels(self) -> int:
        return sum(len(joint["channels"]) for joint in self.joints)

    def validate(self) -> None:
        if not self.joints:
            self.errors.append("no ROOT/JOINT declarations found")
        else:
            roots = [i for i, joint in enumerate(self.joints) if joint["parent"] == -1]
            if len(roots) != 1 or self.joints[roots[0]]["kind"] != "ROOT":
                self.errors.append("hierarchy must contain exactly one ROOT")
            for index, joint in enumerate(self.joints):
                if joint["offset"] is None:
                    self.errors.append(f"joint {joint['name']!r} has no OFFSET")
                if not joint["channels"]:
                    self.errors.append(f"joint {joint['name']!r} has no CHANNELS")
                if joint["parent"] >= index:
                    self.errors.append(
                        f"joint {joint['name']!r} parent index {joint['parent']} is not before the child"
                    )
            root = next((joint for joint in self.joints if joint["parent"] == -1), None)
            if root is not None and len(root["channels"]) != 6:
                self.warnings.append(
                    f"root has {len(root['channels'])} channels; model workflows normally expect 6"
                )
            for joint in self.joints:
                if len(joint["channels"]) not in (3, 6, 9):
                    self.warnings.append(
                        f"joint {joint['name']!r} has {len(joint['channels'])} channels; legacy loaders commonly handle 3/6/9"
                    )

        if self.frames_declared is None:
            self.errors.append("missing Frames header")
        if self.frame_time is None:
            self.errors.append("missing Frame Time header")
        elif not math.isfinite(self.frame_time) or self.frame_time <= 0:
            self.errors.append(f"Frame Time must be finite and positive, got {self.frame_time!r}")
        if self.frames_declared is not None and len(self.motion_rows) != self.frames_declared:
            self.errors.append(
                f"Frames declares {self.frames_declared} rows but parsed {len(self.motion_rows)}"
            )
        expected = self.expected_channels
        for row_index, row in enumerate(self.motion_rows):
            if len(row) != expected:
                self.errors.append(
                    f"motion row {row_index} has {len(row)} values; expected {expected} channels"
                )
            if not all(math.isfinite(value) for value in row):
                self.errors.append(f"motion row {row_index} contains a non-finite value")

    def summary(self, source: Path) -> Dict[str, Any]:
        return {
            "source": str(source),
            "valid": not self.errors,
            "errors": self.errors,
            "warnings": self.warnings,
            "frames_declared": self.frames_declared,
            "frames_parsed": len(self.motion_rows),
            "frame_time_seconds": self.frame_time,
            "fps": (1.0 / self.frame_time if self.frame_time and self.frame_time > 0 else None),
            "joint_count": len(self.joints),
            "channel_count": self.expected_channels,
            "joints": [
                {
                    "index": index,
                    "name": joint["name"],
                    "parent": joint["parent"],
                    "offset": joint["offset"],
                    "channels": joint["channels"],
                    "end_site_offsets": joint["end_sites"],
                }
                for index, joint in enumerate(self.joints)
            ],
        }

    def write_round_trip(self, destination: Path) -> None:
        if not self.joints:
            raise BVHInspectionError("cannot round-trip a BVH with no joints")
        children: Dict[int, List[int]] = {index: [] for index in range(len(self.joints))}
        root: Optional[int] = None
        for index, joint in enumerate(self.joints):
            parent = joint["parent"]
            if parent == -1:
                root = index
            elif parent in children:
                children[parent].append(index)
        if root is None:
            raise BVHInspectionError("cannot round-trip without a root")

        lines: List[str] = ["HIERARCHY"]

        def emit_joint(index: int, depth: int) -> None:
            joint = self.joints[index]
            indent = "\t" * depth
            lines.append(f"{indent}{joint['kind']} {joint['name']}")
            lines.append(f"{indent}{{")
            inner = "\t" * (depth + 1)
            offset = joint["offset"] or [0.0, 0.0, 0.0]
            lines.append(f"{inner}OFFSET {_fmt_vec(offset)}")
            lines.append(f"{inner}CHANNELS {len(joint['channels'])} {' '.join(joint['channels'])}")
            for child in children[index]:
                emit_joint(child, depth + 1)
            end_sites = joint["end_sites"]
            if not children[index] and not end_sites:
                end_sites = [[0.0, 0.0, 0.0]]
            for end_offset in end_sites:
                lines.append(f"{inner}End Site")
                lines.append(f"{inner}{{")
                lines.append(f"{inner}\tOFFSET {_fmt_vec(end_offset)}")
                lines.append(f"{inner}}}")
            lines.append(f"{indent}}}")

        emit_joint(root, 0)
        lines.extend(["MOTION", f"Frames: {len(self.motion_rows)}", f"Frame Time: {_fmt(self.frame_time or 0.0)}"])
        lines.extend(" ".join(_fmt(value) for value in row) for row in self.motion_rows)
        destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def upper_line_starts(line: str, prefix: str) -> bool:
    return line.upper().startswith(prefix.upper()) and (
        len(line) == len(prefix) or line[len(prefix)].isspace()
    )


def _fmt(value: float) -> str:
    return f"{value:.9g}"


def _fmt_vec(values: List[float]) -> str:
    return " ".join(_fmt(float(value)) for value in values)


def inspect(path: Path) -> ParsedBVH:
    parsed = ParsedBVH()
    parsed.parse(path)
    parsed.validate()
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect BVH hierarchy, channels, frame time, and finite motion values without project imports."
    )
    parser.add_argument("input", type=Path, help="BVH file to inspect")
    parser.add_argument("--json", action="store_true", help="emit the summary as JSON")
    parser.add_argument(
        "--round-trip",
        type=Path,
        metavar="OUTPUT_BVH",
        help="write a structural copy to this new path; input is never overwritten",
    )
    parser.add_argument("--force", action="store_true", help="allow replacing an existing --round-trip destination")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    source = args.input.expanduser()
    if not source.is_file():
        print(f"error: input is not a file: {source}", file=sys.stderr)
        return 2
    try:
        parsed = inspect(source)
    except BVHInspectionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    round_trip_error: Optional[str] = None
    if args.round_trip is not None:
        destination = args.round_trip.expanduser()
        try:
            if destination.resolve() == source.resolve():
                raise BVHInspectionError("--round-trip destination must differ from input")
            if destination.exists() and not args.force:
                raise BVHInspectionError(f"destination exists; pass --force to replace: {destination}")
            if parsed.errors:
                raise BVHInspectionError("refusing to round-trip an invalid BVH; fix validation errors first")
            destination.parent.mkdir(parents=True, exist_ok=True)
            parsed.write_round_trip(destination)
        except (OSError, BVHInspectionError) as exc:
            round_trip_error = str(exc)

    summary = parsed.summary(source)
    if args.round_trip is not None:
        summary["round_trip"] = str(args.round_trip.expanduser())
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=False))
    else:
        print(f"BVH: {source}")
        print(f"valid: {summary['valid']}")
        print(f"joints: {summary['joint_count']}  channels/frame: {summary['channel_count']}")
        print(f"frames: {summary['frames_parsed']}/{summary['frames_declared']}  frame_time: {summary['frame_time_seconds']} s")
        if summary["fps"] is not None:
            print(f"nominal_fps: {summary['fps']:.6g}")
        print("topology:")
        for joint in summary["joints"]:
            print(f"  [{joint['index']}] {joint['name']} parent={joint['parent']} channels={len(joint['channels'])}")
        for message in parsed.warnings:
            print(f"warning: {message}")
        for message in parsed.errors:
            print(f"error: {message}")
        if args.round_trip is not None and not parsed.errors and round_trip_error is None:
            print(f"round_trip: {args.round_trip.expanduser()}")
    if round_trip_error is not None:
        print(f"error: {round_trip_error}", file=sys.stderr)

    return 0 if not parsed.errors and round_trip_error is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
