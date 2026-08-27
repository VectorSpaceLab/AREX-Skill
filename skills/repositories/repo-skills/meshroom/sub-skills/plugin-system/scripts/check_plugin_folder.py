#!/usr/bin/env python3
"""Validate Meshroom plugin layout and config without computing nodes."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a Meshroom plugin root without launching Meshroom compute.")
    parser.add_argument("plugin_root", type=Path, help="Plugin root containing a meshroom/ subfolder.")
    parser.add_argument("--repo-root", help="Optional Meshroom source checkout root for import checks.")
    args = parser.parse_args()

    if args.repo_root:
        sys.path.insert(0, str(Path(args.repo_root).resolve()))
    root = args.plugin_root.resolve()
    meshroomDir = root / "meshroom"
    if not meshroomDir.is_dir():
        print(f"invalid: missing {meshroomDir}")
        return 1

    print(f"plugin root ok: {root}")
    configPath = meshroomDir / "config.json"
    if configPath.exists():
        try:
            config = json.loads(configPath.read_text())
            if not isinstance(config, list):
                print("invalid config: expected a JSON list")
                return 1
            for index, entry in enumerate(config):
                if not isinstance(entry, dict) or not entry.get("key") or not entry.get("value"):
                    print(f"invalid config entry {index}: expected key/value")
                    return 1
            print(f"config ok: {len(config)} entries")
        except (OSError, json.JSONDecodeError) as exc:
            print(f"invalid config: {exc}")
            return 1
    else:
        print("config: not present (optional)")

    packages = []
    for candidate in sorted(meshroomDir.iterdir()):
        if candidate.is_dir() and (candidate / "__init__.py").exists():
            packages.append(candidate)
    print("node packages: " + (", ".join(p.name for p in packages) if packages else "none found"))
    templates = sorted(meshroomDir.glob("*.mg"))
    print("templates: " + (", ".join(p.name for p in templates) if templates else "none found"))

    failures = 0
    for package in packages:
        spec = importlib.util.spec_from_file_location(package.name, package / "__init__.py", submodule_search_locations=[str(package)])
        if spec is None or spec.loader is None:
            print(f"package import unavailable: {package.name}")
            failures += 1
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            print(f"package import ok: {package.name}")
        except Exception as exc:  # plugin code is user-provided; report without a traceback
            print(f"package import failed: {package.name}: {type(exc).__name__}: {exc}")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
