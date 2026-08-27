#!/usr/bin/env python3
"""Read-only Brian2 environment report.

The checker deliberately reports capability states rather than executable,
cache, prefix, or checkout paths. It never installs packages, edits
preferences, compiles code, or clears caches. Importing Brian2 may perform the
package's normal import-time logger initialization; no checker-specific
mutation is performed.
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes.util
import importlib
import importlib.metadata
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
from typing import Any

EXPECTED_VERSION = "2.9.0"
# (module, distribution, PEP 440 requirement). Brian's import-time check only
# probes the first four modules; these are the complete declared base set.
REQUIRED_IMPORTS = {
    "numpy": ("numpy", "numpy", ">=2.2.0"),
    "sympy": ("sympy", "sympy", ">=1.2"),
    "pyparsing": ("pyparsing", "pyparsing", ">=3,!=3.2.4"),
    "jinja2": ("jinja2", "Jinja2", ">=2.7"),
    "Cython": ("Cython", "Cython", ">=0.29.21"),
    "setuptools": ("setuptools", "setuptools", ">=61"),
    "packaging": ("packaging", "packaging", ""),
}
WINDOWS_REQUIRED_IMPORTS = {
    "py-cpuinfo": ("cpuinfo", "py-cpuinfo", ""),
}
OPTIONAL_MODULES = {
    "SciPy": ("scipy", "scipy"),
    "Matplotlib": ("matplotlib", "matplotlib"),
    "Pandas": ("pandas", "pandas"),
    "IPython": ("IPython", "ipython"),
    "Jupyter": ("jupyter", "jupyter"),
    "Notebook": ("notebook", "notebook"),
    "brian2tools": ("brian2tools", "brian2tools"),
    "pytest": ("pytest", "pytest"),
}
COMPILER_NAMES = ("g++", "c++", "clang++", "cl")


def _redact(text: object) -> str:
    """Remove common local path forms from an exception summary."""

    value = str(text).replace("\x00", "")
    value = value.replace("pip install -e", "<development-install-command>")
    for secret in (os.getcwd(), os.path.expanduser("~"), sys.prefix):
        if secret:
            value = value.replace(secret, "<local>")
    # Also redact absolute and home-relative paths that were not rooted at one
    # of the values above. The report intentionally exposes no path-bearing
    # values, even when an exception formats one as ``~/...``.
    value = re.sub(r"(?:[A-Za-z]:[\\/]|/)[^\s'\"]+", "<path>", value)
    value = re.sub(r"~[\\/][^\s'\"]+", "<path>", value)
    value = " ".join(value.split())
    return value[:280]


def _error(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {_redact(exc)}"


def _metadata_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None
    except Exception:
        return None


def _module_version(module: object, distribution: str) -> str | None:
    value = getattr(module, "__version__", None)
    if value is not None:
        return str(value)
    return _metadata_version(distribution)


def _check_version(version: str | None, requirement: str) -> str:
    """Classify a version without making packaging a checker hard dependency."""

    if not requirement:
        return "not-checked"
    if version is None:
        return "unknown"
    try:
        from packaging.specifiers import SpecifierSet
        from packaging.version import Version

        return "satisfied" if Version(version) in SpecifierSet(requirement) else "mismatch"
    except Exception:
        return "unavailable"


def _probe_imports() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    required = dict(REQUIRED_IMPORTS)
    if platform.system() == "Windows":
        required.update(WINDOWS_REQUIRED_IMPORTS)
    for label, (module_name, distribution, requirement) in required.items():
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # report the first import boundary, don't abort
            result[label] = {
                "status": "failed",
                "error": _error(exc),
                "requirement": requirement or None,
            }
        else:
            version = _module_version(module, distribution)
            result[label] = {
                "status": "present",
                "version": version,
                "requirement": requirement or None,
                "version_status": _check_version(version, requirement),
            }
    return result


def _probe_optional() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for label, (module_name, distribution) in OPTIONAL_MODULES.items():
        try:
            spec = importlib.util.find_spec(module_name)
        except Exception as exc:
            result[label] = {"status": "error", "error": _error(exc)}
            continue
        if spec is None:
            result[label] = {"status": "missing", "probe": "import-spec"}
        else:
            result[label] = {
                "status": "present",
                "probe": "import-spec-only",
                "version": _metadata_version(distribution),
            }
    return result


def _classify_import_location(spec: Any) -> str:
    """Classify location without returning it or exposing a local path."""

    if spec is None:
        return "not-found"
    origin = getattr(spec, "origin", None)
    if not origin or origin in {"built-in", "frozen"}:
        return "unknown"
    try:
        package_dir = Path(origin).resolve().parent
        project_dir = package_dir.parent
        source_markers = (project_dir / "pyproject.toml", project_dir / ".git")
        if any(marker.exists() for marker in source_markers):
            return "source-like"
    except OSError:
        return "unknown"
    return "installed-or-editable"


def _import_brian() -> tuple[object | None, dict[str, Any]]:
    try:
        spec = importlib.util.find_spec("brian2")
    except Exception as exc:
        return None, {
            "status": "failed",
            "error": _error(exc),
            "location_class": "unknown",
        }

    location_class = _classify_import_location(spec)
    # Brian's import-time diagnostics should be represented in the JSON report,
    # not interleaved with its compact output.
    captured = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            module = importlib.import_module("brian2")
    except Exception as exc:
        details: dict[str, Any] = {
            "status": "failed",
            "error": _error(exc),
            "location_class": location_class,
        }
        diagnostic = _redact(captured.getvalue())
        if diagnostic:
            details["import_diagnostic"] = diagnostic
        return None, details

    details = {
        "status": "present",
        "version": str(getattr(module, "__version__", "unknown")),
        "location_class": location_class,
    }
    details["version_status"] = (
        "satisfied" if details["version"] == EXPECTED_VERSION else "mismatch"
    )
    return module, details


def _safe_pref(prefs: Any, name: str) -> tuple[Any, str | None]:
    try:
        value = prefs[name]
    except Exception as exc:
        return None, _error(exc)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value, None
    if isinstance(value, type):
        return getattr(value, "class_name", value.__name__), None
    return type(value).__name__, None


def _probe_brian_state(module: object | None) -> dict[str, Any]:
    state: dict[str, Any] = {
        "target": None,
        "target_error": None,
        "available_targets": [],
        "compiler_preference": None,
        "cache": {"configuration": "not-available"},
    }
    if module is None:
        return state
    prefs = getattr(module, "prefs", None)
    if prefs is None:
        state["target_error"] = "BrianGlobalPreferences unavailable"
        return state

    target, error = _safe_pref(prefs, "codegen.target")
    state["target"] = target
    state["target_error"] = error
    compiler, error = _safe_pref(prefs, "codegen.cpp.compiler")
    state["compiler_preference"] = compiler
    if error:
        state["compiler_preference_error"] = error

    cache, error = _safe_pref(prefs, "codegen.runtime.cython.cache_dir")
    if error:
        state["cache"] = {"configuration": "unavailable", "error": error}
    elif cache is None:
        state["cache"] = {
            "configuration": "cython-default",
            "path_reported": False,
            "filesystem_probe": "not-run",
        }
    elif isinstance(cache, str):
        # Do not echo the configured value. os.access is read-only, but this is
        # intentionally not attempted for the default path to avoid resolving
        # or leaking user-specific cache details.
        cache_path = Path(cache).expanduser()
        state["cache"] = {
            "configuration": "explicit",
            "path_reported": False,
            "exists": cache_path.exists(),
            "writable": os.access(cache_path, os.W_OK) if cache_path.exists() else False,
        }
    else:
        state["cache"] = {
            "configuration": "invalid-type",
            "path_reported": False,
        }

    try:
        from brian2.codegen.targets import codegen_targets

        names = []
        for target_class in codegen_targets:
            name = getattr(target_class, "class_name", None) or getattr(
                target_class, "__name__", None
            )
            if name:
                names.append(str(name))
        state["available_targets"] = sorted(set(names))
    except Exception as exc:
        state["available_targets_error"] = _error(exc)
    return state


def build_report() -> dict[str, Any]:
    try:
        brian_spec = importlib.util.find_spec("brian2")
    except Exception:
        brian_spec = None
    brian_module, brian_import = _import_brian()
    available_compilers = [name for name in COMPILER_NAMES if shutil.which(name)]
    cwd = Path.cwd()
    source_shadowing = (cwd / "brian2").is_dir() or (cwd / "brian2.py").is_file()
    metadata_version = _metadata_version("Brian2") or _metadata_version("brian2")

    return {
        "checker": {
            "read_only": True,
            "compiler_probe": "executable-name-only",
            "optional_probe": "import-spec-only",
            "paths_reported": False,
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "supported": sys.version_info >= (3, 12),
            "platform": sys.platform,
            "machine": platform.machine(),
        },
        "package": {
            "distribution": "Brian2",
            "expected_version": EXPECTED_VERSION,
            "metadata_version": metadata_version,
            "import": brian_import,
            "import_spec_found": brian_spec is not None,
            "current_directory_shadowing_risk": source_shadowing,
        },
        "required_imports": _probe_imports(),
        "optional_dependencies": _probe_optional(),
        "compiler": {
            "available_names": available_compilers,
            "available": bool(available_compilers),
        },
        "gsl": {
            "native_library_name_present": ctypes.util.find_library("gsl") is not None,
            "headers_probed": False,
            "full_support_proved": False,
        },
        "codegen": _probe_brian_state(brian_module),
    }


def _strict_failures(report: dict[str, Any], require_compiler: bool) -> list[str]:
    failures: list[str] = []
    if not report["python"]["supported"]:
        failures.append("python<3.12")
    metadata_version = report["package"]["metadata_version"]
    if metadata_version != EXPECTED_VERSION:
        failures.append("distribution-version-mismatch")
    imported = report["package"]["import"]
    if imported.get("status") != "present":
        failures.append("brian2-import")
    elif imported.get("version_status") != "satisfied":
        failures.append("brian2-import-version-mismatch")
    for name, result in report["required_imports"].items():
        if result.get("status") != "present":
            failures.append(f"required-import:{name}")
        elif result.get("version_status") in {"mismatch", "unknown", "unavailable"}:
            failures.append(f"required-version:{name}")
    if require_compiler and not report["compiler"]["available"]:
        failures.append("compiler-not-found")
    return failures


def _print_compact(report: dict[str, Any], failures: list[str]) -> None:
    py = report["python"]
    package = report["package"]
    imported = package["import"]
    print("Brian2 environment check (read-only)")
    print(f"Python: {py['version']} ({'supported' if py['supported'] else 'too old'})")
    print(
        "Package: metadata="
        f"{package['metadata_version'] or 'missing'}, "
        f"import={imported.get('version', imported.get('status'))}"
    )
    print(
        "Import location class: "
        f"{imported.get('location_class', 'unknown')}; "
        f"current-directory shadowing risk={package['current_directory_shadowing_risk']}"
    )
    print(
        "Required imports: "
        + ", ".join(
            f"{name}={result['status']}"
            + (f"/{result['version_status']}" if result.get("version_status") else "")
            for name, result in report["required_imports"].items()
        )
    )
    optional = report["optional_dependencies"]
    print(
        "Optional: "
        + ", ".join(f"{name}={result['status']}" for name, result in optional.items())
    )
    compiler = report["compiler"]
    print(
        "Compiler names: "
        + (", ".join(compiler["available_names"]) if compiler["available_names"] else "none")
        + " (name-only probe)"
    )
    codegen = report["codegen"]
    print(
        "Codegen: "
        f"target={codegen.get('target')!r}, "
        f"available={','.join(codegen.get('available_targets', [])) or 'unknown'}, "
        f"cache={codegen.get('cache', {}).get('configuration', 'unknown')}"
    )
    gsl = report["gsl"]
    print(
        "GSL: "
        f"library-name={'present' if gsl['native_library_name_present'] else 'not-found'}, "
        "headers/full support=not-proved"
    )
    if imported.get("status") == "failed":
        print(f"Brian import error: {imported.get('error', 'unknown')}")
    if failures:
        print("Strict failures: " + ", ".join(failures))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report Brian2 imports, dependency versions, compiler names, target, cache state, and optional packages without mutation."
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return non-zero unless Python, Brian2 2.9.0, dependency constraints, required imports, and Brian import pass",
    )
    parser.add_argument(
        "--require-compiler",
        action="store_true",
        help="with --strict, also require a compiler executable name",
    )
    args = parser.parse_args(argv)
    report = build_report()
    failures = _strict_failures(report, args.require_compiler)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_compact(report, failures)
    return 1 if args.strict and failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
