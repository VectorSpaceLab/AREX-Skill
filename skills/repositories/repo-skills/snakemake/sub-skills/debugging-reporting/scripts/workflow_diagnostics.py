#!/usr/bin/env python3
"""Create a safe Snakemake diagnostics command plan and optionally run it.

The script is intentionally self-contained and only shells out to the active
`snakemake` executable or `python -m snakemake`. It does not depend on the
Snakemake source checkout.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable


SNAKEMAKE_FLAGS = {
    "dry-run": ["--cores", "1", "--dry-run", "--printshellcmds"],
    "lint-json": ["--lint", "json"],
    "summary": ["--summary"],
    "detailed-summary": ["--detailed-summary"],
    "dag": ["--dag"],
    "rulegraph": ["--rulegraph"],
    "filegraph": ["--filegraph"],
    "debug-dag": ["--debug-dag", "--cores", "1", "--dry-run"],
}

OUTPUT_FILES = {
    "dry-run": "dry-run.txt",
    "lint-json": "lint.json",
    "summary": "summary.tsv",
    "detailed-summary": "detailed-summary.tsv",
    "dag": "dag.dot",
    "rulegraph": "rulegraph.dot",
    "filegraph": "filegraph.dot",
    "debug-dag": "debug-dag.txt",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plan or run safe Snakemake diagnostics: dry-run, lint JSON, "
            "summaries, graph outputs, and debug-DAG output."
        )
    )
    parser.add_argument(
        "--snakefile",
        default="Snakefile",
        help="Snakefile path to pass with --snakefile when it is not the default Snakefile.",
    )
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="Target file or rule to include. Repeat for multiple targets. Defaults to Snakemake's default target.",
    )
    parser.add_argument(
        "--outdir",
        default="diagnostics",
        help="Directory for generated diagnostic outputs when --run is used.",
    )
    parser.add_argument(
        "--snakemake-cmd",
        default="snakemake",
        help="Snakemake command to invoke. Use 'python -m snakemake' if the console script is unavailable.",
    )
    parser.add_argument(
        "--include",
        choices=sorted(SNAKEMAKE_FLAGS),
        action="append",
        help="Only include this diagnostic. Repeat to select several. Defaults to all diagnostics.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run commands and write outputs. Without this flag, print a JSON command plan only.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="When running, continue after a command exits non-zero and record the exit code.",
    )
    return parser.parse_args()


def split_command(command: str) -> list[str]:
    return shlex.split(command)


def build_base(args: argparse.Namespace) -> list[str]:
    command = split_command(args.snakemake_cmd)
    snakefile = Path(args.snakefile)
    if args.snakefile != "Snakefile" or not snakefile.name == "Snakefile":
        command.extend(["--snakefile", args.snakefile])
    command.extend(args.target)
    return command


def selected_names(includes: Iterable[str] | None) -> list[str]:
    if includes:
        return list(dict.fromkeys(includes))
    return list(SNAKEMAKE_FLAGS)


def build_plan(args: argparse.Namespace) -> list[dict[str, object]]:
    base = build_base(args)
    plan = []
    for name in selected_names(args.include):
        command = [*base, *SNAKEMAKE_FLAGS[name]]
        plan.append(
            {
                "name": name,
                "command": command,
                "output": str(Path(args.outdir) / OUTPUT_FILES[name]),
                "note": note_for(name),
            }
        )
    return plan


def note_for(name: str) -> str:
    notes = {
        "dry-run": "Safe topology/execution preview; reasons appear in output without --reason.",
        "lint-json": "Non-zero exit can mean lint findings, not command failure.",
        "summary": "Most useful after outputs and .snakemake metadata exist.",
        "detailed-summary": "Adds input and shell-command details when metadata is available.",
        "dag": "DOT job graph; top-level Snakefile prints can corrupt graph text.",
        "rulegraph": "DOT rule graph; less crowded than job DAG.",
        "filegraph": "DOT graph with rules and input/output files.",
        "debug-dag": "Prints candidate/selected jobs and wildcards during DAG inference.",
    }
    return notes[name]


def run_plan(plan: list[dict[str, object]], outdir: Path, continue_on_error: bool) -> int:
    outdir.mkdir(parents=True, exist_ok=True)
    results = []
    overall = 0
    for item in plan:
        output = Path(str(item["output"]))
        output.parent.mkdir(parents=True, exist_ok=True)
        command = [str(part) for part in item["command"]]
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        output.write_text(completed.stdout, encoding="utf-8")
        result = {
            "name": item["name"],
            "command": command,
            "output": str(output),
            "returncode": completed.returncode,
            "note": item["note"],
        }
        results.append(result)
        if completed.returncode != 0:
            overall = completed.returncode if overall == 0 else overall
            if not continue_on_error:
                break
    manifest = outdir / "manifest.json"
    manifest.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
    return overall


def main() -> int:
    args = parse_args()
    plan = build_plan(args)
    if not args.run:
        print(json.dumps(plan, indent=2))
        return 0
    return run_plan(plan, Path(args.outdir), args.continue_on_error)


if __name__ == "__main__":
    sys.exit(main())
