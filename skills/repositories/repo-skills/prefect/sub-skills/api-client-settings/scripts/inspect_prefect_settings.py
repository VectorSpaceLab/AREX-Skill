#!/usr/bin/env python3
"""Inspect Prefect settings and profiles without contacting a Prefect API."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def _load_prefect() -> tuple[Any, Any, Any, Any]:
    try:
        from prefect.settings import get_current_settings
        from prefect.settings.models.root import Settings
        from prefect.settings.profiles import _read_profiles_from
        from prefect.settings.legacy import _get_settings_fields
    except Exception as exc:  # pragma: no cover - diagnostic script path
        print(f"Failed to import Prefect settings: {exc}", file=sys.stderr)
        sys.exit(2)
    return get_current_settings, Settings, _read_profiles_from, _get_settings_fields


def _redact_key(name: str, value: str | None, include_secrets: bool) -> str | None:
    if value is None or include_secrets:
        return value
    lowered = name.lower()
    if any(token in lowered for token in ("key", "token", "password", "secret", "auth")):
        return "<redacted>"
    return value


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, default=str))


def _safe_default(value: Any) -> Any:
    if value.__class__.__name__ == "PydanticUndefinedType":
        return None
    try:
        json.dumps(value, default=str)
    except TypeError:
        return str(value)
    return value


def _setting_rows(Settings: Any, settings_fields: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    def walk(model: Any, prefix: str = "") -> None:
        for field_name, field in model.model_fields.items():
            path = f"{prefix}.{field_name}" if prefix else field_name
            annotation = field.annotation
            if hasattr(annotation, "model_fields"):
                walk(annotation, path)
                continue
            setting = settings_fields.get(path)
            if path in seen:
                continue
            seen.add(path)
            rows.append(
                {
                    "accessor": path,
                    "environment_variable": setting.name if setting else None,
                    "description": field.description,
                    "default": _safe_default(field.default),
                }
            )

    walk(Settings)
    rows.sort(key=lambda row: row["accessor"])
    return rows


def _validate_profiles(path: Path, read_profiles_from: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "exists": path.exists(), "ok": False}
    if not path.exists():
        result["error"] = "profiles file does not exist"
        return result

    try:
        profiles = read_profiles_from(path)
    except Exception as exc:
        result["error"] = f"failed to read TOML: {exc}"
        return result

    result["active"] = profiles.active_name
    result["profiles"] = sorted(profiles.names)
    errors: dict[str, str] = {}
    for name, profile in profiles.items():
        try:
            profile.validate_settings()
        except Exception as exc:
            errors[name] = str(exc)
    result["ok"] = not errors
    if errors:
        result["validation_errors"] = errors
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect effective Prefect settings, schema metadata, and profiles TOML without network calls.",
    )
    parser.add_argument(
        "--profiles-path",
        type=Path,
        help="Profiles TOML path to validate. Defaults to the effective settings profiles_path.",
    )
    parser.add_argument(
        "--validate-profiles",
        action="store_true",
        help="Validate the profiles TOML file with Prefect's profile parser and setting validators.",
    )
    parser.add_argument(
        "--schema-summary",
        action="store_true",
        help="Include setting count and a compact list of accessors/environment variables.",
    )
    parser.add_argument(
        "--show-unset",
        action="store_true",
        help="Include settings that are not explicitly set in the current context.",
    )
    parser.add_argument(
        "--include-secrets",
        action="store_true",
        help="Print secret-like values instead of redacting them. Use with care.",
    )
    args = parser.parse_args()

    get_current_settings, Settings, read_profiles_from, get_settings_fields = _load_prefect()

    try:
        settings = get_current_settings()
    except Exception as exc:
        _print_json({"ok": False, "error": f"failed to construct settings: {exc}"})
        return 1

    env_values = settings.to_environment_variables(
        exclude_unset=not args.show_unset,
        include_secrets=True,
        include_aliases=False,
    )
    redacted_env = {
        key: _redact_key(key, value, args.include_secrets)
        for key, value in sorted(env_values.items())
    }

    data: dict[str, Any] = {
        "ok": True,
        "prefect_version": getattr(__import__("prefect"), "__version__", None),
        "api_url": _redact_key("PREFECT_API_URL", str(settings.api.url) if settings.api.url else None, args.include_secrets),
        "profiles_path": str(settings.profiles_path) if settings.profiles_path else None,
        "active_profile_env": os.environ.get("PREFECT_PROFILE"),
        "explicit_environment": redacted_env,
    }

    if args.schema_summary:
        fields = get_settings_fields(Settings)
        rows = _setting_rows(Settings, fields)
        data["schema"] = {
            "title": Settings.model_json_schema().get("title"),
            "setting_count": len(rows),
            "settings": rows,
        }

    if args.validate_profiles:
        profiles_path = args.profiles_path or settings.profiles_path
        if profiles_path is None:
            data["profiles_validation"] = {"ok": False, "error": "no profiles path configured"}
        else:
            data["profiles_validation"] = _validate_profiles(Path(profiles_path), read_profiles_from)
            if not data["profiles_validation"].get("ok"):
                data["ok"] = False

    _print_json(data)
    return 0 if data["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
