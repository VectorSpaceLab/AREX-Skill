#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Observal Contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only Observal repository inspector for the repo-development skill.

The helper summarizes repository markers, package versions, Make targets, test
layout, selected evidence files, and repository scripts as JSON. It does not
write files, call Docker, call the network, invoke project code, or print the
absolute local checkout path.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

MARKER_PATHS = (
    "AGENTS.md",
    "CONTRIBUTING.md",
    "AI_POLICY.md",
    "Makefile",
    "SETUP.md",
    "SECURITY.md",
    "pyproject.toml",
    "observal-server/pyproject.toml",
    "package.json",
    "web/package.json",
    ".pre-commit-config.yaml",
    ".release.toml",
    "CHANGELOG.md",
    "REUSE.toml",
    "docker/docker-compose.yml",
    "observal_cli",
    "observal-server",
    "web",
    "packages/observal-shared",
    "scripts",
    "tools/release.py",
    "tests",
    "tests/e2e",
    "observal_cli/tests",
    "observal-server/tests",
)

EVIDENCE_FILES = (
    "AGENTS.md",
    "CONTRIBUTING.md",
    "AI_POLICY.md",
    "Makefile",
    "SETUP.md",
    "docs/DEVELOPMENT_GUIDE.md",
    "docs/testing/Testing_Guide.md",
    "docs/code-review.md",
    "SECURITY.md",
    "pyproject.toml",
    "observal-server/pyproject.toml",
    "package.json",
    "web/package.json",
    ".pre-commit-config.yaml",
    ".release.toml",
    ".github/pull_request_template.md",
)

KEY_WEB_DEPENDENCIES = (
    "@tanstack/react-query",
    "@tanstack/react-router",
    "@vitejs/plugin-react",
    "react",
    "react-dom",
    "typescript",
    "vite",
    "eslint",
    "@playwright/test",
)

MAX_READ_BYTES = 512 * 1024


def _read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) > MAX_READ_BYTES:
        data = data[:MAX_READ_BYTES]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace")


def _sha256_12(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    except OSError:
        return None


def _line_count(text: str | None) -> int | None:
    if text is None:
        return None
    return len(text.splitlines())


def _first_markdown_heading(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or None
    return None


def _python_docstring(text: str) -> str | None:
    try:
        module = ast.parse(text)
    except SyntaxError:
        return None
    docstring = ast.get_docstring(module)
    if not docstring:
        return None
    return " ".join(docstring.strip().split())[:240]


def _comment_headline(text: str) -> str | None:
    comments: list[str] = []
    for line in text.splitlines()[:80]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#!") or stripped.startswith("# SPDX"):
            continue
        if stripped.startswith("#"):
            comments.append(stripped.lstrip("# ").strip())
        elif comments:
            break
    if not comments:
        return None
    return " ".join(comments)[:240]


def _headline(relative_path: str, text: str | None) -> str | None:
    if text is None:
        return None
    suffix = Path(relative_path).suffix.lower()
    if suffix == ".md":
        return _first_markdown_heading(text)
    if suffix == ".py":
        return _python_docstring(text) or _comment_headline(text)
    if suffix == ".sh":
        return _comment_headline(text)
    if suffix in {".toml", ".yaml", ".yml", ".json"}:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith(("#", "//", "{", "}", "[")):
                return stripped[:240]
    return None


def _file_summary(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    exists = path.exists()
    summary: dict[str, Any] = {"path": relative_path, "exists": exists}
    if not exists:
        return summary
    summary["type"] = "directory" if path.is_dir() else "file"
    if path.is_dir():
        try:
            summary["direct_children"] = len(list(path.iterdir()))
        except OSError:
            summary["direct_children"] = None
        return summary
    text = _read_text(path)
    summary.update(
        {
            "bytes": path.stat().st_size,
            "lines": _line_count(text),
            "sha256_12": _sha256_12(path),
            "headline": _headline(relative_path, text),
        }
    )
    return summary


def _load_toml(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    text = _read_text(path)
    if text is None:
        return {}
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        return {"_parse_error": str(exc)}


def _load_json(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    text = _read_text(path)
    if text is None:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"_parse_error": str(exc)}
    return data if isinstance(data, dict) else {"_unexpected_json_type": type(data).__name__}


def _project_summary(pyproject: dict[str, Any]) -> dict[str, Any]:
    project = pyproject.get("project", {}) if isinstance(pyproject, dict) else {}
    tool = pyproject.get("tool", {}) if isinstance(pyproject, dict) else {}
    ruff = tool.get("ruff", {}) if isinstance(tool, dict) else {}
    pytest_options = tool.get("pytest", {}).get("ini_options", {}) if isinstance(tool, dict) else {}
    dependency_groups = pyproject.get("dependency-groups", {}) if isinstance(pyproject, dict) else {}
    optional_deps = project.get("optional-dependencies", {}) if isinstance(project, dict) else {}
    return {
        "name": project.get("name"),
        "version": project.get("version"),
        "requires_python": project.get("requires-python"),
        "license": project.get("license"),
        "dependency_count": len(project.get("dependencies", []) or []),
        "optional_dependency_groups": sorted(optional_deps) if isinstance(optional_deps, dict) else [],
        "dependency_groups": sorted(dependency_groups) if isinstance(dependency_groups, dict) else [],
        "ruff_line_length": ruff.get("line-length"),
        "ruff_target_version": ruff.get("target-version"),
        "pytest_testpaths": pytest_options.get("testpaths"),
        "pytest_asyncio_mode": pytest_options.get("asyncio_mode"),
    }


def _package_summary(package_json: dict[str, Any]) -> dict[str, Any]:
    dependencies = package_json.get("dependencies", {})
    dev_dependencies = package_json.get("devDependencies", {})
    scripts = package_json.get("scripts", {})
    picked: dict[str, str] = {}
    if isinstance(dependencies, dict):
        picked.update({key: dependencies[key] for key in KEY_WEB_DEPENDENCIES if key in dependencies})
    if isinstance(dev_dependencies, dict):
        picked.update({key: dev_dependencies[key] for key in KEY_WEB_DEPENDENCIES if key in dev_dependencies})
    return {
        "name": package_json.get("name"),
        "version": package_json.get("version"),
        "private": package_json.get("private"),
        "package_manager": package_json.get("packageManager"),
        "engines": package_json.get("engines", {}),
        "script_names": sorted(scripts) if isinstance(scripts, dict) else [],
        "dependency_count": len(dependencies) if isinstance(dependencies, dict) else None,
        "dev_dependency_count": len(dev_dependencies) if isinstance(dev_dependencies, dict) else None,
        "key_dependency_versions": picked,
    }


def _make_targets(root: Path) -> list[dict[str, str]]:
    text = _read_text(root / "Makefile")
    if text is None:
        return []
    targets: list[dict[str, str]] = []
    for line in text.splitlines():
        if "##" not in line or line.startswith("\t"):
            continue
        left, description = line.split("##", 1)
        if ":" not in left:
            continue
        target = left.split(":", 1)[0].strip()
        if not target or target.startswith(".") or " " in target or "$" in target:
            continue
        targets.append({"target": target, "description": description.strip()})
    return targets


def _count_files(root: Path, relative_dir: str, pattern: str) -> int | None:
    directory = root / relative_dir
    if not directory.exists() or not directory.is_dir():
        return None
    try:
        return sum(1 for path in directory.rglob(pattern) if path.is_file())
    except OSError:
        return None


def _sample_files(root: Path, relative_dir: str, pattern: str, limit: int = 12) -> list[str]:
    directory = root / relative_dir
    if not directory.exists() or not directory.is_dir():
        return []
    try:
        return sorted(str(path.relative_to(root)) for path in directory.rglob(pattern) if path.is_file())[:limit]
    except OSError:
        return []


def _test_layout(root: Path) -> dict[str, Any]:
    return {
        "root_py_tests": _count_files(root, "tests", "test_*.py"),
        "server_local_py_tests": _count_files(root, "observal-server/tests", "test_*.py"),
        "cli_local_py_tests": _count_files(root, "observal_cli/tests", "test_*.py"),
        "playwright_specs": _count_files(root, "tests/e2e", "*.spec.ts"),
        "sample_root_tests": _sample_files(root, "tests", "test_*.py"),
        "sample_server_local_tests": _sample_files(root, "observal-server/tests", "test_*.py"),
        "sample_cli_local_tests": _sample_files(root, "observal_cli/tests", "test_*.py"),
        "sample_e2e_specs": _sample_files(root, "tests/e2e", "*.spec.ts"),
    }


def _script_paths(root: Path) -> list[str]:
    paths: list[Path] = []
    scripts_dir = root / "scripts"
    if scripts_dir.exists():
        paths.extend(sorted(scripts_dir.glob("*.py")))
        paths.extend(sorted(scripts_dir.glob("*.sh")))
    release = root / "tools/release.py"
    if release.exists():
        paths.append(release)
    return [str(path.relative_to(root)) for path in sorted(paths)]


def _package_versions(root: Path) -> dict[str, Any]:
    root_pyproject = _load_toml(root, "pyproject.toml")
    server_pyproject = _load_toml(root, "observal-server/pyproject.toml")
    root_package = _load_json(root, "package.json")
    web_package = _load_json(root, "web/package.json")
    release_manifest = _load_toml(root, ".release.toml")
    return {
        "root_python_project": _project_summary(root_pyproject),
        "server_python_project": _project_summary(server_pyproject),
        "root_node_package": _package_summary(root_package),
        "web_node_package": _package_summary(web_package),
        "release_manifest": {
            "version": release_manifest.get("version"),
            "channel": release_manifest.get("channel"),
            "previous_tag": release_manifest.get("previous_tag"),
            "commit_count": release_manifest.get("commit_count"),
        },
    }


def inspect_repo(root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "repo_root_label": root.name,
        "markers": {relative_path: (root / relative_path).exists() for relative_path in MARKER_PATHS},
        "package_versions": _package_versions(root),
        "make_targets": _make_targets(root),
        "test_layout": _test_layout(root),
        "selected_evidence_files": [_file_summary(root, relative_path) for relative_path in EVIDENCE_FILES],
        "repo_scripts": [_file_summary(root, relative_path) for relative_path in _script_paths(root)],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="repository root to inspect")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    args = parser.parse_args()

    root = Path(args.repo_root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(json.dumps({"error": "repo root is not a directory"}), file=sys.stderr)
        return 2

    data = inspect_repo(root)
    if args.pretty:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(json.dumps(data, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
