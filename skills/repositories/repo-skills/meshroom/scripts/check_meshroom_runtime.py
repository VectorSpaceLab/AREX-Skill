#!/usr/bin/env python3
"""
Check a Meshroom Python runtime without starting the full GUI or running a pipeline.

Examples:
  python check_meshroom_runtime.py
  python check_meshroom_runtime.py --init-nodes --cli-help --repo-root /path/to/Meshroom
"""

from __future__ import annotations

import argparse
import importlib
import os
from pathlib import Path
import subprocess
import sys
from typing import Iterable


def addRepoRoot(repoRoot: str | None) -> None:
    if not repoRoot:
        return
    root = Path(repoRoot).resolve()
    if not root.exists():
        raise SystemExit(f"repo root does not exist: {root}")
    sys.path.insert(0, root.as_posix())


def checkImports(modules: Iterable[str]) -> None:
    for moduleName in modules:
        module = importlib.import_module(moduleName)
        print(f"import ok: {moduleName}")


def checkMeshroom(initNodes: bool) -> None:
    import meshroom

    print(f"Meshroom version: {meshroom.__version__}")
    if initNodes:
        from meshroom.common import Backend
        meshroom.setupEnvironment(Backend.STANDALONE)
        import meshroom.core

        meshroom.core.initNodes()
        providers = meshroom.core.pluginManager.getNodeDescProviders()
        print(f"registered node descriptors: {len(providers)}")
        print("sample node descriptors: " + ", ".join(sorted(providers)[:10]))


def runHelp(repoRoot: str | None, scriptName: str) -> None:
    if not repoRoot:
        print(f"skip CLI help for {scriptName}: --repo-root was not provided")
        return
    script = Path(repoRoot).resolve() / "bin" / scriptName
    if not script.exists():
        print(f"skip CLI help for {scriptName}: script not found at {script}")
        return
    proc = subprocess.run(
        [sys.executable, script.as_posix(), "-h"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=20,
        check=False,
    )
    firstLine = proc.stdout.splitlines()[0] if proc.stdout else "<no output>"
    if proc.returncode != 0:
        raise SystemExit(f"{scriptName} -h failed with {proc.returncode}: {firstLine}")
    print(f"CLI help ok: {scriptName}: {firstLine}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Meshroom imports, built-in node discovery, and optional CLI help.")
    parser.add_argument("--repo-root", help="Optional Meshroom source checkout root for checking bin/ scripts.")
    parser.add_argument("--init-nodes", action="store_true", help="Initialize built-in node descriptors.")
    parser.add_argument("--ui", action="store_true", help="Also import PySide6 and meshroom.ui.app without starting the GUI event loop.")
    parser.add_argument("--localfarm", action="store_true", help="Also import Meshroom LocalFarm modules without starting a daemon.")
    parser.add_argument("--cli-help", action="store_true", help="Run safe '-h' checks for repo bin scripts; requires --repo-root.")
    args = parser.parse_args()

    addRepoRoot(args.repo_root)

    modules = ["meshroom", "meshroom.core", "meshroom.core.desc", "meshroom.env"]
    if args.ui:
        modules.extend(["PySide6", "meshroom.ui.app"])
    if args.localfarm:
        modules.extend([
            "localfarm.localFarmLauncher",
            "localfarm.localFarmClient",
            "meshroom.submitters.localFarm.localFarmSubmitter",
        ])
    checkImports(modules)
    checkMeshroom(args.init_nodes)

    if args.cli_help:
        for scriptName in [
            "meshroom_info",
            "meshroom_compute",
            "meshroom_batch",
            "meshroom_submit",
            "meshroom_status",
            "meshroom_statistics",
            "meshroom_newNodeType",
            "meshroom_localfarm",
        ]:
            runHelp(args.repo_root, scriptName)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
