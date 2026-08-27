#!/usr/bin/env python3
"""Check installed Pydantic AI CLI help entry points without network calls.

Usage:
    python check_cli_help.py
    python check_cli_help.py --json

The script runs only help/version-style commands. It does not call model
providers, start web servers, read credentials, or require the original source
repository checkout.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


@dataclass
class CheckResult:
    name: str
    command: list[str]
    ok: bool
    returncode: int | None
    first_line: str
    error: str | None = None


@dataclass
class CheckCommand:
    name: str
    run: list[str]
    display: list[str]


def run_command(command: CheckCommand) -> CheckResult:
    try:
        completed = subprocess.run(
            command.run,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError as exc:
        return CheckResult(command.name, command.display, False, None, '', str(exc))
    except subprocess.TimeoutExpired:
        return CheckResult(command.name, command.display, False, None, '', 'timed out after 15 seconds')

    output = (completed.stdout or completed.stderr).strip()
    first_line = output.splitlines()[0] if output else ''
    return CheckResult(command.name, command.display, completed.returncode == 0, completed.returncode, first_line)


def resolve_console_script(name: str) -> str | None:
    if script_path := shutil.which(name):
        return script_path

    executable_dir = Path(sys.executable).resolve().parent
    candidates = [
        executable_dir / name,
        executable_dir / f'{name}.exe',
        executable_dir / 'Scripts' / name,
        executable_dir / 'Scripts' / f'{name}.exe',
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None


def cli_api_command(prog_name: str, args: list[str]) -> list[str]:
    code = f'from pydantic_ai._cli import cli; raise SystemExit(cli({args!r}, prog_name={prog_name!r}))'
    return [sys.executable, '-c', code]


def candidate_commands() -> list[CheckCommand]:
    commands: list[CheckCommand] = []

    clai_path = resolve_console_script('clai')
    if clai_path:
        commands.extend(
            [
                CheckCommand('clai --help', [clai_path, '--help'], ['clai', '--help']),
                CheckCommand('clai web --help', [clai_path, 'web', '--help'], ['clai', 'web', '--help']),
            ]
        )
    else:
        commands.extend(
            [
                CheckCommand(
                    'pydantic_ai._cli as clai --help',
                    cli_api_command('clai', ['--help']),
                    ['python', '-c', 'from pydantic_ai._cli import cli; cli(["--help"], prog_name="clai")'],
                ),
                CheckCommand(
                    'pydantic_ai._cli as clai web --help',
                    cli_api_command('clai', ['web', '--help']),
                    ['python', '-c', 'from pydantic_ai._cli import cli; cli(["web", "--help"], prog_name="clai")'],
                ),
            ]
        )

    pai_path = resolve_console_script('pai')
    if pai_path:
        commands.append(CheckCommand('pai --help', [pai_path, '--help'], ['pai', '--help']))
    else:
        commands.append(
            CheckCommand(
                'pydantic_ai._cli as pai --help',
                cli_api_command('pai', ['--help']),
                ['python', '-c', 'from pydantic_ai._cli import cli; cli(["--help"], prog_name="pai")'],
            )
        )

    return commands


def main() -> int:
    parser = argparse.ArgumentParser(description='Check installed Pydantic AI CLI help commands.')
    parser.add_argument('--json', action='store_true', help='Print machine-readable JSON results.')
    args = parser.parse_args()

    results = [run_command(command) for command in candidate_commands()]

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        for result in results:
            status = 'OK' if result.ok else 'FAIL'
            command_text = ' '.join(result.command)
            print(f'[{status}] {result.name}: {command_text}')
            if result.first_line:
                print(f'  {result.first_line}')
            if result.error:
                print(f'  {result.error}')

    return 0 if any(result.ok and 'clai' in result.name for result in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
