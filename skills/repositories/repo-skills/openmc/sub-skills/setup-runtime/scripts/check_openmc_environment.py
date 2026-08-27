#!/usr/bin/env python3
"""Run read-only OpenMC runtime diagnostics.

The helper checks the Python package by default.  Optional checks are enabled
with ``--executable`` and ``--cross-sections`` (or a configured
``OPENMC_CROSS_SECTIONS`` environment variable).  It can also inspect an
explicit shared library with ``--library``.  Executable probing always invokes
only the fixed ``--version`` argument, without a shell or model input.

No check downloads data, builds or installs software, changes environment
variables, or writes files.
"""

from __future__ import annotations

import argparse
import ctypes
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any
from urllib.parse import urlparse
import xml.etree.ElementTree as ET


_LIBRARY_NAMES = (
    "libopenmc.so",
    "libopenmc.dylib",
    "libopenmc.dll",
    "openmc.dll",
)
_LIBRARY_GLOBS = ("libopenmc.so*", "libopenmc.dylib*", "libopenmc.dll")


def _result(status: str, **fields: Any) -> dict[str, Any]:
    return {"status": status, **fields}


def _absolute(path: Path, *, base: Path | None = None) -> Path:
    """Return an absolute, non-strict path without requiring the target."""
    path = Path(os.path.expandvars(os.path.expanduser(str(path))))
    if not path.is_absolute():
        path = (base or Path.cwd()) / path
    return path.resolve(strict=False)


def package_probe() -> dict[str, Any]:
    """Probe distribution metadata and the base Python import."""
    try:
        distribution_version = importlib.metadata.version("openmc")
    except importlib.metadata.PackageNotFoundError:
        distribution_version = None

    try:
        module = importlib.import_module("openmc")
    except Exception as exc:  # imports are reported, not re-raised
        return _result(
            "fail",
            distribution_version=distribution_version,
            reason=f"import failed: {type(exc).__name__}: {exc}",
        )

    imported_version = getattr(module, "__version__", None)
    return _result(
        "pass",
        distribution_version=distribution_version,
        imported_version=imported_version,
        location=str(getattr(module, "__file__", "")) or None,
        warning=("package version is unavailable" if imported_version is None else None),
    )


def _resolve_executable(requested: str) -> tuple[Path | None, str | None]:
    """Resolve a path or a PATH name without invoking it."""
    has_separator = os.sep in requested or (os.altsep and os.altsep in requested)
    if has_separator or Path(requested).is_absolute():
        candidate = _absolute(Path(requested))
        if not candidate.is_file():
            return None, "explicit path is not a file"
        if not os.access(candidate, os.X_OK):
            return None, "explicit path is not executable"
        return candidate, None

    resolved = shutil.which(requested)
    if resolved is None:
        return None, "name was not found on PATH"
    candidate = _absolute(Path(resolved))
    if not candidate.is_file():
        return None, "PATH resolution did not produce a file"
    return candidate, None


def executable_probe(requested: str | None) -> dict[str, Any]:
    """Resolve and invoke only ``--version`` for an explicitly requested exe."""
    if requested is None:
        return _result(
            "skipped",
            reason="not requested; pass --executable NAME_OR_PATH to probe",
        )

    resolved, resolution_error = _resolve_executable(requested)
    if resolved is None:
        return _result(
            "fail",
            requested=requested,
            reason=resolution_error,
        )

    try:
        completed = subprocess.run(
            [str(resolved), "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
        return _result(
            "fail",
            requested=requested,
            resolved=str(resolved),
            reason=f"could not run fixed --version probe: {type(exc).__name__}: {exc}",
        )

    output = (completed.stdout + completed.stderr).strip()
    result = _result(
        "pass" if completed.returncode == 0 else "fail",
        requested=requested,
        resolved=str(resolved),
        returncode=completed.returncode,
        output=output,
    )
    if completed.returncode != 0:
        result["reason"] = "--version returned a nonzero status"
    return result


def _package_library_candidates(package: dict[str, Any]) -> list[Path]:
    location = package.get("location")
    if not location:
        return []
    library_dir = Path(location).parent / "lib"
    candidates: list[Path] = [library_dir / name for name in _LIBRARY_NAMES]
    for pattern in _LIBRARY_GLOBS:
        candidates.extend(sorted(library_dir.glob(pattern)))

    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        absolute = _absolute(candidate)
        if absolute not in seen:
            seen.add(absolute)
            unique.append(absolute)
    return unique


def _load_library(path: Path) -> tuple[bool, str | None]:
    try:
        ctypes.CDLL(str(path))
    except Exception as exc:  # platform loader failures vary by Python/OS
        return False, f"{type(exc).__name__}: {exc}"
    return True, None


def native_library_probe(
    package: dict[str, Any], explicit_library: str | None
) -> dict[str, Any]:
    """Report package-local/native library availability without raising."""
    if package.get("status") != "pass":
        return _result("skipped", reason="base package import failed")

    if explicit_library:
        candidates = [_absolute(Path(explicit_library))]
        requested = explicit_library
    else:
        candidates = _package_library_candidates(package)
        requested = None

    existing = [path for path in candidates if path.is_file()]
    result: dict[str, Any] = {
        "requested": requested,
        "candidates": [str(path) for path in candidates],
        "existing": [str(path) for path in existing],
    }
    if not existing:
        result.update(
            status="fail" if explicit_library else "missing",
            reason=(
                "explicit shared-library path is not a file"
                if explicit_library
                else "no package-local libopenmc shared library was found"
            ),
        )
        return result

    load_errors: list[str] = []
    for path in existing:
        loaded, error = _load_library(path)
        if loaded:
            result.update(status="pass", loaded=str(path))
            return result
        load_errors.append(f"{path}: {error}")
    result.update(status="fail", load_errors=load_errors)
    return result


def python_binding_probe(package: dict[str, Any]) -> dict[str, Any]:
    """Try the optional ctypes binding and turn loader errors into diagnostics."""
    if package.get("status") != "pass":
        return _result("skipped", reason="base package import failed")
    try:
        importlib.import_module("openmc.lib")
    except Exception as exc:
        return _result(
            "unavailable",
            reason=f"import openmc.lib failed: {type(exc).__name__}: {exc}",
        )
    return _result("pass", reason="import openmc.lib succeeded")


def _is_uri(raw: str) -> bool:
    parsed = urlparse(raw)
    return bool(parsed.scheme and (parsed.netloc or parsed.scheme == "file"))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _data_root(index: Path, root: ET.Element) -> tuple[Path, str | None]:
    """Return the base for relative references and the declared directory.

    OpenMC uses a declared ``<directory>`` value as supplied.  Its documented
    and generated form is an absolute path; when a relative value is supplied,
    the native runtime interprets it relative to its working directory, which
    is also the diagnostic's current working directory.
    """
    declared: str | None = None
    for element in root.iter():
        if _local_name(element.tag) == "directory":
            declared = (element.text or "").strip() or None
            break
    if not declared:
        return index.parent, None
    return _absolute(Path(declared)), declared


def cross_sections_probe(explicit_path: str | None) -> dict[str, Any]:
    """Parse an index and check every local XML ``path`` reference."""
    configured = explicit_path or os.environ.get("OPENMC_CROSS_SECTIONS")
    source = "argument" if explicit_path else "OPENMC_CROSS_SECTIONS"
    if not configured:
        return _result(
            "skipped",
            source=source,
            reason="not configured; pass --cross-sections PATH to validate",
        )

    index = _absolute(Path(configured))
    if not index.is_file():
        return _result(
            "fail",
            source=source,
            path=str(index),
            reason="cross_sections.xml does not exist as a file",
        )

    try:
        root = ET.parse(index).getroot()
    except (ET.ParseError, OSError) as exc:
        return _result(
            "fail",
            source=source,
            path=str(index),
            reason=f"cannot parse cross_sections.xml: {type(exc).__name__}: {exc}",
        )

    reference_base, declared_directory = _data_root(index, root)
    references: list[dict[str, Any]] = []
    missing: list[str] = []
    non_files: list[str] = []
    skipped_uris: list[str] = []

    for element in root.iter():
        raw = element.attrib.get("path")
        if not raw:
            continue
        item: dict[str, Any] = {"tag": _local_name(element.tag), "raw": raw}
        if _is_uri(raw):
            item["kind"] = "uri"
            skipped_uris.append(raw)
        else:
            target = _absolute(Path(raw), base=reference_base)
            item.update(
                kind="absolute" if Path(raw).is_absolute() else "relative",
                resolved=str(target),
                exists=target.exists(),
                file=target.is_file(),
            )
            if not target.exists():
                missing.append(str(target))
            elif not target.is_file():
                non_files.append(str(target))
        references.append(item)

    failed = bool(missing or non_files)
    result = _result(
        "fail" if failed else "pass",
        source=source,
        path=str(index),
        root_tag=_local_name(root.tag),
        declared_directory=declared_directory,
        reference_base=str(reference_base),
        reference_count=len(references),
        references=references,
        missing_references=missing,
        non_file_references=non_files,
        skipped_uri_references=skipped_uris,
    )
    if not references:
        result["note"] = "index parsed but contains no local path attributes"
    return result


def collect(args: argparse.Namespace) -> dict[str, Any]:
    package = package_probe()
    executable = executable_probe(args.executable)
    cross_sections = cross_sections_probe(args.cross_sections)
    native_library = native_library_probe(package, args.library)
    binding = python_binding_probe(package)

    requested_failures: list[str] = []
    if package["status"] == "fail":
        requested_failures.append("package")
    if args.executable is not None and executable["status"] == "fail":
        requested_failures.append("executable")
    if (args.cross_sections or os.environ.get("OPENMC_CROSS_SECTIONS")) and cross_sections[
        "status"
    ] == "fail":
        requested_failures.append("cross_sections")
    if args.library is not None and native_library["status"] == "fail":
        requested_failures.append("library")

    return {
        "python": {"executable": sys.executable, "version": sys.version.split()[0]},
        "package": package,
        "executable": executable,
        "native_library": native_library,
        "python_binding": binding,
        "cross_sections": cross_sections,
        "requested_failures": requested_failures,
        "notes": [
            "Diagnostics are read-only: no downloads, builds, installs, or environment mutations.",
            "Executable probing uses only a fixed --version argument and never a shell or model input.",
            "A passing Python import does not imply that the executable, shared library, or data index is ready.",
        ],
    }


def _print_item(name: str, item: dict[str, Any]) -> None:
    print(f"{name}: {item.get('status', 'unknown')}")
    for field in (
        "reason",
        "warning",
        "imported_version",
        "distribution_version",
        "requested",
        "resolved",
        "returncode",
        "output",
        "loaded",
        "path",
        "reference_count",
        "missing_references",
        "non_file_references",
    ):
        value = item.get(field)
        if value not in (None, "", [], {}):
            print(f"  {field}: {value}")


def print_text(report: dict[str, Any]) -> None:
    print("OpenMC runtime diagnostics (read-only)")
    print(f"python: {report['python']['executable']} ({report['python']['version']})")
    for name in (
        "package",
        "executable",
        "native_library",
        "python_binding",
        "cross_sections",
    ):
        _print_item(name, report[name])
    failures = report["requested_failures"]
    print(f"requested failures: {', '.join(failures) if failures else 'none'}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check OpenMC package, optional executable, native library, and "
            "cross_sections.xml references without changing the environment."
        )
    )
    parser.add_argument(
        "--executable",
        metavar="NAME_OR_PATH",
        help="OpenMC executable name for PATH lookup or an explicit executable path.",
    )
    parser.add_argument(
        "--library",
        metavar="PATH",
        help="Optional explicit libopenmc shared-library path to load.",
    )
    parser.add_argument(
        "--cross-sections",
        metavar="PATH",
        help="Optional cross_sections.xml path to parse and validate.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the complete structured report as JSON.",
    )
    args = parser.parse_args()
    report = collect(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 1 if report["requested_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
