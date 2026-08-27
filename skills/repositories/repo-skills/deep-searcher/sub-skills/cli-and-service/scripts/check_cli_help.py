#!/usr/bin/env python3
"""Check DeepSearcher CLI help in a fresh temporary working directory.

This helper runs the root, query, and load help screens without contacting
provider APIs. It uses a dummy OPENAI_API_KEY, a temporary working directory,
and optional console-script discovery so it can surface help-time initialization
failures without depending on the original repository checkout.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path
from typing import Sequence

HELP_COMMANDS = {
    "root": (),
    "query": ("query",),
    "load": ("load",),
}
EXPECTED_HELP_TOKENS = {
    "root": ("usage: deepsearcher", "query", "load"),
    "query": ("--max_iter",),
    "load": (
        "--batch_size",
        "--collection_name",
        "--collection_desc",
        "--force_new_collection",
    ),
}
ENTRYPOINT_CHOICES = ("auto", "module", "console")
COMMAND_CHOICES = ("root", "query", "load", "all")


@dataclass
class HelpProbe:
    command: str
    entrypoint_requested: str
    entrypoint_used: str
    ok: bool
    exit_code: int
    stdout: str
    stderr: str
    note: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run DeepSearcher CLI help in a temp cwd and classify common initialization failures."
    )
    parser.add_argument(
        "--command",
        choices=COMMAND_CHOICES,
        default="all",
        help="Which help screen to probe (default: all).",
    )
    parser.add_argument(
        "--entrypoint",
        choices=ENTRYPOINT_CHOICES,
        default="auto",
        help="How to invoke the CLI: module, console script, or auto-detect (default: auto).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=90,
        help="Subprocess timeout in seconds for each help probe.",
    )
    parser.add_argument(
        "--no-dummy-openai-key",
        action="store_true",
        help="Do not inject a dummy OPENAI_API_KEY when the variable is unset.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    return parser.parse_args()


def get_console_script() -> str:
    try:
        for entry_point in metadata.entry_points(group="console_scripts"):
            if entry_point.name == "deepsearcher":
                return f"{entry_point.name}={entry_point.value}"
    except Exception:  # pragma: no cover - metadata API differs slightly by Python version
        return "unavailable"
    return "missing"


def classify_failure(stderr: str) -> str:
    lowered = stderr.lower()
    if "openaierror" in lowered or "missing credentials" in lowered:
        return "provider credentials are missing or the default OpenAI config is active"
    if "scrapeoptions" in lowered:
        return "the installed FireCrawl client is incompatible with this checkout"
    if "milvus-lite" in lowered and "required" in lowered:
        return "local Milvus Lite support is missing"
    if "showcollectionsresponse has no \"shards_num\" field" in lowered:
        return "pymilvus and milvus-lite versions are mismatched"
    if "pkg_resources" in lowered:
        return "setuptools is too new for the pinned milvus-lite release"
    if "datadirlockederror" in lowered:
        return "the local Milvus Lite database is locked by another process"
    if "module not found" in lowered or "modulenotfounderror" in lowered:
        return "a required package is missing from the environment"
    return "the help probe failed for an environment-specific reason"


def find_console_script() -> str | None:
    local_candidate = Path(sys.executable).resolve().parent / "deepsearcher"
    if local_candidate.exists():
        return str(local_candidate)
    if os.name == "nt":
        windows_candidate = local_candidate.with_suffix(".exe")
        if windows_candidate.exists():
            return str(windows_candidate)
    path_candidate = shutil.which("deepsearcher")
    if path_candidate:
        return path_candidate
    return None


def resolve_entrypoint(mode: str) -> tuple[str, Sequence[str], str]:
    console_path = find_console_script()
    if mode == "console":
        if console_path:
            return "console", (console_path,), ""
        return "module", (sys.executable, "-m", "deepsearcher.cli"), "console script missing; using module fallback"
    if mode == "module":
        return "module", (sys.executable, "-m", "deepsearcher.cli"), ""
    if console_path:
        return "console", (console_path,), ""
    return "module", (sys.executable, "-m", "deepsearcher.cli"), "console script missing; using module fallback"


def run_probe(command: str, entrypoint_mode: str, timeout: int, inject_dummy_key: bool) -> HelpProbe:
    entrypoint_used, prefix, fallback_note = resolve_entrypoint(entrypoint_mode)
    help_args = HELP_COMMANDS[command] + ("--help",)
    with tempfile.TemporaryDirectory(prefix="deepsearcher-cli-help-") as tmp:
        env = os.environ.copy()
        if inject_dummy_key:
            env.setdefault("OPENAI_API_KEY", "dummy")
        command_line = list(prefix) + list(help_args)
        try:
            completed = subprocess.run(
                command_line,
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            note = f"help probe timed out after {timeout} seconds"
            if fallback_note:
                note = f"{fallback_note}; {note}"
            return HelpProbe(
                command=command,
                entrypoint_requested=entrypoint_mode,
                entrypoint_used=entrypoint_used,
                ok=False,
                exit_code=-1,
                stdout=stdout.strip(),
                stderr=stderr.strip(),
                note=note,
            )

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    note = fallback_note
    missing_tokens = [token for token in EXPECTED_HELP_TOKENS[command] if token not in stdout]
    ok = completed.returncode == 0 and not missing_tokens
    if completed.returncode != 0:
        classified = classify_failure(stderr)
        note = f"{note}; {classified}" if note else classified
    elif missing_tokens:
        token_note = f"help output is missing expected tokens: {', '.join(missing_tokens)}"
        note = f"{note}; {token_note}" if note else token_note
    else:
        note = note or "help completed and expected command flags were present"

    return HelpProbe(
        command=command,
        entrypoint_requested=entrypoint_mode,
        entrypoint_used=entrypoint_used,
        ok=ok,
        exit_code=completed.returncode,
        stdout=stdout,
        stderr=stderr,
        note=note,
    )


def choose_commands(selection: str) -> list[str]:
    if selection == "all":
        return ["root", "query", "load"]
    return [selection]


def main() -> int:
    args = parse_args()
    if args.timeout <= 0:
        raise SystemExit("--timeout must be a positive integer")
    probes = [
        run_probe(command, args.entrypoint, args.timeout, not args.no_dummy_openai_key)
        for command in choose_commands(args.command)
    ]
    ok = all(probe.ok for probe in probes)
    report = {
        "ok": ok,
        "console_script": get_console_script(),
        "entrypoint_requested": args.entrypoint,
        "probes": [asdict(probe) for probe in probes],
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("DeepSearcher CLI help check")
        print("===========================")
        print(f"console script: {report['console_script']}")
        for probe in probes:
            print(f"- {probe.command}: {'OK' if probe.ok else 'FAIL'} (exit {probe.exit_code}, entrypoint={probe.entrypoint_used})")
            if probe.note:
                print(f"  note: {probe.note}")
            if probe.stderr and not probe.ok:
                print(f"  stderr: {probe.stderr}")
        print(f"overall: {'PASS' if ok else 'FAIL'}")

    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
