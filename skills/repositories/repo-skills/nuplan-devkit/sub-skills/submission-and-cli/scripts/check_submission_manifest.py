#!/usr/bin/env python3
"""Safely preflight a nuPlan submission manifest.

The checker reads one JSON manifest and files below ``--root``.  It is
intentionally dependency-free: it does not import nuPlan, execute a planner,
start Docker, access a network, read credentials, or write files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Sequence, Tuple


PROTECTED_FILES = (
    "nuplan/submission/protos/challenge.proto",
    "nuplan/submission/challenge_pb2.py",
    "nuplan/submission/challenge_pb2_grpc.py",
    "nuplan/submission/submission_container.py",
    "nuplan/submission/submission_planner.py",
)

# The checker is pinned to the v1.2.2 source tree used by this skill.  Checking
# both the manifest declaration and these files prevents a locally consistent
# but organizer-incompatible protocol from being packaged.
PROTECTED_SHA256 = {
    "nuplan/submission/protos/challenge.proto": "35ccc2e8b2c6c84744f27e9daf2eeea3f57cd3ae25edfd78be50169e82cc4c51",
    "nuplan/submission/challenge_pb2.py": "c9e0493c463db9546f099074b4b3723a108f2297306cca5740e9b737afdb7117",
    "nuplan/submission/challenge_pb2_grpc.py": "c875c1cb224d7fbadc842eb2ba52b5a6afc0e4c80e38b926edff3933e0ca8fd0",
    "nuplan/submission/submission_container.py": "7df2d3bdde708d959553e35fc42d6ede98f5165c6bed532a3682b6614b25d543",
    "nuplan/submission/submission_planner.py": "51f250e093e6194ece3c71b4bd9e42dee205965bf2245316c28f961e972a5894",
}

MIN_HORIZON_SECONDS = 8.0
REQUIRED_POSE_FIELDS = ("x", "y", "heading")
TIMESTAMP_FIELDS = ("time_us", "timestamp")


class Checker:
    """Collect deterministic diagnostics without mutating the submission."""

    def __init__(self, root: Path, quiet: bool = False) -> None:
        self.root = root
        self.quiet = quiet
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    @staticmethod
    def _manifest_relative_path(value: Any, label: str) -> Optional[str]:
        """Return a safe POSIX-relative path, or ``None`` after a diagnostic.

        Manifest paths must not cause a check to escape the supplied root.  A
        backslash is normalized so manifests made on Windows are checked with
        the same semantics on every platform.
        """
        if not isinstance(value, str) or not value:
            return None
        normalized = value.replace("\\", "/")
        path = PurePosixPath(normalized)
        if path.is_absolute() or ".." in path.parts:
            return None
        parts = [part for part in path.parts if part not in ("", ".")]
        return "/".join(parts) if parts else None

    def _root_file(self, value: Any, label: str) -> Optional[Path]:
        relative = self._manifest_relative_path(value, label)
        if relative is None:
            self.error("{} must be a non-empty path relative to --root".format(label))
            return None
        path = self.root.joinpath(*PurePosixPath(relative).parts)
        try:
            path.resolve(strict=False).relative_to(self.root)
        except ValueError:
            self.error("{} resolves outside --root".format(label))
            return None
        except OSError as exc:
            self.error("cannot resolve {}: {}".format(label, exc))
            return None
        return path

    def check_protected_files(self, changed_files: Any) -> None:
        """Reject declared or observed edits to organizer-owned files."""
        if not self.root.is_dir():
            self.error("submission root is not a directory: {}".format(self.root))

        for relative in PROTECTED_FILES:
            path = self.root.joinpath(*PurePosixPath(relative).parts)
            try:
                path.resolve(strict=False).relative_to(self.root)
            except (OSError, ValueError):
                self.error("protected file resolves outside --root: {}".format(relative))
                continue
            if path.is_symlink():
                self.error("protected file must not be a symlink: {}".format(relative))
                continue
            if not path.is_file():
                self.error("submission root is missing protected base file: {}".format(relative))
                continue
            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError as exc:
                self.error("cannot read protected file {}: {}".format(relative, exc))
                continue
            if digest != PROTECTED_SHA256[relative]:
                self.error("protected file content differs from the v1.2.2 base: {}".format(relative))

        if changed_files is None:
            self.warning("manifest has no changed_files list; root digest checks still protect protocol files")
            return
        if not isinstance(changed_files, list):
            self.error("changed_files must be a JSON list of repository-relative path strings")
            return

        normalized: List[str] = []
        for index, item in enumerate(changed_files):
            relative = self._manifest_relative_path(item, "changed_files[{}]".format(index))
            if relative is None:
                self.error("changed_files[{}] must be a safe path relative to --root".format(index))
            else:
                normalized.append(relative)

        edited = sorted(set(PROTECTED_FILES).intersection(normalized))
        if edited:
            self.error("protected files are declared changed: " + ", ".join(edited))

    def check_entrypoint(self, value: Any) -> None:
        entrypoint = value if value is not None else "nuplan/entrypoint_submission.sh"
        path = self._root_file(entrypoint, "entrypoint")
        if path is None:
            return
        if not path.is_file():
            self.error("entrypoint does not exist: {}".format(entrypoint))
            return
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            self.error("cannot read entrypoint {}: {}".format(entrypoint, exc))
            return
        if "run_submission_planner.py" not in text:
            self.error("entrypoint does not invoke run_submission_planner.py: {}".format(entrypoint))
        if "planner=" not in text:
            self.error("entrypoint does not select a planner config with planner=: {}".format(entrypoint))

    @staticmethod
    def _finite_number(value: Any, label: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("{} must be a finite number".format(label))
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("{} must be a finite number".format(label))
        return number

    def check_planner_config(self, planner_config: Any) -> None:
        if not isinstance(planner_config, dict):
            self.error("planner_config must be an object with horizon_seconds and sampling_time")
            return

        for key in ("horizon_seconds", "sampling_time"):
            if key not in planner_config:
                self.error("planner_config is missing {}".format(key))

        try:
            horizon = self._finite_number(planner_config.get("horizon_seconds"), "horizon_seconds")
            if horizon < MIN_HORIZON_SECONDS:
                self.error("horizon_seconds must be at least {:.1f}".format(MIN_HORIZON_SECONDS))
        except ValueError as exc:
            self.error(str(exc))

        try:
            sampling_time = self._finite_number(planner_config.get("sampling_time"), "sampling_time")
            if sampling_time <= 0:
                self.error("sampling_time must be greater than zero")
            elif sampling_time > 1:
                self.error("sampling_time must be at most 1 second for the documented 1 Hz minimum")
        except ValueError as exc:
            self.error(str(exc))

    def _timestamp(self, point: Dict[str, Any], index: int) -> Optional[int]:
        present = [field for field in TIMESTAMP_FIELDS if field in point]
        if not present:
            self.error(
                "trajectory[{}] is missing timestamp signal (use integer time_us or timestamp microseconds)".format(
                    index
                )
            )
            return None

        values: List[Tuple[str, int]] = []
        for field in present:
            value = point[field]
            if isinstance(value, bool) or not isinstance(value, int):
                self.error("trajectory[{}].{} must be an integer in microseconds".format(index, field))
            else:
                values.append((field, value))

        if len(values) == 2 and values[0][1] != values[1][1]:
            self.error("trajectory[{}].time_us and .timestamp disagree".format(index))
        return values[0][1] if values else None

    def check_trajectory(self, trajectory: Any, current_time_us: Any = None) -> None:
        if not isinstance(trajectory, list):
            self.error("trajectory must be a JSON list of representative output points")
            return
        if len(trajectory) < 2:
            self.error("trajectory must contain at least two points")
            return

        timestamps: List[int] = []
        for index, point in enumerate(trajectory):
            if not isinstance(point, dict):
                self.error("trajectory[{}] must be an object".format(index))
                continue

            for field in REQUIRED_POSE_FIELDS:
                if field not in point:
                    self.error("trajectory[{}] is missing {}".format(index, field))
                else:
                    try:
                        self._finite_number(point[field], "trajectory[{}].{}".format(index, field))
                    except ValueError as exc:
                        self.error(str(exc))

            timestamp = self._timestamp(point, index)
            if timestamp is not None:
                timestamps.append(timestamp)

        if len(timestamps) != len(trajectory):
            return

        for index, (previous, current) in enumerate(zip(timestamps, timestamps[1:]), start=1):
            if current <= previous:
                self.error("trajectory timestamps must be strictly increasing (point {})".format(index))

        if current_time_us is not None:
            if isinstance(current_time_us, bool) or not isinstance(current_time_us, int):
                self.error("current_time_us must be an integer in microseconds")
            elif timestamps[0] < current_time_us:
                # A trajectory may start at the current state (as SimplePlanner
                # does); it must not start in the past.
                self.error("first trajectory timestamp must not precede current_time_us")

        horizon = (timestamps[-1] - timestamps[0]) / 1_000_000.0
        if horizon < MIN_HORIZON_SECONDS:
            self.error(
                "trajectory timestamp horizon is {:.3f}s; it must be at least {:.1f}s".format(
                    horizon, MIN_HORIZON_SECONDS
                )
            )

    def report(self) -> int:
        if not self.quiet:
            for warning in self.warnings:
                print("WARNING: " + warning)
            for error in self.errors:
                print("ERROR: " + error)
        if self.errors:
            print("FAIL: {} error(s), {} warning(s)".format(len(self.errors), len(self.warnings)))
            return 1
        print("PASS: static submission manifest checks passed ({} warning(s))".format(len(self.warnings)))
        return 0


def load_manifest(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError("manifest root must be a JSON object")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check planner output, config values, entrypoint wiring, and protected paths without side effects."
    )
    parser.add_argument(
        "--manifest", required=True, type=Path, help="JSON manifest describing static submission facts"
    )
    parser.add_argument("--root", type=Path, default=Path("."), help="Submission root (default: current directory)")
    parser.add_argument("--quiet", action="store_true", help="Suppress individual warnings and errors")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = (Path.cwd() / manifest_path).resolve()

    try:
        manifest = load_manifest(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: cannot load manifest {}: {}".format(manifest_path, exc))
        return 2

    checker = Checker(root, quiet=args.quiet)
    checker.check_protected_files(manifest.get("changed_files"))
    checker.check_entrypoint(manifest.get("entrypoint"))
    checker.check_planner_config(manifest.get("planner_config"))
    checker.check_trajectory(manifest.get("trajectory"), manifest.get("current_time_us"))
    return checker.report()


if __name__ == "__main__":
    sys.exit(main())
