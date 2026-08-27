#!/usr/bin/env python3
"""Create and inspect a tiny classwise CNN layout without training."""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import sys
import tempfile

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[5]
for candidate in (SCRIPT_DIR, REPO_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from inspect_image_dataset import detect_layout

ONE_PIXEL_PNG = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII='
)


def write_fixture(root: Path) -> None:
    for class_name in ['class_a', 'class_b']:
        class_dir = root / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        for idx in range(2):
            (class_dir / f'{class_name}_{idx}.png').write_bytes(ONE_PIXEL_PNG)


def main() -> int:
    parser = argparse.ArgumentParser(description='Smoke-check image layout classification for Libra CNN workflows.')
    parser.add_argument('--keep', help='Directory where the synthetic fixture should be written and kept.')
    parser.add_argument('--json', action='store_true', help='Emit JSON report.')
    args = parser.parse_args()

    if args.keep:
        data_root = Path(args.keep)
        data_root.mkdir(parents=True, exist_ok=True)
        write_fixture(data_root)
        report = detect_layout(data_root)
    else:
        with tempfile.TemporaryDirectory(prefix='libra-cnn-layout-') as tmpdir:
            data_root = Path(tmpdir)
            write_fixture(data_root)
            report = detect_layout(data_root)
            report['fixture_removed_after_run'] = True
            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print(f"synthetic_layout: {report['detected_read_mode']}")
                print('recommended_call: c.convolutional_query("predict class", read_mode="classwise", epochs=1)')
            return 0

    report['fixture_removed_after_run'] = False
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"synthetic_layout: {report['detected_read_mode']}")
        print(f"fixture_path: {data_root}")
        print('recommended_call: c.convolutional_query("predict class", read_mode="classwise", epochs=1)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
