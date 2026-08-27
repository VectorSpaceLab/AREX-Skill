#!/usr/bin/env python3
"""Inspect Libra image dataset layout without training a model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[5]
for candidate in (SCRIPT_DIR, REPO_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif'}
IGNORED_DIRS = {'proc_training_set', 'proc_testing_set', 'generated_images', '__pycache__'}


def image_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob('*') if item.is_file() and item.suffix.lower() in IMAGE_EXTS)


def class_dirs(path: Path) -> List[Dict[str, object]]:
    if not path.exists() or not path.is_dir():
        return []
    rows = []
    for child in sorted(path.iterdir()):
        if child.is_dir() and child.name not in IGNORED_DIRS:
            count = image_count(child)
            if count:
                rows.append({'name': child.name, 'image_count': count})
    return rows


def detect_layout(data_path: Path) -> Dict[str, object]:
    data_path = data_path.resolve()
    train = data_path / 'training_set'
    test = data_path / 'testing_set'
    proc_train = data_path / 'proc_training_set'
    proc_test = data_path / 'proc_testing_set'

    report: Dict[str, object] = {
        'data_path': str(data_path),
        'has_training_set': train.is_dir(),
        'has_testing_set': test.is_dir(),
        'has_proc_training_set': proc_train.is_dir(),
        'has_proc_testing_set': proc_test.is_dir(),
        'root_class_dirs': class_dirs(data_path),
        'training_class_dirs': class_dirs(train),
        'testing_class_dirs': class_dirs(test),
        'detected_read_mode': 'unknown',
        'notes': [],
    }

    if train.is_dir() and test.is_dir():
        report['detected_read_mode'] = 'setwise'
        if len(report['training_class_dirs']) != len(report['testing_class_dirs']):
            report['notes'].append('training_set and testing_set have different class counts')
    elif proc_train.is_dir() and proc_test.is_dir():
        report['detected_read_mode'] = 'already_processed'
    elif len(report['root_class_dirs']) >= 2:
        report['detected_read_mode'] = 'classwise'
    else:
        report['notes'].append('No setwise/classwise image layout was detected')
    return report


def resolve_image_value(value: object, data_path: Path) -> Optional[str]:
    if not isinstance(value, str) or not value:
        return None
    raw = Path(value)
    candidates = [raw]
    if not raw.is_absolute():
        candidates.append(data_path / raw)
        for child in data_path.iterdir() if data_path.exists() else []:
            if child.is_dir():
                candidates.append(child / raw)
    for candidate in candidates:
        if candidate.exists() and candidate.suffix.lower() in IMAGE_EXTS:
            return str(candidate)
    return None


def inspect_csv(csv_path: Path, data_path: Path, image_column: Optional[str] = None) -> Dict[str, object]:
    import pandas as pd

    df = pd.read_csv(csv_path)
    report: Dict[str, object] = {
        'csv_path': str(csv_path.resolve()),
        'columns': list(df.columns),
        'row_count': int(df.shape[0]),
        'detected_read_mode': 'csvwise',
        'image_column': image_column,
        'label_candidates': [],
        'notes': [],
    }

    if image_column and image_column not in df.columns:
        report['notes'].append(f'image_column {image_column!r} is not present in CSV')
        return report

    if not image_column:
        for col in df.columns:
            hits = 0
            samples = df[col].dropna().astype(object).head(20).tolist()
            for value in samples:
                if resolve_image_value(value, data_path):
                    hits += 1
            if hits:
                image_column = col
                break
        report['image_column'] = image_column

    if not image_column:
        report['notes'].append('No image path column was detected; pass --image-column explicitly')

    for col in df.columns:
        if col != image_column:
            uniques = df[col].dropna().unique()
            if 1 < len(uniques) <= max(20, int(len(df) * 0.75)):
                report['label_candidates'].append(col)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description='Inspect image dataset layout for Libra convolutional_query.')
    parser.add_argument('--data-path', default='.', help='Image data root or directory containing image subfolders.')
    parser.add_argument('--csv', help='Optional CSV labels file for csvwise workflows.')
    parser.add_argument('--image-column', help='Known image/path column in the CSV.')
    parser.add_argument('--json', action='store_true', help='Emit JSON report.')
    args = parser.parse_args()

    data_path = Path(args.data_path)
    report = detect_layout(data_path)
    if args.csv:
        report['csvwise'] = inspect_csv(Path(args.csv), data_path, args.image_column)
        report['suggested_read_mode'] = 'csvwise'
    else:
        report['suggested_read_mode'] = report['detected_read_mode']

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"data_path: {report['data_path']}")
        print(f"detected_read_mode: {report['detected_read_mode']}")
        print(f"suggested_read_mode: {report['suggested_read_mode']}")
        if report.get('root_class_dirs'):
            print('root classes: ' + ', '.join(f"{c['name']}({c['image_count']})" for c in report['root_class_dirs']))
        if report.get('training_class_dirs'):
            print('training classes: ' + ', '.join(f"{c['name']}({c['image_count']})" for c in report['training_class_dirs']))
        if report.get('testing_class_dirs'):
            print('testing classes: ' + ', '.join(f"{c['name']}({c['image_count']})" for c in report['testing_class_dirs']))
        for note in report.get('notes', []):
            print(f'note: {note}')
        if args.csv:
            csv_report = report['csvwise']
            print(f"csv image_column: {csv_report.get('image_column')}")
            print('csv label_candidates: ' + ', '.join(csv_report.get('label_candidates', [])))
            for note in csv_report.get('notes', []):
                print(f'csv note: {note}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
