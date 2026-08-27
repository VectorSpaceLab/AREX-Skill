#!/usr/bin/env python3
"""Safely diagnose optional Biotite interface dependencies.

This script checks import availability for optional visualization and interface
packages without launching PyMOL, opening GUI windows, rendering images, running
simulations, or downloading data.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import shutil
import sys
from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass
class ProbeResult:
    name: str
    available: bool
    version: str | None
    detail: str
    recovery: str


def _distribution_version(*names: str) -> str | None:
    for name in names:
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            continue
    return None


def _probe_import(
    name: str,
    module: str,
    recovery: str,
    distributions: Iterable[str] = (),
) -> ProbeResult:
    try:
        imported = importlib.import_module(module)
    except Exception as error:  # noqa: BLE001 - report actionable diagnostics
        return ProbeResult(
            name=name,
            available=False,
            version=_distribution_version(*distributions),
            detail=f"cannot import {module}: {type(error).__name__}: {error}",
            recovery=recovery,
        )
    version = _distribution_version(*distributions)
    if version is None:
        version = getattr(imported, "__version__", None)
    return ProbeResult(
        name=name,
        available=True,
        version=str(version) if version is not None else None,
        detail=f"imported {module}",
        recovery="No action needed for import availability.",
    )


def _probe_command(name: str, command: str, recovery: str) -> ProbeResult:
    path = shutil.which(command)
    return ProbeResult(
        name=name,
        available=path is not None,
        version=None,
        detail=f"found executable {command}" if path else f"executable {command} not found on PATH",
        recovery="No action needed for command availability." if path else recovery,
    )


def collect_results() -> list[ProbeResult]:
    results = [
        _probe_import(
            "biotite",
            "biotite",
            "Install Biotite before using this repo skill.",
            ("biotite",),
        ),
        _probe_import(
            "matplotlib",
            "matplotlib",
            "Install Matplotlib or skip Biotite plotting helpers.",
            ("matplotlib",),
        ),
        _probe_import(
            "rdkit",
            "rdkit",
            "Install RDKit only for cheminformatics conversion workflows.",
            ("rdkit", "rdkit-pypi"),
        ),
        _probe_import(
            "openmm",
            "openmm",
            "Install OpenMM only for simulation interop workflows.",
            ("openmm",),
        ),
        _probe_import(
            "pymol",
            "pymol2",
            "Install PyMOL/pymol2 or use non-PyMOL visualization/export alternatives.",
            ("pymol", "pymol-open-source"),
        ),
        _probe_import(
            "IPython",
            "IPython.display",
            "Install IPython only when using PyMOL notebook display helpers.",
            ("ipython",),
        ),
        _probe_command(
            "ffmpeg",
            "ffmpeg",
            "Install ffmpeg or avoid pymol_interface.play(..., format='mp4') and some GIF workflows.",
        ),
        _probe_command(
            "ImageMagick",
            "magick",
            "Install ImageMagick or use ffmpeg/still images instead of ImageMagick GIF export.",
        ),
    ]
    return results


def print_text(results: Iterable[ProbeResult]) -> None:
    for result in results:
        status = "OK" if result.available else "MISSING"
        version = f" version={result.version}" if result.version else ""
        print(f"[{status}] {result.name}{version}")
        print(f"  detail: {result.detail}")
        if not result.available:
            print(f"  recovery: {result.recovery}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check optional Biotite interface dependencies without launching GUI, "
            "rendering, simulating, or downloading data."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 1 when any optional dependency is missing.",
    )
    args = parser.parse_args()

    results = collect_results()
    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2, sort_keys=True))
    else:
        print_text(results)

    if args.strict and any(not result.available for result in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
