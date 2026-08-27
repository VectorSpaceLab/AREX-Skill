#!/usr/bin/env python3
"""Validate TaskingAI environment files without starting services.

The checker is safe by default: it reads key=value files, validates required
variables for TaskingAI service roles, and never contacts Docker, databases,
object storage, model providers, or remote URLs.

Examples:
  python check_taskingai_env.py --env-file .env --profile compose
  python check_taskingai_env.py --env-file backend.env --profile backend-api
  python check_taskingai_env.py --env-file plugin.env --profile plugin
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

SECRET_HINTS = ("KEY", "SECRET", "PASSWORD", "TOKEN")
HEX64_RE = re.compile(r"^[a-fA-F0-9]{64}$")
URL_RE = re.compile(r"^https?://")

PROFILE_REQUIRED: Mapping[str, Sequence[str]] = {
    "compose": (
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "REDIS_PASSWORD",
        "REDIS_DB",
        "AES_ENCRYPTION_KEY",
        "JWT_SECRET_KEY",
        "HOST_URL",
        "OBJECT_STORAGE_TYPE",
        "PROJECT_ID",
        "DEFAULT_ADMIN_USERNAME",
        "DEFAULT_ADMIN_PASSWORD",
    ),
    "backend-api": (
        "TASKINGAI_INFERENCE_URL",
        "TASKINGAI_PLUGIN_URL",
        "POSTGRES_URL",
        "AES_ENCRYPTION_KEY",
        "OBJECT_STORAGE_TYPE",
        "PATH_TO_VOLUME",
        "PROJECT_ID",
    ),
    "backend-web": (
        "TASKINGAI_INFERENCE_URL",
        "TASKINGAI_PLUGIN_URL",
        "POSTGRES_URL",
        "AES_ENCRYPTION_KEY",
        "JWT_SECRET_KEY",
        "DEFAULT_ADMIN_USERNAME",
        "DEFAULT_ADMIN_PASSWORD",
        "OBJECT_STORAGE_TYPE",
        "PATH_TO_VOLUME",
        "PROJECT_ID",
    ),
    "inference": ("AES_ENCRYPTION_KEY",),
    "plugin": ("AES_ENCRYPTION_KEY", "OBJECT_STORAGE_TYPE", "PATH_TO_VOLUME"),
}

S3_REQUIRED = (
    "S3_ENDPOINT",
    "S3_ACCESS_KEY_ID",
    "S3_ACCESS_KEY_SECRET",
    "S3_BUCKET_NAME",
)
PLUGIN_S3_EXTRA = ("S3_IMAGE_BUCKET_NAME",)
LOCAL_REQUIRED = ("HOST_URL",)


def parse_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            raise ValueError(f"{path}:{line_no}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            raise ValueError(f"{path}:{line_no}: empty key")
        values[key] = value
    return values


def redacted(values: Mapping[str, str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for key, value in values.items():
        if any(hint in key.upper() for hint in SECRET_HINTS):
            out[key] = "<set>" if value else "<empty>"
        else:
            out[key] = value
    return out


def require(values: Mapping[str, str], keys: Iterable[str], errors: List[str], label: str) -> None:
    for key in keys:
        if not values.get(key):
            errors.append(f"missing {label} variable: {key}")


def warn_if_default_secret(values: Mapping[str, str], warnings: List[str]) -> None:
    for key in ("AES_ENCRYPTION_KEY", "JWT_SECRET_KEY", "DEFAULT_ADMIN_PASSWORD"):
        value = values.get(key, "")
        if key in ("AES_ENCRYPTION_KEY", "JWT_SECRET_KEY") and value and not HEX64_RE.match(value):
            warnings.append(f"{key} is set but is not a 64-character hex string")
        if key == "DEFAULT_ADMIN_PASSWORD" and value in {"TaskingAI321", "admin", "password"}:
            warnings.append("DEFAULT_ADMIN_PASSWORD appears to be a documented/default value; rotate it for non-local deployments")


def validate(values: Mapping[str, str], profile: str) -> Dict[str, object]:
    errors: List[str] = []
    warnings: List[str] = []
    require(values, PROFILE_REQUIRED[profile], errors, profile)

    storage = values.get("OBJECT_STORAGE_TYPE", "").lower()
    if storage:
        if storage == "s3":
            require(values, S3_REQUIRED, errors, "s3 storage")
            if profile == "plugin":
                # plugin/config.py falls back to S3_BUCKET_NAME when S3_IMAGE_BUCKET_NAME is absent.
                if not values.get("S3_IMAGE_BUCKET_NAME") and not values.get("S3_BUCKET_NAME"):
                    require(values, PLUGIN_S3_EXTRA, errors, "plugin s3 image storage")
            if not values.get("S3_BUCKET_PUBLIC_DOMAIN"):
                warnings.append("S3_BUCKET_PUBLIC_DOMAIN is empty; generated URLs may use service-specific fallbacks or be unavailable publicly")
        elif storage == "local":
            if profile in {"compose", "backend-api", "backend-web", "plugin"}:
                require(values, LOCAL_REQUIRED, errors, "local storage")
            if not values.get("PATH_TO_VOLUME") and profile in {"backend-api", "backend-web", "plugin"}:
                errors.append("local storage requires PATH_TO_VOLUME for backend/plugin file persistence")
        else:
            errors.append("OBJECT_STORAGE_TYPE must be either 'local' or 's3'")

    for key in ("HOST_URL", "TASKINGAI_INFERENCE_URL", "TASKINGAI_PLUGIN_URL", "S3_ENDPOINT"):
        value = values.get(key)
        if value and key != "S3_ENDPOINT" and not URL_RE.match(value):
            warnings.append(f"{key} does not start with http:// or https://")

    if values.get("TASKINGAI_INFERENCE_URL") and "localhost" in values["TASKINGAI_INFERENCE_URL"]:
        warnings.append("TASKINGAI_INFERENCE_URL uses localhost; inside Docker Compose it should usually be the inference service DNS name, not the host loopback")
    if values.get("TASKINGAI_PLUGIN_URL") and "localhost" in values["TASKINGAI_PLUGIN_URL"]:
        warnings.append("TASKINGAI_PLUGIN_URL uses localhost; inside Docker Compose it should usually be the plugin service DNS name, not the host loopback")

    warn_if_default_secret(values, warnings)
    return {"profile": profile, "ok": not errors, "errors": errors, "warnings": warnings, "redacted_values": redacted(values)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate TaskingAI service environment variables")
    parser.add_argument("--env-file", required=True, help="Path to a dotenv-style KEY=VALUE file")
    parser.add_argument("--profile", choices=sorted(PROFILE_REQUIRED), default="compose")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)

    try:
        values = parse_env_file(Path(args.env_file))
        result = validate(values, args.profile)
    except Exception as exc:
        print(f"check_taskingai_env.py: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"TaskingAI env profile: {result['profile']}")
        print(f"Status: {'ok' if result['ok'] else 'failed'}")
        for warning in result["warnings"]:  # type: ignore[index]
            print(f"WARNING: {warning}")
        for error in result["errors"]:  # type: ignore[index]
            print(f"ERROR: {error}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
