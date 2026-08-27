#!/usr/bin/env python3
"""Inspect MUNIT folder/list dataset layouts without importing MUNIT.

This helper counts images and validates list-file path resolution. It performs
no downloads, crops, writes, training, inference, or CUDA work.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

IMG_EXTENSIONS = ('.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG', '.ppm', '.PPM', '.bmp', '.BMP')
FOLDER_SPLITS = ['trainA', 'trainB', 'testA', 'testB']
LIST_PAIRS = [
    ('trainA', 'data_folder_train_a', 'data_list_train_a'),
    ('testA', 'data_folder_test_a', 'data_list_test_a'),
    ('trainB', 'data_folder_train_b', 'data_list_train_b'),
    ('testB', 'data_folder_test_b', 'data_list_test_b'),
]


def parse_scalar(text: str) -> Any:
    value = text.strip()
    if not value:
        return ''
    lower = value.lower()
    if lower in {'true', 'false'}:
        return lower == 'true'
    if lower in {'none', 'null', '~'}:
        return None
    if re.match(r'^[+-]?\d+$', value):
        try:
            return int(value)
        except ValueError:
            pass
    if re.match(r'^[+-]?(\d+\.\d*|\d*\.\d+|\d+)(e[+-]?\d+)?$', value, re.I):
        try:
            return float(value)
        except ValueError:
            pass
    return value.strip('"\'')


def parse_simple_yaml(path: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    stack: List[Tuple[int, Dict[str, Any]]] = [(0, data)]
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.split('#', 1)[0].rstrip()
        if not line.strip() or ':' not in line:
            continue
        indent = len(line) - len(line.lstrip(' '))
        key, value = line.strip().split(':', 1)
        key = key.strip()
        value = value.strip()
        while stack and indent < stack[-1][0]:
            stack.pop()
        current = stack[-1][1]
        if value == '':
            current[key] = {}
            stack.append((indent + 2, current[key]))
        else:
            current[key] = parse_scalar(value)
    return data


def load_config(path: Path) -> Tuple[Dict[str, Any], str]:
    try:
        import yaml  # type: ignore
        with path.open('r', encoding='utf-8') as handle:
            loaded = yaml.safe_load(handle)
        if isinstance(loaded, dict):
            return loaded, 'pyyaml.safe_load'
    except Exception:
        pass
    return parse_simple_yaml(path), 'built-in-simple-yaml'


def resolve_path(value: Any, repo_root: Path, config_dir: Path) -> Path:
    p = Path(str(value))
    if p.is_absolute():
        return p
    repo_candidate = repo_root / p
    config_candidate = config_dir / p
    if repo_candidate.exists() or not config_candidate.exists():
        return repo_candidate
    return config_candidate


def image_files(root: Path) -> List[Path]:
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob('*') if p.is_file() and p.name.endswith(IMG_EXTENSIONS))


def read_list(path: Path) -> List[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def inspect_folder_mode(conf: Dict[str, Any], repo_root: Path, config_dir: Path) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    root = resolve_path(conf.get('data_root', ''), repo_root, config_dir)
    splits = []
    for split in FOLDER_SPLITS:
        p = root / split
        files = image_files(p)
        row = {'split': split, 'path': str(p), 'exists': p.is_dir(), 'image_count': len(files)}
        if files[:3]:
            row['examples'] = [str(x.relative_to(p)) for x in files[:3]]
        splits.append(row)
        if not p.is_dir():
            errors.append(f'missing split directory: {p}')
        elif not files:
            errors.append(f'split contains no supported images: {p}')
    display_size = conf.get('display_size')
    if isinstance(display_size, int):
        for row in splits:
            if row['exists'] and row['image_count'] < display_size:
                errors.append(f"display_size={display_size} exceeds {row['split']} image_count={row['image_count']}")
    else:
        warnings.append('display_size is missing or not an integer; cannot compare against split counts')
    return {'mode': 'folder', 'data_root': str(root), 'splits': splits, 'errors': errors, 'warnings': warnings}


def inspect_list_mode(conf: Dict[str, Any], repo_root: Path, config_dir: Path) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    splits = []
    for split, folder_key, list_key in LIST_PAIRS:
        if folder_key not in conf or list_key not in conf:
            errors.append(f'missing list-mode keys for {split}: {folder_key}, {list_key}')
            continue
        folder = resolve_path(conf[folder_key], repo_root, config_dir)
        list_path = resolve_path(conf[list_key], repo_root, config_dir)
        entries = read_list(list_path)
        missing = []
        label_like = []
        for entry in entries:
            if len(entry.split()) > 1:
                label_like.append(entry)
            if not (folder / entry).is_file():
                missing.append(entry)
        row = {
            'split': split,
            'folder_key': folder_key,
            'folder': str(folder),
            'folder_exists': folder.is_dir(),
            'list_key': list_key,
            'list_file': str(list_path),
            'list_exists': list_path.is_file(),
            'entry_count': len(entries),
            'missing_entry_count': len(missing),
            'missing_examples': missing[:5],
            'label_like_examples': label_like[:5],
        }
        splits.append(row)
        if not folder.is_dir():
            errors.append(f'{folder_key} is not a directory: {folder}')
        if not list_path.is_file():
            errors.append(f'{list_key} is not a file: {list_path}')
        if not entries:
            errors.append(f'{list_key} has no entries: {list_path}')
        if missing:
            errors.append(f'{split}: {len(missing)} list entries do not resolve under {folder}; first examples: {missing[:3]}')
        if label_like:
            warnings.append(f'{split}: list entries contain whitespace; MUNIT does not split labels and will treat the whole line as a path')
    display_size = conf.get('display_size')
    if isinstance(display_size, int):
        for row in splits:
            if row['entry_count'] < display_size:
                errors.append(f"display_size={display_size} exceeds {row['split']} entry_count={row['entry_count']}")
    else:
        warnings.append('display_size is missing or not an integer; cannot compare against list counts')
    return {'mode': 'list', 'splits': splits, 'errors': errors, 'warnings': warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description='Inspect MUNIT dataset folder/list layout without imports, downloads, or CUDA.')
    parser.add_argument('--config', required=True, help='Path to the MUNIT YAML config.')
    parser.add_argument('--repo-root', default='.', help="User's MUNIT checkout root for resolving repo-relative paths.")
    parser.add_argument('--json', action='store_true', help='Emit JSON report.')
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    repo_root = Path(args.repo_root)
    if not repo_root.is_absolute():
        repo_root = Path.cwd() / repo_root
    if not config_path.exists():
        print(f'FAIL config not found: {config_path}', file=sys.stderr)
        return 2

    conf, parser_name = load_config(config_path)
    if 'data_root' in conf:
        report = inspect_folder_mode(conf, repo_root, config_path.parent)
    else:
        report = inspect_list_mode(conf, repo_root, config_path.parent)
    report['config'] = str(config_path)
    report['parser'] = parser_name

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"MUNIT dataset inspection: {config_path}")
        print(f"parser: {parser_name}")
        print(f"mode: {report['mode']}")
        for row in report.get('splits', []):
            if report['mode'] == 'folder':
                print(f"{row['split']}: exists={row['exists']} images={row['image_count']} path={row['path']}")
            else:
                print(f"{row['split']}: folder_exists={row['folder_exists']} list_exists={row['list_exists']} entries={row['entry_count']} missing={row['missing_entry_count']}")
        for item in report['warnings']:
            print(f'WARN {item}')
        for item in report['errors']:
            print(f'FAIL {item}')
        if not report['errors']:
            print('OK dataset layout checks passed')
    return 2 if report['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
