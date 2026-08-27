#!/usr/bin/env python3
"""Inspect the UltraRAG Flask UI backend from a checkout-aware environment.

This helper creates the Flask application, prints the resolved storage root,
shows the discovered routes, and summarizes the available servers/pipelines.

Usage:
  python inspect_ui_backend.py --repo-root /path/to/UltraRAG
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path


def _add_repo_root(repo_root: Path) -> None:
    repo_root = repo_root.resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Path to the UltraRAG checkout.",
    )
    parser.add_argument(
        "--storage-root",
        help="Optional storage root to use instead of a temporary directory.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    _add_repo_root(repo_root)

    if args.storage_root:
        storage_root = Path(args.storage_root).expanduser().resolve()
        storage_root.mkdir(parents=True, exist_ok=True)
        os.environ["ULTRARAG_UI_STORAGE_ROOT"] = str(storage_root)
        temp_ctx = None
    else:
        temp_ctx = tempfile.TemporaryDirectory(prefix="ultrarag-ui-")
        storage_root = Path(temp_ctx.name)
        os.environ["ULTRARAG_UI_STORAGE_ROOT"] = str(storage_root)

    frontend_dir = repo_root / "ui" / "frontend" / "dist"
    if frontend_dir.exists():
        os.environ.setdefault("ULTRARAG_FRONTEND_DIR", str(frontend_dir))

    try:
        from ui.backend.app import create_app
        from ui.backend import pipeline_manager as pm
        from ui.backend import storage_paths as sp

        app = create_app(admin_mode=False)
        print(f"storage_root={sp.UI_STORAGE_ROOT}")
        print(f"frontend_dir={os.environ.get('ULTRARAG_FRONTEND_DIR', sp.PROJECT_ROOT / 'ui' / 'frontend' / 'dist')}")
        print("routes:")
        for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
            methods = ",".join(sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"}))
            print(f"  {methods:>16} {rule.rule}")

        try:
            servers = pm.list_servers()
            pipelines = pm.list_pipelines()
            tools = pm.list_server_tools()
            print(f"servers={len(servers)}")
            print(f"tools={len(tools)}")
            print(f"pipelines={len(pipelines)}")
        except Exception as exc:
            print(f"pipeline_manager_summary=FAIL {type(exc).__name__}: {exc}")
            return 1

        return 0
    except Exception as exc:
        print(f"ui_backend=FAIL {type(exc).__name__}: {exc}")
        return 1
    finally:
        if temp_ctx is not None:
            temp_ctx.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
