#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert an AutoML-generated hparam file into PocketFlow CLI flags."""

from __future__ import print_function

import argparse
import re
import sys
from collections import OrderedDict

REQUIRED_KEYS = [
    'ws_prune_ratio_exp',
    'ws_iter_ratio_beg',
    'ws_iter_ratio_end',
    'ws_update_mask_step',
]
LINE_RE = re.compile(r'^([A-Za-z0-9_]+)\s*=\s*(.+)$')


def _normalize_value(raw_value):
    value = raw_value.strip()
    if '##' not in value and '#' in value:
        value = value.split('#', 1)[0].strip()
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description='Convert AutoML-generated hyper-parameters into PocketFlow flags.')
    parser.add_argument('file_path', help='generated hparam file')
    args = parser.parse_args(argv)

    values = OrderedDict()
    placeholder_keys = []
    malformed_lines = []

    try:
        handle = open(args.file_path, 'r')
    except IOError as exc:
        parser.error(str(exc))
    with handle:
        for lineno, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            match = LINE_RE.match(line)
            if match is None:
                malformed_lines.append('line {}: {}'.format(lineno, raw_line.rstrip()))
                continue
            name = match.group(1)
            raw_value = _normalize_value(match.group(2))
            if raw_value.startswith('##') and raw_value.endswith('##'):
                placeholder_keys.append(name)
                continue
            values[name] = raw_value

    missing = [key for key in REQUIRED_KEYS if key not in values]
    problems = []
    if placeholder_keys:
        unique_placeholders = []
        for name in placeholder_keys:
            if name not in unique_placeholders:
                unique_placeholders.append(name)
        problems.append('placeholders still present for: {}'.format(', '.join(unique_placeholders)))
    if missing:
        problems.append('missing required field(s): {}'.format(', '.join(missing)))
    if malformed_lines:
        problems.append('malformed line(s): {}'.format('; '.join(malformed_lines)))
    if problems:
        parser.error(' ; '.join(problems))

    try:
        prune_ratio_exp = float(values['ws_prune_ratio_exp'])
        iter_ratio_beg = float(values['ws_iter_ratio_beg'])
        iter_ratio_end = float(values['ws_iter_ratio_end'])
        update_mask_step = int(float(values['ws_update_mask_step']))
    except ValueError as exc:
        parser.error('unable to parse numeric values: {}'.format(exc))

    iter_ratio_end = iter_ratio_beg + iter_ratio_end * (1.0 - iter_ratio_beg)

    output = []
    output.append('--ws_prune_ratio_exp {:.4f}'.format(prune_ratio_exp))
    output.append('--ws_iter_ratio_beg {:.4f}'.format(iter_ratio_beg))
    output.append('--ws_iter_ratio_end {:.4f}'.format(iter_ratio_end))
    output.append('--ws_update_mask_step {}'.format(update_mask_step))
    print(' '.join(output))
    return 0


if __name__ == '__main__':
    sys.exit(main())
