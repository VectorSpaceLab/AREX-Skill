#!/usr/bin/env python3
"""Print safe Raster Vision PyTorch example run commands.

This helper only renders command strings; it never executes them.
"""

from __future__ import annotations

import argparse
import shlex
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ExampleSpec:
    key: str
    module: str
    raw_uri_local: str
    processed_uri_local: str | None
    root_uri_local: str
    raw_uri_remote: str
    processed_uri_remote: str | None
    root_uri_remote: str
    extra_args: tuple[tuple[str, str], ...] = ()


EXAMPLE_SPECS: tuple[ExampleSpec, ...] = (
    ExampleSpec(
        key='spacenet-rio-cc',
        module='rastervision.pytorch_backend.examples.chip_classification.spacenet_rio',
        raw_uri_local='/opt/data/raw-data/spacenet-dataset',
        processed_uri_local='/opt/data/examples/0.31.0/processed-data/spacenet-rio-cc',
        root_uri_local='/opt/data/examples/0.31.0/output/spacenet-rio-cc',
        raw_uri_remote='s3://spacenet-dataset/',
        processed_uri_remote='s3://raster-vision/examples/0.31.0/processed-data/spacenet-rio-cc',
        root_uri_remote='s3://raster-vision/examples/0.31.0/output/spacenet-rio-cc',
    ),
    ExampleSpec(
        key='isprs-potsdam-ss',
        module='rastervision.pytorch_backend.examples.semantic_segmentation.isprs_potsdam',
        raw_uri_local='/opt/data/raw-data/isprs-potsdam/',
        processed_uri_local='/opt/data/examples/0.31.0/processed-data/isprs-potsdam-ss',
        root_uri_local='/opt/data/examples/0.31.0/output/isprs-potsdam-ss/',
        raw_uri_remote='s3://raster-vision-raw-data/isprs-potsdam',
        processed_uri_remote='s3://raster-vision/examples/0.31.0/processed-data/isprs-potsdam-ss',
        root_uri_remote='s3://raster-vision/examples/0.31.0/output/isprs-potsdam-ss',
    ),
    ExampleSpec(
        key='spacenet-vegas-buildings-ss',
        module='rastervision.pytorch_backend.examples.semantic_segmentation.spacenet_vegas',
        raw_uri_local='s3://spacenet-dataset/',
        processed_uri_local=None,
        root_uri_local='/opt/data/examples/0.31.0/output/spacenet-vegas-buildings-ss',
        raw_uri_remote='s3://spacenet-dataset/',
        processed_uri_remote=None,
        root_uri_remote='s3://raster-vision/examples/0.31.0/output/spacenet-vegas-buildings-ss',
        extra_args=(('target', 'buildings'),),
    ),
    ExampleSpec(
        key='spacenet-vegas-roads-ss',
        module='rastervision.pytorch_backend.examples.semantic_segmentation.spacenet_vegas',
        raw_uri_local='s3://spacenet-dataset/',
        processed_uri_local=None,
        root_uri_local='/opt/data/examples/0.31.0/output/spacenet-vegas-roads-ss',
        raw_uri_remote='s3://spacenet-dataset/',
        processed_uri_remote=None,
        root_uri_remote='s3://raster-vision/examples/0.31.0/output/spacenet-vegas-roads-ss',
        extra_args=(('target', 'roads'),),
    ),
    ExampleSpec(
        key='cowc-potsdam-od',
        module='rastervision.pytorch_backend.examples.object_detection.cowc_potsdam',
        raw_uri_local='/opt/data/raw-data/isprs-potsdam',
        processed_uri_local='/opt/data/examples/0.31.0/processed-data/cowc-potsdam-od',
        root_uri_local='/opt/data/examples/0.31.0/output/cowc-potsdam-od',
        raw_uri_remote='s3://raster-vision-raw-data/isprs-potsdam',
        processed_uri_remote='s3://raster-vision/examples/0.31.0/processed-data/cowc-potsdam-od',
        root_uri_remote='s3://raster-vision/examples/0.31.0/output/cowc-potsdam-od',
    ),
    ExampleSpec(
        key='xview-od',
        module='rastervision.pytorch_backend.examples.object_detection.xview',
        raw_uri_local='s3://raster-vision-xview-example/raw-data',
        processed_uri_local='/opt/data/examples/0.31.0/processed-data/xview-od',
        root_uri_local='/opt/data/examples/0.31.0/output/xview-od',
        raw_uri_remote='s3://raster-vision-xview-example/raw-data',
        processed_uri_remote='s3://raster-vision/examples/0.31.0/processed-data/xview-od',
        root_uri_remote='s3://raster-vision/examples/0.31.0/output/xview-od',
    ),
)

EXAMPLE_MAP = {spec.key: spec for spec in EXAMPLE_SPECS}
DEFAULT_KEYS = [spec.key for spec in EXAMPLE_SPECS]


def build_command(spec: ExampleSpec, mode: str, test: bool) -> str:
    if mode == 'remote':
        runner = 'batch'
        raw_uri = spec.raw_uri_remote
        processed_uri = spec.processed_uri_remote
        root_uri = spec.root_uri_remote
    else:
        runner = 'inprocess'
        raw_uri = spec.raw_uri_local
        processed_uri = spec.processed_uri_local
        root_uri = spec.root_uri_local

    parts: list[str] = ['rastervision', 'run', runner, spec.module]
    parts += ['-a', 'raw_uri', raw_uri]
    if processed_uri is not None:
        parts += ['-a', 'processed_uri', processed_uri]
    parts += ['-a', 'root_uri', root_uri]
    parts += ['-a', 'test', 'True' if test else 'False']
    for key, value in spec.extra_args:
        parts += ['-a', key, value]
    if mode == 'remote':
        parts += ['--splits', '3']
    parts += ['--pipeline-run-name', spec.key]
    return shlex.join(parts)


def selected_modes(args: argparse.Namespace) -> list[str]:
    if args.local or args.remote:
        modes: list[str] = []
        if args.local:
            modes.append('local')
        if args.remote:
            modes.append('remote')
        return modes
    return ['local', 'remote']


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='list_example_commands.py',
        description='Print safe Raster Vision PyTorch example run commands.',
        epilog=(
            'Examples:\n'
            '  python scripts/list_example_commands.py --help\n'
            '  python scripts/list_example_commands.py spacenet-rio-cc --local\n'
            '  python scripts/list_example_commands.py isprs-potsdam-ss --remote --test\n'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'keys',
        nargs='*',
        help='Example keys to print. Omit to print every known key.',
    )
    parser.add_argument(
        '--local',
        action='store_true',
        help='Print only the local inprocess command.',
    )
    parser.add_argument(
        '--remote',
        action='store_true',
        help='Print only the remote batch command.',
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Render the commands with -a test True.',
    )
    return parser.parse_args(argv)


def validate_keys(keys: Iterable[str]) -> list[str]:
    keys = list(keys)
    invalid = [key for key in keys if key not in EXAMPLE_MAP]
    if invalid:
        valid = ', '.join(DEFAULT_KEYS)
        raise SystemExit(f'Unknown example key(s): {", ".join(invalid)}. Valid keys: {valid}')
    return keys


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    keys = validate_keys(args.keys) if args.keys else DEFAULT_KEYS
    modes = selected_modes(args)

    for key in keys:
        spec = EXAMPLE_MAP[key]
        for mode in modes:
            print(f'# {key} [{mode}{", test=True" if args.test else ""}]')
            print(build_command(spec, mode, args.test))
            print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
