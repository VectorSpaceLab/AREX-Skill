#!/usr/bin/env python
from __future__ import print_function

import argparse
import inspect
import json
import os
import sys

DISTILLED_SETTINGS = {
    'max_len': 20,
    'max_tries': 1000,
    'diversity': 0.5,
    'bpm': 130,
    'default_epochs': 128,
    'train_batch_size': 128,
    'lstm_units': 128,
    'dropout': 0.2,
    'loss': 'categorical_crossentropy',
    'optimizer': 'rmsprop',
    'output_extension': '.midi'
}

REQUIRED_DEPENDENCIES = ['numpy', 'music21', 'theano', 'keras']
REPO_MODULES = ['generator', 'lstm']


def _safe_import(name):
    __import__(name)
    return sys.modules[name]


def _module_version(module):
    for attr in ('__version__', 'VERSION', 'version'):
        value = getattr(module, attr, None)
        if value:
            return value
    return None


def _signature_text(obj):
    try:
        sig = inspect.signature(obj)
        return str(sig)
    except Exception:
        try:
            spec = inspect.getargspec(obj)
            bits = list(spec.args)
            if spec.varargs:
                bits.append('*' + spec.varargs)
            if spec.keywords:
                bits.append('**' + spec.keywords)
            return '(' + ', '.join(bits) + ')'
        except Exception:
            return None


def _ensure_repo_root(repo_root):
    if not repo_root:
        return None
    abs_root = os.path.abspath(repo_root)
    if abs_root not in sys.path:
        sys.path.insert(0, abs_root)
    return abs_root


def _backend_state(expect_theano):
    backend = os.environ.get('KERAS_BACKEND')
    state = {
        'KERAS_BACKEND': backend,
        'expect_theano': bool(expect_theano),
        'matches_expectation': None,
    }
    if expect_theano:
        state['matches_expectation'] = bool(backend and backend.lower() == 'theano')
    return state


def _collect_imports(check_repo_modules, repo_root):
    report = {
        'dependencies': {},
        'repo_modules': {},
        'errors': [],
    }

    for dep in REQUIRED_DEPENDENCIES:
        try:
            mod = _safe_import(dep)
            report['dependencies'][dep] = {
                'status': 'ok',
                'version': _module_version(mod),
            }
        except Exception as exc:
            report['dependencies'][dep] = {
                'status': 'error',
                'error': '%s: %s' % (exc.__class__.__name__, exc),
            }
            report['errors'].append('dependency import failed: %s' % dep)

    if check_repo_modules and repo_root:
        _ensure_repo_root(repo_root)
        for mod_name in REPO_MODULES:
            try:
                mod = _safe_import(mod_name)
                module_info = {
                    'status': 'ok',
                    'version': _module_version(mod),
                    'signatures': {},
                }
                for attr_name in ('generate', 'main') if mod_name == 'generator' else ('build_model',):
                    if hasattr(mod, attr_name):
                        module_info['signatures'][attr_name] = _signature_text(getattr(mod, attr_name))
                report['repo_modules'][mod_name] = module_info
            except Exception as exc:
                report['repo_modules'][mod_name] = {
                    'status': 'error',
                    'error': '%s: %s' % (exc.__class__.__name__, exc),
                }
                report['errors'].append('repo module import failed: %s' % mod_name)
    return report


def _format_human(result):
    lines = []
    lines.append('status: %s' % result['status'])
    backend = result.get('backend', {})
    if backend:
        lines.append('KERAS_BACKEND: %s' % backend.get('KERAS_BACKEND'))
        if backend.get('expect_theano'):
            lines.append('expect_theano: true')
            lines.append('matches_expectation: %s' % backend.get('matches_expectation'))
    if result.get('settings'):
        lines.append('settings:')
        for key in sorted(result['settings']):
            lines.append('  %s=%s' % (key, result['settings'][key]))
    imports = result.get('imports', {})
    if imports:
        lines.append('imports:')
        for dep in REQUIRED_DEPENDENCIES:
            dep_info = imports.get('dependencies', {}).get(dep, {})
            lines.append('  %s: %s%s' % (
                dep,
                dep_info.get('status'),
                (' (%s)' % dep_info.get('version')) if dep_info.get('version') else '',
            ))
        for mod_name in REPO_MODULES:
            if mod_name in imports.get('repo_modules', {}):
                mod_info = imports['repo_modules'][mod_name]
                lines.append('  %s: %s' % (mod_name, mod_info.get('status')))
                for attr_name, sig in sorted(mod_info.get('signatures', {}).items()):
                    lines.append('    %s%s' % (attr_name, sig if sig else ''))
    warnings = result.get('warnings', [])
    if warnings:
        lines.append('warnings:')
        for warning in warnings:
            lines.append('  - %s' % warning)
    errors = result.get('errors', [])
    if errors:
        lines.append('errors:')
        for error in errors:
            lines.append('  - %s' % error)
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Safe diagnostic for the legacy deepjazz LSTM generation path.'
    )
    parser.add_argument('--repo-root', help='optional path to a deepjazz-style source tree')
    parser.add_argument('--check-imports', action='store_true',
                        help='import the legacy dependencies and repo modules when available')
    parser.add_argument('--show-settings', action='store_true',
                        help='print distilled generation and model settings')
    parser.add_argument('--json', action='store_true',
                        help='emit JSON instead of human-readable text')
    parser.add_argument('--expect-theano', action='store_true',
                        help='treat a non-Theano KERAS_BACKEND as an error')
    args = parser.parse_args(argv)

    # Safe-by-default behavior: if the caller did not request any specific
    # action, show the distilled settings and dependency imports.
    if args.repo_root and not args.check_imports:
        args.check_imports = True
    if not args.check_imports and not args.show_settings and not args.repo_root:
        args.check_imports = True
        args.show_settings = True

    result = {
        'status': 'ok',
        'backend': _backend_state(args.expect_theano),
        'settings': DISTILLED_SETTINGS if args.show_settings else None,
        'imports': None,
        'warnings': [],
        'errors': [],
    }

    if args.expect_theano and not result['backend'].get('matches_expectation'):
        result['status'] = 'error'
        result['errors'].append('KERAS_BACKEND does not match the requested Theano backend')

    if args.check_imports:
        imports = _collect_imports(check_repo_modules=bool(args.repo_root), repo_root=args.repo_root)
        result['imports'] = imports
        if imports['errors']:
            result['status'] = 'error'
            result['errors'].extend(imports['errors'])
    else:
        result['imports'] = {'dependencies': {}, 'repo_modules': {}, 'errors': []}

    if args.repo_root and not os.path.exists(args.repo_root):
        result['status'] = 'error'
        result['errors'].append('repo-root does not exist: %s' % args.repo_root)

    if args.repo_root and args.check_imports and not result['imports']['repo_modules']:
        result['warnings'].append('repo-root was provided, but no repo modules were inspected')

    if args.json:
        sys.stdout.write(json.dumps(result, indent=2, sort_keys=True, default=str) + '\n')
    else:
        sys.stdout.write(_format_human(result) + '\n')

    return 0 if result['status'] == 'ok' else 1


if __name__ == '__main__':
    sys.exit(main())
