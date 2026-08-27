#!/usr/bin/env python3
"""Report safe SkyPilot repo-development checks for a checkout.

By default this helper only inspects files and prints recommended commands. It
never formats code, runs tests, starts API servers, contacts clouds, or mutates
the checkout. Pass --check-import to run a read-only `import sky` probe with the
current Python interpreter.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shlex
import subprocess
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

REQUIRED_MARKERS = (
    'pyproject.toml',
    'format.sh',
    'sky/__init__.py',
    'sky/setup_files/dependencies.py',
)

FORMAT_SCOPES = ('sky/', 'tests/', 'examples/', 'llm/', 'docs/')

TEST_RECOMMENDATIONS: Tuple[Tuple[str, Tuple[str, ...], Tuple[str, ...]], ...] = (
    (
        'task/resources/yaml',
        ('sky/task.py', 'sky/resources.py', 'sky/data/storage.py',
         'tests/test_yamls/', 'tests/test_yaml_parser.py'),
        ('pytest tests/unit_tests/test_sky/test_task.py tests/unit_tests/test_resources.py tests/test_yaml_parser.py',),
    ),
    (
        'cli validation',
        ('sky/client/cli/', 'tests/unit_tests/test_sky/test_cli_', 'tests/test_cli.py'),
        ('pytest tests/unit_tests/test_sky/test_cli_launch_validation.py tests/unit_tests/test_sky/test_cli_helpers.py tests/unit_tests/test_sky/test_cli_json_output.py',),
    ),
    (
        'sdk/api server compatibility',
        ('sky/client/sdk.py', 'sky/client/sdk_async.py', 'sky/client/common.py',
         'sky/server/', 'tests/unit_tests/test_sky/server/',
         'tests/unit_tests/test_client_sdks.py', 'tests/test_api',
         'tests/test_api_compatibility.py'),
        ('pytest tests/unit_tests/test_client_sdks.py tests/unit_tests/test_sky/client/test_sdk_async.py tests/unit_tests/test_sky/server/test_versions.py tests/unit_tests/test_sky/server/requests/test_payloads.py',
         'pytest tests/test_api_compatibility.py'),
    ),
    (
        'managed jobs',
        ('sky/jobs/', 'tests/unit_tests/test_sky/jobs/', 'tests/test_jobs'),
        ('pytest tests/unit_tests/test_sky/jobs/test_client_sdk.py tests/unit_tests/test_sky/jobs/test_recovery_strategy.py tests/unit_tests/test_sky/jobs/test_server_core.py',),
    ),
    (
        'serving',
        ('sky/serve/', 'tests/unit_tests/test_serve_', 'tests/skyserve/',
         'tests/test_serve'),
        ('pytest tests/unit_tests/test_serve_service.py tests/unit_tests/test_serve_autoscaler.py tests/unit_tests/test_serve_proto_converter.py',),
    ),
    (
        'cloud/kubernetes/storage',
        ('sky/clouds/', 'sky/provision/', 'sky/data/', 'sky/workspaces/',
         'tests/unit_tests/kubernetes/', 'tests/unit_tests/test_sky/clouds/',
         'tests/unit_tests/test_sky/storage/', 'tests/test_storage.py'),
        ('pytest tests/unit_tests/kubernetes tests/unit_tests/test_sky/clouds/test_kubernetes.py tests/unit_tests/test_sky/storage/test_storage_utils.py',),
    ),
    (
        'backend/execution',
        ('sky/backends/', 'sky/execution.py', 'sky/optimizer.py',
         'tests/unit_tests/test_sky/backends/', 'tests/test_optimizer'),
        ('pytest tests/unit_tests/test_sky/backends tests/test_optimizer_dryruns.py',),
    ),
)

CRITICAL_PATHS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ('managed jobs recovery',
     ('sky/jobs/controller.py', 'sky/jobs/recovery_strategy.py')),
    ('execution backend',
     ('sky/backends/cloud_vm_ray_backend.py', 'sky/backends/backend_utils.py')),
    ('api server', ('sky/server/', 'sky/client/sdk.py', 'sky/client/sdk_async.py')),
    ('cli/sdk interface', ('sky/client/cli/', 'sky/client/sdk.py')),
)


def _run_command(
    args: Sequence[str],
    cwd: pathlib.Path,
    timeout: int = 20,
) -> Tuple[int, str, str]:
    try:
        completed = subprocess.run(
            list(args),
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return 127, '', str(exc)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ''
        stderr = exc.stderr if isinstance(exc.stderr, str) else ''
        return 124, stdout, stderr or f'timed out after {timeout}s'
    return completed.returncode, completed.stdout, completed.stderr


def _quote_command(command: Sequence[str]) -> str:
    return ' '.join(shlex.quote(part) for part in command)


def _find_repo_root(start: pathlib.Path) -> Optional[pathlib.Path]:
    start = start.resolve()
    candidates = [start] + list(start.parents)
    for candidate in candidates:
        if all((candidate / marker).exists() for marker in REQUIRED_MARKERS):
            return candidate
    return None


def _is_skypilot_root(repo_root: pathlib.Path) -> bool:
    return all((repo_root / marker).exists() for marker in REQUIRED_MARKERS)


def _normalize_path(path: str) -> str:
    return path.strip().replace(os.sep, '/')


def _dedupe(items: Iterable[str]) -> List[str]:
    seen = set()
    ordered = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _git_changed_files(repo_root: pathlib.Path,
                       base_ref: str) -> Tuple[List[str], List[str]]:
    notes: List[str] = []
    changed: List[str] = []

    returncode, stdout, stderr = _run_command(
        ('git', 'merge-base', base_ref, 'HEAD'), repo_root)
    merge_base = stdout.strip() if returncode == 0 else ''
    if merge_base:
        diff_args = ('git', 'diff', '--name-only', '--diff-filter=ACMRT',
                     merge_base, 'HEAD')
        returncode, stdout, stderr = _run_command(diff_args, repo_root)
        if returncode == 0:
            changed.extend(_normalize_path(line) for line in stdout.splitlines()
                           if line.strip())
        else:
            notes.append(f'git diff failed against {base_ref}: {stderr.strip()}')
    else:
        notes.append(
            f'Could not find merge-base with {base_ref}; using worktree status only.'
        )

    returncode, stdout, stderr = _run_command(
        ('git', 'status', '--porcelain=v1', '--untracked-files=normal'),
        repo_root)
    if returncode == 0:
        for line in stdout.splitlines():
            if not line:
                continue
            path = line[3:] if len(line) > 3 else line
            if ' -> ' in path:
                path = path.split(' -> ', 1)[1]
            changed.append(_normalize_path(path))
    else:
        notes.append(f'git status failed: {stderr.strip()}')

    return _dedupe(path for path in changed if path), notes


def _matches(path: str, prefixes: Iterable[str]) -> bool:
    return any(path == prefix.rstrip('/') or path.startswith(prefix)
               for prefix in prefixes)


def _python_files_for_format(paths: Iterable[str]) -> List[str]:
    files = []
    for path in paths:
        if not path.endswith(('.py', '.pyi')):
            continue
        if not _matches(path, FORMAT_SCOPES):
            continue
        if path.startswith('sky/schemas/generated/'):
            continue
        files.append(path)
    return files


def _recommend_commands(paths: Sequence[str]) -> Dict[str, Any]:
    commands: List[Dict[str, Any]] = []
    cautions: List[str] = []
    matched_areas: List[str] = []

    python_files = _python_files_for_format(paths)
    if python_files:
        commands.append({
            'reason': 'format/lint changed Python files',
            'command': 'bash format.sh --files ' + ' '.join(
                shlex.quote(path) for path in python_files),
            'safe_by_default': False,
        })
    else:
        commands.append({
            'reason': 'format/lint changed files against origin/master',
            'command': 'bash format.sh',
            'safe_by_default': False,
        })

    for area, prefixes, area_commands in TEST_RECOMMENDATIONS:
        if any(_matches(path, prefixes) for path in paths):
            matched_areas.append(area)
            for command in area_commands:
                commands.append({
                    'reason': f'focused tests for {area}',
                    'command': command,
                    'safe_by_default': True,
                })

    if any(path.startswith('sky/schemas/proto/') and path.endswith('.proto')
           for path in paths):
        commands.append({
            'reason': 'regenerate protobuf outputs',
            'command': ('python -m grpc_tools.protoc '
                        '--proto_path=sky/schemas/generated=sky/schemas/proto '
                        '--python_out=. --grpc_python_out=. --pyi_out=. '
                        'sky/schemas/proto/*.proto'),
            'safe_by_default': False,
        })
        commands.append({
            'reason': 'verify protobuf generated diff',
            'command': 'git diff -- sky/schemas/generated/',
            'safe_by_default': True,
        })

    if any(path.startswith('sky/dashboard/') for path in paths):
        commands.extend([
            {
                'reason': 'install dashboard dependencies',
                'command': 'npm --prefix sky/dashboard install',
                'safe_by_default': False,
            },
            {
                'reason': 'dashboard lint',
                'command': 'npm --prefix sky/dashboard run lint',
                'safe_by_default': True,
            },
            {
                'reason': 'dashboard format check',
                'command': 'npm --prefix sky/dashboard run format:check',
                'safe_by_default': True,
            },
            {
                'reason': 'dashboard tests',
                'command': 'npm --prefix sky/dashboard run test',
                'safe_by_default': True,
            },
            {
                'reason': 'dashboard production build before API-server manual test',
                'command': 'npm --prefix sky/dashboard run build',
                'safe_by_default': False,
            },
        ])

    if any(path.startswith(('docs/', 'docs/source/')) for path in paths):
        commands.append({
            'reason': 'docs build or link validation when docs dependencies are available',
            'command': 'consult docs tooling and run the narrow docs build/check for touched pages',
            'safe_by_default': False,
        })

    if any(path in ('requirements-dev.txt', 'pyproject.toml') or
           path.startswith('sky/setup_files/') for path in paths):
        commands.append({
            'reason': 'dependency/package consistency',
            'command': 'python -m pip check',
            'safe_by_default': True,
        })

    if any(path.startswith(('tests/smoke_tests/', 'tests/test_smoke.py'))
           for path in paths):
        cautions.append(
            'Smoke-test files changed; local smoke tests may launch cloud resources. '
            'Use focused tests or CI comments only after explicit approval.')

    for label, prefixes in CRITICAL_PATHS:
        if any(_matches(path, prefixes) for path in paths):
            cautions.append(
                f'Critical path touched: {label}. Review compatibility, state, '
                'retry/race behavior, latency, and cleanup invariants.')

    if any(path.startswith(('.github/workflows/', '.buildkite/')) for path in paths):
        cautions.append(
            'CI workflow files changed; verify syntax and consider affected GitHub Actions or Buildkite trigger behavior.'
        )

    if any(path.startswith('sky/server/') or path.startswith('sky/client/')
           for path in paths):
        cautions.append(
            'Client/server changes may require API_VERSION gating, payload defaults, remote version branching, and /quicktest-core.'
        )

    return {
        'matched_areas': _dedupe(matched_areas),
        'commands': _dedupe_command_records(commands),
        'cautions': _dedupe(cautions),
    }


def _dedupe_command_records(commands: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    ordered = []
    for command in commands:
        key = (command.get('reason'), command.get('command'))
        if key in seen:
            continue
        seen.add(key)
        ordered.append(command)
    return ordered


def _read_tool_versions(repo_root: pathlib.Path) -> Dict[str, str]:
    versions: Dict[str, str] = {}
    requirements = repo_root / 'requirements-dev.txt'
    if not requirements.exists():
        return versions
    for line in requirements.read_text(encoding='utf-8').splitlines():
        stripped = line.strip()
        if '==' not in stripped or stripped.startswith('#'):
            continue
        name, version = stripped.split('==', 1)
        if name in {'yapf', 'pylint', 'pylint-quotes', 'isort', 'mypy'}:
            versions[name] = version
    return versions


def _check_import(repo_root: pathlib.Path, timeout: int) -> Dict[str, Any]:
    code = (
        'import json\n'
        'import sky\n'
        'print(json.dumps({'
        '"version": getattr(sky, "__version__", "<unknown>"), '
        '"commit": getattr(sky, "__commit__", "<unknown>")'
        '}))\n')
    env = os.environ.copy()
    env.setdefault('SKYPILOT_DISABLE_USAGE_COLLECTION', '1')
    try:
        completed = subprocess.run(
            [sys.executable, '-c', code],
            cwd=str(repo_root),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stderr = exc.stderr if isinstance(exc.stderr, str) else ''
        return {'ok': False, 'returncode': 124, 'stderr': stderr or 'timed out'}
    except Exception as exc:  # pylint: disable=broad-except
        return {'ok': False, 'returncode': None, 'stderr': str(exc)}

    result: Dict[str, Any] = {
        'ok': completed.returncode == 0,
        'returncode': completed.returncode,
        'stdout': completed.stdout.strip(),
        'stderr': completed.stderr.strip(),
    }
    if completed.returncode == 0 and completed.stdout.strip():
        try:
            result['metadata'] = json.loads(completed.stdout.strip().splitlines()[-1])
        except json.JSONDecodeError:
            pass
    return result


def _build_report(args: argparse.Namespace) -> Tuple[Dict[str, Any], int]:
    requested_root = pathlib.Path(args.repo_root)
    repo_root = _find_repo_root(requested_root)
    if repo_root is None:
        report = {
            'ok': False,
            'error': 'Could not locate a SkyPilot checkout from --repo-root.',
            'required_markers': list(REQUIRED_MARKERS),
        }
        return report, 2

    changed_files, notes = _git_changed_files(repo_root, args.base_ref)
    recommendations = _recommend_commands(changed_files)
    report: Dict[str, Any] = {
        'ok': _is_skypilot_root(repo_root),
        'repo_root': '<detected SkyPilot checkout>',
        'repo_root_basename': repo_root.name,
        'base_ref': args.base_ref,
        'changed_files': changed_files,
        'notes': notes,
        'tool_versions': _read_tool_versions(repo_root),
        'recommendations': recommendations,
        'reminders': [
            'Commands are recommendations only; this helper does not execute them.',
            'Run cloud smoke tests only with explicit approval because they can create billable resources.',
            'Include exact commands run and skipped expensive checks in the PR Tested section.',
        ],
    }
    if args.check_import:
        report['import_check'] = _check_import(repo_root, args.import_timeout)
    return report, 0 if report['ok'] else 1


def _print_text(report: Dict[str, Any]) -> None:
    if not report.get('ok'):
        print(f"Error: {report.get('error', 'not a SkyPilot checkout')}")
        markers = report.get('required_markers') or []
        if markers:
            print('Required markers:')
            for marker in markers:
                print(f'  - {marker}')
        return

    print('SkyPilot repo sanity report')
    print(f"Repo root: {report['repo_root']}")
    print(f"Repo directory name: {report.get('repo_root_basename', '<unknown>')}")
    print(f"Base ref: {report['base_ref']}")

    versions = report.get('tool_versions') or {}
    if versions:
        print('\nPinned dev tool versions:')
        for name in sorted(versions):
            print(f'  - {name}=={versions[name]}')

    notes = report.get('notes') or []
    if notes:
        print('\nNotes:')
        for note in notes:
            print(f'  - {note}')

    changed_files = report.get('changed_files') or []
    print(f'\nChanged files detected: {len(changed_files)}')
    for path in changed_files[:40]:
        print(f'  - {path}')
    if len(changed_files) > 40:
        print(f'  ... {len(changed_files) - 40} more')

    recommendations = report.get('recommendations') or {}
    matched = recommendations.get('matched_areas') or []
    if matched:
        print('\nMatched areas:')
        for area in matched:
            print(f'  - {area}')

    commands = recommendations.get('commands') or []
    if commands:
        print('\nRecommended commands:')
        for record in commands:
            marker = 'read-only/focused' if record.get('safe_by_default') else 'opt-in/may mutate or be broad'
            print(f"  - {record['reason']} ({marker})")
            print(f"    {record['command']}")

    cautions = recommendations.get('cautions') or []
    if cautions:
        print('\nCautions:')
        for caution in cautions:
            print(f'  - {caution}')

    import_check = report.get('import_check')
    if import_check is not None:
        print('\nImport check:')
        print(f"  - ok: {import_check.get('ok')}")
        if import_check.get('metadata'):
            metadata = import_check['metadata']
            print(f"  - version: {metadata.get('version')}")
            print(f"  - commit: {metadata.get('commit')}")
        elif import_check.get('stderr'):
            print(f"  - stderr: {import_check.get('stderr')}")

    reminders = report.get('reminders') or []
    if reminders:
        print('\nReminders:')
        for reminder in reminders:
            print(f'  - {reminder}')


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Inspect a SkyPilot checkout and print recommended repo-development '
            'commands for changed files. No formatting, tests, API servers, cloud '
            'checks, or mutation are performed by default.'),
    )
    parser.add_argument(
        '--repo-root',
        default='.',
        help='Path inside or at the SkyPilot checkout to inspect.',
    )
    parser.add_argument(
        '--base-ref',
        default='origin/master',
        help='Git ref used to classify changed files when available.',
    )
    parser.add_argument(
        '--check-import',
        action='store_true',
        help='Run a read-only `import sky` probe with the current Python.',
    )
    parser.add_argument(
        '--import-timeout',
        type=int,
        default=30,
        help='Timeout in seconds for --check-import.',
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Emit machine-readable JSON.',
    )
    args = parser.parse_args(argv)

    report, returncode = _build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
    return returncode


if __name__ == '__main__':
    raise SystemExit(main())
