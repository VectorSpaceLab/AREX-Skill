#!/usr/bin/env python3
"""Shared smoke checker for the Unstract repo skill.

This script is intentionally conservative:
- It verifies the shared Python package family.
- It can optionally import the backend route and hosted-MCP modules with safe
  test defaults.
- It can optionally validate a tool-registry config directory without pulling
  images or writing output.

Run it from a checkout of the repository or pass `--repo-root` explicitly.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as md
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Iterable

DEFAULT_BACKEND_ENV = {
    "DJANGO_SETTINGS_MODULE": "backend.settings.test",
    "DB_SCHEMA": "public",
    "DJANGO_SECRET_KEY": "test-secret-key-not-for-production",
    "ENCRYPTION_KEY": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
    "CELERY_BROKER_BASE_URL": "redis://localhost:6379",
    "CELERY_BROKER_USER": "guest",
    "CELERY_BROKER_PASS": "guest",
    "SYSTEM_ADMIN_USERNAME": "admin",
    "SYSTEM_ADMIN_PASSWORD": "admin",
    "SYSTEM_ADMIN_EMAIL": "admin@example.com",
    "ENABLE_LOG_HISTORY": "False",
    "INDEXING_FLAG_TTL": "3600",
    "STRUCTURE_TOOL_IMAGE_URL": "docker:test",
    "STRUCTURE_TOOL_IMAGE_NAME": "test-structure-tool",
    "STRUCTURE_TOOL_IMAGE_TAG": "test",
    "WORKFLOW_EXECUTION_DIR_PREFIX": "/tmp/unstract-workflow-exec",
}

SHARED_DISTS = [
    "unstract-sdk1",
    "unstract-core",
    "unstract-connectors",
    "unstract-filesystem",
    "unstract-flags",
    "unstract-tool-registry",
    "unstract-tool-sandbox",
    "unstract-workflow-execution",
]

SOURCE_ROOTS = [
    Path("backend"),
    Path("unstract/sdk1/src"),
    Path("unstract/core/src"),
    Path("unstract/connectors/src"),
    Path("unstract/filesystem/src"),
    Path("unstract/flags/src"),
    Path("unstract/tool-registry/src"),
    Path("unstract/tool-sandbox/src"),
    Path("unstract/workflow-execution/src"),
]


def _repo_root(path: str | None) -> Path:
    return Path(path or Path.cwd()).resolve()


def _add_path(path: Path) -> None:
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)


def _add_source_roots(repo_root: Path) -> None:
    # Prepend the declared roots in order so backend stays ahead of any later
    # worker-path additions that could otherwise shadow backend packages.
    roots = [repo_root / rel for rel in SOURCE_ROOTS if (repo_root / rel).exists()]
    for root in reversed(roots):
        _add_path(root)


def _print_versions(names: Iterable[str]) -> None:
    for name in names:
        try:
            version = md.version(name)
        except md.PackageNotFoundError:
            print(f"- {name}: MISSING (source import may still succeed)")
        else:
            print(f"- {name}: {version}")


def _apply_backend_defaults() -> None:
    for key, value in DEFAULT_BACKEND_ENV.items():
        os.environ.setdefault(key, value)


def _import_and_show(name: str):
    module = importlib.import_module(name)
    print(f"- {name}: {getattr(module, '__file__', '<namespace>')}")
    return module


def _check_backend(repo_root: Path) -> None:
    print("\n[backend]")
    _apply_backend_defaults()
    backend_dir = repo_root / "backend"
    if backend_dir.exists():
        _add_path(backend_dir)

    import django  # noqa: WPS433

    django.setup()

    from django.conf import settings  # noqa: WPS433

    base_urls = _import_and_show("backend.base_urls")
    public_urls_v2 = _import_and_show("backend.public_urls_v2")
    tenant_urls_v2 = _import_and_show("backend.urls_v2")
    mcp_urls = _import_and_show("mcp_server.urls")
    registry = _import_and_show("mcp_server.registry")

    print(f"- settings module: {os.environ['DJANGO_SETTINGS_MODULE']}")
    print(f"- backend path: {backend_dir}")
    print(f"- PATH_PREFIX: {settings.PATH_PREFIX}")
    print(f"- API_DEPLOYMENT_PATH_PREFIX: {settings.API_DEPLOYMENT_PATH_PREFIX}")
    print(f"- MCP_PLATFORM_SERVER_ENABLED: {settings.MCP_PLATFORM_SERVER_ENABLED}")
    print(f"- base urlpatterns: {len(base_urls.urlpatterns)}")
    print(f"- public v2 urlpatterns: {len(public_urls_v2.urlpatterns)}")
    print(f"- tenant v2 urlpatterns: {len(tenant_urls_v2.urlpatterns)}")
    print(f"- deployment MCP urlpatterns: {len(mcp_urls.urlpatterns)}")
    print(f"- deployment MCP tools: {len(registry.DEPLOYMENT_TOOLS.names())}")
    print(f"- platform MCP tools: {len(registry.PLATFORM_TOOLS.names())}")


def _check_tool_registry(config_dir: Path) -> None:
    print("\n[tool-registry]")
    registry_file = config_dir / "registry.yaml"
    private_tools = config_dir / "private_tools.json"
    public_tools = config_dir / "public_tools.json"

    if not registry_file.exists():
        raise FileNotFoundError(f"registry file not found: {registry_file}")

    try:
        import yaml  # noqa: WPS433
    except Exception as exc:  # pragma: no cover - dependency issue surfaced directly
        raise RuntimeError("PyYAML is required for tool-registry validation") from exc

    data = yaml.safe_load(registry_file.read_text(encoding="utf-8")) or {}
    tools = data.get("tools", [])
    if not isinstance(tools, list):
        raise TypeError("registry.yaml: 'tools' must be a list")
    bad = [tool for tool in tools if not isinstance(tool, str) or not tool.strip()]
    if bad:
        raise ValueError(f"registry.yaml: invalid tool entries: {bad!r}")

    print(f"- config dir: {config_dir}")
    print(f"- registry tools: {len(tools)}")
    if tools:
        print(f"- first tool: {tools[0]}")
    for file in (private_tools, public_tools):
        if file.exists():
            loaded = json.loads(file.read_text(encoding="utf-8") or "{}")
            print(f"- {file.name}: {len(loaded)} entries")
        else:
            print(f"- {file.name}: missing (ok for a dry validation)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect shared Unstract packages")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root to use for backend imports and config lookups.",
    )
    parser.add_argument(
        "--backend",
        action="store_true",
        help="Also import backend route and hosted-MCP modules.",
    )
    parser.add_argument(
        "--tool-registry",
        action="store_true",
        help="Also validate a tool-registry config directory.",
    )
    parser.add_argument(
        "--tool-registry-config",
        type=Path,
        default=None,
        help="Directory containing registry.yaml, private_tools.json, and public_tools.json.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = _repo_root(str(args.repo_root) if args.repo_root else None)

    print("[shared-packages]")
    _add_source_roots(repo_root)
    _print_versions(SHARED_DISTS)

    workflow_mod = _import_and_show("unstract.workflow_execution.workflow_execution")
    print("- WorkflowExecutionService signature:")
    print(f"  {inspect.signature(workflow_mod.WorkflowExecutionService)}")

    if args.backend:
        _check_backend(repo_root)

    if args.tool_registry:
        config_dir_raw = args.tool_registry_config or os.environ.get(
            "TOOL_REGISTRY_CONFIG_PATH"
        )
        if not config_dir_raw:
            raise SystemExit(
                "tool-registry validation requested but no config dir was supplied. "
                "Set TOOL_REGISTRY_CONFIG_PATH or pass --tool-registry-config."
            )
        _check_tool_registry(Path(config_dir_raw).resolve())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
