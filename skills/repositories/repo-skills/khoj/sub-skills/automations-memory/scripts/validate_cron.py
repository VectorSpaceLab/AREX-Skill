#!/usr/bin/env python3
"""Validate and normalize Khoj automation cron strings without starting Khoj.

This helper mirrors the API-level cron handling used by Khoj automations:
strip whitespace, keep the first five fields, replace '?' with '*', reject
non-numeric minute fields, and optionally describe the schedule with
cron_descriptor when that optional dependency is installed.
"""

from __future__ import annotations

import argparse
import json
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class CronValidationError(ValueError):
    """Raised for a user-facing cron validation failure."""


def normalize_cron(cron: str) -> str:
    parts = cron.strip().split()
    if not parts:
        raise CronValidationError("crontime is required")
    if len(parts) < 5:
        raise CronValidationError("crontime must contain at least five fields")
    if len(parts) > 5:
        parts = parts[:5]
    normalized = " ".join(parts).replace("?", "*")
    minute_value = normalized.split()[0]
    if not minute_value.isdigit():
        raise CronValidationError(
            "minute-level recurrence is unsupported; use a single numeric minute in the first field"
        )
    minute = int(minute_value)
    if minute < 0 or minute > 59:
        raise CronValidationError("minute field must be between 0 and 59")
    return normalized


def describe_cron(cron: str) -> tuple[str | None, str | None]:
    try:
        import cron_descriptor  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return None, "cron_descriptor is not installed; description skipped"

    try:
        description = cron_descriptor.get_description(cron)
    except Exception as error:  # pragma: no cover - depends on optional package wording
        raise CronValidationError(f"invalid crontime: {error}") from error
    if not description:
        raise CronValidationError("invalid crontime")
    return description, None


def validate_trigger(cron: str, timezone_name: str) -> str | None:
    try:
        from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return "apscheduler is not installed; trigger validation skipped"

    try:
        CronTrigger.from_crontab(cron, ZoneInfo(timezone_name))
    except Exception as error:  # pragma: no cover - depends on APScheduler wording
        raise CronValidationError(f"invalid crontime: {error}") from error
    return None


def validate_timezone(timezone_name: str) -> tuple[str, str | None]:
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return "UTC", f"unknown timezone {timezone_name!r}; Khoj's synchronous scheduler falls back to UTC"
    return timezone_name, None


def build_payload(cron: str, timezone_name: str, include_description: bool) -> dict[str, Any]:
    normalized = normalize_cron(cron)
    effective_timezone, timezone_warning = validate_timezone(timezone_name)
    trigger_warning = validate_trigger(normalized, effective_timezone)
    description = None
    description_warning = None
    if include_description:
        description, description_warning = describe_cron(normalized)

    payload: dict[str, Any] = {
        "ok": True,
        "input": cron,
        "normalized": normalized,
        "timezone": effective_timezone,
        "query_prefix": "/automated_task",
        "api_behavior": "Khoj create/edit accepts this cron shape after adding /automated_task to the inferred execution query.",
        "warnings": [],
    }
    if description:
        payload["description"] = description
    if timezone_warning:
        payload["warnings"].append(timezone_warning)
    if trigger_warning:
        payload["warnings"].append(trigger_warning)
    if description_warning:
        payload["warnings"].append(description_warning)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and normalize a Khoj automation cron string without starting the Khoj server."
    )
    parser.add_argument("cron", help="Cron expression, e.g. '0 9 * * 1'. Extra fields are truncated like the API.")
    parser.add_argument(
        "--timezone",
        default="UTC",
        help="IANA timezone to check for scheduling context. Defaults to UTC.",
    )
    parser.add_argument(
        "--no-description",
        action="store_true",
        help="Skip cron_descriptor-based human description even when cron_descriptor is installed.",
    )
    args = parser.parse_args()

    try:
        payload = build_payload(args.cron, args.timezone, include_description=not args.no_description)
    except CronValidationError as error:
        payload = {
            "ok": False,
            "input": args.cron,
            "error": str(error),
            "query_prefix": "/automated_task",
            "api_behavior": "Khoj create/edit rejects invalid cron and non-numeric minute fields before scheduling.",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
