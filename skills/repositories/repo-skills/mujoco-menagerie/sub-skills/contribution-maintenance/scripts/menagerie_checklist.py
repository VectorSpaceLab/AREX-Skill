#!/usr/bin/env python3
"""Emit a scoped MuJoCo Menagerie maintainer check plan from changed paths.

The script is intentionally non-mutating. It classifies changed paths and prints
commands for formatting, license checks, structural tests, gallery rendering,
and final local CI-equivalent validation.

Examples:
  python menagerie_checklist.py unitree_go2/go2.xml unitree_go2/LICENSE
  python menagerie_checklist.py --repo-root . --base origin/main
  python menagerie_checklist.py --format json path/to/file.xml
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shlex
import subprocess
import sys
from collections.abc import Iterable

SKIP_TOP_LEVEL_DIRS = {
  '.git',
  '.github',
  'assets',
  'opensource',
  'skills',
  'test',
}
NO_SCENE_REQUIRED = {'realsense_d435i'}
TOOLING_FILES = {
  '.pre-commit-config.yaml',
  'Makefile',
  'format_xml.py',
  'regenerate_license.py',
  'generate_gallery.py',
}
GALLERY_TOP_LEVEL_FILES = {'README.md', 'generate_gallery.py'}
PYTHON_TEST_CMD = 'uv run --with-requirements test/requirements.txt pytest'


def _shell_join(parts: Iterable[str]) -> str:
  return ' '.join(shlex.quote(str(part)) for part in parts)


def _normalize_path(raw: str, root: pathlib.Path) -> str:
  path = pathlib.Path(raw)
  if path.is_absolute():
    try:
      return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
      return path.as_posix().lstrip('/')
  return path.as_posix().lstrip('./')


def _dedupe(items: Iterable[str]) -> list[str]:
  seen = set()
  out = []
  for item in items:
    if item and item not in seen:
      out.append(item)
      seen.add(item)
  return out


def _git_changed_paths(root: pathlib.Path, base: str | None) -> list[str]:
  if base:
    cmd = ['git', '-C', str(root), 'diff', '--name-only', base, '--']
    result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]

  paths: list[str] = []
  for diff_args in (['diff', '--name-only', '--cached'], ['diff', '--name-only']):
    result = subprocess.run(
      ['git', '-C', str(root), *diff_args],
      check=False,
      text=True,
      capture_output=True,
    )
    if result.returncode == 0:
      paths.extend(line.strip() for line in result.stdout.splitlines() if line.strip())
  return _dedupe(paths)


def _top_component(path: str) -> str:
  return path.split('/', 1)[0]


def _is_model_dir_path(path: str) -> bool:
  if '/' not in path:
    return False
  top = _top_component(path)
  return bool(top) and not top.startswith('.') and top not in SKIP_TOP_LEVEL_DIRS


def _pytest_k_for_dirs(model_dirs: list[str]) -> str | None:
  if not model_dirs:
    return None
  return ' or '.join(model_dirs)


def _command(command: str, reason: str, level: str = 'recommended') -> dict[str, str]:
  return {'level': level, 'command': command, 'reason': reason}


def classify(paths: list[str], root: pathlib.Path) -> dict[str, object]:
  xml_files = sorted(p for p in paths if p.endswith('.xml'))
  scene_xmls = sorted(p for p in xml_files if pathlib.Path(p).name.startswith('scene'))
  model_dirs = sorted({_top_component(p) for p in paths if _is_model_dir_path(p)})
  model_license_files = sorted(
    p for p in paths if p.endswith('/LICENSE') and _is_model_dir_path(p)
  )
  top_license_changed = 'LICENSE' in paths
  license_related = bool(model_license_files or top_license_changed or any(p == 'regenerate_license.py' for p in paths))
  changelog_files = sorted(p for p in paths if pathlib.Path(p).name == 'CHANGELOG.md')
  contributors_changed = 'CONTRIBUTORS.md' in paths
  tooling_files = sorted(p for p in paths if p in TOOLING_FILES or p.startswith('test/'))
  gallery_related = any(
    p in GALLERY_TOP_LEVEL_FILES
    or p.startswith('assets/')
    or p == 'generate_gallery.py'
    for p in paths
  )
  model_assets = sorted(
    p
    for p in paths
    if _is_model_dir_path(p) and ('/assets/' in p or '/meshes/' in p)
  )
  docs_only = bool(paths) and not any(
    [
      xml_files,
      model_dirs,
      license_related,
      contributors_changed,
      tooling_files,
      gallery_related,
      model_assets,
    ]
  )

  model_dir_status = []
  for model_dir in model_dirs:
    dir_path = root / model_dir
    changed_under_dir = [p for p in paths if p == model_dir or p.startswith(f'{model_dir}/')]
    has_changed_xml = any(p.endswith('.xml') for p in changed_under_dir)
    if dir_path.is_dir():
      has_xml = any(dir_path.glob('*.xml')) or has_changed_xml
      missing = []
      for required in ('README.md', 'LICENSE', 'CHANGELOG.md'):
        if not (dir_path / required).is_file():
          missing.append(required)
      if model_dir not in NO_SCENE_REQUIRED and not any(dir_path.glob('scene*.xml')):
        missing.append('scene*.xml')
      status = {
        'directory': model_dir,
        'exists': True,
        'has_xml': has_xml,
        'missing_required': missing,
        'note': 'known scene exemption' if model_dir in NO_SCENE_REQUIRED else '',
      }
    else:
      status = {
        'directory': model_dir,
        'exists': False,
        'has_xml': has_changed_xml,
        'missing_required': ['README.md', 'LICENSE', 'CHANGELOG.md', 'scene*.xml'],
        'note': 'directory not present at repo root when checklist was run',
      }
    model_dir_status.append(status)

  return {
    'paths': paths,
    'xml_files': xml_files,
    'scene_xmls': scene_xmls,
    'model_dirs': model_dirs,
    'model_license_files': model_license_files,
    'top_license_changed': top_license_changed,
    'license_related': license_related,
    'changelog_files': changelog_files,
    'contributors_changed': contributors_changed,
    'tooling_files': tooling_files,
    'gallery_related': gallery_related,
    'model_assets': model_assets,
    'docs_only': docs_only,
    'model_dir_status': model_dir_status,
  }


def build_plan(info: dict[str, object]) -> list[dict[str, str]]:
  paths = info['paths']
  xml_files = info['xml_files']
  model_dirs = info['model_dirs']
  scene_xmls = info['scene_xmls']
  contributors_changed = bool(info['contributors_changed'])
  license_related = bool(info['license_related'])
  gallery_related = bool(info['gallery_related'])
  tooling_files = info['tooling_files']
  model_assets = info['model_assets']
  docs_only = bool(info['docs_only'])

  commands: list[dict[str, str]] = []

  if not paths:
    commands.append(
      _command(
        'make all',
        'No changed paths were supplied; run the full documented local check set for PR readiness.',
        'fallback',
      )
    )
    commands.append(
      _command(
        'make gallery',
        'Run only if the change affects README gallery entries, thumbnails, or gallery metadata.',
        'conditional',
      )
    )
    return commands

  if xml_files:
    quoted_xml = _shell_join(['uv', 'run', 'format_xml.py', '--check', *xml_files])
    commands.append(
      _command(quoted_xml, 'Changed XML must match the Menagerie MJCF formatter.')
    )
    bundled = _shell_join(['python', 'scripts/format_mjcf_xml.py', '--check', *xml_files])
    commands.append(
      _command(
        bundled,
        'Portable formatter check if the repo formatter is unavailable.',
        'alternative',
      )
    )

  if license_related or model_dirs:
    commands.append(
      _command(
        'uv run regenerate_license.py --check',
        'Top-level LICENSE must match all model directory LICENSE files.',
      )
    )
    commands.append(
      _command(
        'python scripts/check_menagerie_license.py --root . --check',
        'Portable license consistency check.',
        'alternative',
      )
    )

  if model_dirs or contributors_changed:
    k_expr = _pytest_k_for_dirs(model_dirs)
    if k_expr:
      commands.append(
        _command(
          f'{PYTHON_TEST_CMD} test/model_dir_test.py -q -k {shlex.quote(k_expr)}',
          'Structural layout checks for affected model directories.',
        )
      )
    else:
      commands.append(
        _command(
          f'{PYTHON_TEST_CMD} test/model_dir_test.py::ContributorsTest -q',
          'Contributors list must remain sorted by first name.',
        )
      )

  if contributors_changed and model_dirs:
    commands.append(
      _command(
        f'{PYTHON_TEST_CMD} test/model_dir_test.py::ContributorsTest -q',
        'Contributor sorting check is explicit when CONTRIBUTORS.md changed.',
      )
    )

  if scene_xmls or model_assets or (xml_files and model_dirs):
    k_expr = _pytest_k_for_dirs(model_dirs)
    if k_expr:
      commands.append(
        _command(
          f'{PYTHON_TEST_CMD} test/model_test.py -q -k {shlex.quote(k_expr)}',
          'Repo-native targeted compile/short-step smoke for affected scene XMLs; route failures to model-loading.',
        )
      )
    else:
      commands.append(
        _command(
          f'{PYTHON_TEST_CMD} test/model_test.py -q',
          'Compile/short-step smoke; route failures to model-loading.',
          'conditional',
        )
      )

  if gallery_related:
    commands.append(
      _command(
        'make gallery',
        'Gallery-related files changed; render thumbnails and refresh the generated README model section when writes are allowed.',
        'conditional',
      )
    )

  if tooling_files:
    commands.append(
      _command(
        'make all',
        'Tooling, tests, Makefile, pre-commit config, or gallery script changed; run the full documented local check set.',
      )
    )
    commands.append(
      _command(
        f'{PYTHON_TEST_CMD} -n auto',
        'Closest local reproduction of the GitHub build workflow.',
        'conditional',
      )
    )
  elif not docs_only:
    commands.append(
      _command('make check', 'Final fast pre-commit check before committing.'))
    if model_dirs or xml_files or license_related:
      commands.append(
        _command(
          'make test',
          'Run before pushing model, XML, license, or directory-layout changes; use make all for final PR readiness.',
          'recommended',
        )
      )
  else:
    commands.append(
      _command(
        'make check',
        'Docs-only changes still benefit from whitespace/YAML/merge-conflict and formatting hooks.',
        'recommended',
      )
    )

  return commands


def _markdown(info: dict[str, object], commands: list[dict[str, str]]) -> str:
  lines: list[str] = []
  paths = info['paths']
  lines.append('# Menagerie Scoped Check Plan')
  lines.append('')
  if paths:
    lines.append('## Changed paths')
    for path in paths:
      lines.append(f'- `{path}`')
  else:
    lines.append('No changed paths were supplied or discovered.')
  lines.append('')

  lines.append('## Classification')
  for key in (
    'xml_files',
    'scene_xmls',
    'model_dirs',
    'model_license_files',
    'changelog_files',
    'tooling_files',
    'model_assets',
  ):
    values = info[key]
    if values:
      lines.append(f'- {key}: ' + ', '.join(f'`{v}`' for v in values))
  bool_keys = ['top_license_changed', 'contributors_changed', 'gallery_related', 'docs_only']
  for key in bool_keys:
    if info[key]:
      lines.append(f'- {key}: yes')
  if not any(info[key] for key in ('xml_files', 'model_dirs', 'license_related', 'contributors_changed', 'gallery_related', 'tooling_files', 'docs_only')):
    lines.append('- No specialized class detected; use final `make check` or `make all` based on risk.')
  lines.append('')

  model_dir_status = info['model_dir_status']
  if model_dir_status:
    lines.append('## Model directory notes')
    for status in model_dir_status:
      missing = status['missing_required']
      note = f"; {status['note']}" if status.get('note') else ''
      if missing:
        lines.append(
          f"- `{status['directory']}`: missing/verify "
          + ', '.join(f'`{item}`' for item in missing)
          + note
        )
      else:
        lines.append(f"- `{status['directory']}`: required layout files present{note}")
    lines.append('')

  lines.append('## Commands')
  for item in commands:
    lines.append(f"- **{item['level']}**: `{item['command']}`")
    lines.append(f"  - {item['reason']}")
  lines.append('')

  lines.append('## Route reminders')
  lines.append('- Route model selection, category, gallery inclusion, and scene exemption decisions to `model-catalog`.')
  lines.append('- Route compile/step smoke failures, missing meshes, MuJoCo warnings, and viewer/runtime issues to `model-loading`.')
  lines.append('- Route semantic MJCF edits, attachment/composition, keyframes, actuator tuning, and MJX conversion work to `model-editing`.')
  lines.append('- Do not claim skipped checks passed; list skipped checks with the reason.')
  lines.append('')
  return '\n'.join(lines)


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description='Emit a scoped Menagerie maintainer check plan from changed paths.'
  )
  parser.add_argument('paths', nargs='*', help='Changed paths, relative to the repo root.')
  parser.add_argument(
    '--repo-root',
    type=pathlib.Path,
    default=pathlib.Path.cwd(),
    help='Repo root for path normalization and optional Git diff discovery.',
  )
  parser.add_argument(
    '--base',
    help='Git base/ref. When provided, changed paths are read with git diff --name-only BASE --.',
  )
  parser.add_argument(
    '--format',
    choices=('markdown', 'json'),
    default='markdown',
    help='Output format.',
  )
  args = parser.parse_args(argv)

  root = args.repo_root.resolve()
  raw_paths = list(args.paths)
  if not raw_paths:
    try:
      raw_paths = _git_changed_paths(root, args.base)
    except Exception as exc:  # pylint: disable=broad-exception-caught
      print(f'WARNING: could not discover changed paths from git: {exc}', file=sys.stderr)
      raw_paths = []

  paths = sorted(_dedupe(_normalize_path(path, root) for path in raw_paths))
  info = classify(paths, root)
  commands = build_plan(info)
  output = {'classification': info, 'commands': commands}

  if args.format == 'json':
    print(json.dumps(output, indent=2, sort_keys=True))
  else:
    print(_markdown(info, commands))
  return 0


if __name__ == '__main__':
  sys.exit(main())
