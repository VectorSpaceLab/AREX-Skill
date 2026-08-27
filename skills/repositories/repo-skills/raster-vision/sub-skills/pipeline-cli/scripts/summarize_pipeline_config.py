#!/usr/bin/env python3
"""Summarize a Raster Vision pipeline config without running commands."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from typing import Any


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            'Load a Raster Vision config module or JSON file, build the '
            'pipeline, and print the derived pipeline summary without '
            'executing any commands.'
        ))
    parser.add_argument(
        '--config',
        required=True,
        help='Raster Vision config module path, .py file, or .json file.')
    parser.add_argument(
        '--runner',
        default=None,
        help='Runner name to pass into get_config(s).')
    parser.add_argument(
        '--arg',
        dest='args',
        action='append',
        nargs=2,
        metavar=('KEY', 'VALUE'),
        default=[],
        help='Repeatable config argument passed to get_config(s).')
    parser.add_argument(
        '--tmp-dir',
        '--tmpdir',
        dest='tmp_dir',
        default=None,
        help='Root directory for temporary files used while building the pipeline.')
    return parser.parse_args()


def _convert_bool_args(args: dict[str, Any]) -> dict[str, Any]:
    try:
        from rastervision.pipeline.cli import convert_bool_args
    except Exception:  # pragma: no cover - import failure handled by caller
        return args
    return convert_bool_args(args)


def _load_configs(config_path: str, runner: str | None,
                  args: dict[str, Any]) -> list[Any]:
    from rastervision.pipeline.cli import get_configs

    return get_configs(config_path, runner, args)


def _summarize_single_config(cfg: Any, tmp_dir: str) -> dict[str, Any]:
    with redirect_stdout(StringIO()):
        cfg.update()
        if hasattr(cfg, 'recursive_validate_config'):
            cfg.recursive_validate_config()
        pipeline = cfg.build(tmp_dir)

        if not all(
                hasattr(pipeline, attr)
                for attr in ('commands', 'split_commands', 'gpu_commands')):
            raise TypeError(
                'summarize_pipeline_config.py expects an RVPipeline-style '
                'config with commands, split_commands, and gpu_commands.')

        commands = list(pipeline.commands)
        split_commands = list(pipeline.split_commands)
        gpu_commands = list(pipeline.gpu_commands)

    if not hasattr(cfg, 'get_config_uri'):
        raise TypeError(
            'summarize_pipeline_config.py expects a Raster Vision PipelineConfig '
            'with get_config_uri().')

    model_bundle_uri = None
    if hasattr(cfg, 'get_model_bundle_uri'):
        model_bundle_uri = cfg.get_model_bundle_uri()

    return {
        'root_uri': cfg.root_uri,
        'commands': commands,
        'split_commands': split_commands,
        'gpu_commands': gpu_commands,
        'output_uris': {
            'config_uri': cfg.get_config_uri(),
            'analyze_uri': getattr(cfg, 'analyze_uri', None),
            'chip_uri': getattr(cfg, 'chip_uri', None),
            'train_uri': getattr(cfg, 'train_uri', None),
            'predict_uri': getattr(cfg, 'predict_uri', None),
            'eval_uri': getattr(cfg, 'eval_uri', None),
            'bundle_uri': getattr(cfg, 'bundle_uri', None),
            'model_bundle_uri': model_bundle_uri,
        },
    }


def main() -> int:
    ns = _parse_args()
    arg_dict = dict(ns.args)
    arg_dict = _convert_bool_args(arg_dict)

    if ns.tmp_dir is not None:
        os.makedirs(ns.tmp_dir, exist_ok=True)

    cfgs = _load_configs(ns.config, ns.runner, arg_dict)

    tmpdir_kwargs = {'dir': ns.tmp_dir} if ns.tmp_dir is not None else {}
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(**tmpdir_kwargs) as tmp_dir:
        for index, cfg in enumerate(cfgs):
            summary = _summarize_single_config(cfg, tmp_dir)
            summary['index'] = index
            summary['config_type'] = type(cfg).__name__
            results.append(summary)

    json.dump(
        {
            'config': ns.config,
            'runner': ns.runner,
            'results': results,
        },
        sys.stdout,
        indent=2,
        sort_keys=True)
    sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
