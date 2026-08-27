#!/usr/bin/env python3
"""Read-only DeepDanbooru training preflight; never launches training."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

from validate_project_config import load_config, resolve_target, validate_config

REQUIRED_COLUMNS = {"id", "md5", "file_ext", "tag_string", "tag_count_general"}
SUPPORTED_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_DETAILS = 20


def read_only_connect(path: Path) -> sqlite3.Connection:
    encoded = quote(str(path.resolve()), safe="/")
    connection = sqlite3.connect(f"file:{encoded}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def load_tags(path: Path, errors: list[str], warnings: list[str]) -> list[str]:
    if not path.is_file():
        errors.append(f"tags file does not exist: {path}")
        return []
    try:
        with path.open("r", encoding="utf-8") as stream:
            tags = [line.strip() for line in stream if line.strip()]
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read tags file: {exc}")
        return []
    if not tags:
        errors.append("tags.txt has no nonblank tags")
    duplicate_count = len(tags) - len(set(tags))
    if duplicate_count:
        warnings.append(f"tags.txt contains {duplicate_count} duplicate line(s)")
    return tags


def inspect_image(path: Path, extension: str) -> str | None:
    try:
        size = path.stat().st_size
        if size == 0:
            return "file is empty"
        with path.open("rb") as stream:
            header = stream.read(12)
    except OSError as exc:
        return str(exc)
    if extension == "png" and not header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "extension is png but PNG signature is missing"
    if extension in {"jpg", "jpeg"} and not header.startswith(b"\xff\xd8\xff"):
        return "extension is jpg/jpeg but JPEG signature is missing"
    return None


def inspect_database(
    database: Path,
    minimum_tag_count: int,
    tag_set: set[str],
    max_image_checks: int,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(database),
        "columns": [],
        "total_rows": None,
        "eligible_rows": None,
        "checked_rows": 0,
        "missing_images": [],
        "malformed_records": [],
        "records_without_known_tags": [],
        "errors": [],
        "warnings": [],
    }
    if not database.is_file():
        result["errors"].append(f"database file does not exist: {database}")
        return result

    try:
        connection = read_only_connect(database)
        try:
            table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='posts'"
            ).fetchone()
            if table is None:
                result["errors"].append("database is missing table: posts")
                return result
            info = connection.execute("PRAGMA table_info(posts)").fetchall()
            columns = {row["name"] for row in info}
            result["columns"] = sorted(columns)
            missing = sorted(REQUIRED_COLUMNS - columns)
            if missing:
                result["errors"].append(
                    "posts is missing required columns: " + ", ".join(missing)
                )
                return result

            result["total_rows"] = connection.execute(
                "SELECT COUNT(*) FROM posts"
            ).fetchone()[0]
            where_sql = (
                "(file_ext='png' OR file_ext='jpg' OR file_ext='jpeg') "
                "AND tag_count_general >= ?"
            )
            result["eligible_rows"] = connection.execute(
                f"SELECT COUNT(*) FROM posts WHERE {where_sql}",
                (minimum_tag_count,),
            ).fetchone()[0]
            if result["eligible_rows"] == 0:
                result["errors"].append(
                    "no eligible posts at the configured minimum_tag_count"
                )
                return result

            query = (
                "SELECT id, md5, file_ext, tag_string FROM posts "
                f"WHERE {where_sql} ORDER BY id"
            )
            parameters: tuple[Any, ...]
            if max_image_checks > 0:
                query += " LIMIT ?"
                parameters = (minimum_tag_count, max_image_checks)
            else:
                parameters = (minimum_tag_count,)

            image_root = database.parent / "images"
            for row in connection.execute(query, parameters):
                result["checked_rows"] += 1
                row_id = row["id"]
                md5 = row["md5"]
                extension = row["file_ext"]
                tag_string = row["tag_string"]
                if (
                    not isinstance(md5, str)
                    or len(md5) < 2
                    or "/" in md5
                    or "\\" in md5
                ):
                    if len(result["malformed_records"]) < MAX_DETAILS:
                        result["malformed_records"].append(
                            {"id": row_id, "reason": "md5 is null, short, or unsafe"}
                        )
                    continue
                if extension not in SUPPORTED_EXTENSIONS:
                    if len(result["malformed_records"]) < MAX_DETAILS:
                        result["malformed_records"].append(
                            {"id": row_id, "reason": f"unsupported extension {extension!r}"}
                        )
                    continue
                if not isinstance(tag_string, str) or not tag_string.strip():
                    if len(result["malformed_records"]) < MAX_DETAILS:
                        result["malformed_records"].append(
                            {"id": row_id, "reason": "tag_string is null or empty"}
                        )
                elif tag_set and not (set(tag_string.split()) & tag_set):
                    if len(result["records_without_known_tags"]) < MAX_DETAILS:
                        result["records_without_known_tags"].append(row_id)

                image_path = image_root / md5[:2] / f"{md5}.{extension}"
                if not image_path.is_file():
                    if len(result["missing_images"]) < MAX_DETAILS:
                        result["missing_images"].append(str(image_path))
                    continue
                image_problem = inspect_image(image_path, extension)
                if image_problem and len(result["malformed_records"]) < MAX_DETAILS:
                    result["malformed_records"].append(
                        {"id": row_id, "reason": image_problem, "path": str(image_path)}
                    )

            if result["missing_images"]:
                result["errors"].append(
                    f"checked rows include missing images (showing up to {MAX_DETAILS})"
                )
            if result["malformed_records"]:
                result["errors"].append(
                    f"checked rows include malformed/empty records or files (showing up to {MAX_DETAILS})"
                )
            if result["records_without_known_tags"]:
                result["warnings"].append(
                    f"{len(result['records_without_known_tags'])} shown row(s) have no tag present in tags.txt"
                )
            if result["checked_rows"] < result["eligible_rows"]:
                result["warnings"].append(
                    f"image checks are sampled: checked {result['checked_rows']} of {result['eligible_rows']} eligible rows"
                )
        finally:
            connection.close()
    except sqlite3.Error as exc:
        result["errors"].append(f"SQLite inspection failed: {exc}")
    return result


def inspect_checkpoints(project_dir: Path) -> dict[str, Any]:
    checkpoint_dir = project_dir / "checkpoints"
    state_file = checkpoint_dir / "checkpoint"
    files = sorted(path.name for path in checkpoint_dir.iterdir()) if checkpoint_dir.is_dir() else []
    result: dict[str, Any] = {
        "directory": str(checkpoint_dir),
        "exists": checkpoint_dir.is_dir(),
        "state_file": str(state_file) if state_file.is_file() else None,
        "file_count": len(files),
        "sample_files": files[:10],
        "warnings": [],
    }
    if files and not state_file.is_file():
        result["warnings"].append(
            "checkpoint directory is non-empty but has no TensorFlow checkpoint state file"
        )
    if state_file.is_file():
        try:
            first_line = state_file.read_text(encoding="utf-8").splitlines()[0]
            result["latest_checkpoint_record"] = first_line
        except (OSError, UnicodeError, IndexError) as exc:
            result["warnings"].append(f"cannot read checkpoint state: {exc}")
    return result


def check_distributions() -> dict[str, Any]:
    requirements = {
        "DeepDanbooru": "1.0.0",
        "tensorflow": None,
        "tensorflow-io": None,
    }
    result: dict[str, Any] = {"versions": {}, "errors": [], "warnings": []}
    for distribution, exact_version in requirements.items():
        try:
            version = importlib.metadata.version(distribution)
            result["versions"][distribution] = version
            if exact_version is not None and version != exact_version:
                result["errors"].append(
                    f"{distribution} version is {version}, expected {exact_version}"
                )
        except importlib.metadata.PackageNotFoundError:
            result["errors"].append(f"required distribution is not installed: {distribution}")
    return result


def probe_imports() -> dict[str, Any]:
    result: dict[str, Any] = {"modules": {}, "errors": []}
    for module_name in ("tensorflow", "tensorflow_io", "deepdanbooru"):
        try:
            module = importlib.import_module(module_name)
            result["modules"][module_name] = getattr(module, "__version__", "unknown")
        except Exception as exc:  # diagnostic boundary: report optional dependency failures
            result["errors"].append(
                f"cannot import {module_name}: {type(exc).__name__}: {exc}"
            )
    return result


def probe_tensorflow() -> dict[str, Any]:
    result: dict[str, Any] = {"cpus": [], "gpus": [], "errors": [], "notes": []}
    try:
        tensorflow = importlib.import_module("tensorflow")
        result["version"] = getattr(tensorflow, "__version__", "unknown")
        result["cpus"] = [device.name for device in tensorflow.config.list_physical_devices("CPU")]
        result["gpus"] = [device.name for device in tensorflow.config.list_physical_devices("GPU")]
        if not result["cpus"]:
            result["errors"].append("TensorFlow exposes no CPU device")
        if result["gpus"]:
            result["notes"].append(
                "GPU discovery is not end-to-end GPU verification; this skill verifies CPU only"
            )
        else:
            result["notes"].append("no GPU discovered; CPU is the required backend")
    except Exception as exc:
        result["errors"].append(
            f"TensorFlow probe failed: {type(exc).__name__}: {exc}"
        )
    return result


def append_nested_messages(report: dict[str, Any], key: str, value: dict[str, Any]) -> None:
    report[key] = value
    for message in value.get("errors", []):
        report["errors"].append(f"{key}: {message}")
    for message in value.get("warnings", []):
        report["warnings"].append(f"{key}: {message}")


def print_human(report: dict[str, Any], warnings_as_errors: bool) -> None:
    failed = bool(report["errors"] or (warnings_as_errors and report["warnings"]))
    print(f"{'FAIL' if failed else 'PASS'}: training preflight")
    for message in report["errors"]:
        print(f"  error: {message}")
    for message in report["warnings"]:
        print(f"  warning: {message}")
    summary = report.get("summary", {})
    for key, value in summary.items():
        print(f"  {key}: {value}")
    checkpoint = report.get("checkpoints", {})
    if checkpoint.get("state_file"):
        print("  resume: latest checkpoint state exists; training will restore automatically")
    elif checkpoint:
        print("  resume: no checkpoint state file found")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only preflight for a DeepDanbooru project, tags, SQLite records, "
            "image paths, checkpoints, and optional runtime packages. Never trains."
        )
    )
    parser.add_argument("target", type=Path, help="Project directory or project.json file.")
    parser.add_argument(
        "--database",
        type=Path,
        help="Explicit database to validate; it must match project.json after path resolution.",
    )
    parser.add_argument(
        "--runtime-cwd",
        type=Path,
        default=Path.cwd(),
        help="Working directory used for relative database_path (default: current directory).",
    )
    parser.add_argument(
        "--max-image-checks",
        type=int,
        default=1000,
        help="Maximum eligible image rows to inspect in ID order; 0 checks all (default: 1000).",
    )
    parser.add_argument(
        "--source-model",
        type=Path,
        help="Check existence of a planned --source-model and reject its mixed-precision hazard.",
    )
    parser.add_argument(
        "--check-packages",
        action="store_true",
        help="Check installed distribution versions without importing them.",
    )
    parser.add_argument(
        "--probe-imports",
        action="store_true",
        help="Import tensorflow, tensorflow_io, and deepdanbooru and report failures.",
    )
    parser.add_argument(
        "--probe-tensorflow",
        action="store_true",
        help="Import TensorFlow and require a visible CPU; GPU discovery remains unverified.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON report.")
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Return failure when warnings are present.",
    )
    args = parser.parse_args(argv)

    report: dict[str, Any] = {
        "errors": [],
        "warnings": [],
        "summary": {},
        "safety": {
            "read_only": True,
            "network": False,
            "launches_training": False,
        },
    }
    if args.max_image_checks < 0:
        report["errors"].append("--max-image-checks must be >= 0")

    config_path, project_dir = resolve_target(args.target)
    runtime_cwd = args.runtime_cwd.expanduser().resolve()
    report["summary"]["config_path"] = str(config_path)
    report["summary"]["runtime_cwd"] = str(runtime_cwd)

    config: dict[str, Any] | None = None
    if not config_path.is_file():
        report["errors"].append(f"project config does not exist: {config_path}")
    else:
        try:
            config = load_config(config_path)
            config_report = validate_config(config, project_dir, runtime_cwd)
            append_nested_messages(report, "config", config_report)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            report["errors"].append(f"cannot load project config: {exc}")

    tags = load_tags(project_dir / "tags.txt", report["errors"], report["warnings"])
    report["summary"]["tag_count"] = len(tags)

    if config is not None and not report.get("config", {}).get("errors") and args.max_image_checks >= 0:
        configured_database = Path(report["config"]["info"]["database_path"])
        database = args.database.expanduser().resolve() if args.database else configured_database
        if args.database and database != configured_database:
            report["errors"].append(
                "--database does not match the database_path resolved for training; update project.json or runtime CWD"
            )
        database_report = inspect_database(
            database,
            config["minimum_tag_count"],
            set(tags),
            args.max_image_checks,
        )
        append_nested_messages(report, "database", database_report)
        report["summary"]["database_path"] = str(database)
        report["summary"]["total_rows"] = database_report.get("total_rows")
        report["summary"]["eligible_rows"] = database_report.get("eligible_rows")
        report["summary"]["checked_rows"] = database_report.get("checked_rows")

        model_name = config.get("model")
        final_model = project_dir / f"model-{model_name}.keras"
        if final_model.exists():
            report["warnings"].append(
                f"final export already exists and may be replaced: {final_model}"
            )
        if args.source_model:
            source_model = args.source_model.expanduser().resolve()
            report["summary"]["source_model"] = str(source_model)
            if not source_model.is_file():
                report["errors"].append(f"source model does not exist: {source_model}")
            if config.get("mixed_precision", False):
                report["errors"].append(
                    "DeepDanbooru 1.0.0 cannot safely export when --source-model is combined with mixed_precision=true"
                )

    checkpoints = inspect_checkpoints(project_dir)
    append_nested_messages(report, "checkpoints", checkpoints)

    if args.check_packages:
        append_nested_messages(report, "packages", check_distributions())
    if args.probe_imports:
        append_nested_messages(report, "imports", probe_imports())
    if args.probe_tensorflow:
        tensorflow_report = probe_tensorflow()
        report["tensorflow"] = tensorflow_report
        for message in tensorflow_report.get("errors", []):
            report["errors"].append(f"tensorflow: {message}")

    failed = bool(report["errors"] or (args.warnings_as_errors and report["warnings"]))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report, args.warnings_as_errors)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
