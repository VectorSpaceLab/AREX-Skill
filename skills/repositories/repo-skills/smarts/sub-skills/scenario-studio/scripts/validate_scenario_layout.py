#!/usr/bin/env python3
"""Read-only validation of a SMARTS scenario source and generated layout.

This checker never imports scenario.py, loads pickles, runs a map builder, cleans
files, or contacts external services. It checks names and the artifact contract
that can be established safely from filesystem paths alone.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


KNOWN_MAP_NAMES = {"map.net.xml", "map.xodr"}
KNOWN_MAP_SUFFIXES = (".net.xml", ".xodr", ".tfrecord")
OPTIONAL_BUILD = {
    "build/missions.pkl": "ego missions",
    "build/bubbles.pkl": "bubbles",
    "build/friction_map.pkl": "friction patches",
    "build/scenario_metadata.yaml": "metadata",
}


def _map_candidates(root: Path) -> list[Path]:
    candidates = []
    for child in sorted(root.iterdir()):
        if not child.is_file():
            continue
        if child.name in KNOWN_MAP_NAMES or child.name.endswith(KNOWN_MAP_SUFFIXES):
            candidates.append(child)
        elif ".tfrecord" in child.name or "log_map_archive" in child.name:
            candidates.append(child)
    return candidates


def validate(root: Path, require_build: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []
    if not root.exists():
        return [f"scenario does not exist: {root}"], notes
    if not root.is_dir():
        return [f"scenario is not a directory: {root}"], notes

    maps = _map_candidates(root)
    map_spec = root / "build" / "map" / "map_spec.pkl"
    if not maps and not map_spec.is_file():
        errors.append(
            "no recognized local map source (map.net.xml, map.xodr, a supported "
            ".net.xml/.tfrecord source) or build/map/map_spec.pkl"
        )
    elif maps:
        notes.append("map source: " + ", ".join(p.name for p in maps))
    else:
        notes.append("map source: serialized build/map/map_spec.pkl")

    scenario_py = root / "scenario.py"
    if scenario_py.is_file():
        notes.append("authoring entry point: scenario.py")
    else:
        notes.append("no scenario.py; treating this as a map/prebuilt scenario")

    build = root / "build"
    if require_build:
        required = {
            "build/build.db": "build cache",
            "build/map/map.glb": "generated map geometry",
        }
        for relative, label in required.items():
            if not (root / relative).is_file():
                errors.append(f"missing required generated {label}: {relative}")
        if not build.is_dir():
            errors.append("missing generated build directory: build/")
    elif not build.exists():
        notes.append("build/ is absent; source layout only")
    else:
        for relative, label in OPTIONAL_BUILD.items():
            if (root / relative).exists():
                notes.append(f"generated {label}: {relative}")
        traffic = root / "build" / "traffic"
        if traffic.is_dir():
            routes = sorted(
                p.name
                for p in traffic.iterdir()
                if p.is_file() and (p.name.endswith(".rou.xml") or p.name.endswith(".smarts.xml"))
            )
            notes.append(f"generated traffic routes: {len(routes)}")
        if (root / "build" / "map" / "map.glb").is_file():
            notes.append("generated map geometry: build/map/map.glb")

    # Keep this filesystem-only: a source map can still be malformed or use an
    # unavailable optional backend, which the runtime build must report.
    if any(p.suffix == ".xodr" or p.name.endswith(".xodr") for p in maps):
        notes.append("OpenDRIVE source detected; optional parser/backend is required to build it")
    if any(".tfrecord" in p.name or "log_map_archive" in p.name for p in maps):
        notes.append("dataset-backed map detected; external data/integration is not probed")
    return errors, notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only SMARTS scenario source/build layout validator."
    )
    parser.add_argument("--scenario", required=True, type=Path, help="scenario directory")
    parser.add_argument(
        "--require-build",
        action="store_true",
        help="fail unless build/build.db and build/map/map.glb exist",
    )
    args = parser.parse_args(argv)
    root = args.scenario.expanduser().resolve()
    errors, notes = validate(root, args.require_build)
    for note in notes:
        print(f"OK: {note}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"VALID: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
