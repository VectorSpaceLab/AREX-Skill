#!/usr/bin/env python3
"""Safely inspect a Dagster OSS instance configuration directory."""

import argparse
import os
from pathlib import Path
from typing import Any, Optional


KNOWN_TOP_LEVEL_KEYS = {
    "auto_materialize",
    "backfills",
    "code_servers",
    "compute_logs",
    "concurrency",
    "event_log_storage",
    "local_artifact_storage",
    "nux",
    "retention",
    "run_coordinator",
    "run_launcher",
    "run_monitoring",
    "run_queue",
    "run_retries",
    "run_storage",
    "schedule_storage",
    "scheduler",
    "schedules",
    "secrets",
    "sensors",
    "storage",
    "telemetry",
}


def _load_yaml(path: Path) -> tuple[Optional[Any], Optional[str]]:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return None, "PyYAML is not installed; skipped YAML parsing."

    try:
        with path.open("r", encoding="utf8") as config_file:
            parsed = yaml.safe_load(config_file)
    except Exception as exc:
        return None, f"Failed to parse YAML: {exc}"

    return parsed, None


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve())
    except OSError:
        return str(path)


def inspect_config(dagster_home: Path, config_path: Path) -> int:
    exit_code = 0

    print("Dagster instance configuration check")
    print(f"DAGSTER_HOME: {_display_path(dagster_home)}")
    print(f"dagster.yaml: {_display_path(config_path)}")

    if not dagster_home.exists():
        print("ERROR: DAGSTER_HOME directory does not exist.")
        print("Create it or point services at the intended persistent instance directory.")
        return 2

    if not dagster_home.is_dir():
        print("ERROR: DAGSTER_HOME is not a directory.")
        return 2

    if not config_path.exists():
        print("WARNING: dagster.yaml was not found.")
        print("Dagster can use defaults, but production services should share an explicit instance config.")
        print("Common next steps:")
        print("- Add dagster.yaml under DAGSTER_HOME.")
        print("- Configure durable storage for multi-service deployments.")
        print("- Run one dagster-daemon process for schedules, sensors, run queueing, and monitoring.")
        return 1

    if not config_path.is_file():
        print("ERROR: dagster.yaml path exists but is not a file.")
        return 2

    parsed_config, parse_warning = _load_yaml(config_path)
    if parse_warning:
        print(f"WARNING: {parse_warning}")
        if parse_warning.startswith("Failed to parse"):
            exit_code = 2

    if isinstance(parsed_config, dict):
        keys = sorted(str(key) for key in parsed_config.keys())
        print("Top-level keys: " + (", ".join(keys) if keys else "<none>"))

        unknown_keys = sorted(key for key in keys if key not in KNOWN_TOP_LEVEL_KEYS)
        if unknown_keys:
            print("NOTE: Unrecognized top-level keys found: " + ", ".join(unknown_keys))
            print("Check for typos or project-specific custom instance config.")

        if "storage" not in parsed_config and not any(
            key in parsed_config for key in ("run_storage", "event_log_storage", "schedule_storage")
        ):
            print("WARNING: No explicit instance storage configuration found.")
            print("For production, configure shared durable storage such as Postgres or MySQL.")
            exit_code = max(exit_code, 1)

        if "run_monitoring" not in parsed_config:
            print("NOTE: run_monitoring is not configured; crashed or stuck run workers may need manual triage.")

        if "run_retries" not in parsed_config:
            print("NOTE: run_retries is not configured; whole-run infrastructure retries are disabled by default in OSS.")

        run_coordinator = parsed_config.get("run_coordinator")
        concurrency = parsed_config.get("concurrency")
        run_queue = parsed_config.get("run_queue")
        if run_queue and not run_coordinator:
            print("NOTE: Found legacy run_queue config; consider current run_coordinator/concurrency config for new deployments.")
        if run_coordinator and not concurrency:
            print("NOTE: run_coordinator is configured; verify run concurrency limits are set where intended.")

        scheduler = parsed_config.get("scheduler")
        if scheduler is None:
            print("NOTE: Default daemon-backed scheduler is expected unless overridden elsewhere.")

        if any(key in parsed_config for key in ("schedules", "sensors", "backfills", "run_monitoring")) or run_coordinator:
            print("REMINDER: dagster-daemon must run against this same DAGSTER_HOME for automation and queues.")
    elif parsed_config is None and parse_warning and parse_warning.startswith("PyYAML"):
        print("Install PyYAML for structural validation, or inspect the file manually.")
    elif parsed_config is None:
        print("WARNING: dagster.yaml is empty or parsed as null.")
        exit_code = max(exit_code, 1)
    else:
        print("WARNING: dagster.yaml did not parse to a mapping/object.")
        exit_code = max(exit_code, 1)

    print("Common production guidance:")
    print("- Use one shared DAGSTER_HOME across webserver, daemon, and run workers.")
    print("- Use one daemon process for schedules, sensors, run queueing, and monitoring.")
    print("- Use shared durable storage and compute logs for multi-container or multi-node deployments.")
    print("- Keep secrets in environment variables or platform secret stores, not literal YAML values.")

    return exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely inspect a DAGSTER_HOME/dagster.yaml path and print common Dagster OSS "
            "deployment guidance without starting services."
        )
    )
    parser.add_argument(
        "--dagster-home",
        default=os.environ.get("DAGSTER_HOME"),
        help="Path to DAGSTER_HOME. Defaults to the DAGSTER_HOME environment variable.",
    )
    parser.add_argument(
        "--config",
        help="Optional explicit dagster.yaml path. Defaults to <DAGSTER_HOME>/dagster.yaml.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.dagster_home:
        print("ERROR: Provide --dagster-home or set DAGSTER_HOME.")
        return 2

    dagster_home = Path(args.dagster_home).expanduser()
    config_path = Path(args.config).expanduser() if args.config else dagster_home / "dagster.yaml"
    return inspect_config(dagster_home, config_path)


if __name__ == "__main__":
    raise SystemExit(main())
