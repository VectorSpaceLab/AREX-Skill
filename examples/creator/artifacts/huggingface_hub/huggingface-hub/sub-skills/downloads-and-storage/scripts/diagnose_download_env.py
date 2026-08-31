#!/usr/bin/env python3
"""Read-only Hugging Face download/cache configuration diagnostic.

The helper performs no network requests, downloads, installs, credential reads,
or deletions. It reports effective import-time configuration, cache path state,
free space, token *presence* (never a token value), Xet availability, and an
optional `scan_cache_dir` summary.

Examples:
    python diagnose_download_env.py --pretty
    python diagnose_download_env.py --scan-cache --pretty
    python diagnose_download_env.py --cache-dir /path/to/hub/cache --scan-cache
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect effective huggingface_hub download, cache, offline, symlink, "
            "and Xet settings without contacting the Hub or changing files."
        )
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Hub repository cache to report/scan instead of the effective HF_HUB_CACHE.",
    )
    parser.add_argument(
        "--scan-cache",
        action="store_true",
        help="Read the selected Hub cache with scan_cache_dir and summarize warnings/incomplete files.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser


def _path_state(path: str | Path) -> dict[str, Any]:
    target = Path(path).expanduser()
    probe = target
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent

    state: dict[str, Any] = {
        "path": str(target),
        "exists": target.exists(),
        "kind": "directory" if target.is_dir() else "file" if target.is_file() else "missing",
        "nearest_existing_parent": str(probe),
        "writable_if_exists": os.access(target, os.W_OK) if target.exists() else None,
    }
    try:
        usage = shutil.disk_usage(probe)
    except OSError as error:
        state["disk_usage_error"] = f"{type(error).__name__}: {error}"
    else:
        state["disk_total_bytes"] = usage.total
        state["disk_used_bytes"] = usage.used
        state["disk_free_bytes"] = usage.free
    return state


def _env_presence(name: str) -> dict[str, Any]:
    value = os.environ.get(name)
    return {"set": value is not None, "nonempty": bool(value)}


def _safe_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def _safe_endpoint(value: str) -> str:
    """Keep endpoint identity while removing userinfo and query credentials."""
    parsed = urlsplit(value)
    host = parsed.hostname or ""
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    netloc = f"<redacted>@{host}" if parsed.username is not None or parsed.password is not None else host
    # Query strings and fragments can carry access material even without URL userinfo.
    return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))


def _load_hub() -> tuple[Any, Any, Any, Any]:
    try:
        import huggingface_hub
        from huggingface_hub import constants, scan_cache_dir
        from huggingface_hub.utils._runtime import is_xet_available
    except ImportError as error:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": (
                        "huggingface_hub is not importable in this Python environment: "
                        f"{type(error).__name__}: {error}"
                    ),
                    "python": sys.version.split()[0],
                }
            ),
            file=sys.stdout,
        )
        raise SystemExit(2) from error
    return huggingface_hub, constants, scan_cache_dir, is_xet_available


def _scan_summary(scan_cache_dir: Any, cache_dir: Path) -> dict[str, Any]:
    try:
        report = scan_cache_dir(cache_dir)
    except Exception as error:
        return {
            "ok": False,
            "error_type": type(error).__name__,
            "error": str(error),
        }

    revisions = sum(len(repo.revisions) for repo in report.repos)
    return {
        "ok": True,
        "repository_count": len(report.repos),
        "revision_count": revisions,
        "size_on_disk_bytes": report.size_on_disk,
        "incomplete_file_count": len(report.incomplete_files),
        "incomplete_size_on_disk_bytes": report.incomplete_size_on_disk,
        "warning_count": len(report.warnings),
        "warnings": [str(warning) for warning in report.warnings],
    }


def main() -> int:
    args = _parser().parse_args()
    huggingface_hub, constants, scan_cache_dir, is_xet_available = _load_hub()

    hub_cache = (args.cache_dir or Path(constants.HF_HUB_CACHE)).expanduser()
    xet_cache = Path(constants.HF_XET_CACHE).expanduser()
    token_path = Path(constants.HF_TOKEN_PATH).expanduser()

    report: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "network_requests": False,
        "python": sys.version.split()[0],
        "package": {
            "distribution": "huggingface_hub",
            "distribution_version": _safe_version("huggingface_hub"),
            "module_version": getattr(huggingface_hub, "__version__", None),
        },
        "effective_import_time_settings": {
            "endpoint": _safe_endpoint(constants.ENDPOINT),
            "offline": bool(constants.HF_HUB_OFFLINE),
            "disable_symlinks": bool(constants.HF_HUB_DISABLE_SYMLINKS),
            "disable_symlink_warning": bool(constants.HF_HUB_DISABLE_SYMLINKS_WARNING),
            "disable_implicit_token": bool(constants.HF_HUB_DISABLE_IMPLICIT_TOKEN),
            "disable_xet": bool(constants.HF_HUB_DISABLE_XET),
            "xet_high_performance": bool(constants.HF_XET_HIGH_PERFORMANCE),
            "etag_timeout_seconds": constants.HF_HUB_ETAG_TIMEOUT,
            "download_timeout_seconds": constants.HF_HUB_DOWNLOAD_TIMEOUT,
        },
        "paths": {
            "hf_home": _path_state(constants.HF_HOME),
            "hub_cache": _path_state(hub_cache),
            "xet_cache": _path_state(xet_cache),
            "token_file": {
                "configured": True,
                "exists": token_path.is_file(),
            },
        },
        "credentials": {
            "hf_token_environment": _env_presence("HF_TOKEN"),
            "stored_token_file_present": token_path.is_file(),
            "token_value_read": False,
        },
        "xet": {
            "hf_xet_distribution_version": _safe_version("hf-xet"),
            "module_discoverable": importlib.util.find_spec("hf_xet") is not None,
            "available_to_huggingface_hub": bool(is_xet_available()),
            "chunk_cache_size_environment": os.environ.get("HF_XET_CHUNK_CACHE_SIZE_BYTES"),
            "shard_cache_limit_environment": os.environ.get("HF_XET_SHARD_CACHE_SIZE_LIMIT"),
            "range_gets_environment": os.environ.get("HF_XET_NUM_CONCURRENT_RANGE_GETS"),
            "sequential_write_environment_set": "HF_XET_RECONSTRUCT_WRITE_SEQUENTIALLY" in os.environ,
        },
        "notes": [
            "Environment variables are consumed when huggingface_hub is imported; restart Python after changing them.",
            "Cache metadata, refs, and tree listings are not proof that every payload file is materialized.",
            "Use dry-run cleanup commands and inspect their selection before any cache deletion.",
        ],
    }

    if args.scan_cache:
        report["cache_scan"] = _scan_summary(scan_cache_dir, hub_cache)
        if not report["cache_scan"]["ok"]:
            report["ok"] = False

    json.dump(report, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
