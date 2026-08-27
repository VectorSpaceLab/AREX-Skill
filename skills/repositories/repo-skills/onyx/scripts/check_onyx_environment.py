#!/usr/bin/env python3
"""Read-only sanity checks for an Onyx checkout.

The script checks repository layout, package metadata, optional Python source
imports, and host tool availability. It never installs packages, starts
services, contacts the network, or mutates Docker/Kubernetes/database state.

Example:
    python skills/onyx/scripts/check_onyx_environment.py --repo-root .
    python skills/onyx/scripts/check_onyx_environment.py --repo-root . --check-python-imports
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any


REQUIRED_PATHS = [
    "AGENTS.md",
    "pyproject.toml",
    "uv.lock",
    "backend/AGENTS.md",
    "backend/onyx",
    "backend/tests",
    "web/AGENTS.md",
    "web/package.json",
    "mobile/AGENTS.md",
    "mobile/package.json",
    "cli/README.md",
    "tools/ods/README.md",
    "deployment/docker_compose/README.md",
]

OPTIONAL_TOOLS = [
    "uv",
    "python3.13",
    "bun",
    "go",
    "docker",
    "psql",
    "helm",
    "kubectl",
    "gh",
    "nvidia-smi",
]

IMPORT_MODULES = [
    "onyx",
    "onyx.configs.constants",
    "onyx.connectors.interfaces",
    "onyx.chat.process_message",
    "onyx.indexing.models",
    "onyx.document_index.factory",
    "onyx.server.features.persona.api",
]


def _status(ok: bool, detail: str) -> dict[str, Any]:
    return {"ok": ok, "detail": detail}


def _repo_path(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise argparse.ArgumentTypeError(f"repo root does not exist: {value}")
    return path


def check_paths(repo_root: Path) -> dict[str, dict[str, Any]]:
    return {
        rel: _status((repo_root / rel).exists(), "present" if (repo_root / rel).exists() else "missing")
        for rel in REQUIRED_PATHS
    }


def check_pyproject(repo_root: Path) -> dict[str, Any]:
    text = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    facts: dict[str, Any] = {
        "requires_python_3_13": 'requires-python = ">=3.13"' in text,
        "uv_package_false": "package = false" in text,
        "has_backend_group": "backend = [" in text,
        "has_dev_group": "dev = [" in text,
        "has_model_server_group": "model_server = [" in text,
    }
    return facts


def check_tools() -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for tool in OPTIONAL_TOOLS:
        path = shutil.which(tool)
        results[tool] = _status(path is not None, "found" if path else "not found on PATH")
    return results


def check_imports(repo_root: Path) -> dict[str, dict[str, Any]]:
    backend_root = repo_root / "backend"
    if not backend_root.exists():
        return {name: _status(False, "backend directory missing") for name in IMPORT_MODULES}

    sys.path.insert(0, str(backend_root))
    results: dict[str, dict[str, Any]] = {}
    for module_name in IMPORT_MODULES:
        try:
            # Some Onyx imports configure logging and emit startup notices. Keep
            # JSON mode parseable by forwarding import-time stdout to stderr.
            with contextlib.redirect_stdout(sys.stderr):
                module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - diagnostic tool reports import failures.
            results[module_name] = _status(False, f"{type(exc).__name__}: {exc}")
        else:
            module_file = getattr(module, "__file__", "built-in or namespace")
            results[module_name] = _status(True, str(module_file))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Onyx checkout sanity checks")
    parser.add_argument("--repo-root", type=_repo_path, default=Path.cwd(), help="Onyx repository root")
    parser.add_argument(
        "--check-python-imports",
        action="store_true",
        help="Temporarily add <repo-root>/backend to sys.path and import selected Onyx modules",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()

    repo_root: Path = args.repo_root
    result: dict[str, Any] = {
        "repo_root_basename": repo_root.name,
        "python_version": sys.version.split()[0],
        "paths": check_paths(repo_root),
        "pyproject": check_pyproject(repo_root) if (repo_root / "pyproject.toml").exists() else {},
        "tools": check_tools(),
    }
    if args.check_python_imports:
        result["imports"] = check_imports(repo_root)

    has_missing_required_path = any(not row["ok"] for row in result["paths"].values())
    has_failed_import = any(
        not row["ok"] for row in result.get("imports", {}).values()
    )

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Onyx environment check for repository: {repo_root.name}")
        print(f"Python: {result['python_version']}")
        print("\nRequired paths:")
        for rel, row in result["paths"].items():
            marker = "OK" if row["ok"] else "MISS"
            print(f"  {marker:4} {rel}")
        print("\npyproject facts:")
        for key, value in result["pyproject"].items():
            print(f"  {key}: {value}")
        print("\nOptional tools:")
        for tool, row in result["tools"].items():
            marker = "OK" if row["ok"] else "WARN"
            print(f"  {marker:4} {tool}: {row['detail']}")
        if args.check_python_imports:
            print("\nPython source imports:")
            for name, row in result["imports"].items():
                marker = "OK" if row["ok"] else "FAIL"
                print(f"  {marker:4} {name}: {row['detail']}")

    return 1 if (has_missing_required_path or has_failed_import) else 0


if __name__ == "__main__":
    raise SystemExit(main())
