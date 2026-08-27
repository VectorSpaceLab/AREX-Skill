#!/usr/bin/env python3
"""Perform help-only or static checks of an installed Mellea CLI.

This script has two deliberately safe modes:

* ``static`` reads installed package metadata and parses CLI modules as Python
  source. It does not import command callbacks.
* ``help`` executes only fixed, allowlisted ``m ... --help`` commands without a
  shell. It cannot start a server, call a backend, rewrite files, train, or
  upload.
"""

from __future__ import annotations

import argparse
import ast
import importlib.metadata
import importlib.util
import shutil
import subprocess
import sys
from importlib.machinery import PathFinder
from pathlib import Path

EXPECTED_VERSION = "0.8.0.dev0"
EXPECTED_ENTRY_POINT = "cli.m:cli"

HELP_TARGETS: dict[str, tuple[str, ...]] = {
    "root": ("--help",),
    "serve": ("serve", "--help"),
    "alora": ("alora", "--help"),
    "alora-train": ("alora", "train", "--help"),
    "alora-upload": ("alora", "upload", "--help"),
    "alora-add-readme": ("alora", "add-readme", "--help"),
    "decompose": ("decompose", "--help"),
    "decompose-run": ("decompose", "run", "--help"),
    "eval": ("eval", "--help"),
    "eval-run": ("eval", "run", "--help"),
    "fix": ("fix", "--help"),
    "fix-genslots": ("fix", "genslots", "--help"),
}

# Markers are intentionally simple and are checked only after successful AST
# parsing. They verify the installed command and serving surface without loading
# Typer, FastAPI, Uvicorn, a backend, or an application module.
STATIC_MARKERS: dict[tuple[str, str], tuple[str, ...]] = {
    ("cli", "m.py"): (
        'cli.command(name="serve")',
        "cli.add_typer(alora_app)",
        "cli.add_typer(decompose_app)",
        "cli.add_typer(eval_app)",
        "cli.add_typer(fix_app)",
    ),
    ("cli", "serve/commands.py"): ("def serve(",),
    ("cli", "serve/app.py"): (
        '@app.get("/health")',
        'route_path = "/v1/chat/completions"',
        "uvicorn.run(",
    ),
    ("cli", "serve/schema_converter.py"): ("def json_schema_to_pydantic(",),
    ("cli", "serve/streaming.py"): ("async def stream_chat_completion_chunks(",),
    ("cli", "alora/commands.py"): (
        'alora_app.command("train")',
        'alora_app.command("upload")',
        'alora_app.command("add-readme")',
    ),
    ("cli", "decompose/__init__.py"): ('app.command(name="run"',),
    ("cli", "eval/commands.py"): ('eval_app.command("run")',),
    ("cli", "fix/__init__.py"): ('fix_app.command("genslots")',),
    ("mellea", "serve/models.py"): (
        "class ChatMessage(",
        "class TextContent(",
        "class ImageUrlContent(",
        "class InputAudioContent(",
    ),
}

DEPENDENCY_PROBES: dict[str, tuple[str, ...]] = {
    "cli": ("typer",),
    "server": ("fastapi", "uvicorn"),
    "hf/alora": ("torch", "datasets", "peft", "transformers", "trl", "huggingface_hub"),
}


def _package_root(name: str) -> Path:
    """Locate an installed package without importing it."""
    spec = PathFinder.find_spec(name, sys.path)
    if spec is None or not spec.submodule_search_locations:
        raise RuntimeError(f"installed package {name!r} was not found")
    return Path(next(iter(spec.submodule_search_locations)))


def _metadata_check(failures: list[str]) -> None:
    """Check Mellea distribution metadata and the console entry point."""
    try:
        distribution = importlib.metadata.distribution("mellea")
    except importlib.metadata.PackageNotFoundError:
        failures.append("the mellea distribution is not installed")
        return

    version = distribution.version
    print(f"Mellea version: {version}")
    if version != EXPECTED_VERSION:
        print(
            f"NOTE: this skill targets {EXPECTED_VERSION}; use installed help as "
            "the authority for a different version."
        )

    entry_points = [
        ep
        for ep in distribution.entry_points
        if ep.group == "console_scripts" and ep.name == "m"
    ]
    if not entry_points:
        failures.append("console entry point 'm' is missing")
    elif all(ep.value != EXPECTED_ENTRY_POINT for ep in entry_points):
        values = ", ".join(sorted(ep.value for ep in entry_points))
        failures.append(
            f"console entry point 'm' does not resolve to {EXPECTED_ENTRY_POINT!r}; found {values}"
        )
    else:
        print(f"Console entry point: m -> {EXPECTED_ENTRY_POINT}")


def _dependency_check() -> None:
    """Report optional dependency availability without importing packages."""
    print("Dependency availability (static find-spec only):")
    for extra, modules in DEPENDENCY_PROBES.items():
        missing = [name for name in modules if importlib.util.find_spec(name) is None]
        if missing:
            print(f"- {extra}: INCOMPLETE (missing {', '.join(missing)})")
        else:
            print(f"- {extra}: available")


def _source_check(failures: list[str]) -> None:
    """Parse installed source modules and check fixed surface markers."""
    roots: dict[str, Path] = {}
    for package in {package for package, _ in STATIC_MARKERS}:
        try:
            roots[package] = _package_root(package)
        except RuntimeError as exc:
            failures.append(str(exc))

    checked = 0
    for (package, relative), markers in STATIC_MARKERS.items():
        root = roots.get(package)
        if root is None:
            continue
        path = root / relative
        label = f"{package}/{relative}"
        if not path.is_file():
            failures.append(f"missing installed module {label}")
            continue
        try:
            source = path.read_text(encoding="utf-8")
            ast.parse(source, filename=label)
        except (OSError, SyntaxError) as exc:
            failures.append(f"cannot parse {label}: {exc}")
            continue

        checked += 1
        for marker in markers:
            if marker not in source:
                failures.append(f"{label}: expected surface marker absent: {marker}")

    print(f"Installed modules parsed: {checked}/{len(STATIC_MARKERS)}")


def static_check() -> int:
    """Run read-only metadata, dependency, and source checks."""
    failures: list[str] = []
    _metadata_check(failures)
    _dependency_check()
    _source_check(failures)

    if failures:
        print("CLI static check: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("CLI static check: PASS")
    print("No command callback, backend, network request, or server was started.")
    return 0


def _resolve_targets(requested: list[str]) -> list[str]:
    """Expand the fixed 'all' target while preserving a stable order."""
    if "all" in requested:
        return list(HELP_TARGETS)
    return list(dict.fromkeys(requested))


def help_check(targets: list[str], timeout: float) -> int:
    """Run fixed shell-free help commands and nothing else."""
    executable = shutil.which("m")
    if executable is None:
        print(
            "The 'm' executable is not on PATH. Activate the intended environment "
            "or run this checker through that environment.",
            file=sys.stderr,
        )
        return 1

    failures = 0
    for target in _resolve_targets(targets):
        argv = [executable, *HELP_TARGETS[target]]
        display = "m " + " ".join(HELP_TARGETS[target])
        print(f"\n=== {display} ===")
        try:
            result = subprocess.run(
                argv,
                check=False,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            print(f"Help probe timed out after {timeout:g}s", file=sys.stderr)
            failures += 1
            continue

        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        if result.returncode != 0:
            print(
                f"Help probe failed for {target!r} with exit {result.returncode}",
                file=sys.stderr,
            )
            failures += 1

    if failures:
        print(f"CLI help check: FAIL ({failures} target(s))", file=sys.stderr)
        return 1
    print("CLI help check: PASS")
    print("Only fixed commands ending in --help were executed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the safe checker."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("static", "help"),
        required=True,
        help="static parses installed files; help renders allowlisted CLI help",
    )
    parser.add_argument(
        "--target",
        action="append",
        choices=(*HELP_TARGETS, "all"),
        default=[],
        help="help target; repeat to inspect several, or use all",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="per-help-command timeout in seconds (default: 15)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch one explicitly safe checker mode."""
    args = build_parser().parse_args(argv)
    if args.timeout <= 0:
        print("--timeout must be positive", file=sys.stderr)
        return 2
    if args.mode == "static":
        if args.target:
            print("--target is valid only with --mode help", file=sys.stderr)
            return 2
        return static_check()
    if not args.target:
        print("--mode help requires at least one --target", file=sys.stderr)
        return 2
    return help_check(args.target, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
