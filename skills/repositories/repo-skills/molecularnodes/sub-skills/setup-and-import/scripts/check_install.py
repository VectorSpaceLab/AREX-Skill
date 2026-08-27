#!/usr/bin/env python3
"""Read-only, offline MolecularNodes installation and compatibility checker.

The default path checks the runtime visible to this interpreter.  It does not
read a MolecularNodes checkout, add one to ``sys.path``, create a cache, or make
network requests.  ``--repo-root`` is deliberately limited to parsing the
checkout's TOML metadata; it never imports code from that directory.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.util
import os
from pathlib import Path
import re
import sys
import tomllib
from typing import Any

# Keep the checker read-only even when importing source-based dependencies.
sys.dont_write_bytecode = True

EXPECTED_PACKAGE = "5.2.0"
EXPECTED_PYTHON = (3, 13)
EXPECTED_BLENDER = (5, 2, 0)

# These are the package's direct runtime requirements.  ``griddataformats``
# exposes the import package ``gridData``.  Version checks use distribution
# metadata when available; imports remain the authoritative runtime probe.
REQUIRED_MODULES: tuple[tuple[str, str, str | None], ...] = (
    ("bpy", "bpy", "5.2.*"),
    ("databpy", "databpy", ">=0.8.0"),
    ("nodebpy", "nodebpy", ">=520.11"),
    ("biotite", "biotite", ">=1.7.1"),
    ("MDAnalysis", "MDAnalysis", ">=2.10"),
    ("mrcfile", "mrcfile", None),
    ("starfile", "starfile", None),
    ("imdclient", "imdclient", ">=0.2.3"),
    ("pandas", "pandas", "<3.0.0"),
    ("griddataformats", "gridData", ">=1.2.0"),
)

ABSOLUTE_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]|/)[^\s,;:)]+")
VERSION_RE = re.compile(r"\d+(?:\.\d+)*")


class Results:
    def __init__(self) -> None:
        self.failures = 0
        self.warnings = 0

    def emit(self, status: str, check: str, detail: str) -> None:
        print(f"{status:<5} {check}: {detail}")
        if status == "FAIL":
            self.failures += 1
        elif status == "WARN":
            self.warnings += 1


def safe_detail(value: object) -> str:
    """Keep exception text useful without echoing private absolute paths."""

    text = str(value).replace("\n", " ").strip()
    return ABSOLUTE_PATH_RE.sub("<path>", text) or "no additional detail"


def version_tuple(value: object) -> tuple[int, ...] | None:
    match = VERSION_RE.search(str(value))
    if not match:
        return None
    return tuple(int(part) for part in match.group(0).split("."))


def compare_versions(left: tuple[int, ...], right: tuple[int, ...]) -> int:
    width = max(len(left), len(right))
    a = left + (0,) * (width - len(left))
    b = right + (0,) * (width - len(right))
    return (a > b) - (a < b)


def satisfies(version: object, specifier: str | None) -> bool | None:
    """Support the simple specifiers used by MolecularNodes metadata."""

    if specifier is None:
        return True
    actual = version_tuple(version)
    if actual is None:
        return None
    if specifier.endswith(".*"):
        expected = version_tuple(specifier[:-2])
        return expected is not None and actual[: len(expected)] == expected
    if specifier.startswith(">="):
        expected = version_tuple(specifier[2:])
        return expected is not None and compare_versions(actual, expected) >= 0
    if specifier.startswith(">"):
        expected = version_tuple(specifier[1:])
        return expected is not None and compare_versions(actual, expected) > 0
    if specifier.startswith("<="):
        expected = version_tuple(specifier[2:])
        return expected is not None and compare_versions(actual, expected) <= 0
    if specifier.startswith("<"):
        expected = version_tuple(specifier[1:])
        return expected is not None and compare_versions(actual, expected) < 0
    if specifier.startswith("=="):
        expected = version_tuple(specifier[2:])
        return expected is not None and compare_versions(actual, expected) == 0
    expected = version_tuple(specifier)
    return expected is not None and compare_versions(actual, expected) == 0


def checkout_root(path: Path) -> Path | None:
    """Return a probable MolecularNodes checkout root without reading source."""

    try:
        candidate = path.resolve()
    except OSError:
        return None
    candidates = (candidate, *candidate.parents)
    for parent in candidates:
        if (
            (parent / ".git").exists()
            and (parent / "pyproject.toml").is_file()
            and (parent / "molecularnodes" / "blender_manifest.toml").is_file()
        ):
            return parent
    return None


def path_is_checkout_entry(entry: str) -> bool:
    try:
        path = Path(entry or os.curdir).resolve()
    except OSError:
        return False
    return checkout_root(path) is not None


def import_without_checkout(module_name: str) -> tuple[Any | None, str | None]:
    """Import a runtime package without falling back to this source checkout."""

    original_path = sys.path[:]
    try:
        sys.path[:] = [entry for entry in sys.path if not path_is_checkout_entry(entry)]
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return None, "not found outside a source checkout"
        origin = getattr(spec, "origin", None)
        if origin and checkout_root(Path(origin).parent) is not None:
            return None, "only a source checkout was discoverable"
        return importlib.import_module(module_name), None
    except Exception as exc:  # Import errors are reported as required failures.
        return None, f"{type(exc).__name__}: {safe_detail(exc)}"
    finally:
        sys.path[:] = original_path


def distribution_version(
    distribution_name: str, *, ignore_checkout: bool = True
) -> tuple[str | None, str | None]:
    try:
        dist = metadata.distribution(distribution_name)
    except metadata.PackageNotFoundError:
        return None, "distribution metadata not found"
    except Exception as exc:
        return None, f"{type(exc).__name__}: {safe_detail(exc)}"

    if ignore_checkout:
        try:
            location = Path(dist.locate_file(""))
            if checkout_root(location) is not None:
                return None, "only source-checkout metadata was found"
        except OSError:
            pass
    return dist.version, None


def check_python(results: Results) -> None:
    actual = sys.version_info[:2]
    if actual != EXPECTED_PYTHON:
        results.emit(
            "FAIL",
            "python",
            f"{actual[0]}.{actual[1]} found; package requires Python 3.13.x",
        )
    else:
        results.emit("PASS", "python", f"{actual[0]}.{actual[1]} compatible")


def check_distribution_metadata(results: Results) -> None:
    version, reason = distribution_version("molecularnodes")
    if version is None:
        results.emit("WARN", "molecularnodes metadata", reason or "unavailable")
    elif version != EXPECTED_PACKAGE:
        results.emit(
            "FAIL",
            "molecularnodes metadata",
            f"version {version}; expected {EXPECTED_PACKAGE}",
        )
    else:
        results.emit("PASS", "molecularnodes metadata", f"version {version}")


def check_module(
    results: Results,
    label: str,
    module_name: str,
    specifier: str | None,
    imported: dict[str, Any],
) -> None:
    module, reason = import_without_checkout(module_name)
    if module is None:
        results.emit("FAIL", f"import {label}", reason or "import failed")
        return

    imported[module_name] = module
    version, metadata_reason = distribution_version(label)
    if version is None:
        version = getattr(module, "__version__", None)
    if specifier is not None:
        if version is None:
            results.emit(
                "WARN",
                f"version {label}",
                f"imported, but version metadata is unavailable (requires {specifier})",
            )
        else:
            compatible = satisfies(version, specifier)
            if compatible is False:
                results.emit(
                    "FAIL",
                    f"version {label}",
                    f"{version} does not satisfy {specifier}",
                )
            elif compatible is True:
                results.emit("PASS", f"import {label}", f"imported; version {version}")
            else:
                results.emit(
                    "WARN",
                    f"version {label}",
                    f"imported; could not interpret version {version}",
                )
    else:
        suffix = f"; version {version}" if version is not None else ""
        results.emit("PASS", f"import {label}", f"imported{suffix}")


def check_bpy_host(results: Results, imported: dict[str, Any]) -> None:
    bpy = imported.get("bpy")
    if bpy is None:
        return
    app = getattr(bpy, "app", None)
    host_version = getattr(app, "version", None)
    if not isinstance(host_version, (tuple, list)) or len(host_version) < 2:
        results.emit("FAIL", "bpy host", "bpy.app.version is unavailable")
        return
    try:
        actual = tuple(int(value) for value in host_version[:3])
    except (TypeError, ValueError):
        results.emit("FAIL", "bpy host", "bpy.app.version is not numeric")
        return
    if actual < EXPECTED_BLENDER:
        results.emit(
            "FAIL",
            "bpy host",
            f"{'.'.join(map(str, actual))} found; Blender 5.2.0 or newer is required",
        )
    else:
        results.emit("PASS", "bpy host", f"{'.'.join(map(str, actual))} compatible")


def check_molecularnodes_api(results: Results, imported: dict[str, Any]) -> None:
    package = imported.get("molecularnodes")
    if package is None:
        return
    missing = [name for name in ("Molecule", "download") if not hasattr(package, name)]
    try:
        download = importlib.import_module("molecularnodes.download")
        reader = importlib.import_module("molecularnodes.entities.molecule.reader")
        if not hasattr(download, "StructureDownloader"):
            missing.append("download.StructureDownloader")
        if not hasattr(reader, "read_structure"):
            missing.append("entities.molecule.reader.read_structure")
    except Exception as exc:
        results.emit("FAIL", "MolecularNodes API", f"API imports failed: {safe_detail(exc)}")
        return
    if missing:
        results.emit("FAIL", "MolecularNodes API", "missing " + ", ".join(missing))
    else:
        results.emit("PASS", "MolecularNodes API", "Molecule, downloader, and reader available")


def check_operator_registration(results: Results, imported: dict[str, Any]) -> None:
    bpy = imported.get("bpy")
    if bpy is None:
        return
    try:
        operator_namespace = getattr(bpy.ops, "mn", None)
        registered = operator_namespace is not None and hasattr(
            operator_namespace, "import_fetch"
        )
    except Exception as exc:
        results.emit("WARN", "Blender operators", f"probe unavailable: {safe_detail(exc)}")
        return
    if registered:
        results.emit("PASS", "Blender operators", "mn.import_fetch is registered")
    else:
        results.emit(
            "WARN",
            "Blender operators",
            "mn.import_fetch is not registered; enable/register the extension for UI imports",
        )


def read_toml(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle), None
    except FileNotFoundError:
        return None, "metadata file not found"
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return None, f"{type(exc).__name__}: {safe_detail(exc)}"


def check_repo_metadata(results: Results, repo_root: str) -> None:
    """Check only declared project/extension metadata from an explicit root."""

    root = Path(repo_root).expanduser()
    if not root.is_dir():
        results.emit("FAIL", "repo metadata", "--repo-root is not a directory")
        return

    project, reason = read_toml(root / "pyproject.toml")
    if project is None:
        results.emit("FAIL", "repo pyproject", reason or "unreadable")
    else:
        table = project.get("project", {})
        checks = (
            (table.get("name") == "molecularnodes", "project.name is molecularnodes"),
            (table.get("version") == EXPECTED_PACKAGE, "project.version is 5.2.0"),
            (table.get("requires-python") == "~=3.13.0", "requires Python ~=3.13.0"),
            (
                "nodebpy>=520.11" in table.get("dependencies", []),
                "declares nodebpy>=520.11",
            ),
            (
                "bpy==5.2.*" in table.get("optional-dependencies", {}).get("bpy", []),
                "declares the bpy 5.2 extra",
            ),
        )
        for passed, detail in checks:
            results.emit("PASS" if passed else "FAIL", "repo pyproject", detail)

    manifest, reason = read_toml(root / "molecularnodes" / "blender_manifest.toml")
    if manifest is None:
        results.emit("FAIL", "repo manifest", reason or "unreadable")
    else:
        checks = (
            (manifest.get("id") == "molecularnodes", "manifest id is molecularnodes"),
            (manifest.get("version") == EXPECTED_PACKAGE, "manifest version is 5.2.0"),
            (manifest.get("blender_version_min") == "5.2.0", "minimum Blender is 5.2.0"),
        )
        for passed, detail in checks:
            results.emit("PASS" if passed else "FAIL", "repo manifest", detail)

        wheels = manifest.get("wheels", [])
        nodebpy_versions = [
            version_tuple(match.group(1))
            for wheel in wheels
            if (match := re.search(r"nodebpy-([0-9][^-/]+)", str(wheel)))
        ]
        nodebpy_versions = [version for version in nodebpy_versions if version is not None]
        if nodebpy_versions and not any(
            compare_versions(version, (520, 11)) >= 0 for version in nodebpy_versions
        ):
            results.emit(
                "FAIL",
                "repo manifest",
                "bundled nodebpy wheel is below declared >=520.11 requirement",
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check MolecularNodes 5.2.0 runtime compatibility without network or writes."
    )
    parser.add_argument(
        "--repo-root",
        help="optional checkout root; read pyproject/manifest metadata only",
    )
    args = parser.parse_args(argv)

    results = Results()
    print("MolecularNodes setup check (read-only; network not attempted)")
    check_python(results)
    check_distribution_metadata(results)

    imported: dict[str, Any] = {}
    for label, module_name, specifier in REQUIRED_MODULES:
        check_module(results, label, module_name, specifier, imported)

    package, reason = import_without_checkout("molecularnodes")
    if package is None:
        results.emit("FAIL", "import molecularnodes", reason or "import failed")
    else:
        imported["molecularnodes"] = package
        results.emit("PASS", "import molecularnodes", "imported")

    check_bpy_host(results, imported)
    check_molecularnodes_api(results, imported)
    check_operator_registration(results, imported)

    if args.repo_root:
        check_repo_metadata(results, args.repo_root)

    print(
        f"Summary: {results.failures} failure(s), {results.warnings} warning(s); "
        "no files written"
    )
    return 1 if results.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
