#!/usr/bin/env python3
"""Validate common EdgeConnect config path mistakes.

This checker loads a YAML config without importing the repo package, verifies
mode-dependent flist requirements, and spots path resolution problems that
frequently break dataset preparation.
"""

import argparse
from pathlib import Path
import sys

DEFAULTS = {
    'MODE': 1,
    'MASK': 3,
    'EDGE': 1,
    'NMS': 1,
}

KNOWN_KEYS = {
    'PATH',
    'MODE', 'MODEL', 'MASK', 'EDGE', 'NMS', 'SEED', 'GPU', 'DEBUG', 'VERBOSE',
    'TRAIN_FLIST', 'VAL_FLIST', 'TEST_FLIST',
    'TRAIN_EDGE_FLIST', 'VAL_EDGE_FLIST', 'TEST_EDGE_FLIST',
    'TRAIN_MASK_FLIST', 'VAL_MASK_FLIST', 'TEST_MASK_FLIST',
    'RESULTS',
}

PATH_KEYS = {
    'TRAIN_FLIST', 'VAL_FLIST', 'TEST_FLIST',
    'TRAIN_EDGE_FLIST', 'VAL_EDGE_FLIST', 'TEST_EDGE_FLIST',
    'TRAIN_MASK_FLIST', 'VAL_MASK_FLIST', 'TEST_MASK_FLIST',
    'RESULTS',
}

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description='Validate EdgeConnect config paths and data-list wiring.'
    )
    parser.add_argument('--config', required=True, help='path to config.yml or a directory containing it')
    parser.add_argument('--cwd', default='.', help='runtime working directory used to resolve relative paths')
    parser.add_argument('--mode', help='optional override for mode: 1/train, 2/test, or 3/eval')
    parser.add_argument('--check-listed-files', action='store_true', help='also validate entries inside text flists')
    parser.add_argument('--strict-keys', action='store_true', help='fail on unknown YAML keys instead of warning')
    return parser.parse_args(argv)


def load_yaml_config(path):
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError('PyYAML is required to validate EdgeConnect configs') from exc

    with path.open('r', encoding='utf-8') as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError('config root must be a mapping')

    return data


def resolve_config_path(raw_path):
    path = Path(raw_path).expanduser().resolve()
    if path.is_dir():
        for candidate in (path / 'config.yml', path / 'config.yaml'):
            if candidate.exists():
                return candidate.resolve()
        raise FileNotFoundError('no config.yml or config.yaml found in %s' % path)
    if not path.exists():
        raise FileNotFoundError('config path does not exist: %s' % path)
    return path


def parse_mode(value):
    if value is None:
        return None
    if isinstance(value, int):
        if value in (1, 2, 3):
            return value
        raise ValueError('mode must be 1, 2, or 3')

    text = str(value).strip().lower()
    aliases = {
        '1': 1,
        'train': 1,
        '2': 2,
        'test': 2,
        '3': 3,
        'eval': 3,
    }
    if text not in aliases:
        raise ValueError('mode must be 1/train, 2/test, or 3/eval')
    return aliases[text]


def effective_int(config, key):
    value = config.get(key, DEFAULTS.get(key))
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError('%s must be an integer' % key)


def resolve_from(base_dir, raw_value):
    value = Path(str(raw_value)).expanduser()
    if value.is_absolute():
        return value
    return (base_dir / value).expanduser().resolve()


def collect_directory_issues(directory):
    warnings = []
    errors = []
    top_level = [child for child in directory.iterdir() if child.is_file() and child.suffix.lower() in IMAGE_EXTENSIONS]
    if not top_level:
        errors.append('directory has no top-level jpg/png-style images')

    nested = [child for child in directory.rglob('*') if child.is_file() and child.parent != directory and child.suffix.lower() in IMAGE_EXTENSIONS]
    if nested:
        warnings.append('directory contains nested images that the runtime loader will ignore')

    return warnings, errors


def collect_text_list_issues(path, cwd, check_entries):
    warnings = []
    errors = []
    try:
        with path.open('r', encoding='utf-8') as handle:
            entries = [line.strip() for line in handle if line.strip() and not line.lstrip().startswith('#')]
    except UnicodeDecodeError:
        return warnings, ['file is not readable as UTF-8 text; treat it as a direct asset path instead']

    if not entries:
        return warnings, ['list file is empty']

    if len(entries) == 1:
        warnings.append('list file contains a single entry; Dataset.load_flist uses np.genfromtxt and can fail on one-line lists')

    if check_entries:
        missing = []
        for entry in entries:
            candidate = Path(entry).expanduser()
            if not candidate.is_absolute():
                candidate = (cwd / candidate).expanduser().resolve()
            if not candidate.exists() or not candidate.is_file():
                missing.append(entry)
            if len(missing) >= 20:
                break
        if missing:
            errors.append('%d listed path(s) do not exist or are not files: %s' % (len(missing), ', '.join(missing)))

    return warnings, errors


def validate_relative_path(value, cwd, config_dir):
    runtime_path = (cwd / value).expanduser().resolve()
    config_path = (config_dir / value).expanduser().resolve()

    if runtime_path.exists():
        return runtime_path, config_path, None
    if config_path.exists():
        return runtime_path, config_path, 'path exists only relative to the config directory, but EdgeConnect resolves relative paths from cwd'
    return runtime_path, config_path, 'path does not exist from the launch working directory'


def validate_value(key, raw_value, cwd, config_dir, check_listed_files):
    warnings = []
    errors = []

    if raw_value is None or raw_value == '':
        errors.append('missing value')
        return warnings, errors

    if isinstance(raw_value, (list, tuple)):
        if not raw_value:
            errors.append('empty list')
            return warnings, errors
        for index, item in enumerate(raw_value):
            child_warnings, child_errors = validate_value('%s[%d]' % (key, index), item, cwd, config_dir, check_listed_files)
            warnings.extend(child_warnings)
            errors.extend(child_errors)
        return warnings, errors

    path = Path(str(raw_value)).expanduser()
    if key == 'RESULTS':
        if path.is_absolute():
            runtime_path = path.resolve()
            if runtime_path.exists() and not runtime_path.is_dir():
                errors.append('output path already exists as a file')
            return warnings, errors

        runtime_path = (cwd / path).expanduser().resolve()
        config_path = (config_dir / path).expanduser().resolve()
        if runtime_path.exists() and not runtime_path.is_dir():
            errors.append('output path already exists as a file')
        elif config_path.exists() and not runtime_path.exists():
            warnings.append('relative output path exists only relative to the config directory; runtime will use cwd')
        return warnings, errors

    if path.is_absolute():
        runtime_path = path.resolve()
        config_path = runtime_path
    else:
        runtime_path, config_path, relative_issue = validate_relative_path(str(path), cwd, config_dir)
        if relative_issue:
            errors.append(relative_issue)
            return warnings, errors

    if runtime_path.is_dir():
        directory_warnings, directory_errors = collect_directory_issues(runtime_path)
        warnings.extend(directory_warnings)
        errors.extend(directory_errors)
        if not directory_errors and check_listed_files:
            warnings.append('directory input is valid, but directory mode only reads top-level jpg/png files')
        return warnings, errors

    if runtime_path.is_file():
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            list_warnings, list_errors = collect_text_list_issues(runtime_path, cwd, check_listed_files)
            warnings.extend(list_warnings)
            errors.extend(list_errors)
        return warnings, errors

    # If we get here, the file does not exist from cwd but might be a direct
    # asset path that is only meaningful in another location.
    if path.is_absolute():
        errors.append('path does not exist: %s' % runtime_path)
    else:
        errors.append('path does not exist from the launch working directory')

    return warnings, errors


def mode_requirements(mode, mask, edge):
    required = []
    if mode in (1, 3):
        required.extend(['TRAIN_FLIST', 'VAL_FLIST'])
        if edge == 2:
            required.extend(['TRAIN_EDGE_FLIST', 'VAL_EDGE_FLIST'])
        if mask in (3, 4, 5):
            required.extend(['TRAIN_MASK_FLIST', 'VAL_MASK_FLIST'])
    elif mode == 2:
        required.extend(['TEST_FLIST', 'TEST_MASK_FLIST'])
        if edge == 2:
            required.append('TEST_EDGE_FLIST')
    return required


def main(argv=None):
    args = parse_args(argv)
    warnings = []
    errors = []

    try:
        config_path = resolve_config_path(args.config)
        cwd = Path(args.cwd).expanduser().resolve()
        if not cwd.is_dir():
            raise NotADirectoryError('cwd is not a directory: %s' % cwd)
        config = load_yaml_config(config_path)
    except Exception as exc:
        print('error: %s' % exc, file=sys.stderr)
        return 1

    if 'PATH' in config:
        warnings.append(('PATH', 'ignored by the runtime; PATH is derived from the config file location'))

    for key in config:
        if key not in KNOWN_KEYS:
            if args.strict_keys:
                errors.append((key, 'unknown config key'))
            else:
                warnings.append((key, 'unknown config key'))

    try:
        mode = parse_mode(args.mode) if args.mode is not None else parse_mode(config.get('MODE', DEFAULTS['MODE']))
        mask = effective_int(config, 'MASK')
        edge = effective_int(config, 'EDGE')
    except Exception as exc:
        print('error: %s' % exc, file=sys.stderr)
        return 1

    if mode == 2 and config.get('MASK') != 6:
        warnings.append(('MASK', 'test mode ignores MASK because the loader forces one-to-one masks'))
    if mode != 2 and config.get('MASK') == 6:
        warnings.append(('MASK', 'MASK=6 is only meaningful in test mode'))
    if config.get('RESULTS') is not None and mode != 2:
        warnings.append(('RESULTS', 'RESULTS is only used in test mode'))

    required_keys = mode_requirements(mode, mask, edge)

    # Validate keys that are required for the active mode.
    for key in required_keys:
        value = config.get(key)
        child_warnings, child_errors = validate_value(key, value, cwd, config_path.parent, args.check_listed_files)
        warnings.extend((key, message) for message in child_warnings)
        errors.extend((key, message) for message in child_errors)

    # Validate any additional path keys that were explicitly provided.
    for key in PATH_KEYS:
        if key in required_keys:
            continue
        if key not in config or config.get(key) in {None, ''}:
            continue
        child_warnings, child_errors = validate_value(key, config.get(key), cwd, config_path.parent, args.check_listed_files)
        warnings.extend((key, message) for message in child_warnings)
        errors.extend((key, message) for message in child_errors)
        if key.endswith('EDGE_FLIST') and edge != 2:
            warnings.append((key, 'present but ignored because EDGE=1'))
        elif key.endswith('MASK_FLIST') and (mode == 2 or mask not in (3, 4, 5)):
            warnings.append((key, 'present but ignored because the current mode does not use an external mask list'))

    for key, message in warnings:
        print('warning: %s: %s' % (key, message))

    if errors:
        for key, message in errors:
            print('error: %s: %s' % (key, message), file=sys.stderr)
        print('summary: %d error(s), %d warning(s)' % (len(errors), len(warnings)))
        return 1

    print('summary: 0 error(s), %d warning(s)' % len(warnings))
    print('config path validation passed for %s' % config_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
