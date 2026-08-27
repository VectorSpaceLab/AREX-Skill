#!/usr/bin/env python3
"""Preflight the media inputs for a Luminoth prediction job.

This helper is safe: it only inspects paths and reports what Luminoth's
prediction CLI is likely to do with them. It does not run inference or mutate
any files.

Examples:
  python scripts/check_prediction_inputs.py ./image.jpg
  python scripts/check_prediction_inputs.py ./media --save-media-to ./preds --output ./preds/objects.json
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

IMAGE_FORMATS = {'jpg', 'jpeg', 'png'}
VIDEO_FORMATS = {'mov', 'mp4', 'avi'}


def get_file_type(filename: str):
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if extension in IMAGE_FORMATS:
        return 'image'
    if extension in VIDEO_FORMATS:
        return 'video'
    return None


def resolve_files(path_or_dir):
    files = []
    ignored = []
    missing = []

    for entry in path_or_dir:
        if os.path.isdir(entry):
            for name in sorted(os.listdir(entry)):
                file_type = get_file_type(name)
                full_path = os.path.join(entry, name)
                if file_type in {'image', 'video'}:
                    files.append(full_path)
                elif os.path.isfile(full_path):
                    ignored.append(full_path)
        else:
            file_type = get_file_type(entry)
            if file_type in {'image', 'video'}:
                if os.path.exists(entry):
                    files.append(entry)
                else:
                    missing.append(entry)
            elif os.path.exists(entry):
                ignored.append(entry)
            else:
                missing.append(entry)

    return files, ignored, missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Preflight Luminoth prediction inputs.'
    )
    parser.add_argument('path_or_dir', nargs='+', help='Image, video, or directory to inspect.')
    parser.add_argument('--output', default='-', help='Prediction JSON output path or - for stdout.')
    parser.add_argument('--save-media-to', help='Directory that would receive annotated media.')
    parser.add_argument('--only-class', action='append', default=[], help='Class whitelist passed to prediction.')
    parser.add_argument('--ignore-class', action='append', default=[], help='Class blacklist passed to prediction.')
    args = parser.parse_args()

    if args.only_class and args.ignore_class:
        print('Only one of --only-class or --ignore-class may be specified.', file=sys.stderr)
        return 2

    files, ignored, missing = resolve_files(args.path_or_dir)

    if missing:
        for entry in missing:
            print(f'Input {entry} not found, skipping.', file=sys.stderr)

    if ignored:
        print('ignored non-media inputs: ' + ', '.join(ignored))

    if not files:
        print(
            'No files to predict found. Accepted formats are: jpg, jpeg, png, mov, mp4, avi.',
            file=sys.stderr,
        )
        return 1

    images = [path for path in files if get_file_type(path) == 'image']
    videos = [path for path in files if get_file_type(path) == 'video']

    print(f'found {len(files)} media files: {len(images)} image(s), {len(videos)} video(s)')
    if args.output != '-':
        print(f'prediction JSON output: {args.output}')
    if args.save_media_to:
        print(f'annotated media directory: {args.save_media_to}')

    if videos:
        ffmpeg = shutil.which('ffmpeg')
        if not ffmpeg and args.save_media_to:
            print(
                'FFmpeg is required to save annotated video output, but it was not found on PATH.',
                file=sys.stderr,
            )
            return 1
        if not args.save_media_to:
            print(
                'video inputs were found; Luminoth will not emit JSON for them unless you also save media.',
            )

    if args.only_class:
        print('only-class filters: ' + ', '.join(args.only_class))
    if args.ignore_class:
        print('ignore-class filters: ' + ', '.join(args.ignore_class))

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
