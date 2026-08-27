#!/usr/bin/env python3
"""Smoke-check a FlashText install.

This helper is safe to run from any directory. It imports the installed
`flashtext` package, exercises the core add/extract/replace/load workflows,
and exits non-zero on failure.

Prerequisites:
  - `flashtext` installed in the active Python environment.
  - Optional: `--repo-root` if you want to prepend a local checkout before
    import.

Examples:
  python scripts/check_install.py
  python scripts/check_install.py --json
  python scripts/check_install.py --repo-root /path/to/checkout
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def import_keyword_processor(repo_root: str | None):
    if repo_root:
        sys.path.insert(0, repo_root)
    try:
        from flashtext import KeywordProcessor
    except ImportError as exc:
        raise SystemExit(
            "flashtext is not importable. Install it with `python -m pip install flashtext` "
            "or `python -m pip install -e .` from a checkout."
        ) from exc
    return KeywordProcessor


def assert_equal(label: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def run_smoke_checks(KeywordProcessor):
    checks = []

    kp = KeywordProcessor()
    kp.add_keyword("Big Apple", "New York")
    kp.add_keyword("Bay Area")
    assert_equal(
        "basic extract",
        kp.extract_keywords("I love Big Apple and Bay Area."),
        ["New York", "Bay Area"],
    )
    assert_equal(
        "basic replace",
        kp.replace_keywords("I love Big Apple and Bay Area."),
        "I love New York and Bay Area.",
    )
    checks.append("basic extract/replace")

    kp_cs = KeywordProcessor(case_sensitive=True)
    kp_cs.add_keyword("Big Apple", "New York")
    kp_cs.add_keyword("Bay Area")
    assert_equal(
        "case-sensitive extract",
        kp_cs.extract_keywords("I love big Apple and Bay Area."),
        ["Bay Area"],
    )
    checks.append("case-sensitive matching")

    kp_fuzzy = KeywordProcessor()
    kp_fuzzy.add_keyword("skype", "messenger")
    assert_equal(
        "fuzzy extract",
        kp_fuzzy.extract_keywords("hello, do you have skpe ?", span_info=True, max_cost=1),
        [("messenger", 19, 23)],
    )
    checks.append("fuzzy matching")

    kp_bulk = KeywordProcessor()
    kp_bulk.add_keywords_from_dict({"java": ["java_2e", "java programing"]})
    kp_bulk.add_keywords_from_list(["python"])
    assert_equal("bulk len before removal", len(kp_bulk), 3)
    assert_equal("bulk get_keyword", kp_bulk.get_keyword("java_2e"), "java")
    assert_equal("bulk contains", "python" in kp_bulk, True)
    assert_equal("bulk item access", kp_bulk["python"], "python")
    kp_bulk.remove_keywords_from_list(["python"])
    assert_equal("bulk len after removal", len(kp_bulk), 2)
    assert_equal("bulk contains after removal", "python" in kp_bulk, False)
    assert_equal(
        "bulk keyword map",
        kp_bulk.get_all_keywords(),
        {"java_2e": "java", "java programing": "java"},
    )
    checks.append("bulk add/remove and inspection")

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as handle:
        handle.write("java_2e=>java\n")
        handle.write("product management techniques=>product management\n")
        file_path = Path(handle.name)
    try:
        kp_file = KeywordProcessor()
        kp_file.add_keyword_from_file(str(file_path))
        sentence = "I know java_2e and product management techniques"
        assert_equal(
            "file load extract",
            kp_file.extract_keywords(sentence),
            ["java", "product management"],
        )
        assert_equal(
            "file load replace",
            kp_file.replace_keywords(sentence),
            "I know java and product management",
        )
    finally:
        file_path.unlink(missing_ok=True)
    checks.append("file loading")

    kp_boundary = KeywordProcessor()
    kp_boundary.add_keyword("Big Apple")
    assert_equal(
        "boundary default",
        kp_boundary.extract_keywords("I love Big Apple/Bay Area."),
        ["Big Apple"],
    )
    kp_boundary.add_non_word_boundary("/")
    assert_equal(
        "boundary override",
        kp_boundary.extract_keywords("I love Big Apple/Bay Area."),
        [],
    )
    checks.append("boundary handling")

    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe FlashText smoke check.")
    parser.add_argument(
        "--repo-root",
        help="Optional checkout root to add to sys.path before importing flashtext.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary instead of a human-readable report.",
    )
    args = parser.parse_args()

    KeywordProcessor = import_keyword_processor(args.repo_root)
    checks = run_smoke_checks(KeywordProcessor)

    try:
        pkg_version = version("flashtext")
    except PackageNotFoundError:
        pkg_version = "unknown"

    summary = {
        "package": "flashtext",
        "version": pkg_version,
        "checks": checks,
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"FlashText {summary['version']} smoke checks passed")
        for item in checks:
            print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
