#!/usr/bin/env python3
"""Read-only validator for a Cookiecutter Data Science generated project.

The checker verifies core layout, option-dependent files when expectations are
provided, leftover Jinja delimiters in text files, and key Makefile rules. It is
safe by default: it does not install dependencies, run project code, contact
cloud storage, or mutate files.

Example:
  python validate_generated_project.py ./my_project --module-name my_project --expect-docs mkdocs --expect-tests pytest
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".css",
    ".env",
    ".gitignore",
    ".html",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
}
JINJA_MARKERS = ("{{", "}}", "{%", "%}")


def _errors_for_missing(root: Path, rel_paths: list[str]) -> list[str]:
    return [f"missing required path: {rel}" for rel in rel_paths if not (root / rel).exists()]


def _guess_module(root: Path) -> str | None:
    candidates: list[str] = []
    for child in root.iterdir():
        if not child.is_dir() or child.name in {"data", "docs", "models", "notebooks", "references", "reports", "tests"}:
            continue
        if (child / "__init__.py").is_file():
            candidates.append(child.name)
    if len(candidates) == 1:
        return candidates[0]
    return None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _auto_docs(root: Path) -> str:
    return "mkdocs" if (root / "docs" / "mkdocs.yml").exists() else "none"


def _auto_tests(root: Path) -> str:
    test_file = root / "tests" / "test_data.py"
    if not test_file.exists():
        return "none"
    text = _read_text(test_file)
    if "import pytest" in text:
        return "pytest"
    if "unittest" in text:
        return "unittest"
    return "unknown"


def _auto_scaffold(root: Path, module: str) -> str:
    return "yes" if (root / module / "config.py").exists() else "no"


def _auto_lint(root: Path) -> str:
    if (root / "setup.cfg").exists():
        return "flake8-black-isort"
    text = _read_text(root / "pyproject.toml") if (root / "pyproject.toml").exists() else ""
    if "[tool.ruff]" in text:
        return "ruff"
    return "unknown"


def _check_no_curlies(root: Path) -> list[str]:
    errors: list[str] = []
    ignored_dirs = {".git", ".venv", ".pixi", "__pycache__", ".pytest_cache", "htmlcov", "build", "dist"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignored_dirs]
        for filename in filenames:
            path = Path(dirpath) / filename
            if path.suffix not in TEXT_SUFFIXES:
                continue
            try:
                text = _read_text(path)
            except OSError:
                continue
            if any(marker in text for marker in JINJA_MARKERS):
                errors.append(f"unrendered Jinja marker in {path.relative_to(root)}")
    return errors


def _check_makefile(root: Path, expect_scaffold: str, expect_tests: str) -> list[str]:
    makefile = root / "Makefile"
    if not makefile.exists():
        return ["missing Makefile"]
    text = _read_text(makefile)
    errors: list[str] = []
    for rule in ["requirements", "clean", "lint", "format", "create_environment", "help"]:
        if rule == "create_environment" and "create_environment:" not in text:
            # environment_manager=none legitimately omits this rule.
            continue
        if rule + ":" not in text:
            errors.append(f"Makefile does not expose expected rule or documented omission needs review: {rule}")
    if expect_tests != "none" and "test:" not in text:
        errors.append("expected test rule but Makefile has none")
    if expect_tests == "none" and "test:" in text:
        errors.append("expected no test rule but Makefile contains test")
    if expect_scaffold == "yes" and "data:" not in text:
        errors.append("expected scaffold data rule but Makefile has none")
    if expect_scaffold == "no" and "data:" in text:
        errors.append("expected no scaffold data rule but Makefile contains data")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a CCDS-generated project tree without mutating it.")
    parser.add_argument("project", type=Path, help="Generated project root.")
    parser.add_argument("--module-name", help="Expected generated Python module/package name. Auto-detected when omitted.")
    parser.add_argument("--expect-docs", choices=["mkdocs", "none", "auto"], default="auto")
    parser.add_argument("--expect-tests", choices=["pytest", "unittest", "none", "auto"], default="auto")
    parser.add_argument("--expect-scaffold", choices=["yes", "no", "auto"], default="auto")
    parser.add_argument("--expect-lint", choices=["ruff", "flake8-black-isort", "auto"], default="auto")
    parser.add_argument("--skip-jinja-scan", action="store_true", help="Skip scanning text files for leftover Jinja delimiters.")
    args = parser.parse_args()

    root = args.project.expanduser().resolve()
    errors: list[str] = []
    if not root.is_dir():
        print(f"ERROR: project root is not a directory: {root}", file=sys.stderr)
        return 2

    module = args.module_name or _guess_module(root)
    if not module:
        errors.append("could not auto-detect a single module directory; pass --module-name")
        module = "<module>"

    core_dirs = [
        "data",
        "data/external",
        "data/interim",
        "data/processed",
        "data/raw",
        "docs",
        "models",
        "notebooks",
        "references",
        "reports",
        "reports/figures",
    ]
    core_files = ["Makefile", "README.md", "pyproject.toml", ".env", ".gitignore"]
    if module != "<module>":
        core_dirs.append(module)
        core_files.append(f"{module}/__init__.py")
    errors.extend(_errors_for_missing(root, core_dirs + core_files))

    expect_docs = _auto_docs(root) if args.expect_docs == "auto" else args.expect_docs
    expect_tests = _auto_tests(root) if args.expect_tests == "auto" else args.expect_tests
    expect_scaffold = _auto_scaffold(root, module) if args.expect_scaffold == "auto" and module != "<module>" else args.expect_scaffold
    expect_lint = _auto_lint(root) if args.expect_lint == "auto" else args.expect_lint

    if expect_docs == "mkdocs":
        errors.extend(_errors_for_missing(root, ["docs/mkdocs.yml", "docs/README.md", "docs/docs/index.md", "docs/docs/getting-started.md"]))
    elif expect_docs == "none" and (root / "docs" / "mkdocs.yml").exists():
        errors.append("expected docs=none but docs/mkdocs.yml exists")

    if expect_tests in {"pytest", "unittest"}:
        errors.extend(_errors_for_missing(root, ["tests", "tests/test_data.py"]))
        if (root / "tests" / "test_data.py").exists():
            text = _read_text(root / "tests" / "test_data.py")
            if expect_tests == "pytest" and "import pytest" not in text:
                errors.append("expected pytest starter test but tests/test_data.py does not import pytest")
            if expect_tests == "unittest" and "unittest" not in text:
                errors.append("expected unittest starter test but tests/test_data.py does not use unittest")
    elif expect_tests == "none" and (root / "tests").exists():
        errors.append("expected no tests directory but tests/ exists")

    if module != "<module>":
        scaffold_files = [
            f"{module}/config.py",
            f"{module}/dataset.py",
            f"{module}/features.py",
            f"{module}/modeling/__init__.py",
            f"{module}/modeling/train.py",
            f"{module}/modeling/predict.py",
            f"{module}/plots.py",
        ]
        if expect_scaffold == "yes":
            errors.extend(_errors_for_missing(root, scaffold_files))
        elif expect_scaffold == "no":
            for rel in scaffold_files:
                if (root / rel).exists():
                    errors.append(f"expected scaffold disabled but found {rel}")

    if expect_lint == "ruff":
        if (root / "setup.cfg").exists():
            errors.append("expected Ruff linting but setup.cfg exists")
        pyproject = _read_text(root / "pyproject.toml") if (root / "pyproject.toml").exists() else ""
        if "[tool.ruff]" not in pyproject:
            errors.append("expected Ruff configuration in pyproject.toml")
    elif expect_lint == "flake8-black-isort":
        errors.extend(_errors_for_missing(root, ["setup.cfg"]))
        pyproject = _read_text(root / "pyproject.toml") if (root / "pyproject.toml").exists() else ""
        if "[tool.black]" not in pyproject or "[tool.isort]" not in pyproject:
            errors.append("expected Black and isort configuration in pyproject.toml")

    errors.extend(_check_makefile(root, expect_scaffold, expect_tests))
    if not args.skip_jinja_scan:
        errors.extend(_check_no_curlies(root))

    if errors:
        print("CCDS generated-project validation failed:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1

    print("CCDS generated-project validation passed")
    print(f"root={root}")
    print(f"module={module}")
    print(f"docs={expect_docs} tests={expect_tests} scaffold={expect_scaffold} lint={expect_lint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
