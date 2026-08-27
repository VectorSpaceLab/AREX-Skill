#!/usr/bin/env python3
"""Validate a local nuPlan data layout without downloading or mutating it.

The validator uses only the Python standard library.  It checks the requested
split, map metadata and map.gpkg paths, SQLite table/column shape, and (when a
sensor root is supplied or its conventional local path exists) a bounded set
of sensor blob references.  It deliberately does not construct nuPlan map or
scenario objects because those APIs may create caches or use remote stores.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set
from urllib.parse import quote

DEFAULT_MAP_VERSION = "nuplan-maps-v1.0"
STANDARD_LOCATIONS = (
    "sg-one-north",
    "us-ma-boston",
    "us-nv-las-vegas-strip",
    "us-pa-pittsburgh-hazelwood",
)
REQUIRED_TABLES = {
    "category",
    "camera",
    "ego_pose",
    "image",
    "lidar",
    "lidar_box",
    "lidar_pc",
    "log",
    "scenario_tag",
    "scene",
    "track",
    "traffic_light_status",
}
# These are the columns needed by the read-only checks and the documented
# scenario/sensor joins.  The complete column inventory is in database-and-schema.md.
REQUIRED_COLUMNS = {
    "log": {"token", "logfile", "location", "map_version"},
    "camera": {"token", "log_token", "channel"},
    "image": {"token", "ego_pose_token", "camera_token", "filename_jpg", "timestamp"},
    "lidar": {"token", "log_token", "channel"},
    "lidar_pc": {"token", "scene_token", "ego_pose_token", "lidar_token", "filename", "timestamp"},
    "scene": {"token", "log_token", "goal_ego_pose_token", "roadblock_ids"},
    "scenario_tag": {"token", "lidar_pc_token", "type"},
}


class Report:
    """Ordered findings for stable text and JSON output."""

    def __init__(self) -> None:
        self.findings: List[Dict[str, Any]] = []

    def add(self, level: str, code: str, message: str, **details: Any) -> None:
        finding: Dict[str, Any] = {"level": level, "code": code, "message": message}
        if details:
            finding["details"] = details
        self.findings.append(finding)

    @property
    def errors(self) -> int:
        return sum(item["level"] == "error" for item in self.findings)

    @property
    def warnings(self) -> int:
        return sum(item["level"] == "warning" for item in self.findings)

    def text(self) -> str:
        lines: List[str] = []
        for item in self.findings:
            suffix = ""
            if "details" in item:
                suffix = " " + json.dumps(item["details"], sort_keys=True)
            lines.append(f"{item['level'].upper():7} {item['code']}: {item['message']}{suffix}")
        return "\n".join(lines)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments; argparse supplies the deterministic --help path."""
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a local nuPlan dataset read-only. This command never downloads, "
            "creates, deletes, or rewrites dataset files."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data-root",
        default=os.environ.get("NUPLAN_DATA_ROOT", ""),
        help="Parent containing nuplan-v1.1 (or set NUPLAN_DATA_ROOT).",
    )
    parser.add_argument(
        "--maps-root",
        default=os.environ.get("NUPLAN_MAPS_ROOT", ""),
        help="Map root containing <map-version>.json (defaults to <data-root>/maps).",
    )
    parser.add_argument(
        "--sensor-root",
        default=os.environ.get("NUPLAN_SENSOR_ROOT", ""),
        help="Optional sensor blob root; defaults to the conventional local path when it exists.",
    )
    parser.add_argument(
        "--split",
        choices=("mini", "trainval", "test"),
        default="mini",
        help="Dataset split below nuplan-v1.1 to inspect when --db is not supplied.",
    )
    parser.add_argument(
        "--db",
        action="append",
        default=[],
        help="Explicit local .db file or directory; repeat for multiple inputs.",
    )
    parser.add_argument(
        "--map-version",
        default=os.environ.get("NUPLAN_MAP_VERSION", DEFAULT_MAP_VERSION),
        help="Map metadata basename, without a path or suffix.",
    )
    parser.add_argument(
        "--db-limit",
        type=int,
        default=20,
        help="Maximum discovered DBs to inspect; use 0 for all.",
    )
    parser.add_argument(
        "--blob-samples",
        type=int,
        default=3,
        help="Maximum image and lidar references checked per DB; 0 disables sampling.",
    )
    parser.add_argument(
        "--skip-sensors",
        action="store_true",
        help="Do not inspect the optional sensor root or blob references.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report.")
    args = parser.parse_args(argv)
    if args.db_limit < 0:
        parser.error("--db-limit must be non-negative")
    if args.blob_samples < 0:
        parser.error("--blob-samples must be non-negative")
    return args


def default_data_root(value: str) -> Path:
    return Path(value).expanduser() if value else Path.home() / "nuplan" / "dataset"


def split_path(data_root: Path, split: str) -> Path:
    if split == "test":
        return data_root / "nuplan-v1.1" / "test"
    return data_root / "nuplan-v1.1" / "splits" / split


def discover_db_paths(inputs: Iterable[str], split_dir: Path, report: Report) -> List[Path]:
    """Discover only local, direct-child .db files, matching the builder contract."""
    candidates: List[Path] = []
    values = list(inputs)
    if not values:
        if not split_dir.is_dir():
            report.add("error", "missing-split", "Selected split is not a directory.", path=str(split_dir))
        else:
            candidates.extend(item for item in split_dir.iterdir() if item.is_file() and item.suffix == ".db")
    for raw in values:
        if raw.startswith(("s3://", "http://", "https://")):
            report.add("error", "remote-db", "Remote DB inputs are outside this local-only validator.", input=raw)
            continue
        path = Path(raw).expanduser()
        if path.is_file():
            if path.suffix != ".db":
                report.add("warning", "non-db-input", "Explicit file does not use the .db suffix.", path=str(path))
            candidates.append(path)
        elif path.is_dir():
            candidates.extend(item for item in path.iterdir() if item.is_file() and item.suffix == ".db")
        else:
            report.add("error", "missing-db-path", "Explicit DB file or directory does not exist.", path=str(path))

    unique = sorted({path.resolve() for path in candidates}, key=lambda path: str(path))
    if not unique:
        report.add("error", "no-dbs", "No local .db files were discovered.", directory=str(split_dir))
    return unique


def read_only_connection(path: Path) -> sqlite3.Connection:
    """Open SQLite with mode=ro so even a malformed check cannot write a journal."""
    uri = "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def check_map_root(maps_root: Path, map_version: str, report: Report) -> Set[str]:
    """Validate metadata and every metadata-declared location's expected GPKG path."""
    if not map_version or "/" in map_version or "\\" in map_version or map_version in {".", ".."}:
        report.add("error", "unsafe-map-version", "Map version must be a single metadata basename.", map_version=map_version)
        return set()
    if not maps_root.is_dir():
        report.add("error", "missing-maps-root", "Map root is not a directory.", path=str(maps_root))
        return set()

    metadata_path = maps_root / f"{map_version}.json"
    if not metadata_path.is_file():
        report.add("error", "missing-map-metadata", "Map-version metadata JSON is missing.", path=str(metadata_path))
        return set()
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        report.add("error", "invalid-map-metadata", "Map-version metadata is not valid JSON.", error=str(error))
        return set()
    if not isinstance(metadata, dict):
        report.add("error", "invalid-map-metadata", "Map-version metadata must be a JSON object.")
        return set()

    locations = {str(location) for location in metadata}
    missing_standard = sorted(set(STANDARD_LOCATIONS) - locations)
    if missing_standard:
        report.add(
            "error",
            "missing-map-locations",
            "Map metadata is missing standard nuPlan locations.",
            locations=missing_standard,
        )

    root = maps_root.resolve()
    for location in sorted(locations):
        if not location or Path(location).is_absolute() or "/" in location or "\\" in location or location in {".", ".."}:
            report.add("error", "unsafe-map-location", "Map metadata contains an unsafe location name.", location=location)
            continue
        entry = metadata.get(location)
        if not isinstance(entry, dict) or not isinstance(entry.get("version"), (str, int, float)):
            report.add("error", "invalid-map-entry", "Map location has no usable version in metadata.", location=location)
            continue
        local_version = str(entry["version"])
        if not local_version or "/" in local_version or "\\" in local_version or local_version in {".", ".."}:
            report.add("error", "unsafe-location-version", "Map location version is not a safe path component.", location=location)
            continue
        gpkg = maps_root / location / local_version / "map.gpkg"
        try:
            gpkg.resolve().relative_to(root)
        except ValueError:
            report.add("error", "map-path-escape", "Resolved map.gpkg path escapes the maps root.", location=location)
            continue
        if gpkg.is_file():
            report.add("info", "map-gpkg-present", "Map GeoPackage is present.", location=location, path=str(gpkg))
        else:
            report.add("error", "missing-map-gpkg", "Map GeoPackage is missing.", location=location, path=str(gpkg))
    return locations


def safe_blob_path(sensor_root: Path, key: Any) -> Optional[Path]:
    """Resolve a DB-relative key only if it remains below sensor_root."""
    if not isinstance(key, str) or not key or Path(key).is_absolute():
        return None
    root = sensor_root.resolve()
    candidate = (sensor_root / key).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def check_blob_references(
    connection: sqlite3.Connection,
    db_path: Path,
    sensor_root: Path,
    samples: int,
    report: Report,
) -> None:
    if not sensor_root.is_dir():
        report.add("error", "missing-sensor-root", "The requested sensor root is not a directory.", path=str(sensor_root))
        return
    if samples == 0:
        report.add("info", "sensor-sampling-skipped", "Blob reference sampling was disabled.", db=db_path.name)
        return

    for table, column, code, missing_message in (
        ("lidar_pc", "filename", "lidar-blob", "DB has no lidar blob references."),
        ("image", "filename_jpg", "image-blob", "DB has no image blob references; camera use may be unavailable."),
    ):
        rows = connection.execute(
            f"SELECT {column} AS blob_key FROM {table} WHERE {column} IS NOT NULL ORDER BY rowid LIMIT ?",
            (samples,),
        ).fetchall()
        if not rows:
            report.add("warning" if table == "image" else "error", code + "-empty", missing_message, db=db_path.name)
            continue
        for row in rows:
            key = row["blob_key"]
            path = safe_blob_path(sensor_root, key)
            if path is None:
                report.add("error", "unsafe-blob-key", "DB blob key is empty, absolute, or escapes sensor root.", db=db_path.name, key=key)
            elif path.is_file():
                report.add("info", code, "Referenced sensor blob is present.", db=db_path.name, key=key)
            else:
                report.add("error", code, "Referenced sensor blob is missing.", db=db_path.name, key=key, path=str(path))


def inspect_db(
    db_path: Path,
    sensor_root: Optional[Path],
    map_locations: Set[str],
    samples: int,
    skip_sensors: bool,
    report: Report,
) -> None:
    try:
        connection = read_only_connection(db_path)
    except (OSError, sqlite3.Error) as error:
        report.add("error", "sqlite-open", "Could not open DB read-only.", db=str(db_path), error=str(error))
        return

    try:
        names = {
            str(row["name"])
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        }
        missing_tables = sorted(REQUIRED_TABLES - names)
        if missing_tables:
            report.add("error", "missing-tables", "DB is missing required nuPlan tables.", db=db_path.name, tables=missing_tables)
        for table, required in sorted(REQUIRED_COLUMNS.items()):
            if table not in names:
                continue
            columns = {
                str(row[1])
                for row in connection.execute(f'PRAGMA table_info("{table}")')
            }
            missing_columns = sorted(required - columns)
            if missing_columns:
                report.add(
                    "error",
                    "missing-columns",
                    "DB table is missing columns needed by this skill.",
                    db=db_path.name,
                    table=table,
                    columns=missing_columns,
                )

        if "log" in names:
            logs = connection.execute(
                "SELECT logfile, location, map_version FROM log ORDER BY logfile, rowid"
            ).fetchall()
            if not logs:
                report.add("error", "empty-log", "DB has no log row.", db=db_path.name)
            for row in logs:
                location = "" if row["location"] is None else str(row["location"])
                map_name = "" if row["map_version"] is None else str(row["map_version"])
                if location and map_locations and location not in map_locations:
                    report.add("warning", "unknown-location", "DB log location is absent from map metadata.", db=db_path.name, location=location)
                if map_name and map_locations and map_name not in map_locations:
                    report.add("warning", "unknown-map-name", "DB log map_version is absent from map metadata locations; this may be intentional.", db=db_path.name, map_version=map_name)
                report.add("info", "log-present", "Read DB log metadata.", db=db_path.name, logfile=row["logfile"], location=location, map_version=map_name)
        else:
            report.add("error", "no-log-table", "Cannot inspect DB map identity without the log table.", db=db_path.name)

        if skip_sensors:
            report.add("info", "sensor-check-skipped", "Sensor checks were explicitly skipped.", db=db_path.name)
        elif sensor_root is not None and REQUIRED_TABLES.issubset(names):
            check_blob_references(connection, db_path, sensor_root, samples, report)
    except sqlite3.Error as error:
        report.add("error", "sqlite-query", "Read-only schema inspection failed.", db=str(db_path), error=str(error))
    finally:
        connection.close()


def validate(args: argparse.Namespace) -> Report:
    report = Report()
    data_root = default_data_root(args.data_root)
    maps_root = Path(args.maps_root).expanduser() if args.maps_root else data_root / "maps"
    conventional_sensor_root = data_root / "nuplan-v1.1" / "sensor_blobs"
    explicit_sensor = bool(args.sensor_root)
    requested_sensor_root = Path(args.sensor_root).expanduser() if explicit_sensor else conventional_sensor_root

    if not data_root.is_dir():
        report.add("error", "missing-data-root", "Data root is not a directory.", path=str(data_root))
    map_locations = check_map_root(maps_root, args.map_version, report)
    db_paths = discover_db_paths(args.db, split_path(data_root, args.split), report)
    if args.db_limit and len(db_paths) > args.db_limit:
        report.add("warning", "db-limit", "DB inspection was bounded by --db-limit.", total=len(db_paths), inspected=args.db_limit)
        db_paths = db_paths[: args.db_limit]

    sensor_root: Optional[Path]
    if args.skip_sensors:
        sensor_root = None
    elif explicit_sensor:
        sensor_root = requested_sensor_root
    elif conventional_sensor_root.is_dir():
        sensor_root = conventional_sensor_root
    else:
        sensor_root = None
        report.add("warning", "sensor-root-not-supplied", "No sensor root was supplied or found at its conventional path; DB/map checks continue.", path=str(conventional_sensor_root))

    for db_path in db_paths:
        inspect_db(db_path, sensor_root, map_locations, args.blob_samples, args.skip_sensors, report)
    report.add(
        "info",
        "summary",
        "Validation completed without mutating inputs.",
        data_root=str(data_root),
        maps_root=str(maps_root),
        split=args.split,
        sensor_root=None if sensor_root is None else str(sensor_root),
        dbs_inspected=len(db_paths),
        errors=report.errors,
        warnings=report.warnings,
    )
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = parse_args(argv)
        report = validate(args)
        if args.json:
            print(json.dumps({"findings": report.findings, "errors": report.errors, "warnings": report.warnings}, indent=2, sort_keys=True))
        else:
            print(report.text())
        return 1 if report.errors else 0
    except Exception as error:  # Keep unexpected validator failures distinguishable from data errors.
        print(f"ERROR   validator-exception: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
