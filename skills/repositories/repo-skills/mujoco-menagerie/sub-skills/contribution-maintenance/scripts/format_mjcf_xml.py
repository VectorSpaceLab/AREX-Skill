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
"""Portable Menagerie MJCF XML formatter.

This is adapted from Menagerie's formatter. It enforces the style documented in
CONTRIBUTING.md:
  * 2-space indentation
  * double-quoted attributes
  * self-closing empty elements as <foo/>
  * 120-column wrapping with one-level-deeper continuation indentation
  * preserved comments and blank lines between sibling elements

Examples:
  python format_mjcf_xml.py --check model.xml
  python format_mjcf_xml.py --write model.xml scene.xml
  python format_mjcf_xml.py model.xml > formatted.xml
"""

from __future__ import annotations

import argparse
import difflib
import pathlib
import sys
from collections.abc import Mapping

INDENT = '  '
MAX_WIDTH = 120


def _load_etree():
  try:
    from lxml import etree  # pylint: disable=import-outside-toplevel
  except ModuleNotFoundError as exc:
    raise SystemExit(
      'ERROR: format_mjcf_xml.py requires lxml. Install it with your '
      'environment manager, for example: python -m pip install lxml'
    ) from exc
  return etree


def _escape_attr(value: str) -> str:
  # Collapse runs of whitespace, including newlines, to a single space and
  # strip. XML attribute-value normalization already converts newlines to
  # spaces at parse time, so authored multi-line attribute values cannot be
  # recovered byte-for-byte after parsing.
  value = ' '.join(value.split())
  return (
    value.replace('&', '&amp;')
    .replace('<', '&lt;')
    .replace('>', '&gt;')
    .replace('"', '&quot;')
  )


def _attr_str(attrs: Mapping[str, str]) -> str:
  return ' '.join(f'{k}="{_escape_attr(v)}"' for k, v in attrs.items())


def _blank_lines_between(text_or_tail: str | None) -> int:
  """Return the number of blank lines represented by whitespace text."""
  if not text_or_tail:
    return 0
  return max(0, text_or_tail.count('\n') - 1)


def _format_open_tag(
  tag: str,
  attrs: Mapping[str, str],
  depth: int,
  self_close: bool,
) -> list[str]:
  """Format an opening or self-closing tag, wrapping at MAX_WIDTH."""
  prefix = INDENT * depth
  cont = INDENT * (depth + 1)
  suffix = '/>' if self_close else '>'

  if not attrs:
    return [f'{prefix}<{tag}{suffix}']

  one_line = f'{prefix}<{tag} {_attr_str(attrs)}{suffix}'
  if len(one_line) <= MAX_WIDTH:
    return [one_line]

  lines: list[str] = []
  current = f'{prefix}<{tag}'
  items = list(attrs.items())
  for i, (key, value) in enumerate(items):
    attr = f'{key}="{_escape_attr(value)}"'
    is_last = i == len(items) - 1
    candidate = f'{current} {attr}'
    limit = MAX_WIDTH - (len(suffix) if is_last else 0)
    if len(candidate) <= limit:
      current = candidate
    else:
      lines.append(current)
      current = f'{cont}{attr}'
  lines.append(current + suffix)
  return lines


def _serialize(node, depth: int, out: list[str], etree) -> None:
  prefix = INDENT * depth

  if isinstance(node, etree._Comment):  # pylint: disable=protected-access
    text = node.text or ''
    out.append(f'{prefix}<!--{text}-->')
    return

  tag = node.tag
  attrs = node.attrib
  children = list(node.iterchildren())
  has_children = bool(children)
  text = (node.text or '').strip()
  has_text = bool(text)

  if not has_children and not has_text:
    out.extend(_format_open_tag(tag, attrs, depth, self_close=True))
    return

  out.extend(_format_open_tag(tag, attrs, depth, self_close=False))

  if has_text and not has_children:
    out.append(f'{prefix}{INDENT}{text}')

  for i, child in enumerate(children):
    prev_ws = node.text if i == 0 else children[i - 1].tail
    if _blank_lines_between(prev_ws) > 0:
      out.append('')
    _serialize(child, depth + 1, out, etree)

  out.append(f'{prefix}</{tag}>')


def format_xml(source: str) -> str:
  """Return source XML formatted in Menagerie style."""
  etree = _load_etree()
  parser = etree.XMLParser(remove_blank_text=False, remove_comments=False)
  root = etree.fromstring(source.encode('utf-8'), parser=parser)
  out: list[str] = []
  _serialize(root, 0, out, etree)
  return '\n'.join(out) + '\n'


def _diff(path: pathlib.Path, current: str, formatted: str) -> str:
  return ''.join(
    difflib.unified_diff(
      current.splitlines(keepends=True),
      formatted.splitlines(keepends=True),
      fromfile=str(path),
      tofile=f'{path} (formatted)',
    )
  )


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description='Format Menagerie-style MJCF XML files.')
  mode = parser.add_mutually_exclusive_group()
  mode.add_argument(
    '--check',
    action='store_true',
    help='Exit 1 if any file is not formatted.',
  )
  mode.add_argument(
    '--write',
    action='store_true',
    help='Rewrite files in place.',
  )
  parser.add_argument(
    '--diff',
    action='store_true',
    help='With --check, print unified diffs for unformatted files.',
  )
  parser.add_argument('paths', nargs='+', type=pathlib.Path, help='XML files to process.')
  args = parser.parse_args(argv)

  failed: list[pathlib.Path] = []
  had_error = False

  for path in args.paths:
    try:
      text = path.read_text(encoding='utf-8')
      formatted = format_xml(text)
    except Exception as exc:  # pylint: disable=broad-exception-caught
      print(f'ERROR: failed to format {path}: {exc}', file=sys.stderr)
      had_error = True
      continue

    if args.check:
      if text != formatted:
        failed.append(path)
        if args.diff:
          sys.stderr.write(_diff(path, text, formatted))
    elif args.write:
      if text != formatted:
        path.write_text(formatted, encoding='utf-8')
    else:
      sys.stdout.write(formatted)

  if had_error:
    return 2

  if args.check and failed:
    print('Not formatted:', file=sys.stderr)
    for path in failed:
      print(f'  {path}', file=sys.stderr)
    return 1

  return 0


if __name__ == '__main__':
  sys.exit(main())
