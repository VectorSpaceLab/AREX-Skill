#!/usr/bin/env python3
"""No-network import diagnostics for Pydantic AI integration extras.

Usage:
    python integration_import_check.py --all
    python integration_import_check.py mcp capabilities logfire ag-ui vercel-ai durable

The script checks local import availability and selected constructor signatures.
It never starts MCP servers, opens URLs, launches web apps, connects to durable
backends, validates credentials, or prints secret values.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import inspect
import os
import sys
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Check:
    key: str
    title: str
    imports: tuple[str, ...]
    signatures: tuple[str, ...] = ()
    extra_hint: str | None = None
    env_names: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


CHECKS: dict[str, Check] = {
    'core': Check(
        key='core',
        title='Core Pydantic AI',
        imports=('pydantic_ai', 'pydantic_ai.agent'),
        signatures=('pydantic_ai.Agent',),
        notes=('Core import should work before optional integration checks are meaningful.',),
    ),
    'mcp': Check(
        key='mcp',
        title='MCP client/toolset',
        imports=('pydantic_ai.mcp', 'mcp', 'fastmcp.client'),
        signatures=('pydantic_ai.mcp.MCPToolset', 'pydantic_ai.capabilities.MCP'),
        extra_hint='pydantic-ai-slim[mcp]',
        env_names=('MCP_SERVER_URL',),
        notes=(
            'Checks imports only; no MCP server process or HTTP connection is started.',
            'Use `MCPToolset` for new local MCP client integrations.',
        ),
    ),
    'fastmcp': Check(
        key='fastmcp',
        title='Deprecated FastMCP toolset compatibility',
        imports=('pydantic_ai.toolsets.fastmcp', 'fastmcp.client'),
        signatures=('pydantic_ai.toolsets.fastmcp.FastMCPToolset',),
        extra_hint='pydantic-ai-slim[mcp]',
        notes=('`FastMCPToolset` is deprecated; prefer `pydantic_ai.mcp.MCPToolset`.',),
    ),
    'capabilities': Check(
        key='capabilities',
        title='Capabilities and hooks',
        imports=('pydantic_ai.capabilities',),
        signatures=(
            'pydantic_ai.capabilities.Capability',
            'pydantic_ai.capabilities.Hooks',
            'pydantic_ai.capabilities.WebSearch',
            'pydantic_ai.capabilities.WebFetch',
            'pydantic_ai.capabilities.Instrumentation',
        ),
        notes=('Core capability APIs should import without provider credentials.',),
    ),
    'logfire': Check(
        key='logfire',
        title='Logfire and OTel instrumentation',
        imports=('logfire', 'opentelemetry.trace', 'pydantic_ai.capabilities.instrumentation'),
        signatures=('pydantic_ai.capabilities.Instrumentation',),
        extra_hint='pydantic-ai-slim[logfire]',
        env_names=('LOGFIRE_TOKEN',),
        notes=('Presence of `LOGFIRE_TOKEN` is reported only as set/missing; value is never printed.',),
    ),
    'a2a': Check(
        key='a2a',
        title='A2A / FastA2A',
        imports=('fasta2a', 'fasta2a.pydantic_ai'),
        extra_hint='fasta2a[pydantic-ai]>=0.6.1',
        notes=(
            'The older Pydantic AI `Agent.to_a2a()` path is deprecated; prefer the external FastA2A bridge.',
        ),
    ),
    'ag-ui': Check(
        key='ag-ui',
        title='AG-UI adapter',
        imports=('pydantic_ai.ui.ag_ui', 'ag_ui.core', 'starlette'),
        signatures=('pydantic_ai.ui.ag_ui.AGUIAdapter',),
        extra_hint='pydantic-ai-slim[ag-ui]',
        notes=('No Starlette request is created and no response stream is opened.',),
    ),
    'vercel-ai': Check(
        key='vercel-ai',
        title='Vercel AI adapter',
        imports=('pydantic_ai.ui.vercel_ai', 'starlette'),
        signatures=('pydantic_ai.ui.vercel_ai.VercelAIAdapter',),
        extra_hint='pydantic-ai-slim[web]',
        notes=('Checks protocol adapter imports only; no ASGI app is launched.',),
    ),
    'web': Check(
        key='web',
        title='Built-in web UI',
        imports=('pydantic_ai.ui._web.app', 'starlette', 'uvicorn'),
        signatures=('pydantic_ai.Agent.to_web',),
        extra_hint='pydantic-ai-slim[web]',
        notes=('Does not fetch UI HTML, create a cache file, or launch an ASGI server.',),
    ),
    'durable': Check(
        key='durable',
        title='Durable execution namespaces',
        imports=(
            'pydantic_ai.durable_exec.temporal',
            'pydantic_ai.durable_exec.prefect',
            'pydantic_ai.durable_exec.dbos',
        ),
        signatures=(
            'pydantic_ai.durable_exec.temporal.TemporalAgent',
            'pydantic_ai.durable_exec.prefect.PrefectAgent',
            'pydantic_ai.durable_exec.dbos.DBOSAgent',
        ),
        extra_hint='selected durable backend package such as temporalio, prefect, or dbos',
        env_names=('TEMPORAL_ADDRESS', 'PREFECT_API_URL', 'DBOS_DATABASE_URL'),
        notes=('Backend services are not contacted; imports may fail when a selected backend package is absent.',),
    ),
    'common-web': Check(
        key='common-web',
        title='Local web search/fetch fallbacks',
        imports=('pydantic_ai.common_tools.duckduckgo', 'pydantic_ai.common_tools.web_fetch'),
        extra_hint='pydantic-ai-slim[duckduckgo] and pydantic-ai-slim[web-fetch]',
        notes=('Runtime search/fetch still needs network access; this check only imports fallback tools.',),
    ),
}

ALIASES: dict[str, tuple[str, ...]] = {
    'all': tuple(CHECKS),
    'ui': ('ag-ui', 'vercel-ai', 'web'),
    'mcp-all': ('mcp', 'fastmcp'),
    'integration': tuple(CHECKS),
    'integrations': tuple(CHECKS),
}


def module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def import_module(module_name: str) -> tuple[bool, str | None]:
    try:
        importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic script reports optional import blockers.
        return False, f'{type(exc).__name__}: {exc}'
    return True, None


def resolve_object(dotted_path: str) -> object:
    module_name, attr_name = dotted_path.rsplit('.', 1)
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)


def signature_for(dotted_path: str) -> str:
    obj = resolve_object(dotted_path)
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return '<signature unavailable>'


def env_state(names: Iterable[str]) -> tuple[list[str], list[str]]:
    present: list[str] = []
    missing: list[str] = []
    for name in names:
        if os.getenv(name):
            present.append(name)
        else:
            missing.append(name)
    return present, missing


def print_check(check: Check) -> bool:
    print(f'\n== {check.title} ({check.key}) ==')
    if check.extra_hint:
        print(f'install hint: {check.extra_hint}')

    ok = True
    imported_modules: set[str] = set()
    for module_name in check.imports:
        discoverable = module_available(module_name)
        if not discoverable:
            ok = False
            print(f'import {module_name}: missing')
            continue
        imported, error = import_module(module_name)
        if imported:
            imported_modules.add(module_name)
            print(f'import {module_name}: ok')
        else:
            ok = False
            print(f'import {module_name}: error: {error}')

    for dotted_path in check.signatures:
        module_name = dotted_path.rsplit('.', 1)[0]
        if module_name not in imported_modules and module_name not in sys.modules:
            print(f'signature {dotted_path}: skipped; module import did not succeed')
            ok = False
            continue
        try:
            print(f'signature {dotted_path}: {signature_for(dotted_path)}')
        except Exception as exc:  # noqa: BLE001 - diagnostic script reports optional signature blockers.
            ok = False
            print(f'signature {dotted_path}: error: {type(exc).__name__}: {exc}')

    if check.env_names:
        present, missing = env_state(check.env_names)
        print(f'env names checked: {", ".join(check.env_names)}')
        print(f'env present: {", ".join(present) if present else "none"}')
        print(f'env missing: {", ".join(missing) if missing else "none"}')

    for note in check.notes:
        print(f'note: {note}')

    return ok


def expand_keys(items: list[str], include_all: bool) -> list[str]:
    requested = ['all'] if include_all else items
    if not requested:
        requested = ['core', 'mcp', 'capabilities']

    expanded: list[str] = []
    for item in requested:
        key = item.strip().lower()
        if key in ALIASES:
            for aliased in ALIASES[key]:
                if aliased not in expanded:
                    expanded.append(aliased)
        elif key in CHECKS:
            if key not in expanded:
                expanded.append(key)
        else:
            valid = ', '.join(sorted(set(CHECKS) | set(ALIASES)))
            raise SystemExit(f'unknown check {item!r}; valid checks: {valid}')
    return expanded


def main() -> int:
    parser = argparse.ArgumentParser(description='Check Pydantic AI integration imports without network access.')
    parser.add_argument('checks', nargs='*', help='Checks to run, e.g. mcp capabilities durable ag-ui.')
    parser.add_argument('--all', action='store_true', help='Run all integration checks.')
    parser.add_argument('--list', action='store_true', help='List available checks and aliases, then exit.')
    args = parser.parse_args()

    if args.list:
        print('checks:')
        for key in sorted(CHECKS):
            print(f'  {key}')
        print('aliases:')
        for key in sorted(ALIASES):
            print(f'  {key}: {", ".join(ALIASES[key])}')
        return 0

    keys = expand_keys(args.checks, args.all)
    all_ok = True
    for key in keys:
        all_ok = print_check(CHECKS[key]) and all_ok

    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
