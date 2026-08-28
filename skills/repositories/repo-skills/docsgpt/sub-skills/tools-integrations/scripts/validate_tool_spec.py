#!/usr/bin/env python3
"""Offline preflight for an OpenAPI 3.x or Swagger 2.0 API-tool spec.

No URLs are fetched and no actions are executed. The output identifies generated
action names and risky methods for human review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}
RISKY = {"post", "put", "delete", "patch"}


def load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("{"):
        return json.loads(text)
    if yaml is None:
        raise ValueError("PyYAML is required for YAML specs")
    return yaml.safe_load(text)


def action_name(operation: dict[str, Any], method: str, path: str) -> str:
    raw = operation.get("operationId")
    if not raw:
        slug = re.sub(r"[{}]", "", path)
        slug = re.sub(r"[^A-Za-z0-9]", "_", slug)
        slug = re.sub(r"_+", "_", slug).strip("_")
        raw = f"{method}_{slug}"
    return re.sub(r"[^A-Za-z0-9_-]", "_", str(raw))[:64]


def base_url(spec: dict[str, Any]) -> str:
    if spec.get("swagger") == "2.0":
        host = spec.get("host", "")
        if not host:
            return ""
        schemes = spec.get("schemes") or ["https"]
        return f"{schemes[0]}://{host}{spec.get('basePath', '')}".rstrip("/")
    servers = spec.get("servers") or []
    if isinstance(servers, list) and servers and isinstance(servers[0], dict):
        return str(servers[0].get("url", "")).rstrip("/")
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--allow-http", action="store_true", help="Do not fail an explicit non-HTTPS base URL")
    args = parser.parse_args()
    try:
        spec = load(args.spec)
    except Exception as error:
        print(f"ERROR: cannot parse spec: {error}", file=sys.stderr)
        return 2
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(spec, dict):
        errors.append("specification must be an object")
        spec = {}
    openapi = str(spec.get("openapi", ""))
    swagger = str(spec.get("swagger", ""))
    if not (openapi.startswith("3.") or swagger == "2.0"):
        errors.append("expected OpenAPI 3.x or Swagger 2.0")
    paths = spec.get("paths")
    if not isinstance(paths, dict) or not paths:
        errors.append("no API paths defined")
        paths = {}

    root = base_url(spec)
    if not root:
        warnings.append("no base URL found; generated actions will contain relative paths")
    else:
        parsed = urllib.parse.urlsplit(root)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname:
            errors.append(f"invalid base URL {root!r}")
        elif parsed.scheme == "http" and not args.allow_http:
            errors.append("base URL uses HTTP; use --allow-http only for an approved local/test endpoint")
        if parsed.hostname in {"localhost", "127.0.0.1", "169.254.169.254"}:
            warnings.append("base URL targets local/metadata-like host; DocsGPT URL safety may block it")

    names: dict[str, str] = {}
    actions: list[tuple[str, str, str]] = []
    for path, item in paths.items():
        if not isinstance(item, dict):
            warnings.append(f"path {path!r} is not an object")
            continue
        for method in sorted(METHODS):
            operation = item.get(method)
            if not isinstance(operation, dict):
                continue
            name = action_name(operation, method, str(path))
            where = f"{method.upper()} {path}"
            if name in names:
                errors.append(f"duplicate generated action name {name!r}: {names[name]} and {where}")
            else:
                names[name] = where
            if any("$ref" in str(value) and not str(value).startswith("#/") for value in operation.values()):
                warnings.append(f"{where} may contain external/unresolved references")
            actions.append((name, method.upper(), str(path)))

    if not actions:
        errors.append("no supported operations found")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for name, method, path in actions:
        marker = "REVIEW-SIDE-EFFECT" if method.lower() in RISKY else "READ-LIKE"
        print(f"ACTION {name:40} {method:7} {path} [{marker}]")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"Validated {len(actions)} operation(s); review URLs, schemas, credentials and approvals before saving")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
