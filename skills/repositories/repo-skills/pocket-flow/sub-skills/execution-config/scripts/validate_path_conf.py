#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Validate a PocketFlow path.conf and preview launcher arguments."""

from __future__ import print_function

import argparse
import json
import os
import re
import shlex
import sys
from collections import OrderedDict

RUN_SCRIPT_RE = re.compile(r'at_([0-9A-Za-z]+)_run\.py$')
DATA_DIR_RE = re.compile(r'^data_dir_(local|docker|seven|hdfs)_([0-9A-Za-z]+)$')


def _strip_comment(raw_line):
    return raw_line.split('#', 1)[0].strip()


def _is_unset(value):
    return value == '' or value.lower() == 'none'


def _parse_conf(conf_path):
    entries = OrderedDict()
    with open(conf_path, 'r') as handle:
        for lineno, raw_line in enumerate(handle, 1):
            line = _strip_comment(raw_line)
            if not line:
                continue
            if '=' not in line:
                raise ValueError('line {} is missing "=": {}'.format(lineno, raw_line.rstrip()))
            key, value = [part.strip() for part in line.split('=', 1)]
            if not key:
                raise ValueError('line {} has an empty key'.format(lineno))
            entries[key] = value
    return entries


def _extract_dataset(script_name):
    match = RUN_SCRIPT_RE.search(os.path.basename(script_name))
    if match is None:
        raise ValueError('script name must end with at_<dataset>_run.py: {}'.format(script_name))
    return match.group(1)


def _build_report(mode, script_name, entries):
    dataset = _extract_dataset(script_name)
    warnings = []
    errors = []
    launcher_args = []

    for key, value in entries.items():
        if key.startswith('data_dir_'):
            continue
        if _is_unset(value):
            continue
        launcher_args.extend(['--{}'.format(key), value])

    primary_key = 'data_dir_{}_{}'.format(mode, dataset)
    primary_value = entries.get(primary_key)
    if primary_value is None or _is_unset(primary_value):
        primary_value = '<missing:{}>'.format(primary_key)
        warnings.append('missing mode-specific dataset path {}'.format(primary_key))
        errors.append('required mode-specific dataset path is missing: {}'.format(primary_key))
    launcher_args.extend(['--data_dir_local', primary_value])

    hdfs_key = 'data_dir_hdfs_{}'.format(dataset)
    hdfs_value = entries.get(hdfs_key)
    if hdfs_value is not None and not _is_unset(hdfs_value):
        launcher_args.extend(['--data_dir_hdfs', hdfs_value])

    preview = 'python {}'.format(shlex.quote(script_name))
    if launcher_args:
        preview = '{} {}'.format(preview, ' '.join(shlex.quote(token) for token in launcher_args))

    available_data_keys = [key for key in entries if DATA_DIR_RE.match(key)]

    return {
        'mode': mode,
        'script': script_name,
        'dataset': dataset,
        'primary_data_key': primary_key,
        'primary_data_value': primary_value,
        'available_data_keys': available_data_keys,
        'launcher_args': launcher_args,
        'preview': preview,
        'warnings': warnings,
        'errors': errors,
    }


def _print_report(report):
    print('mode={}'.format(report['mode']))
    print('script={}'.format(report['script']))
    print('dataset={}'.format(report['dataset']))
    print('primary_data_key={}'.format(report['primary_data_key']))
    print('primary_data_value={}'.format(report['primary_data_value']))
    print('preview={}'.format(report['preview']))
    if report['available_data_keys']:
        print('available_data_keys={}'.format(','.join(report['available_data_keys'])))
    for warning in report['warnings']:
        print('warning: {}'.format(warning))
    for error in report['errors']:
        print('error: {}'.format(error))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Validate a PocketFlow path.conf and preview launcher arguments.')
    parser.add_argument('--mode', required=True, choices=['local', 'docker', 'seven'], help='execution mode to preview')
    parser.add_argument('--script', required=True, help='run script filename such as nets/resnet_at_cifar10_run.py')
    parser.add_argument('--conf', required=True, help='path.conf or path.conf.template file')
    parser.add_argument('--json', action='store_true', help='emit machine-readable JSON')
    args = parser.parse_args(argv)

    try:
        entries = _parse_conf(args.conf)
        report = _build_report(args.mode, args.script, entries)
    except Exception as exc:
        print('error: {}'.format(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=False))
    else:
        _print_report(report)
    return 2 if report['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
