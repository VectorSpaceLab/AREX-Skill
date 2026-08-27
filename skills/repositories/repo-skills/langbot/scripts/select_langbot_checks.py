#!/usr/bin/env python3
"""Print or run focused LangBot verification command groups.

By default this only prints commands. Use --run after confirming prerequisites.
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

GROUPS: dict[str, list[str]] = {
    'quick': ['bash scripts/test-quick.sh'],
    'fast-integration': ['bash scripts/test-integration-fast.sh'],
    'api-mcp': [
        'uv run pytest tests/unit_tests/api/http/test_authz.py tests/unit_tests/api/service/test_apikey_service.py -q --tb=short',
        'uv run pytest tests/unit_tests/api/test_mcp_controller.py tests/unit_tests/api/test_mcp_mount_tenant_scope.py tests/unit_tests/api/service/test_mcp_service.py -q --tb=short',
        'uv run --no-sync python tests/manual/mcp_smoke.py',
    ],
    'pipeline': [
        'uv run pytest tests/smoke/test_fake_message_flow.py -q --tb=short',
        'uv run pytest tests/integration/pipeline/test_full_flow.py -q --tb=short',
        'uv run pytest tests/unit_tests/pipeline/test_aggregator.py -q --tb=short',
    ],
    'plugin-box': [
        'uv run pytest tests/unit_tests/plugin/test_handler_actions.py tests/unit_tests/plugin/test_connector_methods.py -q --tb=short',
        'uv run pytest tests/unit_tests/box/test_box_service.py tests/unit_tests/box/test_box_connector.py tests/unit_tests/box/test_workspace.py -q --tb=short',
        '# Optional when Docker/Podman is available: uv run pytest tests/integration_tests/box -q --tb=short',
    ],
    'persistence-rag': [
        'uv run pytest tests/integration/persistence/test_migrations.py -q --tb=short',
        'uv run pytest tests/unit_tests/vector/test_mgr.py tests/unit_tests/vector/test_vdb_filter_conversion.py tests/unit_tests/vector/test_valkey_search_filter.py -q --tb=short',
        '# Optional with service DSN: TEST_POSTGRES_URL=... uv run pytest tests/integration/persistence/test_migrations_postgres.py -q --tb=short',
    ],
    'frontend': ['cd web && pnpm lint', 'cd web && pnpm test:e2e'],
    'skills-lbs': ['cd skills && bin/lbs validate', 'cd skills && bin/lbs index --check'],
}


def main() -> int:
    parser = argparse.ArgumentParser(description='Select focused LangBot verification commands.')
    parser.add_argument('group', choices=sorted(GROUPS), help='Command group to print or run')
    parser.add_argument('--repo-root', default='.', help='LangBot checkout root')
    parser.add_argument('--run', action='store_true', help='Execute commands instead of only printing them')
    args = parser.parse_args()
    repo = pathlib.Path(args.repo_root).resolve()
    commands = GROUPS[args.group]
    print(f'# LangBot check group: {args.group}')
    for command in commands:
        print(command)
    if not args.run:
        return 0
    for command in commands:
        if command.lstrip().startswith('#'):
            continue
        result = subprocess.run(command, cwd=str(repo), shell=True)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
