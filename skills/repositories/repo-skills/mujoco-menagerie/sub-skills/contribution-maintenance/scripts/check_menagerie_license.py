#!/usr/bin/env python3
# Copyright 2026 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Check or regenerate Menagerie's top-level concatenated LICENSE file.

Adapted from Menagerie's license regeneration script. The generated top-level
LICENSE is a deterministic concatenation of every one-level model directory's
LICENSE file, sorted by directory name, followed by the base project license.

Examples:
  python check_menagerie_license.py --root /path/to/checkout --check
  python check_menagerie_license.py --root /path/to/checkout --write
  python check_menagerie_license.py --root /path/to/checkout --print > LICENSE
"""

from __future__ import annotations

import argparse
import pathlib
import sys

HLINE = '=' * 80 + '\n'


def _read_text(path: pathlib.Path) -> str:
  return path.read_text(encoding='utf-8')


def _write_text(path: pathlib.Path, text: str) -> None:
  path.write_text(text, encoding='utf-8')


def _license_files(root: pathlib.Path) -> list[pathlib.Path]:
  """Return model-directory LICENSE files included in the concatenation."""
  files = sorted(root.glob('*/LICENSE'), key=lambda f: f.parent.name)
  return [
    path
    for path in files
    if path.parent.name != 'opensource' and not path.parent.name.startswith('.')
  ]


def get_base_license(root: pathlib.Path) -> str:
  """Return the base project license text.

  Prefer `opensource/LICENSE` when present. Otherwise extract the final section
  from the existing top-level concatenated LICENSE. If the top-level LICENSE is
  not already concatenated, treat the entire file as the base license.
  """
  opensource_license = root / 'opensource' / 'LICENSE'
  if opensource_license.exists():
    return _read_text(opensource_license)

  existing = root / 'LICENSE'
  if existing.exists():
    text = _read_text(existing)
    sections = text.split(HLINE + '\n')
    return sections[-1] if sections else text

  raise FileNotFoundError(
    'Cannot find base license. Expected opensource/LICENSE or an existing '
    'top-level LICENSE.'
  )


def generate_license(root: pathlib.Path) -> str:
  """Generate the complete top-level LICENSE contents for a checkout root."""
  root = root.resolve()
  out = ''
  for license_file in _license_files(root):
    out += HLINE
    out += f"License for contents in the directory '{license_file.parent.name}/'\n"
    out += HLINE + '\n'
    out += _read_text(license_file) + '\n\n'

  out += HLINE
  out += 'The following license applies to all other contents\n'
  out += HLINE + '\n'
  out += get_base_license(root)
  return out


def check_license(root: pathlib.Path) -> tuple[bool, str]:
  """Return (ok, message) for top-level LICENSE consistency."""
  license_path = root / 'LICENSE'
  if not license_path.exists():
    return False, 'FAIL: LICENSE file does not exist.'

  current = _read_text(license_path)
  generated = generate_license(root)
  if current != generated:
    return (
      False,
      "FAIL: LICENSE file is out of date. Regenerate it with the repo's "
      "regenerate_license.py or with this script's --write mode.",
    )
  return True, 'OK: LICENSE file is up to date.'


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description='Check or regenerate Menagerie top-level LICENSE.'
  )
  parser.add_argument(
    '--root',
    type=pathlib.Path,
    default=pathlib.Path.cwd(),
    help='Menagerie checkout root. Defaults to the current working directory.',
  )
  mode = parser.add_mutually_exclusive_group()
  mode.add_argument(
    '--check',
    action='store_true',
    help='Check whether root/LICENSE is current. This is the default mode.',
  )
  mode.add_argument(
    '--write',
    action='store_true',
    help='Regenerate root/LICENSE in place.',
  )
  mode.add_argument(
    '--print',
    dest='print_generated',
    action='store_true',
    help='Print generated LICENSE content to stdout.',
  )
  args = parser.parse_args(argv)

  root = args.root.resolve()
  if not root.is_dir():
    print(f'ERROR: root is not a directory: {root}', file=sys.stderr)
    return 2

  try:
    generated = generate_license(root)
  except Exception as exc:  # pylint: disable=broad-exception-caught
    print(f'ERROR: {exc}', file=sys.stderr)
    return 2

  license_path = root / 'LICENSE'
  if args.write:
    _write_text(license_path, generated)
    print(f'OK: regenerated {license_path}')
    return 0

  if args.print_generated:
    sys.stdout.write(generated)
    return 0

  if not license_path.exists():
    print('FAIL: LICENSE file does not exist.', file=sys.stderr)
    return 1

  current = _read_text(license_path)
  if current != generated:
    print(
      "FAIL: LICENSE file is out of date. Run 'python regenerate_license.py' "
      'or this script with --write to fix.',
      file=sys.stderr,
    )
    print(f'Included model LICENSE files: {len(_license_files(root))}', file=sys.stderr)
    return 1

  print('OK: LICENSE file is up to date.')
  return 0


if __name__ == '__main__':
  sys.exit(main())
