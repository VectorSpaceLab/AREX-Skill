#!/usr/bin/env python3
"""Suggest focused DataChain test commands from changed path names.

Default mode prints suggestions only. Pass --run to execute the suggested pytest
commands; broad nox sessions are never run automatically.

Examples:
  python select_tests.py src/datachain/cli/parser/__init__.py
  python select_tests.py src/datachain/lib/convert/python_to_sql.py src/datachain/sql/types.py
  python select_tests.py --run src/datachain/func/string.py
"""

import argparse
import subprocess
import sys
from pathlib import Path

RULES: list[tuple[tuple[str, ...], list[str]]] = [
    (
        ("src/datachain/cli", "src/datachain/studio.py", "src/datachain/remote/studio.py"),
        [
            "pytest tests/unit/test_cli_parsing.py -q",
            "pytest tests/unit/test_cli_skill.py -q",
            "pytest tests/unit/test_cli_datasets.py -q",
            "pytest tests/test_cli_e2e.py -q",
        ],
    ),
    (
        ("src/datachain/lib/dc/datachain.py",),
        [
            "pytest tests/unit/lib/test_datachain.py -q",
            "pytest tests/func/test_datachain.py -q",
            "pytest tests/func/test_datachain_merge.py -q",
            "pytest tests/func/test_union.py -q",
        ],
    ),
    (
        ("src/datachain/func", "src/datachain/sql"),
        [
            "pytest tests/unit/test_func.py -q",
            "pytest tests/unit/sql -q",
            "pytest tests/func/functions -q",
        ],
    ),
    (
        ("src/datachain/lib/signal_schema.py", "src/datachain/lib/convert", "src/datachain/data_storage"),
        [
            "pytest tests/unit/lib/test_signal_schema.py -q",
            "pytest tests/unit/lib/test_python_to_sql.py -q",
            "pytest tests/unit/lib/test_sql_to_python.py -q",
            "pytest tests/func/test_signal_schema.py -q",
            "pytest tests/func/test_to_csv.py -q",
            "pytest tests/func/test_to_json.py -q",
            "pytest tests/func/test_to_database.py -q",
        ],
    ),
    (
        ("src/datachain/lib/file.py", "src/datachain/client", "src/datachain/fs"),
        [
            "pytest tests/unit/lib/test_file.py -q",
            "pytest tests/unit/test_client.py -q",
            "pytest tests/unit/test_client_s3.py -q",
            "pytest tests/unit/test_client_gcs.py -q",
            "pytest tests/unit/test_client_azure.py -q",
            "pytest tests/func/test_file.py -q",
        ],
    ),
    (
        ("src/datachain/llm",),
        [
            "pytest tests/unit/lib/test_llm.py -q",
            "pytest tests/func/test_llm.py -q",
        ],
    ),
    (
        ("src/datachain/skill",),
        [
            "pytest tests/unit/test_cli_skill.py -q",
            "pytest tests/unit/test_skill_knowledge_collect.py -q",
            "pytest tests/unit/test_skill_knowledge_snapshot.py -q",
            "pytest tests/unit/test_skill_jobs_scripts.py -q",
        ],
    ),
    (
        ("pyproject.toml", "noxfile.py", "setup.py", "setup.cfg"),
        [
            "pytest tests/unit/test_module_exports.py -q",
            "pytest tests/test_import_time.py -q",
            "python -m pip check",
        ],
    ),
    (
        ("docs/",),
        [
            "nox -s docs",
        ],
    ),
]

DEFAULT_COMMANDS = [
    "pytest tests/unit/test_module_exports.py -q",
    "pytest tests/unit/test_cli_parsing.py -q",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print focused pytest/nox commands for DataChain changed paths. "
            "Default mode does not execute tests."
        )
    )
    parser.add_argument("paths", nargs="*", help="Changed files or directories.")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run pytest/python commands that were suggested. Nox commands are printed but not run.",
    )
    return parser


def normalize(path: str) -> str:
    return Path(path).as_posix().lstrip("./")


def suggest(paths: list[str]) -> list[str]:
    if not paths:
        return DEFAULT_COMMANDS
    commands: list[str] = []
    for raw in paths:
        path = normalize(raw)
        for prefixes, suggested in RULES:
            if any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in prefixes):
                for cmd in suggested:
                    if cmd not in commands:
                        commands.append(cmd)
    return commands or DEFAULT_COMMANDS


def run_commands(commands: list[str]) -> int:
    status = 0
    for command in commands:
        if command.startswith("nox "):
            print(f"skip-run: {command}  # run manually after focused pytest passes")
            continue
        print(f"running: {command}")
        completed = subprocess.run(command.split(), check=False)  # noqa: S603,S607 - fixed suggestions.
        if completed.returncode != 0:
            status = completed.returncode
            break
    return status


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    commands = suggest(args.paths)
    print("Suggested DataChain validation commands:")
    for command in commands:
        print(f"  {command}")
    if args.run:
        return run_commands(commands)
    print("Default mode only prints suggestions. Re-run with --run to execute non-nox commands.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
