#!/usr/bin/env python3
"""Quick LaneNet environment and repo-root preflight.

This helper is safe to run. It checks that the repository root is valid,
imports the key LaneNet modules, and reports TensorFlow / GPU visibility.
Use --require-cuda when you want the check to fail if CUDA is not usable.
"""

import argparse
import json
import os
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description='Check that a LaneNet checkout and TensorFlow runtime are ready.'
    )
    parser.add_argument('--repo_root', default=None, help='LaneNet repository root; auto-detected from the current working directory if omitted.')
    parser.add_argument('--data_dir', default=None, help='Optional prepared dataset root to validate.')
    parser.add_argument('--require-cuda', action='store_true', help='Fail if TensorFlow cannot see a CUDA device.')
    parser.add_argument('--strict-data', action='store_true', help='Require gt_image/, gt_binary_image/, gt_instance_image/, and split files when validating data_dir.')
    parser.add_argument('--print-json', action='store_true', help='Emit a JSON summary on stdout.')
    return parser.parse_args()


def discover_repo_root(explicit_root=None):
    if explicit_root:
        root = Path(explicit_root).expanduser().resolve()
        if not (root / 'config' / 'tusimple_lanenet.yaml').is_file():
            raise SystemExit('Missing config/tusimple_lanenet.yaml under resolved repo root: {}'.format(root))
        return root

    start = Path.cwd().resolve()
    for candidate in [start] + list(start.parents):
        if (
            (candidate / 'config' / 'tusimple_lanenet.yaml').is_file()
            and (candidate / 'lanenet_model').is_dir()
            and (candidate / 'trainner').is_dir()
        ):
            return candidate
    raise SystemExit('Could not auto-detect the repository root from the current working directory. Pass --repo_root explicitly.')


def bootstrap_repo(repo_root):
    os.chdir(str(repo_root))
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


def resolve_path(repo_root, value):
    if value is None:
        return None
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (repo_root / path).resolve()


def looks_like_placeholder(text):
    if text is None:
        return False
    text = str(text)
    return 'ROOT_PATH' in text or 'REPO_ROOT_PATH' in text


def tf_backend_summary(tf):
    built_with_cuda = None
    gpu_name = ''
    gpu_devices = []
    try:
        built_with_cuda = tf.test.is_built_with_cuda()
    except Exception:
        pass
    try:
        gpu_name = tf.test.gpu_device_name()
    except Exception:
        try:
            gpu_name = tf.config.list_physical_devices('GPU')[0].name
        except Exception:
            gpu_name = ''
    try:
        gpu_devices = [getattr(dev, 'name', str(dev)) for dev in tf.config.list_physical_devices('GPU')]
    except Exception:
        pass
    if not gpu_devices and gpu_name:
        gpu_devices = [gpu_name]
    return built_with_cuda, gpu_name, gpu_devices


def validate_data_root(data_dir, strict=False):
    if data_dir is None:
        return {'validated': False, 'reason': 'no data_dir provided'}

    required_dirs = [data_dir / 'gt_image', data_dir / 'gt_binary_image', data_dir / 'gt_instance_image']
    split_files = [data_dir / 'train.txt', data_dir / 'val.txt', data_dir / 'test.txt']
    result = {
        'validated': True,
        'data_dir': str(data_dir),
        'required_dirs': [str(path) for path in required_dirs],
        'split_files': [str(path) for path in split_files],
        'missing_dirs': [str(path) for path in required_dirs if not path.is_dir()],
        'missing_split_files': [str(path) for path in split_files if not path.is_file()],
    }
    if strict:
        if result['missing_dirs']:
            raise SystemExit('Prepared dataset layout is incomplete under {}: {}'.format(data_dir, ', '.join(result['missing_dirs'])))
        if result['missing_split_files']:
            raise SystemExit('Strict data validation requires train.txt, val.txt, and test.txt under {}'.format(data_dir))
        for list_path in split_files:
            with list_path.open('r', encoding='utf-8') as handle:
                for line_no, line in enumerate(handle, start=1):
                    if looks_like_placeholder(line):
                        raise SystemExit('{}:{} still contains ROOT_PATH/REPO_ROOT_PATH placeholders'.format(list_path, line_no))
    return result


def main():
    args = parse_args()
    repo_root = discover_repo_root(args.repo_root)
    bootstrap_repo(repo_root)

    from local_utils.config_utils import parse_config_utils

    cfg = parse_config_utils.lanenet_cfg
    data_dir = resolve_path(repo_root, args.data_dir)
    if data_dir is None and not looks_like_placeholder(cfg.DATASET.DATA_DIR):
        data_dir = resolve_path(repo_root, cfg.DATASET.DATA_DIR)

    import tensorflow as tf
    from lanenet_model import lanenet  # noqa: F401
    from lanenet_model import lanenet_postprocess  # noqa: F401
    from data_provider import lanenet_data_feed_pipline  # noqa: F401
    from trainner import tusimple_lanenet_single_gpu_trainner  # noqa: F401
    from trainner import tusimple_lanenet_multi_gpu_trainner  # noqa: F401

    built_with_cuda, gpu_name, gpu_devices = tf_backend_summary(tf)
    if args.require_cuda and not (built_with_cuda and gpu_name):
        raise SystemExit('TensorFlow CUDA backend is not available in this runtime.')

    data_summary = validate_data_root(data_dir, strict=args.strict_data)

    summary = {
        'repo_root': str(repo_root),
        'config_path': str(repo_root / 'config' / 'tusimple_lanenet.yaml'),
        'tensorflow_version': getattr(tf, '__version__', 'unknown'),
        'built_with_cuda': built_with_cuda,
        'gpu_device_name': gpu_name,
        'gpu_devices': gpu_devices,
        'data_summary': data_summary,
        'front_end': cfg.MODEL.FRONT_END,
        'train_batch_size': cfg.TRAIN.BATCH_SIZE,
        'val_batch_size': cfg.TRAIN.VAL_BATCH_SIZE,
        'postprocess': {
            'dbscan_eps': cfg.POSTPROCESS.DBSCAN_EPS,
            'dbscan_min_samples': cfg.POSTPROCESS.DBSCAN_MIN_SAMPLES,
        },
    }

    print('LaneNet environment check passed')
    print('Repo root: {}'.format(summary['repo_root']))
    print('TensorFlow version: {}'.format(summary['tensorflow_version']))
    print('Built with CUDA: {}'.format(summary['built_with_cuda']))
    print('GPU device name: {}'.format(summary['gpu_device_name']))
    print('GPU devices: {}'.format(', '.join(summary['gpu_devices']) if summary['gpu_devices'] else 'none'))
    if data_dir is not None:
        print('Data root: {}'.format(data_dir))
        if data_summary.get('missing_dirs'):
            print('Missing data dirs: {}'.format(', '.join(data_summary['missing_dirs'])))
        if data_summary.get('missing_split_files'):
            print('Missing split files: {}'.format(', '.join(data_summary['missing_split_files'])))
    print('Front end: {}'.format(summary['front_end']))
    print('Train batch size: {}'.format(summary['train_batch_size']))
    print('Val batch size: {}'.format(summary['val_batch_size']))

    if args.print_json:
        print(json.dumps(summary, indent=2, sort_keys=True))

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
