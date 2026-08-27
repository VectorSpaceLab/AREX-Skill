#!/usr/bin/env python3
"""Validate the UnrealCV command schema, generated docs, and API snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from generate_command_schema import generate_schema, render_rst
from update_public_api_snapshot import build_snapshot


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3] / "references" / "unrealcv-source"


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated docs and command coverage")
    parser.add_argument("--repo-root", default=str(_default_repo_root()))
    parser.add_argument("--schema", default="docs/reference/command_schema.json")
    parser.add_argument("--generated-rst", default="docs/reference/commands_generated.rst.txt")
    parser.add_argument("--snapshot", default="client/python/unrealcv/public_api_snapshot.json")
    parser.add_argument("--strict", action="store_true", help="Fail when any coverage gate is incomplete")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.is_dir():
        raise SystemExit(f"Repository root not found: {repo_root}")
    schema_path = repo_root / args.schema
    generated_rst_path = repo_root / args.generated_rst
    snapshot_path = repo_root / args.snapshot

    expected_schema = generate_schema(repo_root)
    current_schema = json.loads(schema_path.read_text(encoding="utf-8"))
    expected_rst = render_rst(expected_schema)
    current_rst = _load_text(generated_rst_path)
    expected_snapshot = build_snapshot(repo_root)
    current_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

    schema_commands = {item["command"] for item in expected_schema.get("commands", [])}
    generated_docs = current_rst
    handwritten_docs = _load_text(repo_root / "docs/reference/commands.rst")
    missing_generated_docs = sorted(command for command in schema_commands if f"``{command}``" not in generated_docs)
    handwritten_count = sum(command in handwritten_docs for command in schema_commands)

    python_docs = _load_text(repo_root / "docs/reference/python_api.rst")
    conf_text = _load_text(repo_root / "docs/conf.py")
    python_autodoc_covered = (
        ".. automodule:: unrealcv.api" in python_docs
        and ":members:" in python_docs
        and "'client', 'python'" in conf_text
    )

    total = len(schema_commands)
    print("Command and API coverage report")
    print(f"- generated_command_docs: {total - len(missing_generated_docs)}/{total}")
    print(f"- hand_written_command_mentions: {handwritten_count}/{total}")
    print(f"- schema_matches_generator: {'yes' if current_schema == expected_schema else 'no'}")
    print(f"- generated_rst_matches_generator: {'yes' if current_rst == expected_rst else 'no'}")
    print(f"- api_snapshot_matches_generator: {'yes' if current_snapshot == expected_snapshot else 'no'}")
    print(f"- local_python_api_autodoc: {'yes' if python_autodoc_covered else 'no'}")

    failures = []
    if current_schema != expected_schema:
        failures.append("command schema is out of date")
    if current_rst != expected_rst:
        failures.append("generated command RST is out of date")
    if current_snapshot != expected_snapshot:
        failures.append("public API snapshot is out of date")
    if missing_generated_docs:
        failures.append(f"generated docs missing {len(missing_generated_docs)} commands")
    if not python_autodoc_covered:
        failures.append("Python API autodoc is not configured to import the local client")

    if args.strict and failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    if failures:
        for failure in failures:
            print(f"WARN: {failure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
