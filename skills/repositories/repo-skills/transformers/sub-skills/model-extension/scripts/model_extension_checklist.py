#!/usr/bin/env python3
"""Local checklist for Transformers model-extension changes.

The script performs static, local checks only. It does not call GitHub or make
network requests; policy items that require `gh` are printed as manual checks.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class Check:
    section: str
    item: str
    status: str
    detail: str


def path_exists(repo: Path, relative: str) -> bool:
    return (repo / relative).exists()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")


def add(checks: list[Check], section: str, item: str, status: str, detail: str) -> None:
    checks.append(Check(section=section, item=item, status=status, detail=detail))


def iter_model_files(repo: Path, model: str | None) -> Iterable[Path]:
    if not model:
        return []
    model_dir = repo / "src" / "transformers" / "models" / model
    if not model_dir.exists():
        return []
    return sorted(path for path in model_dir.rglob("*.py") if path.is_file())


def check_policy(repo: Path, checks: list[Check]) -> None:
    agents = repo / "AGENTS.md"
    if agents.exists():
        text = read_text(agents)
        add(checks, "policy", "AGENTS.md", "ok", "Repository guidance file is present.")
        for phrase in [
            "automatic banning",
            "gh issue view",
            "gh pr list",
            "AI assistance was used",
            "Do not raise PRs without human validation",
        ]:
            status = "ok" if phrase in text else "warn"
            add(checks, "policy", phrase, status, "Confirm this policy point before PR-ready output.")
    else:
        add(checks, "policy", "AGENTS.md", "warn", "AGENTS.md not found at repo root; verify contribution rules manually.")

    for command in [
        "gh issue view <issue_number> --repo huggingface/transformers --comments",
        "gh pr list --repo huggingface/transformers --state open --search \"<issue_number> in:body\"",
        "gh pr list --repo huggingface/transformers --state open --search \"<short area keywords>\"",
    ]:
        add(checks, "policy", "manual duplicate check", "manual", command)


def check_structure(repo: Path, model: str | None, checks: list[Check]) -> None:
    required_roots = [
        "src/transformers/models",
        "src/transformers/models/auto",
        "tests/models/auto",
        "utils",
        "docs/source/en",
    ]
    for relative in required_roots:
        add(
            checks,
            "structure",
            relative,
            "ok" if path_exists(repo, relative) else "warn",
            "Expected Transformers repository path.",
        )

    if not model:
        add(checks, "structure", "--model", "manual", "Pass --model to inspect model-specific files.")
        return

    model_dir = repo / "src" / "transformers" / "models" / model
    add(
        checks,
        "structure",
        f"src/transformers/models/{model}",
        "ok" if model_dir.exists() else "warn",
        "Model package directory should exist for in-tree model work.",
    )

    modular = model_dir / f"modular_{model}.py"
    modeling = model_dir / f"modeling_{model}.py"
    config = model_dir / f"configuration_{model}.py"
    if modular.exists():
        add(checks, "modular", "modular source", "ok", f"Edit source of truth: {modular.as_posix()}")
        add(
            checks,
            "modular",
            "generated modeling",
            "manual" if modeling.exists() else "warn",
            "Generated modeling file is overwritten by modular conversion; do not hand-edit as source of truth.",
        )
    elif modeling.exists() or config.exists():
        add(checks, "modular", "legacy/manual path", "manual", "No modular file found; justify manual architecture path.")
    else:
        add(checks, "modular", "model files", "warn", "No modular, modeling, or configuration file found for this model.")


def check_copied_from(repo: Path, model: str | None, checks: list[Check]) -> None:
    copied_hits: list[str] = []
    for path in iter_model_files(repo, model):
        text = read_text(path)
        if "# Copied from" in text:
            copied_hits.append(path.relative_to(repo).as_posix())
    if copied_hits:
        add(
            checks,
            "copied-from",
            "copied blocks",
            "manual",
            "Do not edit copied blocks directly: " + ", ".join(copied_hits[:8]),
        )
    elif model:
        add(checks, "copied-from", "copied blocks", "ok", "No copied-from markers found in inspected model files.")
    else:
        add(checks, "copied-from", "copied blocks", "manual", "Pass --model to inspect copied-from markers.")


def check_auto_mappings(repo: Path, model: str | None, checks: list[Check]) -> None:
    auto_mapping = repo / "src" / "transformers" / "models" / "auto" / "auto_mappings.py"
    if not auto_mapping.exists():
        add(checks, "auto", "auto_mappings.py", "warn", "Cannot inspect config mapping file.")
        return

    text = read_text(auto_mapping)
    add(checks, "auto", "auto_mappings.py", "ok", "Config and processor mapping source is present.")
    if model:
        key = model.replace("_", "-")
        underscore_key = model.replace("-", "_")
        if f'"{key}"' in text or f'"{underscore_key}"' in text:
            add(checks, "auto", "config mapping", "ok", "Model-like key appears in auto_mappings.py.")
        else:
            add(checks, "auto", "config mapping", "warn", "No obvious model key found; verify CONFIG_MAPPING_NAMES and model_type.")

    for relative in [
        "src/transformers/models/auto/modeling_auto.py",
        "src/transformers/models/auto/tokenization_auto.py",
        "src/transformers/models/auto/processing_auto.py",
        "src/transformers/models/auto/image_processing_auto.py",
        "src/transformers/models/auto/video_processing_auto.py",
    ]:
        add(checks, "auto", relative, "ok" if path_exists(repo, relative) else "warn", "Inspect if this modality changed.")


def check_tests_docs(repo: Path, model: str | None, checks: list[Check]) -> None:
    if model:
        tests_dir = repo / "tests" / "models" / model
        docs_file = repo / "docs" / "source" / "en" / "model_doc" / f"{model}.md"
        add(
            checks,
            "tests",
            f"tests/models/{model}",
            "ok" if tests_dir.exists() else "warn",
            "Expected focused model tests for in-tree model additions.",
        )
        add(
            checks,
            "docs",
            f"docs/source/en/model_doc/{model}.md",
            "ok" if docs_file.exists() else "warn",
            "Expected model documentation page or a documented reason it is not needed.",
        )
    else:
        add(checks, "tests", "model tests", "manual", "Pass --model to inspect focused tests.")
        add(checks, "docs", "model docs", "manual", "Pass --model to inspect model docs.")

    for relative in [
        "docs/source/en/add_new_model.md",
        "docs/source/en/modular_transformers.md",
        "docs/source/en/add_new_pipeline.md",
        "docs/source/en/testing.md",
    ]:
        add(checks, "docs", relative, "ok" if path_exists(repo, relative) else "warn", "Source guidance expected in this repo.")


def check_quality_commands(checks: list[Check]) -> None:
    commands = [
        "pytest tests/models/<model>/ -v",
        "RUN_SLOW=1 pytest tests/models/<model>/ -v",
        "python utils/check_auto.py",
        "python utils/check_modular_conversion.py --files src/transformers/models/<model>/modular_<model>.py",
        "make style",
        "make typing",
        "make fix-repo",
        "make check-repo",
    ]
    for command in commands:
        add(checks, "quality", command, "manual", "Run when relevant to the files changed.")


def build_checks(repo: Path, model: str | None) -> list[Check]:
    checks: list[Check] = []
    check_policy(repo, checks)
    check_structure(repo, model, checks)
    check_copied_from(repo, model, checks)
    check_auto_mappings(repo, model, checks)
    check_tests_docs(repo, model, checks)
    check_quality_commands(checks)
    return checks


def print_text(checks: list[Check]) -> None:
    current_section = None
    for check in checks:
        if check.section != current_section:
            current_section = check.section
            print(f"\n[{current_section}]")
        print(f"- {check.status.upper():6} {check.item}: {check.detail}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a local static checklist for Transformers model-extension work. No network calls are made."
    )
    parser.add_argument("--repo", default=".", help="Path to the Transformers repository root. Defaults to current directory.")
    parser.add_argument("--model", help="Snake-case model directory name to inspect, such as llama or my_new_model.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Exit with status 1 when any warning is found. Manual items do not fail by themselves.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    checks = build_checks(repo, args.model)

    if args.json:
        print(json.dumps([asdict(check) for check in checks], indent=2, sort_keys=True))
    else:
        print(f"Transformers model-extension checklist for: {repo}")
        if args.model:
            print(f"Model: {args.model}")
        print_text(checks)
        print("\nNo GitHub network calls were made. Run the listed gh commands manually before PR-ready output.")

    if args.fail_on_warn and any(check.status == "warn" for check in checks):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
