#!/usr/bin/env python
"""Check a deepjazz-compatible environment without training or playback.

This helper is safe by default. It imports legacy dependencies and, when an
optional --repo-root is supplied, attempts to import deepjazz-style modules for
signature inspection only. It does not train a model, parse large data, play
audio, or write MIDI.
"""
from __future__ import print_function

import argparse
import inspect
import json
import os
import platform
import sys

DEPENDENCIES = ['numpy', 'music21', 'theano', 'keras']
REPO_MODULES = ['grammar', 'qa', 'preprocess', 'lstm', 'generator']
FUNCTIONS = {
    'grammar': ['parse_melody', 'unparse_grammar'],
    'qa': ['prune_grammar', 'prune_notes', 'clean_up_notes'],
    'preprocess': ['get_musical_data', 'get_corpus_data'],
    'lstm': ['build_model'],
    'generator': ['generate', 'main'],
}


def _version(module):
    for attr in ('__version__', 'VERSION_STR', 'VERSION', 'version'):
        value = getattr(module, attr, None)
        if value:
            return value
    return None


def _signature(obj):
    try:
        return str(inspect.signature(obj))
    except Exception:
        try:
            spec = inspect.getargspec(obj)
            args = list(spec.args)
            if spec.varargs:
                args.append('*' + spec.varargs)
            if spec.keywords:
                args.append('**' + spec.keywords)
            return '(' + ', '.join(args) + ')'
        except Exception:
            return None


def _import(name):
    __import__(name)
    return sys.modules[name]


def _check_dependencies():
    results = {}
    errors = []
    for name in DEPENDENCIES:
        try:
            module = _import(name)
            results[name] = {'status': 'ok', 'version': _version(module)}
        except Exception as exc:
            results[name] = {'status': 'error', 'error': '%s: %s' % (exc.__class__.__name__, exc)}
            errors.append('dependency import failed: %s' % name)
    return results, errors


def _check_repo(repo_root):
    results = {}
    errors = []
    if not repo_root:
        return results, errors
    root = os.path.abspath(repo_root)
    if root not in sys.path:
        sys.path.insert(0, root)
    for name in REPO_MODULES:
        try:
            module = _import(name)
            signatures = {}
            for func in FUNCTIONS.get(name, []):
                if hasattr(module, func):
                    signatures[func] = _signature(getattr(module, func))
            results[name] = {'status': 'ok', 'signatures': signatures}
        except Exception as exc:
            results[name] = {'status': 'error', 'error': '%s: %s' % (exc.__class__.__name__, exc)}
            errors.append('repo module import failed: %s' % name)
    return results, errors


def check(args):
    deps, errors = _check_dependencies()
    repo, repo_errors = _check_repo(args.repo_root)
    errors.extend(repo_errors)

    backend = {
        'KERAS_BACKEND': os.environ.get('KERAS_BACKEND'),
        'expect_theano': bool(args.expect_theano),
        'matches_expectation': None,
    }
    if args.expect_theano:
        backend['matches_expectation'] = bool(backend['KERAS_BACKEND'] and backend['KERAS_BACKEND'].lower() == 'theano')
        if not backend['matches_expectation']:
            errors.append('KERAS_BACKEND is not set to theano')

    warnings = []
    if sys.version_info[0] >= 3:
        warnings.append('original deepjazz source is Python 2-era; Python 3 execution needs compatibility patches')
    if not args.repo_root:
        warnings.append('repo module inspection skipped because --repo-root was not supplied')

    return {
        'status': 'ok' if not errors else 'error',
        'python': {
            'version': sys.version,
            'major': sys.version_info[0],
            'platform': platform.platform(),
        },
        'backend': backend,
        'dependencies': deps,
        'repo_modules': repo,
        'warnings': warnings,
        'errors': errors,
    }


def _print_human(report):
    print('status: %s' % report['status'])
    print('python_major: %s' % report['python']['major'])
    print('KERAS_BACKEND: %s' % report['backend']['KERAS_BACKEND'])
    print('dependencies:')
    for name in DEPENDENCIES:
        item = report['dependencies'].get(name, {})
        print('  %s: %s%s' % (name, item.get('status'), ' (%s)' % item.get('version') if item.get('version') else ''))
    if report['repo_modules']:
        print('repo_modules:')
        for name in REPO_MODULES:
            if name not in report['repo_modules']:
                continue
            item = report['repo_modules'][name]
            print('  %s: %s' % (name, item.get('status')))
            for func, sig in sorted(item.get('signatures', {}).items()):
                print('    %s%s' % (func, sig or ''))
    if report['warnings']:
        print('warnings:')
        for item in report['warnings']:
            print('  - %s' % item)
    if report['errors']:
        print('errors:')
        for item in report['errors']:
            print('  - %s' % item)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Check deepjazz legacy dependencies and optional module signatures safely.')
    parser.add_argument('--repo-root', help='optional deepjazz-style source root for module signature inspection')
    parser.add_argument('--expect-theano', action='store_true', help='fail if KERAS_BACKEND is not set to theano')
    parser.add_argument('--json', action='store_true', help='emit JSON report')
    args = parser.parse_args(argv)
    report = check(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report)
    return 0 if report['status'] == 'ok' else 2


if __name__ == '__main__':
    sys.exit(main())
