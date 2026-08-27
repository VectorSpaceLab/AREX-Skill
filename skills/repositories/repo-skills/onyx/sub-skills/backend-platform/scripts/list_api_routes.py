from __future__ import annotations

import argparse
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any


def _resolve_backend_dir(repo_root: Path) -> Path:
    root = repo_root.expanduser().resolve()
    backend_dir = root / "backend"
    if backend_dir.is_dir():
        return backend_dir
    if (root / "onyx").is_dir():
        return root
    raise FileNotFoundError(
        f"Could not find a backend directory under {root}. Pass the repository root or the backend directory."
    )


def _add_backend_to_sys_path(backend_dir: Path) -> None:
    backend_path = str(backend_dir)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


@asynccontextmanager
async def _noop_lifespan(app: Any) -> AsyncIterator[None]:
    del app
    yield


def _load_application() -> Any:
    try:
        with redirect_stdout(sys.stderr):
            from onyx.main import get_application
    except Exception as exc:  # pragma: no cover - exercised through CLI failure paths
        raise RuntimeError(
            "Failed to import onyx.main.get_application. Check the backend path, installed dependencies, and required environment variables."
        ) from exc

    try:
        with redirect_stdout(sys.stderr):
            return get_application(lifespan_override=_noop_lifespan)
    except Exception as exc:  # pragma: no cover - exercised through CLI failure paths
        raise RuntimeError(
            "Failed to build the FastAPI application. Check environment variables, optional service credentials, and startup dependencies."
        ) from exc


def _iter_route_rows(app: Any) -> list[tuple[str, str, str]]:
    from fastapi.routing import APIRoute

    rows: list[tuple[str, str, str]] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        methods = sorted(
            method for method in route.methods if method not in {"HEAD", "OPTIONS"}
        )
        if not methods:
            methods = sorted(route.methods)
        for method in methods:
            rows.append((method, route.path, route.name))
    return sorted(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List Onyx FastAPI routes without starting the API server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the repository root or backend directory",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        backend_dir = _resolve_backend_dir(Path(args.repo_root))
        _add_backend_to_sys_path(backend_dir)
        app = _load_application()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        for method, path, name in _iter_route_rows(app):
            print(f"{method:<6} {path} {name}")
    except BrokenPipeError:
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
