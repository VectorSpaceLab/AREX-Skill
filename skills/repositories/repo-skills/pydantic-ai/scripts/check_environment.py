#!/usr/bin/env python3
"""No-network diagnostic for installed Pydantic AI ecosystem packages.

Usage:
    python scripts/check_environment.py [--json] [--cli] [--optional openai,anthropic,mcp]

The script checks imports, package metadata where available, a deterministic
`Agent(TestModel())` smoke run, and optional CLI help. It never calls model
providers, starts servers, reads credentials, or mutates user files.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


BASE_IMPORTS = {
    'pydantic_ai': 'pydantic-ai or pydantic-ai-slim',
    'pydantic_graph': 'pydantic-graph',
    'pydantic_evals': 'pydantic-evals',
    'clai': 'clai',
}

OPTIONAL_IMPORTS = {
    'openai': ('openai', 'pydantic-ai-slim[openai]'),
    'anthropic': ('anthropic', 'pydantic-ai-slim[anthropic]'),
    'google': ('google.genai', 'pydantic-ai-slim[google]'),
    'groq': ('groq', 'pydantic-ai-slim[groq]'),
    'mistral': ('mistralai', 'pydantic-ai-slim[mistral]'),
    'cohere': ('cohere', 'pydantic-ai-slim[cohere]'),
    'bedrock': ('boto3', 'pydantic-ai-slim[bedrock]'),
    'mcp': ('mcp', 'pydantic-ai-slim[mcp]'),
    'fastmcp': ('fastmcp', 'pydantic-ai-slim[fastmcp]'),
    'logfire': ('logfire', 'pydantic-ai-slim[logfire]'),
    'ag-ui': ('ag_ui', 'pydantic-ai-slim[ag-ui]'),
    'starlette': ('starlette', 'pydantic-ai-slim[ui] or pydantic-ai-slim[web]'),
    'temporal': ('temporalio', 'pydantic-ai-slim[temporal]'),
    'dbos': ('dbos', 'pydantic-ai-slim[dbos]'),
    'prefect': ('prefect', 'pydantic-ai-slim[prefect]'),
    'duckduckgo': ('ddgs', 'pydantic-ai-slim[duckduckgo]'),
    'tavily': ('tavily', 'pydantic-ai-slim[tavily]'),
    'exa': ('exa_py', 'pydantic-ai-slim[exa]'),
}


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    hint: str | None = None


def check_import(module: str, hint: str) -> CheckResult:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:
        return CheckResult(module, False, f'{type(exc).__name__}: {exc}', hint)
    version = getattr(imported, '__version__', None)
    return CheckResult(module, True, f'imported{f" version={version}" if version else ""}')


def check_distribution(dist_name: str) -> CheckResult:
    try:
        version = metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return CheckResult(dist_name, False, 'distribution metadata not found')
    except Exception as exc:
        return CheckResult(dist_name, False, f'{type(exc).__name__}: {exc}')
    return CheckResult(dist_name, True, f'version={version}')


def check_agent_smoke() -> CheckResult:
    try:
        from pydantic_ai import Agent
        from pydantic_ai.models.test import TestModel

        agent = Agent(TestModel(custom_output_text='environment smoke passed'), instructions='Reply with success.')
        result = agent.run_sync('hello')
    except Exception as exc:
        return CheckResult('Agent(TestModel()) smoke', False, f'{type(exc).__name__}: {exc}')
    return CheckResult('Agent(TestModel()) smoke', result.output == 'environment smoke passed', repr(result.output))


def check_cli(command: str) -> CheckResult:
    executable = shutil.which(command)
    if executable is None:
        sibling = Path(sys.executable).resolve().parent / command
        if sibling.exists():
            executable = str(sibling)
    if executable is None:
        return CheckResult(command, False, 'command not found on PATH or beside the current Python', f'Install CLI support for `{command}`.')
    try:
        proc = subprocess.run([executable, '--help'], text=True, capture_output=True, timeout=20, check=False)
    except Exception as exc:
        return CheckResult(command, False, f'{type(exc).__name__}: {exc}')
    detail = f'exit={proc.returncode}; first_line={(proc.stdout or proc.stderr).splitlines()[0] if (proc.stdout or proc.stderr).splitlines() else "no output"}'
    return CheckResult(command, proc.returncode == 0, detail)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Check installed Pydantic AI ecosystem packages without network calls.')
    parser.add_argument('--json', action='store_true', help='Emit JSON instead of text.')
    parser.add_argument('--cli', action='store_true', help='Also run `clai --help` and `pai --help` if available.')
    parser.add_argument(
        '--optional',
        default='',
        help='Comma-separated optional groups to import-check, or `all`. Known groups: ' + ', '.join(sorted(OPTIONAL_IMPORTS)),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results: list[CheckResult] = []

    for module, hint in BASE_IMPORTS.items():
        results.append(check_import(module, f'Install `{hint}`.'))

    for dist_name in ['pydantic-ai', 'pydantic-ai-slim', 'pydantic-graph', 'pydantic-evals', 'clai']:
        results.append(check_distribution(dist_name))

    results.append(check_agent_smoke())

    optional_names = [name.strip() for name in args.optional.split(',') if name.strip()]
    if optional_names == ['all']:
        optional_names = sorted(OPTIONAL_IMPORTS)
    for name in optional_names:
        if name not in OPTIONAL_IMPORTS:
            results.append(CheckResult(name, False, 'unknown optional group', 'Use one of: ' + ', '.join(sorted(OPTIONAL_IMPORTS))))
            continue
        module, hint = OPTIONAL_IMPORTS[name]
        results.append(check_import(module, f'Install `{hint}` if this workflow needs `{name}`.'))

    if args.cli:
        results.append(check_cli('clai'))
        results.append(check_cli('pai'))

    ok = all(result.ok for result in results if not result.name.startswith('pydantic-ai'))

    if args.json:
        payload: dict[str, Any] = {'ok': ok, 'results': [asdict(result) for result in results]}
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for result in results:
            status = 'ok' if result.ok else 'FAIL'
            line = f'[{status}] {result.name}: {result.detail}'
            if result.hint and not result.ok:
                line += f' ({result.hint})'
            print(line)

    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
