#!/usr/bin/env python3
"""Map Khoj changed paths or capability names to focused pytest files.

This helper is intentionally read-only: it does not import Khoj, connect to a
Django database, start services, or execute pytest. It prints candidate test
files and a ready-to-copy command.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class Rule:
    name: str
    tests: tuple[str, ...]
    path_prefixes: tuple[str, ...] = ()
    path_contains: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    notes: str = ""


RULES: tuple[Rule, ...] = (
    Rule(
        name="cli",
        tests=("tests/test_cli.py",),
        path_prefixes=("src/khoj/utils/cli.py",),
        keywords=("cli", "argparse", "flags", "non-interactive", "console"),
        notes="Parser-only coverage; avoid `khoj --help` on unconfigured hosts.",
    ),
    Rule(
        name="markdown-parser",
        tests=("tests/test_markdown_to_entries.py",),
        path_prefixes=("src/khoj/processor/content/markdown/",),
        keywords=("markdown", "md", "parser"),
    ),
    Rule(
        name="org-parser",
        tests=("tests/test_org_to_entries.py", "tests/test_orgnode.py"),
        path_prefixes=("src/khoj/processor/content/org_mode/",),
        keywords=("org", "orgnode"),
    ),
    Rule(
        name="plaintext-parser",
        tests=("tests/test_plaintext_to_entries.py",),
        path_prefixes=("src/khoj/processor/content/plaintext/",),
        keywords=("plaintext", "html", "xml"),
    ),
    Rule(
        name="pdf-parser",
        tests=("tests/test_pdf_to_entries.py",),
        path_prefixes=("src/khoj/processor/content/pdf/",),
        keywords=("pdf", "ocr"),
        notes="OCR test coverage is currently skipped for performance.",
    ),
    Rule(
        name="docx-parser",
        tests=("tests/test_docx_to_entries.py",),
        path_prefixes=("src/khoj/processor/content/docx/",),
        keywords=("docx", "word document"),
    ),
    Rule(
        name="image-parser",
        tests=("tests/test_image_to_entries.py",),
        path_prefixes=("src/khoj/processor/content/images/",),
        keywords=("image", "jpg", "jpeg", "png", "ocr"),
    ),
    Rule(
        name="content-api",
        tests=("tests/test_client.py",),
        path_prefixes=("src/khoj/routers/api_content.py", "src/khoj/processor/content/"),
        keywords=("content api", "upload", "index update", "api/content", "api/update"),
    ),
    Rule(
        name="search",
        tests=("tests/test_text_search.py", "tests/test_client.py"),
        path_prefixes=("src/khoj/search_type/", "src/khoj/routers/api.py"),
        keywords=("search", "text search", "embedding", "cross encoder"),
        notes="Search tests can initialize heavier ML fixtures; choose specific cases when possible.",
    ),
    Rule(
        name="date-filter",
        tests=("tests/test_date_filter.py",),
        path_prefixes=("src/khoj/search_filter/date_filter.py",),
        keywords=("date filter", "natural date", "created", "updated"),
    ),
    Rule(
        name="file-filter",
        tests=("tests/test_file_filter.py",),
        path_prefixes=("src/khoj/search_filter/file_filter.py",),
        keywords=("file filter", "include file", "exclude file"),
    ),
    Rule(
        name="word-filter",
        tests=("tests/test_word_filter.py",),
        path_prefixes=("src/khoj/search_filter/word_filter.py",),
        keywords=("word filter", "include word", "exclude word"),
    ),
    Rule(
        name="grep-files",
        tests=("tests/test_grep_files.py",),
        path_contains=("grep_files",),
        keywords=("grep", "regex", "context lines"),
    ),
    Rule(
        name="helpers",
        tests=("tests/test_helpers.py",),
        path_prefixes=("src/khoj/utils/helpers.py",),
        keywords=("helpers", "utility", "webpage read"),
    ),
    Rule(
        name="conversation-utils",
        tests=("tests/test_conversation_utils.py",),
        path_prefixes=("src/khoj/processor/conversation/utils.py",),
        keywords=("conversation utils", "truncate", "json repair"),
    ),
    Rule(
        name="chat",
        tests=("tests/test_online_chat_actors.py", "tests/test_online_chat_director.py"),
        path_prefixes=(
            "src/khoj/routers/api_chat.py",
            "src/khoj/routers/research.py",
            "src/khoj/processor/conversation/",
            "src/khoj/processor/tools/",
        ),
        keywords=("chat", "director", "actor", "research", "online search", "tool"),
        notes="Many chat cases are chatquality/provider-sensitive; prefer selected tests first.",
    ),
    Rule(
        name="agents",
        tests=("tests/test_agents.py",),
        path_prefixes=("src/khoj/routers/api_agents.py",),
        path_contains=("Agent", "agent"),
        keywords=("agent", "knowledge base", "atomic update"),
    ),
    Rule(
        name="automation",
        tests=("tests/test_api_automation.py",),
        path_prefixes=("src/khoj/routers/api_automation.py",),
        keywords=("automation", "scheduled", "schedule"),
        notes="Current automation tests skip without the required provider key.",
    ),
    Rule(
        name="memory",
        tests=("tests/test_memory_settings.py",),
        path_prefixes=("src/khoj/routers/api_memories.py",),
        path_contains=("UserMemory", "memory"),
        keywords=("memory", "memories", "memory settings"),
    ),
    Rule(
        name="multi-user-auth",
        tests=("tests/test_multiple_users.py", "tests/test_client.py"),
        path_prefixes=("src/khoj/routers/auth.py", "src/khoj/routers/helpers.py"),
        path_contains=("KhojUser", "KhojApiUser", "Subscription"),
        keywords=("auth", "api token", "multi user", "subscription", "billing"),
    ),
    Rule(
        name="db-lock",
        tests=("tests/test_db_lock.py",),
        path_contains=("ProcessLock", "process lock"),
        keywords=("process lock", "db lock", "lock"),
    ),
    Rule(
        name="models-migrations",
        tests=("tests/test_client.py", "tests/test_db_lock.py"),
        path_prefixes=("src/khoj/database/models/", "src/khoj/database/migrations/", "src/khoj/database/admin.py"),
        keywords=("model", "migration", "admin", "django"),
        notes="Add model-owner tests such as agents, memory, search, or API tests based on the changed model.",
    ),
    Rule(
        name="database-adapters",
        tests=("tests/test_client.py", "tests/test_agents.py", "tests/test_memory_settings.py"),
        path_prefixes=("src/khoj/database/adapters/",),
        keywords=("adapter", "orm", "database adapter"),
        notes="Narrow to route/model-specific tests after identifying the adapter function.",
    ),
    Rule(
        name="frontend-web",
        tests=(),
        path_prefixes=("src/interface/web/",),
        keywords=("frontend", "web", "next", "react"),
        notes="Run the web package build/export only when dependency/build side effects are approved.",
    ),
    Rule(
        name="docs",
        tests=(),
        path_prefixes=("documentation/",),
        keywords=("docs", "documentation", "docusaurus"),
        notes="No backend tests are required for docs-only edits unless snippets or behavior changed.",
    ),
)


def normalize_input(value: str) -> str:
    return value.strip().replace("\\", "/")


def looks_like_path(value: str) -> bool:
    return "/" in value or value.endswith(".py") or value.endswith(".md") or value.endswith(".mdx")


def path_matches(rule: Rule, value: str) -> bool:
    normalized = normalize_input(value)
    path = PurePosixPath(normalized)
    path_text = path.as_posix()
    if any(path_text == prefix.rstrip("/") or path_text.startswith(prefix) for prefix in rule.path_prefixes):
        return True
    lower_path = path_text.lower()
    return any(fragment.lower() in lower_path for fragment in rule.path_contains)


def keyword_matches(rule: Rule, value: str) -> bool:
    lower_value = normalize_input(value).lower()
    return any(keyword.lower() in lower_value for keyword in rule.keywords)


def select_rules(items: Iterable[str]) -> list[Rule]:
    selected: list[Rule] = []
    for item in items:
        for rule in RULES:
            matched = path_matches(rule, item) if looks_like_path(item) else keyword_matches(rule, item)
            if matched and rule not in selected:
                selected.append(rule)
    return selected


def unique_tests(rules: Iterable[Rule]) -> list[str]:
    tests: list[str] = []
    for rule in rules:
        for test in rule.tests:
            if test not in tests:
                tests.append(test)
    return tests


def build_result(items: list[str]) -> dict[str, object]:
    rules = select_rules(items)
    tests = unique_tests(rules)
    notes = [f"{rule.name}: {rule.notes}" for rule in rules if rule.notes]
    command = "pytest " + " ".join(tests) if tests else "No pytest files mapped; inspect the change manually."
    return {
        "inputs": items,
        "matched_rules": [rule.name for rule in rules],
        "pytest_files": tests,
        "command": command,
        "notes": notes,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select focused Khoj pytest files for changed paths or capability names.")
    parser.add_argument("items", nargs="*", help="Changed file paths or capability names, e.g. src/khoj/routers/api_content.py markdown")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    parser.add_argument("--from-stdin", action="store_true", help="Read newline-delimited items from stdin and append CLI items.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    items = [normalize_input(item) for item in args.items if item.strip()]
    if args.from_stdin:
        items.extend(normalize_input(line) for line in sys.stdin if line.strip())

    if not items:
        print("Provide changed paths or capability names. Example:")
        print("  python scripts/select_focused_tests.py src/khoj/routers/api_content.py markdown")
        return 2

    result = build_result(items)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("Matched rules:")
    for rule_name in result["matched_rules"]:
        print(f"- {rule_name}")
    if not result["matched_rules"]:
        print("- none")

    print("\nCandidate pytest files:")
    for test_file in result["pytest_files"]:
        print(f"- {test_file}")
    if not result["pytest_files"]:
        print("- none")

    print(f"\nSuggested command:\n{result['command']}")

    notes = result["notes"]
    if notes:
        print("\nNotes:")
        for note in notes:
            print(f"- {note}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
