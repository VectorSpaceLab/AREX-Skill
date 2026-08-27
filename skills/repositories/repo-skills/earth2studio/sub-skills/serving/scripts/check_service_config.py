#!/usr/bin/env python3
"""Validate Earth2Studio serving configuration without contacting services."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default=None)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--require-redis", action="store_true")
    parser.add_argument("--require-object-storage", action="store_true")
    parser.add_argument("--require-auth", action="store_true")
    parser.add_argument("--nensemble", type=int)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    values = dict(os.environ)
    if args.env_file:
        for line in args.env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1); values.setdefault(key.strip(), value.strip().strip("\"'"))
    errors: list[str] = []
    url = args.api_url or values.get("EARTH2STUDIO_API_URL", "http://localhost:8000")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc: errors.append("api URL must be an absolute http(s) URL")
    if args.require_redis and not values.get("REDIS_HOST"): errors.append("REDIS_HOST is required")
    if args.require_object_storage and values.get("OBJECT_STORAGE_ENABLED", "false").lower() != "true": errors.append("OBJECT_STORAGE_ENABLED must be true")
    if args.require_auth and not values.get("EARTH2STUDIO_API_TOKEN"): errors.append("EARTH2STUDIO_API_TOKEN is required")
    if args.nensemble is not None and args.nensemble < 1: errors.append("nensemble must be >= 1")
    if args.batch_size is not None and args.batch_size < 1: errors.append("batch-size must be >= 1")
    if args.nensemble is not None and args.batch_size is not None and args.batch_size > args.nensemble: errors.append("batch-size must not exceed nensemble")
    result = {"ok": not errors, "api_url": f"{parsed.scheme}://{parsed.hostname or '<invalid>'}", "errors": errors, "secret_values_printed": False, "offline": True}
    if args.json: print(json.dumps(result, sort_keys=True))
    else:
        print("Earth2Studio serving configuration: " + ("OK" if not errors else "INCOMPLETE"))
        for error in errors: print("ERROR:", error)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
