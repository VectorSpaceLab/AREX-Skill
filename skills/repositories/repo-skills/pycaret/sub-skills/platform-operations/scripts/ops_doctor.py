#!/usr/bin/env python3
"""Non-secret PyCaret platform operations doctor.

Inspects pycaret_server Settings and checks DB, Redis (when selected), and
storage reachability without printing secret values. The default checks avoid
writing to storage. Use pycaret-server doctor for the package's built-in smoke;
use this helper when you also want redacted configuration context.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse, urlunparse


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect PyCaret server settings and run non-secret DB/storage checks."
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--no-db", action="store_true", help="skip database SELECT 1 check")
    parser.add_argument("--no-storage", action="store_true", help="skip storage backend check")
    parser.add_argument("--no-redis", action="store_true", help="skip Redis check")
    parser.add_argument(
        "--s3-head-bucket",
        action="store_true",
        help="for s3/minio storage, call head_bucket as a read-only network check",
    )
    return parser.parse_args()


def _redact_url(value: str | None) -> str | None:
    if not value:
        return value
    try:
        parsed = urlparse(value)
    except Exception:
        return "<unparseable>"
    if not parsed.scheme:
        return value
    host = parsed.hostname or ""
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    if parsed.username:
        user = quote(unquote(parsed.username), safe="")
        netloc = f"{user}:***@{host}"
    else:
        netloc = host
    return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))


def _status(ok: bool, detail: str, **extra: Any) -> dict[str, Any]:
    return {"ok": ok, "detail": detail, **extra}


def _load_settings() -> tuple[Any | None, dict[str, Any]]:
    try:
        from pycaret_server.config import get_settings

        settings = get_settings()
    except Exception as exc:  # noqa: BLE001
        return None, _status(False, f"could not import/load pycaret_server settings: {type(exc).__name__}: {exc}")
    summary = {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "debug": bool(settings.debug),
        "database_url": _redact_url(settings.database_url),
        "jwt_secret_set": bool(settings.jwt_secret),
        "secrets_key_set": bool(settings.secrets_key),
        "artifact_dir": str(settings.artifact_dir),
        "cors_origins": list(settings.cors_origins),
        "runs_backend": settings.runs_backend,
        "redis_url": _redact_url(settings.redis_url),
        "worker_queues": [q.strip() for q in (settings.worker_queues or "default").split(",") if q.strip()],
        "storage_backend": settings.storage_backend,
        "storage_bucket": settings.storage_bucket,
        "storage_endpoint_url": _redact_url(settings.storage_endpoint_url),
        "storage_region": settings.storage_region,
        "storage_access_key_set": bool(settings.storage_access_key),
        "storage_secret_key_set": bool(settings.storage_secret_key),
        "notebook_backend": settings.notebook_backend,
        "notebook_image_set": bool(settings.notebook_image),
        "smtp_configured": bool(settings.smtp_host),
    }
    return settings, summary


def _check_db(settings: Any) -> dict[str, Any]:
    url = str(settings.database_url)
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import make_url
    except Exception as exc:  # noqa: BLE001
        return _status(False, f"sqlalchemy import failed: {type(exc).__name__}: {exc}")

    try:
        sa_url = make_url(url)
    except Exception:
        sa_url = None
    if sa_url is not None and sa_url.get_backend_name() == "sqlite":
        # Avoid creating a new SQLite file as a side effect of a health check.
        db_name = sa_url.database
        if db_name and db_name not in (":memory:", ""):
            db_path = Path(db_name)
            if not db_path.exists():
                return _status(False, "sqlite database file does not exist; run init/migrate before checking", path=str(db_path))
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return _status(True, "database SELECT 1 succeeded", url=_redact_url(url))
    except Exception as exc:  # noqa: BLE001
        return _status(False, f"database check failed: {type(exc).__name__}: {exc}", url=_redact_url(url))


def _check_redis(settings: Any) -> dict[str, Any]:
    if settings.runs_backend != "redis":
        return _status(True, f"redis skipped because runs_backend={settings.runs_backend}", skipped=True)
    try:
        from pycaret_server.runs.queue_redis import is_healthy

        ok = bool(is_healthy(settings.redis_url))
        return _status(ok, "redis ping succeeded" if ok else "redis ping failed", url=_redact_url(settings.redis_url))
    except Exception as exc:  # noqa: BLE001
        return _status(False, f"redis check failed: {type(exc).__name__}: {exc}", url=_redact_url(settings.redis_url))


def _check_storage(settings: Any, *, s3_head_bucket: bool) -> dict[str, Any]:
    backend = (settings.storage_backend or "local").lower()
    if backend == "local":
        root = Path(settings.artifact_dir)
        if not root.exists():
            return _status(False, "local artifact directory does not exist", path=str(root))
        if not root.is_dir():
            return _status(False, "local artifact path is not a directory", path=str(root))
        return _status(
            os.access(root, os.R_OK | os.X_OK),
            "local artifact directory is accessible" if os.access(root, os.R_OK | os.X_OK) else "local artifact directory is not readable/searchable",
            path=str(root),
            writable=bool(os.access(root, os.W_OK)),
        )
    if backend in {"s3", "minio"}:
        if not settings.storage_bucket:
            return _status(False, "storage bucket is required for s3/minio")
        if not s3_head_bucket:
            return _status(
                True,
                "s3/minio configuration present; pass --s3-head-bucket for read-only bucket reachability check",
                bucket=settings.storage_bucket,
                endpoint=_redact_url(settings.storage_endpoint_url),
            )
        try:
            import boto3  # type: ignore[import-not-found]

            client = boto3.client(
                "s3",
                region_name=settings.storage_region,
                endpoint_url=settings.storage_endpoint_url,
                aws_access_key_id=settings.storage_access_key,
                aws_secret_access_key=settings.storage_secret_key,
            )
            client.head_bucket(Bucket=settings.storage_bucket)
            return _status(True, "s3/minio head_bucket succeeded", bucket=settings.storage_bucket, endpoint=_redact_url(settings.storage_endpoint_url))
        except ImportError:
            return _status(False, "boto3 is not installed; install pycaret-server[s3]")
        except Exception as exc:  # noqa: BLE001
            return _status(False, f"s3/minio head_bucket failed: {type(exc).__name__}: {exc}", bucket=settings.storage_bucket, endpoint=_redact_url(settings.storage_endpoint_url))
    return _status(False, f"unknown storage backend {backend!r}")


def _print_human(result: dict[str, Any]) -> None:
    settings = result["settings"]
    print("PyCaret operations doctor")
    print("settings:")
    for key in sorted(settings):
        print(f"  {key}: {settings[key]}")
    print("checks:")
    for name, check in result["checks"].items():
        label = "OK" if check.get("ok") else "FAIL"
        print(f"  {name:<8} {label}  {check.get('detail')}")


def main() -> int:
    args = _parse_args()
    settings, settings_summary = _load_settings()
    result: dict[str, Any] = {"settings": settings_summary, "checks": {}}
    if settings is None:
        result["checks"]["settings"] = settings_summary
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(settings_summary["detail"], file=sys.stderr)
        return 2

    if not args.no_db:
        result["checks"]["database"] = _check_db(settings)
    if not args.no_redis:
        result["checks"]["redis"] = _check_redis(settings)
    if not args.no_storage:
        result["checks"]["storage"] = _check_storage(settings, s3_head_bucket=args.s3_head_bucket)

    ok = all(check.get("ok") for check in result["checks"].values())
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_human(result)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
