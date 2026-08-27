#!/usr/bin/env python3
"""Read-only ODS CLI dispatch surface checker.

Parses an ods-cli Bash file, lists the top-level dispatch commands, and assigns
one of: help-only, read-only, mutating. The script never executes ods-cli.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

VALID_CATEGORIES = {"help-only", "read-only", "mutating"}

# Conservative classification of the current ODS top-level CLI. Mixed command
# families are marked mutating when any normal subcommand can change host state;
# read-only forms are listed in notes/read_only_forms.
CLASSIFICATION: dict[str, dict[str, object]] = {
    "gpu": {
        "category": "mutating",
        "read_only_forms": ["gpu status", "gpu topology", "gpu assignment", "gpu validate", "gpu reassign --dry-run"],
        "mutating_forms": ["gpu reassign", "gpu reassign --auto", "gpu reassign --manual"],
        "notes": "GPU inspection is read-only except reassignment, which can update .env.",
    },
    "status": {"category": "read-only", "read_only_forms": ["status", "status --json"], "notes": "Reads compose and health state."},
    "status-json": {"category": "read-only", "read_only_forms": ["status-json"], "notes": "Alias for status --json."},
    "list": {"category": "read-only", "read_only_forms": ["list", "list --json"], "notes": "Lists service registry state."},
    "enable": {"category": "mutating", "mutating_forms": ["enable <service>"], "notes": "Enables extension compose files and regenerates compose flags."},
    "disable": {"category": "mutating", "mutating_forms": ["disable <service>"], "notes": "Stops/toggles extension compose files and preserves data."},
    "purge": {"category": "mutating", "mutating_forms": ["purge <service>"], "notes": "Destructive service-data deletion after confirmation."},
    "preset": {
        "category": "mutating",
        "read_only_forms": ["preset list", "preset diff <a> <b>"],
        "mutating_forms": ["preset save", "preset load", "preset delete", "preset export", "preset import"],
        "notes": "Mixed preset family; load overwrites config/extension state.",
    },
    "mode": {
        "category": "mutating",
        "read_only_forms": ["mode"],
        "mutating_forms": ["mode local", "mode cloud", "mode hybrid"],
        "notes": "Mode changes update .env and may enable LiteLLM.",
    },
    "model": {
        "category": "mutating",
        "read_only_forms": ["model current", "model list"],
        "mutating_forms": ["model swap <tier>"],
        "notes": "Swap uses host-agent model activation and can change model state.",
    },
    "remote-provider": {
        "category": "mutating",
        "read_only_forms": ["remote-provider status", "remote-provider plan", "remote-provider test", "remote-provider peer-models list", "remote-provider peer-models download-status"],
        "mutating_forms": ["remote-provider configure", "remote-provider disable", "remote-provider remove", "remote-provider peer-models download", "remote-provider peer-models load", "remote-provider peer-models cancel-download", "remote-provider peer-models delete --yes"],
        "notes": "Mixed remote lifecycle family; raw secrets should never be argv.",
    },
    "stt": {
        "category": "mutating",
        "read_only_forms": ["stt current", "stt status"],
        "mutating_forms": ["stt download [MODEL]"],
        "notes": "Download populates Whisper model cache.",
    },
    "backup": {
        "category": "mutating",
        "read_only_forms": ["backup verify <id>", "backup --list"],
        "mutating_forms": ["backup", "backup --delete <id>"],
        "notes": "Default backup writes artifacts; verify/list are read-only.",
    },
    "restore": {
        "category": "mutating",
        "read_only_forms": ["restore --list", "restore --dry-run <id>"],
        "mutating_forms": ["restore <id>", "restore --force <id>"],
        "notes": "Real restore can overwrite data/config and stop containers.",
    },
    "rollback": {"category": "mutating", "mutating_forms": ["rollback"], "notes": "Restores pre-update state and restarts services."},
    "logs": {"category": "read-only", "read_only_forms": ["logs <service> [lines]"], "notes": "Tails Docker logs and may block."},
    "restart": {"category": "mutating", "mutating_forms": ["restart [service]", "restart --rebuild-images"], "notes": "Recreates/restarts containers."},
    "repair": {"category": "mutating", "mutating_forms": ["repair voice", "repair hermes-workers", "repair rootless-ownership"], "notes": "Starts services, prunes workers, or changes ownership."},
    "start": {"category": "mutating", "mutating_forms": ["start [service]", "start --rebuild-images"], "notes": "Starts containers and may run hooks."},
    "stop": {"category": "mutating", "mutating_forms": ["stop [service]"], "notes": "Stops containers or the stack."},
    "update": {"category": "mutating", "read_only_forms": ["update --dry-run"], "mutating_forms": ["update", "update --force", "update --rebuild-images"], "notes": "Pulls/recreates services after a snapshot."},
    "shell": {"category": "mutating", "mutating_forms": ["shell <service>"], "notes": "Interactive shell inside a container."},
    "config": {"category": "mutating", "read_only_forms": ["config show", "config validate"], "mutating_forms": ["config edit"], "notes": "Mixed family; edit opens .env for mutation."},
    "chat": {"category": "read-only", "read_only_forms": ["chat <message>"], "notes": "Sends a local inference request; consumes resources but does not change config."},
    "benchmark": {"category": "read-only", "read_only_forms": ["benchmark"], "notes": "Runs a local performance request; no config mutation."},
    "doctor": {"category": "read-only", "read_only_forms": ["doctor", "doctor --json", "doctor --report <path>"], "notes": "Writes a diagnostic report but does not change ODS state."},
    "audit": {"category": "read-only", "read_only_forms": ["audit", "audit --json", "audit --strict", "audit <service>"], "notes": "Reads extension manifests/compose contracts."},
    "template": {"category": "mutating", "read_only_forms": ["template list", "template preview <id>"], "mutating_forms": ["template apply <id>"], "notes": "Apply enables services."},
    "agent": {"category": "mutating", "read_only_forms": ["agent status", "agent logs"], "mutating_forms": ["agent start", "agent stop", "agent restart"], "notes": "Manages host-agent service/process."},
    "help": {"category": "help-only", "read_only_forms": ["help", "--help", "-h"], "notes": "Prints usage."},
    "version": {"category": "help-only", "read_only_forms": ["version", "--version", "-v"], "notes": "Prints version."},
}

ALIAS_CANONICAL = {
    "g": "gpu",
    "s": "status",
    "ls": "list",
    "p": "preset",
    "m": "mode",
    "log": "logs",
    "l": "logs",
    "r": "restart",
    "fix": "repair",
    "u": "update",
    "sh": "shell",
    "cfg": "config",
    "c": "chat",
    "bench": "benchmark",
    "b": "benchmark",
    "diag": "doctor",
    "d": "doctor",
    "tmpl": "template",
    "h": "help",
    "--help": "help",
    "-h": "help",
    "v": "version",
    "--version": "version",
    "-v": "version",
}

MUTATION_HINTS = re.compile(
    r"\b(rm\s+-rf|mv\s+|cp\s+|docker\s+compose\s+(?:up|down|stop|restart|pull)|_env_set|systemctl\s+(?:start|stop|restart|disable)|launchctl\s+(?:bootstrap|bootout)|curl\b.*\s-X\s+POST)\b"
)


@dataclass
class CommandRecord:
    command: str
    aliases: list[str]
    function: str
    category: str
    read_only_forms: list[str]
    mutating_forms: list[str]
    notes: str
    source_line: int


def parse_dispatch(text: str) -> list[tuple[int, list[str], str, str]]:
    """Return (line, aliases, function/body, raw body) for main case entries."""
    lines = text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if re.match(r'^case "\$\{1:-help\}" in$', line.strip()):
            start = idx
            break
    if start is None:
        raise ValueError('could not find top-level case "${1:-help}" dispatch')

    entries: list[tuple[int, list[str], str, str]] = []
    for offset, line in enumerate(lines[start + 1 :], start + 2):
        stripped = line.strip()
        if stripped == "esac":
            break
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r'([^)]*)\)\s*(.*?)\s*;;\s*$', stripped)
        if not match:
            continue
        labels = [part.strip() for part in match.group(1).split("|")]
        if labels == ["*"]:
            continue
        body = match.group(2)
        func_match = re.search(r'\b(cmd_[A-Za-z0-9_]+)\b', body)
        function = func_match.group(1) if func_match else ("builtin-help" if "cmd_help" in body else "inline")
        entries.append((offset, labels, function, body))
    return entries


def canonical_for(labels: Iterable[str]) -> str:
    first = next(iter(labels))
    return ALIAS_CANONICAL.get(first, first)


def classify(command: str, labels: list[str], function: str, body: str, function_bodies: dict[str, str]) -> dict[str, object]:
    info = CLASSIFICATION.get(command)
    if info is not None:
        return info

    # Fallback for newly added commands: be conservative if implementation or
    # dispatch body looks mutating. New commands should be added to the table.
    impl = function_bodies.get(function, "")
    if "cmd_help" in body or command in {"help", "version"}:
        return {"category": "help-only", "read_only_forms": labels, "notes": "Inline help/version-like dispatch."}
    if MUTATION_HINTS.search(body) or MUTATION_HINTS.search(impl):
        return {"category": "mutating", "mutating_forms": labels, "notes": "Unclassified command with mutation-like implementation; classify explicitly."}
    return {"category": "read-only", "read_only_forms": labels, "notes": "Unclassified command without obvious mutation hints; classify explicitly."}


def extract_function_bodies(text: str) -> dict[str, str]:
    names = [(m.group(1), m.start()) for m in re.finditer(r'^(cmd_[A-Za-z0-9_]+)\(\)\s*\{', text, re.MULTILINE)]
    bodies: dict[str, str] = {}
    for idx, (name, start) in enumerate(names):
        end = names[idx + 1][1] if idx + 1 < len(names) else len(text)
        bodies[name] = text[start:end]
    return bodies


def records_for(path: Path) -> tuple[list[CommandRecord], list[str]]:
    text = path.read_text(encoding="utf-8")
    function_bodies = extract_function_bodies(text)
    entries = parse_dispatch(text)
    warnings: list[str] = []
    records: list[CommandRecord] = []
    seen: set[str] = set()

    for line, labels, function, body in entries:
        command = canonical_for(labels)
        info = classify(command, labels, function, body, function_bodies)
        category = str(info.get("category", ""))
        if category not in VALID_CATEGORIES:
            warnings.append(f"{command}: invalid category {category!r}")
            category = "mutating"
        if command not in CLASSIFICATION:
            warnings.append(f"{command}: no explicit classification table entry")
        if command in seen:
            warnings.append(f"{command}: duplicate canonical dispatch entry")
        seen.add(command)
        aliases = [label for label in labels if label != command]
        records.append(CommandRecord(
            command=command,
            aliases=aliases,
            function=function,
            category=category,
            read_only_forms=list(info.get("read_only_forms", [])),
            mutating_forms=list(info.get("mutating_forms", [])),
            notes=str(info.get("notes", "")),
            source_line=line,
        ))

    if not records:
        warnings.append("no dispatch commands parsed")
    return records, warnings


def print_text(path: Path, records: list[CommandRecord], warnings: list[str]) -> None:
    print(f"ods-cli: {path}")
    print(f"parsed commands: {len(records)}")
    print()
    for category in ("help-only", "read-only", "mutating"):
        group = [r for r in records if r.category == category]
        print(f"{category} ({len(group)})")
        for rec in group:
            alias_text = f" aliases={','.join(rec.aliases)}" if rec.aliases else ""
            print(f"  - {rec.command}{alias_text} [{rec.function}, line {rec.source_line}]")
            if rec.read_only_forms:
                print(f"      read-only/help forms: {', '.join(rec.read_only_forms)}")
            if rec.mutating_forms:
                print(f"      mutating forms: {', '.join(rec.mutating_forms)}")
            if rec.notes:
                print(f"      notes: {rec.notes}")
        print()
    if warnings:
        print("warnings:", file=sys.stderr)
        for warning in warnings:
            print(f"  - {warning}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parse ODS ods-cli dispatch commands and classify risk without executing the CLI.")
    parser.add_argument("path", nargs="?", help="Path to ods-cli (alternative to --ods-cli).")
    parser.add_argument("--ods-cli", dest="ods_cli", help="Path to ods-cli to parse.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if parsing warnings are found.")
    args = parser.parse_args(argv)

    raw_path = args.ods_cli or args.path
    if not raw_path:
        parser.error("provide --ods-cli PATH or positional PATH")
    path = Path(raw_path)
    if not path.is_file():
        print(f"error: ods-cli not found: {path}", file=sys.stderr)
        return 2

    try:
        records, warnings = records_for(path)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    payload = {
        "ods_cli": str(path),
        "command_count": len(records),
        "commands": [asdict(record) for record in records],
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text(path, records, warnings)

    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
