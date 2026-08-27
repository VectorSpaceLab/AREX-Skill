#!/usr/bin/env python3
"""Preflight a Luminoth object-detection dataset layout.

This helper is safe: it does not write files, convert data, or download
anything. It just instantiates the selected reader and prints a concise summary
of the layout it sees.

Examples:
  python scripts/validate_dataset_layout.py --type pascal --data-dir ./data --split train
  python scripts/validate_dataset_layout.py --type csv --data-dir ./data --split train --override headers=false --override columns=image_id,xmin,ymin,xmax,ymax,label
"""

import argparse
import os
import sys
from pathlib import Path


def add_repo_root(repo_root: str) -> None:
    if not repo_root:
        return
    root = str(Path(repo_root).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)


def parse_override(items):
    result = {}
    for item in items or []:
        if '=' not in item:
            raise ValueError(f'invalid override {item!r}; expected key=value')
        key, value = item.split('=', 1)
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        elif value.lower() == 'none':
            value = None
        else:
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass
        result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Validate a source dataset layout for Luminoth readers.'
    )
    parser.add_argument('--repo-root', help='Optional checkout root to add to sys.path before importing.')
    parser.add_argument('--type', required=True, dest='reader_type', help='Reader type such as pascal, csv, coco, flat, imagenet, openimages, or taggerine.')
    parser.add_argument('--data-dir', required=True, help='Dataset root directory to inspect.')
    parser.add_argument('--split', action='append', required=True, help='Split to inspect. Pass multiple times for multiple splits.')
    parser.add_argument('--only-classes', help='Comma-separated class whitelist to pass through to the reader.')
    parser.add_argument('--only-images', help='Comma-separated image-id whitelist to pass through to the reader.')
    parser.add_argument('--limit-examples', type=int, help='Optional record limit for the reader.')
    parser.add_argument('--class-examples', type=int, help='Optional approximate per-class limit for the reader.')
    parser.add_argument('--override', action='append', default=[], help='Reader-specific key=value override passed to the constructor.')
    args = parser.parse_args()

    add_repo_root(args.repo_root)

    try:
        from luminoth.tools.dataset.readers import get_reader, READERS
    except ImportError as exc:
        print(f'Import failed: {exc}', file=sys.stderr)
        print('Install the Luminoth package and its base dependencies before validating layouts.', file=sys.stderr)
        return 1

    if args.reader_type.lower() not in READERS:
        print('Unknown reader type: {}'.format(args.reader_type), file=sys.stderr)
        print('Known readers: {}'.format(', '.join(sorted(READERS.keys()))), file=sys.stderr)
        return 2

    try:
        reader_cls = get_reader(args.reader_type)
        reader_kwargs = parse_override(args.override)
        for split in args.split:
            reader = reader_cls(
                args.data_dir,
                split,
                only_classes=args.only_classes,
                only_images=args.only_images,
                limit_examples=args.limit_examples,
                class_examples=args.class_examples,
                **reader_kwargs,
            )
            classes = reader.classes
            total = reader.total
            print(
                f'split={split} reader={args.reader_type} total={total} classes={len(classes)}',
            )
            print('classes: ' + ', '.join(map(str, classes)))
    except Exception as exc:
        print(f'Layout validation failed: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
