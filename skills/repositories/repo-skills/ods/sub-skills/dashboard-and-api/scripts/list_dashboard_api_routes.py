#!/usr/bin/env python3
"""List routes from an ODS dashboard-api source tree.

The script is read-only: it imports ``main:app`` from the supplied
``dashboard-api`` directory, inspects FastAPI ``APIRoute`` objects, and prints
method/path/module/auth ownership. It does not start uvicorn, call network
services, launch Docker, or write repository files.

Importing dashboard-api still executes module-level configuration from that
source tree. Set environment variables such as ``DASHBOARD_API_KEY``,
``ODS_INSTALL_DIR``, ``ODS_DATA_DIR``, and ``ODS_EXTENSIONS_DIR`` first when you
need a specific installed-system context.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


def resolve_api_dir(api_dir: Path) -> Path:
    resolved = api_dir.expanduser().resolve()
    if not resolved.is_dir():
        raise SystemExit(f"error: --api-dir is not a directory: {resolved}")
    if not (resolved / "main.py").is_file():
        raise SystemExit(f"error: --api-dir must contain main.py: {resolved}")
    return resolved


def detect_ods_root(api_dir: Path) -> Path | None:
    """Return the ODS product root when api_dir has the standard layout."""
    # Expected suffix: <ods-root>/extensions/services/dashboard-api
    if api_dir.name != "dashboard-api":
        return None
    try:
        services_dir = api_dir.parent
        extensions_dir = services_dir.parent
        ods_root = extensions_dir.parent
    except IndexError:
        return None
    if services_dir.name == "services" and extensions_dir.name == "extensions":
        return ods_root
    return None


def seed_safe_env(api_dir: Path, tmp_data_dir: str) -> None:
    """Seed inert defaults only for variables not already supplied.

    ``security.py`` generates and writes a random API key when
    DASHBOARD_API_KEY is missing. Setting a dummy inspection key avoids that
    import-time side effect while preserving the route dependency graph.
    """
    ods_root = detect_ods_root(api_dir)
    os.environ.setdefault("DASHBOARD_API_KEY", "route-inspection-only")
    os.environ.setdefault("ODS_AGENT_KEY", "")
    os.environ.setdefault("ODS_AGENT_HOST", "127.0.0.1")
    os.environ.setdefault("ODS_AGENT_PORT", "7710")
    os.environ.setdefault("ODS_SESSION_SECRET", "route-inspection-session-secret")
    os.environ.setdefault("GPU_BACKEND", "nvidia")
    os.environ.setdefault("ODS_MODE", "local")
    os.environ.setdefault("ODS_DATA_DIR", tmp_data_dir)
    if ods_root is not None:
        os.environ.setdefault("ODS_INSTALL_DIR", str(ods_root))
        os.environ.setdefault("ODS_EXTENSIONS_DIR", str(ods_root / "extensions" / "services"))


def import_app(api_dir: Path) -> Any:
    sys.path.insert(0, str(api_dir))
    # Avoid accidentally reusing a parent process module named "main".
    sys.modules.pop("main", None)
    try:
        module = importlib.import_module("main")
    except Exception as exc:  # import-time failures need context for users
        raise SystemExit(
            "error: failed to import main:app from dashboard-api. "
            "Install dashboard-api requirements and set any required env vars "
            f"before retrying. Original error: {type(exc).__name__}: {exc}"
        ) from exc
    app = getattr(module, "app", None)
    if app is None:
        raise SystemExit("error: imported main.py but it has no 'app' object")
    return app


def dependency_calls(dependant: Any) -> Iterable[Any]:
    for dep in getattr(dependant, "dependencies", []) or []:
        call = getattr(dep, "call", None)
        if call is not None:
            yield call
        yield from dependency_calls(dep)


def call_name(call: Any) -> str:
    module = getattr(call, "__module__", "")
    name = getattr(call, "__name__", repr(call))
    return f"{module}.{name}" if module else name


def route_requires_bearer(route: Any) -> bool:
    dependant = getattr(route, "dependant", None)
    if dependant is None:
        return False
    return any(call_name(call).endswith("security.verify_api_key") for call in dependency_calls(dependant))


def route_dependencies(route: Any) -> list[str]:
    dependant = getattr(route, "dependant", None)
    if dependant is None:
        return []
    names = sorted({call_name(call) for call in dependency_calls(dependant)})
    return names


def iter_routes(app: Any, include_docs: bool = False) -> list[dict[str, Any]]:
    try:
        from fastapi.routing import APIRoute
    except Exception as exc:
        raise SystemExit(f"error: FastAPI is not importable: {exc}") from exc

    rows: list[dict[str, Any]] = []
    for route in getattr(app, "routes", []):
        if not isinstance(route, APIRoute):
            continue
        path = getattr(route, "path", "")
        if not include_docs and path in {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}:
            continue
        methods = sorted(m for m in (route.methods or []) if m != "HEAD")
        endpoint = getattr(route, "endpoint", None)
        rows.append(
            {
                "methods": methods,
                "path": path,
                "name": getattr(route, "name", ""),
                "module": getattr(endpoint, "__module__", "") if endpoint else "",
                "auth": "bearer" if route_requires_bearer(route) else "route-defined-or-public",
                "dependencies": route_dependencies(route),
            }
        )
    rows.sort(key=lambda item: (item["path"], ",".join(item["methods"]), item["module"], item["name"]))
    return rows


def print_text(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("No FastAPI APIRoute entries found.")
        return
    headers = ("METHODS", "PATH", "AUTH", "MODULE", "NAME")
    data = [
        (",".join(row["methods"]), row["path"], row["auth"], row["module"], row["name"])
        for row in rows
    ]
    widths = [len(header) for header in headers]
    for record in data:
        widths = [max(width, len(str(value))) for width, value in zip(widths, record)]
    fmt = "  ".join(f"{{:<{width}}}" for width in widths)
    print(fmt.format(*headers))
    print(fmt.format(*(('-' * width) for width in widths)))
    for record in data:
        print(fmt.format(*record))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--api-dir",
        type=Path,
        default=Path.cwd(),
        help="dashboard-api source directory containing main.py (default: current directory)",
    )
    parser.add_argument("--json", action="store_true", help="print route data as JSON")
    parser.add_argument(
        "--include-docs",
        action="store_true",
        help="include FastAPI docs/openapi/redoc routes in the output",
    )
    args = parser.parse_args()

    api_dir = resolve_api_dir(args.api_dir)
    print(
        "warning: importing dashboard-api executes module-level configuration; "
        "set env vars first if you need a specific installed-system context.",
        file=sys.stderr,
    )
    with tempfile.TemporaryDirectory(prefix="ods-dashboard-routes-") as tmpdir:
        seed_safe_env(api_dir, tmpdir)
        app = import_app(api_dir)
        rows = iter_routes(app, include_docs=args.include_docs)

    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print_text(rows)
        print(f"\nRoute count: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
