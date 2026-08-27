#!/usr/bin/env python3
"""Inspect SimpleITK source build metadata without mutating the checkout.

The helper reads a SimpleITK source tree and prints JSON with the package
metadata, version components, key CMake options, wrapping options, and selected
maintenance-file presence. It does not configure CMake, install packages,
download dependencies, or write files.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


OPTION_RE = re.compile(r'option\s*\(\s*([A-Za-z0-9_]+)\s+"([^"]*)"\s+([^\)\s]+)', re.MULTILINE)
SET_RE_TEMPLATE = r"set\s*\(\s*{name}\s+([^\)\s#]+)"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print read-only JSON metadata for a SimpleITK source checkout."
    )
    parser.add_argument(
        "repo_root",
        nargs="?",
        default=".",
        help="Path to a SimpleITK source checkout. Defaults to the current directory.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args(argv)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")


def parse_pyproject(text: str) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    simple_patterns = {
        "project_name": r"(?m)^name\s*=\s*\"([^\"]+)\"",
        "requires_python": r"(?m)^requires-python\s*=\s*\"([^\"]+)\"",
        "build_backend": r"(?m)^build-backend\s*=\s*\"([^\"]+)\"",
        "scikit_build_minimum": r"(?m)^minimum-version\s*=\s*\"([^\"]+)\"",
        "cmake_requirement": r"(?m)^cmake\.version\s*=\s*\"([^\"]+)\"",
        "cmake_build_type": r"(?m)^cmake\.build-type\s*=\s*\"([^\"]+)\"",
    }
    for key, pattern in simple_patterns.items():
        match = re.search(pattern, text)
        if match:
            facts[key] = match.group(1)

    defines: dict[str, str] = {}
    in_define_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[tool.scikit-build.cmake.define]":
            in_define_block = True
            continue
        if in_define_block and stripped.startswith("["):
            break
        if in_define_block and "=" in stripped and not stripped.startswith("#"):
            name, value = stripped.split("=", 1)
            defines[name.strip()] = value.strip().strip('"')
    if defines:
        facts["cmake_defines"] = defines
    return facts


def parse_version(version_text: str) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for name in [
        "SimpleITK_VERSION_MAJOR",
        "SimpleITK_VERSION_MINOR",
        "SimpleITK_VERSION_PATCH",
        "SimpleITK_VERSION_TWEAK",
    ]:
        pattern = SET_RE_TEMPLATE.format(name=re.escape(name))
        match = re.search(pattern, version_text)
        result[name] = match.group(1).strip('"') if match else None
    parts = [
        result.get("SimpleITK_VERSION_MAJOR"),
        result.get("SimpleITK_VERSION_MINOR"),
        result.get("SimpleITK_VERSION_PATCH"),
    ]
    result["base_version"] = ".".join(part for part in parts if part)
    return result


def parse_options(text: str) -> list[dict[str, str]]:
    options = []
    for match in OPTION_RE.finditer(text):
        options.append(
            {
                "name": match.group(1),
                "description": " ".join(match.group(2).split()),
                "default": match.group(3).strip('"'),
            }
        )
    return options


def collect_wrapping_languages(language_text: str) -> dict[str, Any]:
    languages = sorted(set(re.findall(r"option\(WRAP_([A-Z]+)\s+\"Wrap", language_text)))
    return {
        "wrap_default_declared": "option(\n  WRAP_DEFAULT" in language_text or "option(WRAP_DEFAULT" in language_text,
        "languages": languages,
        "language_option_count": len(languages),
    }


def file_presence(repo_root: Path) -> dict[str, bool]:
    paths = [
        "pyproject.toml",
        "Version.cmake",
        "CMakeLists.txt",
        "CMake/sitkLanguageOptions.cmake",
        "Wrapping/CMakeLists.txt",
        "Wrapping/Python/CMakeLists.txt",
        "SuperBuild/CMakeLists.txt",
        "SuperBuild/External_Elastix.cmake",
        "Utilities/SetupForDevelopment.sh",
        ".pre-commit-config.yaml",
        ".readthedocs.yml",
        "docs/requirements.txt",
    ]
    return {path: (repo_root / path).exists() for path in paths}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = Path(args.repo_root).expanduser().resolve()

    required = ["pyproject.toml", "CMakeLists.txt", "Version.cmake"]
    missing = [path for path in required if not (repo_root / path).is_file()]
    if missing:
        print(
            json.dumps(
                {
                    "ok": False,
                    "repo_root": str(repo_root),
                    "error": "missing required SimpleITK metadata files",
                    "missing": missing,
                },
                indent=2 if args.pretty else None,
                sort_keys=True,
            )
        )
        return 2

    pyproject_text = read_text(repo_root / "pyproject.toml")
    cmake_text = read_text(repo_root / "CMakeLists.txt")
    version_text = read_text(repo_root / "Version.cmake")
    language_text = read_text(repo_root / "CMake" / "sitkLanguageOptions.cmake") if (repo_root / "CMake" / "sitkLanguageOptions.cmake").exists() else ""

    result = {
        "ok": True,
        "project": "SimpleITK",
        "pyproject": parse_pyproject(pyproject_text),
        "version": parse_version(version_text),
        "top_level_cmake_options": parse_options(cmake_text),
        "wrapping": collect_wrapping_languages(language_text),
        "important_files": file_presence(repo_root),
        "read_only": True,
        "notes": [
            "This helper reads metadata only; it does not configure, build, install, download, or modify files.",
            "Use source-build commands only after deciding that binary wheels or conda-forge packages are insufficient.",
        ],
    }
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
