#!/usr/bin/env python3
"""Build a sorted recursive file list for EdgeConnect data preparation.

The script scans a dataset directory recursively, collects matching image files,
and writes their resolved paths to a text flist. It does not import the repo
package and it fails with a non-zero exit status when the input path is invalid
or when no matching files are found.
"""

import argparse
from pathlib import Path
import sys

DEFAULT_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tif', '.tiff']


def normalize_extensions(values):
    if not values:
        values = DEFAULT_EXTENSIONS

    normalized = []
    seen = set()
    for value in values:
        for token in str(value).split(','):
            ext = token.strip().lower()
            if not ext:
                continue
            if not ext.startswith('.'):
                ext = '.' + ext
            if ext not in seen:
                seen.add(ext)
                normalized.append(ext)

    return normalized


def collect_images(root, extensions):
    if not root.exists():
        raise FileNotFoundError('input path does not exist: %s' % root)
    if not root.is_dir():
        raise NotADirectoryError('input path must be a directory: %s' % root)

    ext_set = {ext.lower() for ext in extensions}
    files = []
    for path in root.rglob('*'):
        if path.is_file() and path.suffix.lower() in ext_set:
            files.append(path.resolve())

    files = sorted(set(files), key=lambda item: str(item))
    if not files:
        raise ValueError('no matching image files found under: %s' % root)
    return files


def write_flist(paths, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(str(path) for path in paths) + '\n', encoding='utf-8')


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description='Build a recursive EdgeConnect flist from an image directory.'
    )
    parser.add_argument('--path', required=True, help='dataset root directory to scan recursively')
    parser.add_argument('--output', required=True, help='output flist file path')
    parser.add_argument(
        '--extensions',
        nargs='*',
        help='optional image extensions, space- or comma-separated; defaults to common image formats'
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    root = Path(args.path).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    extensions = normalize_extensions(args.extensions)

    try:
        images = collect_images(root, extensions)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        print('error: %s' % exc, file=sys.stderr)
        return 1

    try:
        write_flist(images, output)
    except OSError as exc:
        print('error: could not write %s: %s' % (output, exc), file=sys.stderr)
        return 1

    print('wrote %d paths to %s' % (len(images), output))
    return 0


if __name__ == '__main__':
    sys.exit(main())
