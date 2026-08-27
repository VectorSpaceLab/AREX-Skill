#!/usr/bin/env python3
"""Lightweight LangBot checkout/package doctor.

The script checks repository layout, pyproject metadata, config-template keys,
and representative imports without starting LangBot. It is safe by default and
can run from any current working directory.

Examples:
    python scripts/langbot_repo_doctor.py --repo-root /path/to/LangBot
    python scripts/langbot_repo_doctor.py --repo-root . --python .venv/bin/python --json
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

EXPECTED_PATHS = [
    'pyproject.toml', 'main.py', 'src/langbot/__main__.py',
    'src/langbot/pkg/core/app.py', 'src/langbot/pkg/api/mcp/server.py',
    'src/langbot/pkg/api/http/controller/main.py', 'src/langbot/pkg/platform/botmgr.py',
    'src/langbot/pkg/pipeline/pipelinemgr.py', 'src/langbot/pkg/plugin/connector.py',
    'src/langbot/pkg/box/service.py', 'src/langbot/pkg/persistence/mgr.py',
    'src/langbot/templates/config.yaml', 'web/package.json', 'tests/README.md',
]
CONFIG_KEYS = ['api:', 'database:', 'vdb:', 'plugin:', 'mcp:', 'box:', 'space:']
IMPORTS = [
    'langbot', 'langbot.__main__', 'langbot.pkg.core.app',
    'langbot.pkg.api.mcp.server', 'langbot.pkg.pipeline.pipelinemgr',
    'langbot.pkg.platform.botmgr', 'langbot.pkg.provider.tools.toolmgr',
    'langbot.pkg.plugin.connector', 'langbot.pkg.box.service',
    'langbot.pkg.persistence.mgr', 'langbot.pkg.rag.knowledge.kbmgr',
]


def run_import_probe(repo: pathlib.Path, python: str) -> dict:
    src = str(repo / 'src')
    code = """
import importlib, json, sys
sys.path.insert(0, %r)
mods = %r
out = {"ok": [], "failed": []}
for m in mods:
    try:
        importlib.import_module(m)
        out["ok"].append(m)
    except Exception as exc:
        out["failed"].append({"module": m, "error": type(exc).__name__ + ': ' + str(exc)[:300]})
print(json.dumps(out, ensure_ascii=False))
""" % (src, IMPORTS)
    env = os.environ.copy()
    proc = subprocess.run([python, '-I', '-c', code], cwd=str(repo), env=env, text=True, capture_output=True, timeout=30)
    result = {'returncode': proc.returncode, 'stdout': proc.stdout.strip(), 'stderr': proc.stderr.strip()[:1000]}
    try:
        result['parsed'] = json.loads(proc.stdout)
    except Exception:
        pass
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description='Inspect a LangBot checkout/package without starting it.')
    parser.add_argument('--repo-root', default='.', help='LangBot checkout root to inspect')
    parser.add_argument('--python', default=sys.executable, help='Python executable for import probes')
    parser.add_argument('--json', action='store_true', help='Emit JSON instead of a human report')
    args = parser.parse_args()

    repo = pathlib.Path(args.repo_root).resolve()
    report: dict[str, object] = {'repo_root': str(repo), 'missing_paths': [], 'metadata': {}, 'config_keys': {}, 'imports': {}}

    missing = [p for p in EXPECTED_PATHS if not (repo / p).exists()]
    report['missing_paths'] = missing

    pyproject = repo / 'pyproject.toml'
    if pyproject.exists():
        data = tomllib.loads(pyproject.read_text(encoding='utf-8'))
        project = data.get('project', {})
        report['metadata'] = {
            'name': project.get('name'),
            'version': project.get('version'),
            'requires_python': project.get('requires-python'),
            'scripts': project.get('scripts', {}),
        }

    config = repo / 'src/langbot/templates/config.yaml'
    if config.exists():
        text = config.read_text(encoding='utf-8')
        report['config_keys'] = {key.rstrip(':'): key in text for key in CONFIG_KEYS}

    report['imports'] = run_import_probe(repo, args.python)

    failures = bool(missing)
    parsed = report['imports'].get('parsed') if isinstance(report['imports'], dict) else None
    if isinstance(parsed, dict) and parsed.get('failed'):
        failures = True

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print('LangBot repo doctor')
        meta = report.get('metadata', {})
        print('metadata:', meta)
        print('missing paths:', missing or 'none')
        print('config keys:', report.get('config_keys'))
        print('import probe:', report.get('imports'))
        print('status:', 'FAIL' if failures else 'OK')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
