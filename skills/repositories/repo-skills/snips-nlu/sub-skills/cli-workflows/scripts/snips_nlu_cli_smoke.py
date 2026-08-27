#!/usr/bin/env python3
"""Safe Snips NLU CLI smoke checks.

The default run checks CLI availability, package/model version commands, and
subcommand --help output. It deliberately avoids downloads, training, parsing,
metrics execution, and file writes.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

SUBCOMMANDS = (
    "generate-dataset",
    "train",
    "parse",
    "download",
    "download-all-languages",
    "download-entity",
    "download-language-entities",
    "link",
    "cross-val-metrics",
    "train-test-metrics",
)

VERSION_COMMANDS = ("version", "model-version")


@dataclass(frozen=True)
class EntryPoint:
    label: str
    command: Tuple[str, ...]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run safe Snips NLU CLI smoke checks: --help, version, "
            "model-version, and subcommand --help. No downloads or training."
        )
    )
    parser.add_argument(
        "--entrypoint",
        choices=("auto", "module", "console", "both"),
        default="auto",
        help=(
            "CLI entry point to check. 'module' uses the current Python as "
            "python -m snips_nlu; 'console' uses snips-nlu from PATH; 'auto' "
            "prefers the console script when present and falls back to module."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Timeout in seconds for each individual command.",
    )
    parser.add_argument(
        "--commands",
        nargs="*",
        default=list(SUBCOMMANDS),
        help=(
            "Subcommands whose --help output should be checked. Defaults to "
            "all workflow subcommands."
        ),
    )
    parser.add_argument(
        "--skip-subcommand-help",
        action="store_true",
        help="Only check top-level help plus version/model-version commands.",
    )
    parser.add_argument(
        "--expect-version",
        help="Optional exact package version expected from the version command.",
    )
    parser.add_argument(
        "--expect-model-version",
        help="Optional exact model version expected from the model-version command.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary instead of human-readable lines.",
    )
    return parser


def resolve_entrypoints(choice: str) -> Tuple[List[EntryPoint], List[str]]:
    module_ep = EntryPoint("python -m snips_nlu", (sys.executable, "-m", "snips_nlu"))
    console_path = shutil.which("snips-nlu")
    console_ep = EntryPoint("snips-nlu", (console_path,)) if console_path else None
    warnings: List[str] = []

    if choice == "module":
        return [module_ep], warnings
    if choice == "console":
        if console_ep is None:
            return [], ["snips-nlu console script was not found on PATH"]
        return [console_ep], warnings
    if choice == "both":
        entrypoints = [module_ep]
        if console_ep is None:
            warnings.append("snips-nlu console script was not found on PATH")
        else:
            entrypoints.append(console_ep)
        return entrypoints, warnings

    # auto
    if console_ep is not None:
        return [console_ep], warnings
    warnings.append("snips-nlu console script was not found on PATH; using python -m snips_nlu")
    return [module_ep], warnings


def run_command(ep: EntryPoint, args: Sequence[str], timeout: float) -> dict:
    cmd = ep.command + tuple(args)
    label = " ".join((ep.label,) + tuple(args))
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=timeout,
        )
        return {
            "label": label,
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "label": label,
            "ok": False,
            "returncode": None,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": "timed out after %.1f seconds" % timeout,
        }
    except OSError as exc:
        return {
            "label": label,
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }


def nonempty_stdout(result: dict) -> bool:
    return bool(result.get("stdout", "").strip())


def check_entrypoint(
    ep: EntryPoint,
    commands: Iterable[str],
    skip_subcommand_help: bool,
    timeout: float,
    expect_version: Optional[str],
    expect_model_version: Optional[str],
) -> Tuple[List[dict], List[str]]:
    results: List[dict] = []
    failures: List[str] = []

    planned: List[Tuple[str, ...]] = [("--help",)]
    planned.extend((cmd,) for cmd in VERSION_COMMANDS)
    if not skip_subcommand_help:
        planned.extend((cmd, "--help") for cmd in commands)

    for args in planned:
        result = run_command(ep, args, timeout)
        results.append(result)
        if not result["ok"]:
            failures.append("%s failed with return code %s" % (result["label"], result["returncode"]))
            continue
        if args in (("version",), ("model-version",)) and not nonempty_stdout(result):
            failures.append("%s produced empty stdout" % result["label"])
        if args == ("version",) and expect_version is not None:
            actual = result.get("stdout", "").strip().splitlines()[-1] if result.get("stdout") else ""
            if actual != expect_version:
                failures.append("%s expected %r but got %r" % (result["label"], expect_version, actual))
        if args == ("model-version",) and expect_model_version is not None:
            actual = result.get("stdout", "").strip().splitlines()[-1] if result.get("stdout") else ""
            if actual != expect_model_version:
                failures.append("%s expected %r but got %r" % (result["label"], expect_model_version, actual))

    return results, failures


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    entrypoints, warnings = resolve_entrypoints(args.entrypoint)
    all_results: List[dict] = []
    failures: List[str] = []

    if not entrypoints:
        failures.extend(warnings)

    for ep in entrypoints:
        results, ep_failures = check_entrypoint(
            ep,
            args.commands,
            args.skip_subcommand_help,
            args.timeout,
            args.expect_version,
            args.expect_model_version,
        )
        all_results.extend(results)
        failures.extend(ep_failures)

    summary = {
        "ok": not failures,
        "warnings": warnings,
        "failures": failures,
        "results": [
            {
                "label": item["label"],
                "ok": item["ok"],
                "returncode": item["returncode"],
                "stdout_preview": item.get("stdout", "")[:200],
                "stderr_preview": item.get("stderr", "")[:200],
            }
            for item in all_results
        ],
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        for warning in warnings:
            print("WARNING: %s" % warning)
        for item in summary["results"]:
            status = "OK" if item["ok"] else "FAIL"
            print("%s %s" % (status, item["label"]))
            if not item["ok"] and item["stderr_preview"]:
                print("  stderr: %s" % item["stderr_preview"])
        if failures:
            print("Failures:")
            for failure in failures:
                print("- %s" % failure)

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
