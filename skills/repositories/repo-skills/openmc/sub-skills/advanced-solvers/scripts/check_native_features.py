#!/usr/bin/env python3
"""Safely inspect OpenMC native artifacts and optional build features.

The diagnostic is intentionally read-only. It never invokes CMake, a compiler,
the OpenMC executable, a simulation, a package manager, or a network client.
It can be run from any working directory. Pass paths explicitly when more than
one build may be present; relative paths are interpreted relative to the
caller's current directory.

Examples
--------
    python <advanced-solvers-skill-dir>/scripts/check_native_features.py --help
    python <advanced-solvers-skill-dir>/scripts/check_native_features.py
    python <advanced-solvers-skill-dir>/scripts/check_native_features.py \
        --library <path-to-libopenmc.so> --executable <path-to-openmc> \
        --build-dir <build-dir>
"""

from __future__ import annotations

import argparse
import ctypes
import importlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

FEATURES = ("dagmc", "libmesh", "strict_fp", "uwuw")
CACHE_KEYS = (
    "OPENMC_USE_OPENMP",
    "OPENMC_BUILD_TESTS",
    "OPENMC_ENABLE_STRICT_FP",
    "OPENMC_USE_MPI",
    "OPENMC_USE_DAGMC",
    "OPENMC_USE_LIBMESH",
    "OPENMC_USE_UWUW",
)
LIBRARY_NAMES = ("libopenmc.so", "libopenmc.dylib", "libopenmc.dll", "openmc.dll")
EXECUTABLE_NAMES = ("openmc", "openmc.exe")


def _display_path(path: Path) -> str:
    """Return a stable display string without requiring the path to exist."""

    return str(path.expanduser())


def _candidate_from_build(
    build_dir: Path | None, names: tuple[str, ...]
) -> Path | None:
    """Find a conventional artifact below an explicitly supplied build dir."""

    if build_dir is None:
        return None
    for name in names:
        for candidate in (
            build_dir / name,
            build_dir / "bin" / name,
            build_dir / "lib" / name,
            build_dir / "lib64" / name,
        ):
            if candidate.is_file():
                return candidate
    return None


def _select_path(
    explicit: str | None, build_dir: Path | None, names: tuple[str, ...]
) -> tuple[Path | None, str]:
    if explicit is not None:
        return Path(explicit).expanduser(), "explicit"
    candidate = _candidate_from_build(build_dir, names)
    if candidate is not None:
        return candidate, "build-dir"
    return None, "not supplied"


def _parse_bool(value: str) -> bool | str:
    normalized = value.strip().upper()
    if normalized in {"ON", "TRUE", "YES", "Y", "1"}:
        return True
    if normalized in {"OFF", "FALSE", "NO", "N", "0"}:
        return False
    return value.strip()


def _probe_base_import() -> dict[str, Any]:
    """Probe only the Python package; never import ``openmc.lib``."""

    try:
        module = importlib.import_module("openmc")
    except Exception as exc:  # import diagnostics must not produce a traceback
        return {
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    result: dict[str, Any] = {"status": "succeeded"}
    version = getattr(module, "__version__", None)
    if version is not None:
        result["version"] = str(version)
    return result


def _artifact(path: Path | None, kind: str, source: str) -> dict[str, Any]:
    if path is None:
        return {"status": "not supplied", "source": source}

    result: dict[str, Any] = {
        "path": _display_path(path),
        "source": source,
    }
    if not path.exists():
        result["status"] = "missing"
        return result
    if not path.is_file():
        result["status"] = "not a file"
        return result
    result["status"] = "present"
    result["readable"] = os.access(path, os.R_OK)
    if kind == "executable":
        result["executable"] = os.access(path, os.X_OK)
    return result


def _read_cache(build_dir: Path | None) -> dict[str, Any]:
    if build_dir is None:
        return {"status": "not checked"}

    cache = build_dir / "CMakeCache.txt"
    if not cache.is_file():
        return {"status": "not found", "path": _display_path(cache)}

    values: dict[str, Any] = {}
    pattern = re.compile(r"^([^:#=]+)(?::[^=]+)?=(.*)$")
    try:
        lines = cache.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines:
            match = pattern.match(line)
            if match and match.group(1) in CACHE_KEYS:
                values[match.group(1)] = _parse_bool(match.group(2))
    except OSError as exc:
        return {
            "status": "error",
            "path": _display_path(cache),
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    return {"status": "read", "path": _display_path(cache), "values": values}


def _query_features(
    library_path: Path | None, requested: tuple[str, ...]
) -> dict[str, Any]:
    """Query flags only after the supplied library has loaded and exposed the C API."""

    if library_path is None:
        return {
            "status": "not checked",
            "reason": "no shared library was supplied or found",
        }
    if not library_path.is_file():
        return {
            "status": "not checked",
            "reason": "the shared library path is missing or is not a file",
        }
    if not os.access(library_path, os.R_OK):
        return {
            "status": "not usable",
            "reason": "the shared library is not readable",
        }

    try:
        library = ctypes.CDLL(str(library_path))
    except OSError as exc:
        return {
            "status": "not usable",
            "reason": "the shared library could not be loaded",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    try:
        query = library.openmc_get_feature_enabled
    except AttributeError:
        return {
            "status": "not usable",
            "reason": "the loaded library lacks openmc_get_feature_enabled",
        }

    query.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_bool)]
    query.restype = ctypes.c_int
    flags: dict[str, bool] = {}
    errors: dict[str, dict[str, Any]] = {}
    for feature in requested:
        enabled = ctypes.c_bool()
        try:
            code = int(query(feature.encode("ascii"), ctypes.byref(enabled)))
        except (OSError, UnicodeError) as exc:
            errors[feature] = {
                "status": "query error",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        else:
            if code != 0:
                errors[feature] = {
                    "status": "query failed",
                    "return_code": code,
                }
            else:
                flags[feature] = bool(enabled.value)

    result: dict[str, Any] = {"status": "queried", "flags": flags}
    if errors:
        result["errors"] = errors
    return result


def inspect(args: argparse.Namespace) -> dict[str, Any]:
    build_dir = Path(args.build_dir).expanduser() if args.build_dir else None
    library, library_source = _select_path(args.library, build_dir, LIBRARY_NAMES)
    executable, executable_source = _select_path(
        args.executable, build_dir, EXECUTABLE_NAMES
    )
    requested = tuple(args.feature or FEATURES)

    return {
        "base_python_import": _probe_base_import(),
        "build_dir": _display_path(build_dir) if build_dir else None,
        "executable": _artifact(executable, "executable", executable_source),
        "shared_library": _artifact(library, "library", library_source),
        "cmake_cache": _read_cache(build_dir),
        "feature_query": _query_features(library, requested),
        "notes": [
            "Inspection only: no build, simulation, download, or file mutation "
            "was performed.",
            "The base Python import and the native shared-library check are "
            "independent gates.",
            "Feature flags are reported only after the shared library loads and "
            "exposes the feature query.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect OpenMC Python importability, native artifact paths, CMake "
            "settings, and optional feature flags without building or running "
            "OpenMC."
        ),
        epilog=(
            "With no arguments this performs a read-only smoke diagnostic. "
            "Use --library and --executable to inspect a particular build."
        ),
    )
    parser.add_argument("--build-dir", help="CMake build directory to inspect")
    parser.add_argument("--library", help="Explicit libopenmc shared-library path")
    parser.add_argument("--executable", help="Explicit openmc executable path")
    parser.add_argument(
        "--feature",
        action="append",
        choices=FEATURES,
        help="Feature to query; may be repeated (default: all supported queries)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Print machine-readable JSON"
    )
    return parser


def _print_text(report: dict[str, Any]) -> None:
    print("OpenMC native diagnostic (inspection only)")
    base = report["base_python_import"]
    print(f"base Python import: {base['status']}")
    if "version" in base:
        print(f"  version: {base['version']}")
    if "error" in base:
        print(f"  {base['error_type']}: {base['error']}")

    print(f"build directory: {report['build_dir'] or 'not supplied'}")
    for label in ("executable", "shared_library"):
        item = report[label]
        line = f"{label.replace('_', ' ')}: {item['status']}"
        if "path" in item:
            line += f" ({item['path']})"
        print(line)
        if label == "executable" and "executable" in item:
            print(f"  executable permission: {item['executable']}")
        if "readable" in item:
            print(f"  readable: {item['readable']}")
        if "error" in item:
            print(f"  {item['error_type']}: {item['error']}")

    cache = report["cmake_cache"]
    line = f"CMake cache: {cache['status']}"
    if "path" in cache:
        line += f" ({cache['path']})"
    print(line)
    for key, value in cache.get("values", {}).items():
        print(f"  {key}={value}")

    features = report["feature_query"]
    print(f"feature flags: {features['status']}")
    if "reason" in features:
        print(f"  reason: {features['reason']}")
    for name, enabled in features.get("flags", {}).items():
        print(f"  {name}: {'enabled' if enabled else 'disabled'}")
    for name, error in features.get("errors", {}).items():
        detail = error.get("error", error.get("return_code", "unknown"))
        print(f"  {name}: {error['status']} ({detail})")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = inspect(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
