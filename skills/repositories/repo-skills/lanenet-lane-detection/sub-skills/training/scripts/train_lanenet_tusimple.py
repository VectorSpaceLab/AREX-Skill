#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LaneNet training wrapper with explicit preflight and opt-in execution.

The wrapper keeps heavy training opt-in via --run, resolves REPO_ROOT_PATH
placeholders, and checks TFRecord size before starting a graph run.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - runtime environment already provides PyYAML.
    yaml = None

PLACEHOLDER = 'REPO_ROOT_PATH'


def parse_args() -> argparse.Namespace:
    """Parse wrapper arguments."""
    parser = argparse.ArgumentParser(
        description='Preflight and optionally run LaneNet training.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--repo_root',
        type=str,
        default=None,
        help='Repository root that contains config/ and lanenet_model/. If omitted, the wrapper auto-detects it.',
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/tusimple_lanenet.yaml',
        help='Config path relative to repo_root or an absolute path.',
    )
    parser.add_argument(
        '--set',
        dest='overrides',
        action='append',
        default=[],
        metavar='KEY=VALUE',
        help='Override a config key before training; repeat as needed.',
    )
    parser.add_argument(
        '--run',
        action='store_true',
        help='Actually launch training after preflight. Without this flag the wrapper only prints the effective config summary.',
    )
    return parser.parse_args()


def discover_repo_root() -> Path:
    """Discover the repository root by walking up from the current working directory."""
    start = Path.cwd().resolve()
    for candidate in [start] + list(start.parents):
        if (
            (candidate / 'config' / 'tusimple_lanenet.yaml').is_file()
            and (candidate / 'lanenet_model').is_dir()
            and (candidate / 'trainner').is_dir()
        ):
            return candidate
    raise SystemExit('Could not auto-detect the repository root from the current working directory. Pass --repo_root explicitly.')


def resolve_repo_root(repo_root_arg: str | None) -> Path:
    """Resolve the repository root from CLI or auto-detection."""
    if repo_root_arg:
        repo_root = Path(repo_root_arg).expanduser().resolve()
    else:
        repo_root = discover_repo_root()
    if not (repo_root / 'config' / 'tusimple_lanenet.yaml').is_file():
        raise SystemExit(f'Missing config/tusimple_lanenet.yaml under resolved repo root: {repo_root}')
    return repo_root


def bootstrap_repo(repo_root: Path) -> None:
    """Change to repo root and add it to sys.path."""
    os.chdir(repo_root)
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


def replace_placeholder(value: Any, repo_root_str: str) -> Any:
    """Recursively replace REPO_ROOT_PATH placeholders inside config values."""
    if isinstance(value, str):
        return value.replace(PLACEHOLDER, repo_root_str)
    if isinstance(value, list):
        return [replace_placeholder(item, repo_root_str) for item in value]
    if isinstance(value, tuple):
        return tuple(replace_placeholder(item, repo_root_str) for item in value)
    if isinstance(value, dict):
        for key, item in list(value.items()):
            value[key] = replace_placeholder(item, repo_root_str)
        return value
    return value


def parse_override_item(item: str, repo_root_str: str) -> tuple[str, Any]:
    """Parse a KEY=VALUE override token."""
    if '=' not in item:
        raise SystemExit(f'Invalid override token: {item!r}. Expected KEY=VALUE.')
    key, raw_value = item.split('=', 1)
    if yaml is not None:
        parsed_value = yaml.safe_load(raw_value)
    else:  # pragma: no cover - the runtime environment provides PyYAML.
        parsed_value = raw_value
    return key, replace_placeholder(parsed_value, repo_root_str)


def load_effective_config(repo_root: Path, config_arg: str, overrides: list[str]):
    """Load config, resolve placeholders, apply overrides, and publish the effective global config."""
    from local_utils.config_utils import parse_config_utils

    config_path = Path(config_arg).expanduser()
    if not config_path.is_absolute():
        config_path = (repo_root / config_path).resolve()
    if not config_path.is_file():
        raise SystemExit(f'Config file not found: {config_path}')

    cfg = parse_config_utils.Config(config_path=str(config_path))
    cfg = replace_placeholder(cfg, str(repo_root))

    if overrides:
        flat_overrides: list[Any] = []
        for item in overrides:
            key, value = parse_override_item(item, str(repo_root))
            flat_overrides.extend([key, value])
        cfg.update_from_list(flat_overrides)
        cfg = replace_placeholder(cfg, str(repo_root))

    parse_config_utils.lanenet_cfg = cfg
    return cfg, parse_config_utils, config_path


def count_tfrecord_examples(tfrecord_path: Path) -> int:
    """Count records in a TFRecord file using TensorFlow's iterator."""
    import tensorflow as tf

    if not tfrecord_path.is_file():
        return 0
    return sum(1 for _ in tf.python_io.tf_record_iterator(str(tfrecord_path)))


def strip_checkpoint_suffix(path: Path) -> Path:
    """Normalize shard or suffix paths to the TensorFlow checkpoint base path."""
    name = path.name
    for suffix in ('.index', '.meta'):
        if name.endswith(suffix):
            return path.with_name(name[:-len(suffix)])
    if '.data-' in name:
        return path.with_name(name.split('.data-', 1)[0])
    return path


def resolve_checkpoint_path(raw_path: str, repo_root: Path):
    """Resolve a checkpoint directory, shard, or base path to a usable TensorFlow checkpoint base."""
    import tensorflow as tf

    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (repo_root / path).resolve()

    if path.is_dir():
        latest = tf.train.latest_checkpoint(str(path))
        if latest:
            return Path(latest)
        ckpt_state = tf.train.get_checkpoint_state(str(path))
        if ckpt_state and ckpt_state.model_checkpoint_path:
            return Path(ckpt_state.model_checkpoint_path)
        return None

    base_path = strip_checkpoint_suffix(path)
    if Path(str(base_path) + '.index').exists():
        return base_path
    if Path(str(base_path) + '.meta').exists():
        return base_path
    return None


def emit_summary(cfg, repo_root: Path, config_path: Path, logger=None) -> None:
    """Print or log the effective training summary."""
    model_name = f'{cfg.MODEL.FRONT_END}_{cfg.MODEL.MODEL_NAME}'
    data_root = Path(str(cfg.DATASET.DATA_DIR))
    train_tfrecord = data_root / 'tfrecords' / 'tusimple_train.tfrecords'
    val_tfrecord = data_root / 'tfrecords' / 'tusimple_val.tfrecords'
    model_dir = Path(str(cfg.TRAIN.MODEL_SAVE_DIR)) / model_name
    tboard_dir = Path(str(cfg.TRAIN.TBOARD_SAVE_DIR)) / model_name
    lines = [
        'LaneNet training preflight',
        f'Repo root: {repo_root}',
        f'Config: {config_path}',
        f'Front end: {cfg.MODEL.FRONT_END}',
        f'Multi-GPU: {cfg.TRAIN.MULTI_GPU.ENABLE}',
        f'GPU devices: {list(cfg.TRAIN.MULTI_GPU.GPU_DEVICES)}',
        f'Batch size: {cfg.TRAIN.BATCH_SIZE}',
        f'Val batch size: {cfg.TRAIN.VAL_BATCH_SIZE}',
        f'Data root: {data_root}',
        f'Train TFRecord: {train_tfrecord}',
        f'Val TFRecord: {val_tfrecord}',
        f'Model dir: {model_dir}',
        f'TensorBoard dir: {tboard_dir}',
        f'Log dir: {cfg.LOG.SAVE_DIR}',
        f'Restore enabled: {cfg.TRAIN.RESTORE_FROM_SNAPSHOT.ENABLE}',
        f'Restore path: {cfg.TRAIN.RESTORE_FROM_SNAPSHOT.SNAPSHOT_PATH}',
    ]
    for line in lines:
        if logger is None:
            print(line)
        else:
            logger.info(line)


def validate_and_prepare_run(cfg, repo_root: Path, logger, tf_module) -> None:
    """Run preflight checks that should pass before heavy training starts."""
    model_name = f'{cfg.MODEL.FRONT_END}_{cfg.MODEL.MODEL_NAME}'
    data_root = Path(str(cfg.DATASET.DATA_DIR))
    train_tfrecord = data_root / 'tfrecords' / 'tusimple_train.tfrecords'
    val_tfrecord = data_root / 'tfrecords' / 'tusimple_val.tfrecords'

    if cfg.MODEL.FRONT_END not in {'bisenetv2', 'vgg'}:
        raise SystemExit(f'Unsupported MODEL.FRONT_END: {cfg.MODEL.FRONT_END!r}')
    if cfg.SOLVER.OPTIMIZER.lower() not in {'sgd', 'adam'}:
        raise SystemExit(f'Unsupported SOLVER.OPTIMIZER: {cfg.SOLVER.OPTIMIZER!r}')

    log_dir = Path(str(cfg.LOG.SAVE_DIR))
    log_dir.mkdir(parents=True, exist_ok=True)

    if cfg.TRAIN.RESTORE_FROM_SNAPSHOT.ENABLE:
        resolved_ckpt = resolve_checkpoint_path(str(cfg.TRAIN.RESTORE_FROM_SNAPSHOT.SNAPSHOT_PATH), repo_root)
        if resolved_ckpt is None:
            raise SystemExit(
                'Restore was enabled but the checkpoint path could not be resolved. '
                'Provide a checkpoint base path or a checkpoint directory with a latest checkpoint.'
            )
        cfg.TRAIN.RESTORE_FROM_SNAPSHOT.SNAPSHOT_PATH = str(resolved_ckpt)
        logger.info(f'Resolved restore checkpoint: {resolved_ckpt}')

    if not cfg.TRAIN.WARM_UP.ENABLE:
        raise SystemExit(
            'The upstream LaneNet trainer still traces the warm-up branch even when warm-up is disabled. '
            'Keep TRAIN.WARM_UP.ENABLE=True for smoke runs and shorten the run with TRAIN.EPOCH_NUMS/ TRAIN.BATCH_SIZE instead.'
        )

    try:
        cuda_built = tf_module.test.is_built_with_cuda()
        gpu_name = tf_module.test.gpu_device_name()
    except Exception as exc:  # pragma: no cover - depends on host CUDA runtime state.
        raise SystemExit(
            'Validated LaneNet training requires a CUDA-capable TensorFlow 1.15 environment. '
            'GPU detection failed before training could start. Use the prepared GPU environment or run dry-run preflight only.'
        ) from exc
    if not cuda_built or not gpu_name:
        raise SystemExit(
            'Validated LaneNet training requires a CUDA-capable TensorFlow 1.15 environment. '
            'Use the prepared GPU environment or run dry-run preflight only.'
        )

    train_count = count_tfrecord_examples(train_tfrecord)
    if train_count <= 0:
        raise SystemExit(f'Train TFRecord set is missing or empty: {train_tfrecord}')

    train_batch = int(cfg.TRAIN.BATCH_SIZE)
    if train_batch <= 0:
        raise SystemExit(f'Invalid TRAIN.BATCH_SIZE: {train_batch}')

    train_steps = (train_count + train_batch - 1) // train_batch
    logger.info(f'Train record count: {train_count}')
    logger.info(f'Train steps per epoch: {train_steps}')

    if train_steps <= 1:
        raise SystemExit(
            'Training TFRecords are too small for the current batch size. '
            'The source loop iterates range(1, steps_per_epoch), so steps_per_epoch <= 1 would produce no update. '
            'Lower TRAIN.BATCH_SIZE or add more TFRecords.'
        )

    if cfg.TRAIN.MULTI_GPU.ENABLE:
        gpu_devices = list(cfg.TRAIN.MULTI_GPU.GPU_DEVICES)
        gpu_nums = len(gpu_devices)
        if gpu_nums <= 0:
            raise SystemExit('TRAIN.MULTI_GPU.ENABLE is true but GPU_DEVICES is empty.')
        if train_batch < gpu_nums:
            raise SystemExit(
                f'TRAIN.BATCH_SIZE ({train_batch}) is smaller than the GPU count ({gpu_nums}). '
                'Increase the batch size or switch to single-GPU mode.'
            )
        if train_batch % gpu_nums != 0:
            logger.warning(
                'TRAIN.BATCH_SIZE is not divisible by the number of GPUs; the trainer floors the per-GPU batch size.'
            )

        val_count = count_tfrecord_examples(val_tfrecord)
        if val_count <= 0:
            raise SystemExit(f'Validation TFRecord set is missing or empty: {val_tfrecord}')
        val_batch = int(cfg.TRAIN.VAL_BATCH_SIZE)
        if val_batch <= 0:
            raise SystemExit(f'Invalid TRAIN.VAL_BATCH_SIZE: {val_batch}')
        val_steps = (val_count + val_batch - 1) // val_batch
        logger.info(f'Validation record count: {val_count}')
        logger.info(f'Validation steps per epoch: {val_steps}')
        if val_steps <= 1:
            logger.warning(
                'Validation TFRecords are too small for the current validation batch size, so the validation loop may be empty.'
            )

    model_dir = Path(str(cfg.TRAIN.MODEL_SAVE_DIR)) / model_name
    tboard_dir = Path(str(cfg.TRAIN.TBOARD_SAVE_DIR)) / model_name
    logger.info(f'Model output dir: {model_dir}')
    logger.info(f'TensorBoard output dir: {tboard_dir}')
    logger.info('Training preflight completed successfully.')


def main() -> int:
    """Entry point for the bundled training wrapper."""
    args = parse_args()
    repo_root = resolve_repo_root(args.repo_root)
    bootstrap_repo(repo_root)
    cfg, parse_config_utils, config_path = load_effective_config(repo_root, args.config, args.overrides)

    if not args.run:
        emit_summary(cfg, repo_root, config_path, logger=None)
        print('Dry-run only. Add --run to launch training.')
        return 0

    from local_utils.log_util import init_logger

    Path(str(cfg.LOG.SAVE_DIR)).mkdir(parents=True, exist_ok=True)
    logger = init_logger.get_logger(log_file_name_prefix='lanenet_train')
    emit_summary(cfg, repo_root, config_path, logger=logger)

    import tensorflow as tf

    validate_and_prepare_run(cfg, repo_root, logger, tf)

    from trainner import tusimple_lanenet_single_gpu_trainner as single_gpu_trainner
    from trainner import tusimple_lanenet_multi_gpu_trainner as multi_gpu_trainner

    if cfg.TRAIN.MULTI_GPU.ENABLE:
        logger.info('Using multi gpu trainner ...')
        worker = multi_gpu_trainner.LaneNetTusimpleMultiTrainer(cfg=cfg)
    else:
        logger.info('Using single gpu trainner ...')
        worker = single_gpu_trainner.LaneNetTusimpleTrainer(cfg=cfg)

    worker.train()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
