#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Probe PocketFlow runtime dependencies without starting training."""

from __future__ import print_function

import argparse
import contextlib
import importlib
import io
import json
import os
import platform
import subprocess
import sys
from collections import OrderedDict


def _candidate_repo_roots(repo_root):
    candidates = []
    if repo_root:
        candidates.append(os.path.abspath(repo_root))
    candidates.append(os.getcwd())
    current = os.path.abspath(os.path.dirname(__file__))
    while True:
        candidates.append(current)
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    seen = set()
    result = []
    for candidate in candidates:
        real_candidate = os.path.realpath(candidate)
        if real_candidate not in seen:
            result.append(real_candidate)
            seen.add(real_candidate)
    return result


def _prepare_import_path(repo_root):
    for candidate in _candidate_repo_roots(repo_root):
        if os.path.isfile(os.path.join(candidate, 'utils', 'multi_gpu_wrapper.py')):
            if candidate not in sys.path:
                sys.path.insert(0, candidate)
            return True
    fallback = os.path.abspath(repo_root or os.getcwd())
    if fallback not in sys.path:
        sys.path.insert(0, fallback)
    return False


def _capture_import(module_name):
    buffer = io.StringIO()
    record = OrderedDict()
    try:
        with contextlib.redirect_stdout(buffer):
            module = importlib.import_module(module_name)
    except Exception as exc:
        record['ok'] = False
        record['error'] = '{}: {}'.format(exc.__class__.__name__, exc)
        message = buffer.getvalue().strip()
        if message:
            record['message'] = message
        return record
    record['ok'] = True
    message = buffer.getvalue().strip()
    if message:
        record['message'] = message
    version = getattr(module, '__version__', None)
    if version:
        record['version'] = version
    return record


def _probe_gpus(idle_count, threshold):
    record = OrderedDict()
    record['requested_idle_count'] = idle_count
    record['threshold'] = threshold
    cmd = [
        'nvidia-smi', '--query-gpu=index,memory.used,memory.total',
        '--format=csv,noheader,nounits'
    ]
    try:
        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        )
    except FileNotFoundError:
        record['ok'] = False
        record['available'] = False
        record['error'] = 'nvidia-smi not found'
        return record
    except subprocess.CalledProcessError as exc:
        record['ok'] = False
        record['available'] = False
        stderr = (exc.stderr or '').strip()
        stdout = (exc.stdout or '').strip()
        record['error'] = stderr or stdout or str(exc)
        return record

    idle_rows = []
    for raw_line in completed.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        pieces = [piece.strip() for piece in line.split(',')]
        if len(pieces) != 3:
            continue
        try:
            gpu_id = int(pieces[0])
            mem_used = float(pieces[1])
            mem_total = float(pieces[2])
        except ValueError:
            continue
        if mem_total <= 0:
            continue
        usage = mem_used / mem_total
        if usage < threshold:
            idle_rows.append((gpu_id, usage))
    idle_rows.sort(key=lambda item: item[1])
    idle_ids = [gpu_id for gpu_id, _ in idle_rows]
    record['ok'] = True
    record['available'] = True
    record['idle_gpu_ids'] = idle_ids[:max(idle_count, 0)]
    record['enough_idle_gpus'] = len(idle_ids) >= idle_count
    if len(idle_ids) < idle_count:
        record['warning'] = 'not enough idle GPUs; idle GPUs are: {}'.format(idle_ids)
    return record


def _status_from_report(report, strict):
    warnings = []

    wrapper = report['multi_gpu_wrapper']
    if not wrapper.get('ok', False):
        warnings.append('utils.multi_gpu_wrapper: {}'.format(wrapper.get('error', 'unknown')))
    else:
        message = wrapper.get('message', '')
        if message:
            lower = message.lower()
            if 'warning' in lower or 'unsupported' in lower:
                warnings.append('utils.multi_gpu_wrapper: {}'.format(message))

    for key in ('horovod_tensorflow', 'tfplus_tensorflow'):
        entry = report[key]
        if not entry.get('ok', False):
            warnings.append('{} missing (optional): {}'.format(key, entry.get('error', 'not available')))

    gpu_probe = report['gpu_probe']
    if not gpu_probe.get('available', False):
        warnings.append('gpu probe unavailable: {}'.format(gpu_probe.get('error', 'unknown')))
    elif not gpu_probe.get('enough_idle_gpus', True):
        warnings.append(gpu_probe.get('warning', 'not enough idle GPUs'))

    if not report['tensorflow']['ok'] or not report['tf_contrib_lite'].get('ok', False):
        return 'fail', warnings
    if strict and warnings:
        return 'fail', warnings
    if warnings:
        return 'warn', warnings
    return 'ok', warnings


def _build_report(idle_count, threshold, repo_root):
    repo_root_detected = _prepare_import_path(repo_root)
    report = OrderedDict()
    report['python_version'] = platform.python_version()
    report['repo_root_detected'] = repo_root_detected
    report['tensorflow'] = _capture_import('tensorflow')
    if report['tensorflow']['ok']:
        report['tf_contrib_lite'] = _capture_import('tensorflow.contrib.lite.python.lite_constants')
    else:
        report['tf_contrib_lite'] = OrderedDict([
            ('ok', False),
            ('skipped', True),
            ('error', 'tensorflow import failed'),
        ])
    report['multi_gpu_wrapper'] = _capture_import('utils.multi_gpu_wrapper')
    report['horovod_tensorflow'] = _capture_import('horovod.tensorflow')
    report['tfplus_tensorflow'] = _capture_import('tfplus.tensorflow')
    report['gpu_probe'] = _probe_gpus(idle_count, threshold)
    return report


def _print_text(report, status, warnings):
    print('python_version={}'.format(report['python_version']))
    tensorflow = report['tensorflow']
    if tensorflow['ok']:
        version = tensorflow.get('version', 'unknown')
        print('tensorflow=ok {}'.format(version))
    else:
        print('tensorflow=error {}'.format(tensorflow.get('error', 'unknown')))
    lite = report['tf_contrib_lite']
    if lite.get('skipped'):
        print('tf.contrib.lite.python.lite_constants=skipped {}'.format(lite.get('error', '')))
    elif lite['ok']:
        print('tf.contrib.lite.python.lite_constants=ok')
    else:
        print('tf.contrib.lite.python.lite_constants=error {}'.format(lite.get('error', 'unknown')))
    wrapper = report['multi_gpu_wrapper']
    if wrapper['ok']:
        print('utils.multi_gpu_wrapper=ok')
        if wrapper.get('message'):
            print('multi_gpu_message={}'.format(wrapper['message']))
    else:
        print('utils.multi_gpu_wrapper=error {}'.format(wrapper.get('error', 'unknown')))
    for key in ('horovod_tensorflow', 'tfplus_tensorflow'):
        entry = report[key]
        if entry['ok']:
            print('{}=ok'.format(key))
        else:
            print('{}=missing (optional): {}'.format(key, entry.get('error', 'unknown')))
    gpu_probe = report['gpu_probe']
    if gpu_probe.get('available', False):
        idle_ids = gpu_probe.get('idle_gpu_ids', [])
        print('gpu_probe=ok')
        print('idle_gpu_ids={}'.format(','.join(str(gpu_id) for gpu_id in idle_ids)))
        if not gpu_probe.get('enough_idle_gpus', True):
            print('gpu_warning={}'.format(gpu_probe.get('warning', 'not enough idle GPUs')))
    else:
        print('gpu_probe=unavailable {}'.format(gpu_probe.get('error', 'unknown')))
    for warning in warnings:
        print('warning: {}'.format(warning))
    print('status={}'.format(status))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Probe PocketFlow runtime dependencies without starting training.')
    parser.add_argument('--idle-count', type=int, default=1, help='number of idle GPUs to look for')
    parser.add_argument('--threshold', type=float, default=0.5, help='maximum memory-use ratio for an idle GPU')
    parser.add_argument('--repo-root', default=None, help='PocketFlow checkout root; defaults to autodetection')
    parser.add_argument('--json', action='store_true', help='emit machine-readable JSON')
    parser.add_argument('--strict', action='store_true', help='treat warnings as failures')
    args = parser.parse_args(argv)

    report = _build_report(args.idle_count, args.threshold, args.repo_root)
    status, warnings = _status_from_report(report, args.strict)
    report['status'] = status
    report['warnings'] = warnings

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=False))
    else:
        _print_text(report, status, warnings)
    return 1 if status == 'fail' else 0


if __name__ == '__main__':
    sys.exit(main())
