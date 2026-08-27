#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Parse a PocketFlow TensorFlow log into AutoML result fields."""

from __future__ import print_function

import argparse
import re
import sys
from collections import OrderedDict

PATTERNS = OrderedDict([
    ('accuracy', re.compile(r'INFO:tensorflow:accuracy:\s*([-+0-9.eE]+)')),
    ('prune_ratio', re.compile(r'INFO:tensorflow:pruning ratio:\s*([-+0-9.eE]+)')),
    ('loss', re.compile(r'INFO:tensorflow:loss:\s*([-+0-9.eE]+)')),
])


def _extract_metrics(file_path):
    metrics = {}
    try:
        with open(file_path, 'r') as handle:
            for raw_line in handle:
                for name, pattern in PATTERNS.items():
                    match = pattern.search(raw_line)
                    if match is not None:
                        metrics[name] = float(match.group(1))
    except IOError as exc:
        raise ValueError(str(exc))
    return metrics


def main(argv=None):
    parser = argparse.ArgumentParser(description='Convert PocketFlow TensorFlow logs to AutoML metrics.')
    parser.add_argument('file_path', help='TensorFlow log file')
    args = parser.parse_args(argv)

    try:
        metrics = _extract_metrics(args.file_path)
    except ValueError as exc:
        parser.error(str(exc))

    missing = [name for name in PATTERNS if name not in metrics]
    if missing:
        parser.error('missing required metric(s): {}'.format(', '.join(missing)))

    print('object_value={:.6f}'.format(metrics['accuracy']))
    print('prune_ratio={:.6f}'.format(metrics['prune_ratio']))
    print('loss={:.6f}'.format(metrics['loss']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
