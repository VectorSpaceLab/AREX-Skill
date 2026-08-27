#!/usr/bin/env python3
"""Smoke-test the public Luminoth install.

This helper is safe to run from any directory. It imports the public package,
prints the main versions and route names, and can optionally parse a config file.
It does not download data, mutate checkpoints, or start training.

Examples:
  python scripts/check_luminoth_install.py
  python scripts/check_luminoth_install.py --sample-config examples/sample_config.yml
  python scripts/check_luminoth_install.py --repo-root /path/to/checkout
"""

import argparse
import inspect
import os
import sys
from pathlib import Path


def add_repo_root(repo_root: str) -> None:
    if not repo_root:
        return
    root = str(Path(repo_root).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)


def get_attr_path(obj, dotted):
    current = obj
    for part in dotted.split('.'):
        if isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
        else:
            if not hasattr(current, part):
                return None
            current = getattr(current, part)
    return current


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Check that Luminoth and its main public APIs import.'
    )
    parser.add_argument(
        '--repo-root',
        help='Optional checkout root to add to sys.path before importing.',
    )
    parser.add_argument(
        '--sample-config',
        help='Optional config file to resolve with luminoth.utils.config.get_config.',
    )
    args = parser.parse_args()

    add_repo_root(args.repo_root)

    try:
        import tensorflow as tf
        import luminoth
        from luminoth.cli import cli
        from luminoth.datasets.datasets import DATASETS
        from luminoth.io import read_image
        from luminoth.models.models import MODELS
        from luminoth.tasks import Detector
        from luminoth.tools.dataset.readers import READERS
        from luminoth.utils.config import get_config
        from luminoth.vis import vis_objects
    except ImportError as exc:
        print(f'Import check failed: {exc}', file=sys.stderr)
        print(
            'Missing a required dependency? Luminoth needs TensorFlow 1.x and '
            'the base runtime dependencies before its public APIs import.',
            file=sys.stderr,
        )
        return 1
    except Exception as exc:  # pragma: no cover - defensive smoke helper.
        print(f'Import check failed: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1

    print(f'luminoth {luminoth.__version__}')
    print(f'tensorflow {tf.__version__}')
    print('cli commands: ' + ', '.join(sorted(cli.commands.keys())))
    print('models: ' + ', '.join(sorted(MODELS.keys())))
    print('datasets: ' + ', '.join(sorted(DATASETS.keys())))
    print('readers: ' + ', '.join(sorted(READERS.keys())))
    print(f'Detector signature: {inspect.signature(Detector)}')
    print(f'read_image signature: {inspect.signature(read_image)}')
    print(f'vis_objects signature: {inspect.signature(vis_objects)}')

    if args.sample_config:
        config = get_config(args.sample_config)
        print(
            'resolved config: '
            f'model.type={get_attr_path(config, "model.type")}, '
            f'dataset.type={get_attr_path(config, "dataset.type")}, '
            f'dataset.dir={get_attr_path(config, "dataset.dir")}, '
            f'train.job_dir={get_attr_path(config, "train.job_dir")}, '
            f'train.run_name={get_attr_path(config, "train.run_name")} '
        )

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
