#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate LaneNet TFRecords from a prepared TuSimple dataset.

This bundled wrapper keeps the upstream zero-arg generate_tfrecords() entry point,
but it adds:
- repository-root auto-discovery,
- optional in-memory dataset-root overrides,
- placeholder/path preflights before TFRecord writing.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from types import SimpleNamespace

LOG = logging.getLogger("make_tusimple_tfrecords")
CLI_ARGS = None


def init_args():
    """
    Parse runtime overrides for the prepared TuSimple dataset.
    """
    parser = argparse.ArgumentParser(
        description="Generate LaneNet TFRecords from a prepared TuSimple dataset."
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root. Auto-detected if omitted.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Config file path relative to the repository root or absolute.",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Prepared dataset root that contains gt_image/, gt_binary_image/, and gt_instance_image/.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require a valid train/val/test split trio instead of letting LaneNet auto-generate it.",
    )
    return parser.parse_args()


def _looks_like_placeholder(value):
    text = str(value)
    return "ROOT_PATH" in text or "REPO_ROOT_PATH" in text


def _find_repo_root(explicit_root=None):
    if explicit_root:
        root = Path(explicit_root).expanduser().resolve()
        if not (root / "config" / "tusimple_lanenet.yaml").is_file():
            raise FileNotFoundError(
                f"{root} does not look like the repository root because config/tusimple_lanenet.yaml is missing"
            )
        return root

    start = Path.cwd().resolve()
    for candidate in [start] + list(start.parents):
        if (candidate / "config" / "tusimple_lanenet.yaml").is_file() and (candidate / "data_provider").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not locate the repository root from the current working directory. Pass --repo-root or run the wrapper from a repo checkout."
    )


def _resolve_config_path(repo_root, config_arg):
    if config_arg is None:
        return repo_root / "config" / "tusimple_lanenet.yaml"

    config_path = Path(config_arg).expanduser()
    if config_path.is_absolute():
        return config_path
    return (repo_root / config_path).resolve()


def _resolve_data_dir(repo_root, cfg, data_dir_arg):
    if data_dir_arg is not None:
        data_dir = Path(data_dir_arg).expanduser()
        if not data_dir.is_absolute():
            data_dir = (repo_root / data_dir).resolve()
        return data_dir

    data_dir_text = str(cfg.DATASET.DATA_DIR)
    if _looks_like_placeholder(data_dir_text):
        return None

    data_dir = Path(data_dir_text).expanduser()
    if data_dir.is_absolute():
        return data_dir
    return (repo_root / data_dir).resolve()


def _resolve_dataset_file(repo_root, data_dir, file_text):
    file_path = Path(file_text).expanduser()
    if file_path.is_absolute():
        return file_path

    candidates = [
        (repo_root / file_path).resolve(),
        (data_dir / file_path).resolve(),
        (data_dir.parent / file_path).resolve(),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _validate_index_file(list_path, repo_root, data_dir):
    rows_seen = 0
    with list_path.open("r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            rows_seen += 1
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(
                    f"{list_path}:{line_no} should contain exactly 3 paths, got {len(parts)}"
                )
            if any(_looks_like_placeholder(part) for part in parts):
                raise ValueError(
                    f"{list_path}:{line_no} still contains ROOT_PATH/REPO_ROOT_PATH placeholders"
                )

            resolved_paths = [_resolve_dataset_file(repo_root, data_dir, part) for part in parts]
            for resolved_path in resolved_paths:
                if not resolved_path.exists():
                    raise FileNotFoundError(
                        f"{list_path}:{line_no} references missing file: {resolved_path}"
                    )

            basenames = {path.name for path in resolved_paths}
            if len(basenames) != 1:
                raise ValueError(
                    f"{list_path}:{line_no} uses mismatched basenames: {parts}"
                )

    if rows_seen == 0:
        raise ValueError(f"{list_path} contains no usable rows")

    return rows_seen


def _validate_prepared_dataset(cfg, repo_root, strict=False):
    if _looks_like_placeholder(cfg.DATASET.DATA_DIR):
        raise ValueError(
            "DATASET.DATA_DIR still contains a placeholder. Pass --data-dir or edit the config before generating TFRecords."
        )

    data_dir = _resolve_data_dir(repo_root, cfg, None)
    if data_dir is None:
        raise ValueError(
            "DATASET.DATA_DIR still cannot be resolved. Pass --data-dir or replace the placeholder paths in the config."
        )

    required_dirs = [
        data_dir / "gt_image",
        data_dir / "gt_binary_image",
        data_dir / "gt_instance_image",
    ]
    if not all(path.is_dir() for path in required_dirs):
        if (data_dir / "image").is_dir() and not (data_dir / "gt_image").exists():
            raise FileNotFoundError(
                f"{data_dir} contains image/ but not gt_image/. LaneNetDataProducer expects gt_image/, gt_binary_image/, and gt_instance_image/ at the dataset root."
            )
        missing = [str(path) for path in required_dirs if not path.is_dir()]
        raise FileNotFoundError(
            f"Prepared dataset layout is incomplete under {data_dir}: {', '.join(missing)}"
        )

    list_paths = [
        _resolve_dataset_file(repo_root, data_dir, cfg.DATASET.TRAIN_FILE_LIST),
        _resolve_dataset_file(repo_root, data_dir, cfg.DATASET.VAL_FILE_LIST),
        _resolve_dataset_file(repo_root, data_dir, cfg.DATASET.TEST_FILE_LIST),
    ]
    existing = [path.exists() for path in list_paths]

    if strict:
        if not all(existing):
            raise ValueError(
                "Strict mode requires valid train.txt, val.txt, and test.txt before TFRecord generation."
            )
    else:
        if any(existing) and not all(existing):
            LOG.warning(
                "Only some split files exist; LaneNetDataProducer will rewrite train.txt, val.txt, and test.txt from gt_image/."
            )
        if not any(existing):
            LOG.info(
                "Split files are missing; LaneNetDataProducer will auto-split gt_image/ into train, val, and test."
            )

    for list_path in list_paths:
        if list_path.exists():
            _validate_index_file(list_path, repo_root, data_dir)

    return data_dir


def _bootstrap_runtime(repo_root, config_arg, data_dir_arg):
    os.chdir(repo_root)
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from local_utils.config_utils.parse_config_utils import Config
    from local_utils.config_utils import parse_config_utils

    config_path = _resolve_config_path(repo_root, config_arg)
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    cfg = Config(config_path=str(config_path))

    if data_dir_arg is not None:
        data_dir = Path(data_dir_arg).expanduser()
        if not data_dir.is_absolute():
            data_dir = (repo_root / data_dir).resolve()
        cfg.DATASET.DATA_DIR = str(data_dir)
        cfg.DATASET.TRAIN_FILE_LIST = str(data_dir / "train.txt")
        cfg.DATASET.VAL_FILE_LIST = str(data_dir / "val.txt")
        cfg.DATASET.TEST_FILE_LIST = str(data_dir / "test.txt")

    parse_config_utils.lanenet_cfg = cfg

    sys.modules.pop("data_provider.lanenet_data_feed_pipline", None)
    sys.modules.pop("data_provider.tf_io_pipline_tools", None)
    return cfg


def generate_tfrecords():
    """
    Generate LaneNet TFRecords using the current CLI overrides.
    """
    args = CLI_ARGS or SimpleNamespace(repo_root=None, config=None, data_dir=None, strict=False)
    repo_root = _find_repo_root(args.repo_root)
    cfg = _bootstrap_runtime(repo_root, args.config, args.data_dir)
    data_dir = _validate_prepared_dataset(cfg, repo_root, strict=args.strict)

    from data_provider import lanenet_data_feed_pipline

    LOG.info("Using repository root: %s", repo_root)
    LOG.info("Using dataset root: %s", data_dir)
    producer = lanenet_data_feed_pipline.LaneNetDataProducer()
    producer.generate_tfrecords()
    return


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    global CLI_ARGS
    CLI_ARGS = init_args()
    generate_tfrecords()


if __name__ == "__main__":
    main()
