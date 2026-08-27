#!/usr/bin/env python3
"""List or run the curated stdlib smoke checks for this subtree.

Default mode lists the checks only. Pass --run to execute the curated checks.
The script never executes arbitrary project code; it only runs the fixed
Cat_command and Execute Shell Command smoke targets when asked.
"""

from __future__ import annotations

import argparse
import difflib
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

CHECK_IDS = ("cat-command", "execute-shell-command-test")


@dataclass(frozen=True)
class CheckSpec:
    description: str
    project_dir: str
    required_paths: tuple[str, ...]


CHECKS: dict[str, CheckSpec] = {
    "cat-command": CheckSpec(
        description="Run Cat_command/cat.py on Cat_command/test_cat.txt and compare stdout exactly.",
        project_dir="Cat_command",
        required_paths=("Cat_command/cat.py", "Cat_command/test_cat.txt"),
    ),
    "execute-shell-command-test": CheckSpec(
        description="Run Execute Shell Command/execute_shell_command_test.py.",
        project_dir="Execute Shell Command",
        required_paths=(
            "Execute Shell Command/execute_shell_command.py",
            "Execute Shell Command/execute_shell_command_test.py",
        ),
    ),
}


@dataclass
class RunResult:
    check_id: str
    ok: bool
    message: str


def quote_command(parts: Iterable[object]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n")


def parser_factory() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "List the curated safe native checks for cli-algorithms-and-utilities "
            "or run them against a target checkout."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Target checkout root. Defaults to the current working directory.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--list",
        dest="show_list",
        action="store_true",
        help="List the curated checks and exit (default).",
    )
    mode.add_argument(
        "--run",
        dest="run_mode",
        action="store_true",
        help="Run the curated checks that exist under the target checkout.",
    )
    parser.add_argument(
        "--check",
        nargs="+",
        choices=CHECK_IDS,
        help="Restrict the list or run to the selected curated checks.",
    )
    return parser


def validate_root(root: Path) -> Path:
    resolved = root.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Target root does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"Target root is not a directory: {resolved}")
    return resolved


def selected_check_ids(args: argparse.Namespace) -> list[str]:
    if args.check:
        return list(args.check)
    return list(CHECK_IDS)


def missing_paths(root: Path, spec: CheckSpec) -> list[Path]:
    return [root / rel for rel in spec.required_paths if not (root / rel).exists()]


def list_checks(root: Path, check_ids: list[str]) -> int:
    print(f"Target root: {root}")
    print("Curated checks:")
    for check_id in check_ids:
        spec = CHECKS[check_id]
        missing = missing_paths(root, spec)
        status = "available" if not missing else "missing"
        print(f"- {check_id}: {spec.description}")
        print(f"  project dir: {spec.project_dir}")
        print(f"  status: {status}")
        print(f"  paths: {', '.join(spec.required_paths)}")
        if missing:
            print(f"  missing: {', '.join(str(path.relative_to(root)) for path in missing)}")
    print("Use --run to execute the curated checks.")
    return 0


def run_cat_command(root: Path, spec: CheckSpec) -> RunResult:
    project_dir = root / spec.project_dir
    script = project_dir / "cat.py"
    fixture = project_dir / "test_cat.txt"
    command = [sys.executable, script, fixture]
    display = quote_command(command)
    print(f"[cat-command] {display}")

    proc = subprocess.run(
        [sys.executable, str(script), str(fixture)],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        details = [f"exit code: {proc.returncode}"]
        if proc.stdout:
            details.append("stdout:\n" + proc.stdout.rstrip())
        if proc.stderr:
            details.append("stderr:\n" + proc.stderr.rstrip())
        return RunResult("cat-command", False, "\n".join(details))

    expected = normalize_text(fixture.read_text(encoding="utf-8"))
    actual = normalize_text(proc.stdout)
    if actual != expected:
        diff = "".join(
            difflib.unified_diff(
                expected.splitlines(keepends=True),
                actual.splitlines(keepends=True),
                fromfile="expected test_cat.txt",
                tofile="actual stdout",
            )
        )
        message = "stdout did not match test_cat.txt exactly"
        if diff:
            message += "\n" + diff.rstrip()
        return RunResult("cat-command", False, message)

    return RunResult("cat-command", True, "stdout matched test_cat.txt")


def run_execute_shell_command_test(root: Path, spec: CheckSpec) -> RunResult:
    project_dir = root / spec.project_dir
    test_file = project_dir / "execute_shell_command_test.py"
    command = [sys.executable, test_file]
    display = quote_command(command)
    print(f"[execute-shell-command-test] {display}")

    proc = subprocess.run(
        [sys.executable, str(test_file)],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        details = [f"exit code: {proc.returncode}"]
        if proc.stdout:
            details.append("stdout:\n" + proc.stdout.rstrip())
        if proc.stderr:
            details.append("stderr:\n" + proc.stderr.rstrip())
        return RunResult("execute-shell-command-test", False, "\n".join(details))

    return RunResult("execute-shell-command-test", True, "unittest completed successfully")


def run_checks(root: Path, check_ids: list[str]) -> int:
    failures = 0
    runners = {
        "cat-command": run_cat_command,
        "execute-shell-command-test": run_execute_shell_command_test,
    }

    for check_id in check_ids:
        spec = CHECKS[check_id]
        missing = missing_paths(root, spec)
        if missing:
            print(f"[{check_id}] MISSING: {', '.join(str(path.relative_to(root)) for path in missing)}")
            failures += 1
            continue

        result = runners[check_id](root, spec)
        if result.ok:
            print(f"[{check_id}] PASS: {result.message}")
        else:
            print(f"[{check_id}] FAIL: {result.message}")
            failures += 1

    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = parser_factory()
    args = parser.parse_args(argv)

    try:
        root = validate_root(args.root)
    except (FileNotFoundError, NotADirectoryError) as exc:
        parser.error(str(exc))

    check_ids = selected_check_ids(args)

    if args.run_mode:
        return run_checks(root, check_ids)

    return list_checks(root, check_ids)


if __name__ == "__main__":
    raise SystemExit(main())
