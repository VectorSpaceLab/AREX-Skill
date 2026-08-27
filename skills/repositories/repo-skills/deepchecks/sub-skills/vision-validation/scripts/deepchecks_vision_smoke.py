#!/usr/bin/env python3
"""Build a tiny in-memory VisionData object for safe smoke testing.

The script uses only local data, makes no network calls, and writes no files.
It is intentionally small so `--help` works even before optional vision imports
happen.
"""
from __future__ import annotations

import argparse
import json
from typing import Dict, Tuple

import numpy as np


class TinyBatchLoader:
    """Re-iterable batch loader backed by in-memory batch dictionaries."""

    def __init__(self, batches):
        self._batches = list(batches)

    def __iter__(self):
        return iter(self._batches)

    def __len__(self):
        return len(self._batches)


def make_rgb_image(offset: int) -> np.ndarray:
    """Create a tiny, non-constant uint8 RGB image."""
    base = np.array(
        [
            [[0, 12, 24], [36, 48, 60]],
            [[72, 84, 96], [108, 120, 132]],
        ],
        dtype=np.int16,
    )
    return np.clip(base + offset, 0, 255).astype(np.uint8)


def build_classification_batches() -> Tuple[TinyBatchLoader, Dict[int, str]]:
    batches = [
        {
            'images': [make_rgb_image(0), make_rgb_image(6)],
            'labels': [0, 1],
            'predictions': [
                np.array([0.85, 0.15], dtype=np.float32),
                np.array([0.20, 0.80], dtype=np.float32),
            ],
            'image_identifiers': ['cls-0', 'cls-1'],
        },
        {
            'images': [make_rgb_image(20), make_rgb_image(26)],
            'labels': [1, 0],
            'predictions': [
                np.array([0.12, 0.88], dtype=np.float32),
                np.array([0.77, 0.23], dtype=np.float32),
            ],
            'image_identifiers': ['cls-2', 'cls-3'],
        },
    ]
    return TinyBatchLoader(batches), {0: 'cat', 1: 'dog'}


def build_detection_batches() -> Tuple[TinyBatchLoader, Dict[int, str]]:
    batches = [
        {
            'images': [make_rgb_image(0), make_rgb_image(8)],
            'labels': [
                np.array([[0, 0, 0, 1, 1]], dtype=np.float32),
                np.array([[1, 0, 0, 1, 1]], dtype=np.float32),
            ],
            'predictions': [
                np.array([[0, 0, 1, 1, 0.90, 0]], dtype=np.float32),
                np.array([[0, 0, 1, 1, 0.80, 1]], dtype=np.float32),
            ],
            'image_identifiers': ['det-0', 'det-1'],
        },
        {
            'images': [make_rgb_image(18), make_rgb_image(24)],
            'labels': [
                np.array([[0, 0, 0, 1, 1]], dtype=np.float32),
                np.array([[1, 0, 0, 1, 1]], dtype=np.float32),
            ],
            'predictions': [
                np.array([[0, 0, 1, 1, 0.75, 0]], dtype=np.float32),
                np.array([[0, 0, 1, 1, 0.70, 1]], dtype=np.float32),
            ],
            'image_identifiers': ['det-2', 'det-3'],
        },
    ]
    return TinyBatchLoader(batches), {0: 'person', 1: 'car'}


def build_segmentation_batches() -> Tuple[TinyBatchLoader, Dict[int, str]]:
    labels_a = np.array([[0, 1], [1, 0]], dtype=np.int64)
    labels_b = np.array([[1, 0], [0, 1]], dtype=np.int64)
    preds_a = np.array(
        [
            [[0.90, 0.20], [0.15, 0.80]],
            [[0.10, 0.80], [0.85, 0.20]],
        ],
        dtype=np.float32,
    )
    preds_b = np.array(
        [
            [[0.25, 0.75], [0.60, 0.40]],
            [[0.75, 0.25], [0.40, 0.60]],
        ],
        dtype=np.float32,
    )
    batches = [
        {
            'images': [make_rgb_image(0), make_rgb_image(12)],
            'labels': [labels_a, labels_b],
            'predictions': [preds_a, preds_b],
            'image_identifiers': ['seg-0', 'seg-1'],
        },
        {
            'images': [make_rgb_image(22), make_rgb_image(34)],
            'labels': [labels_b, labels_a],
            'predictions': [preds_b, preds_a],
            'image_identifiers': ['seg-2', 'seg-3'],
        },
    ]
    return TinyBatchLoader(batches), {0: 'background', 1: 'foreground'}


def build_other_batches() -> Tuple[TinyBatchLoader, None]:
    batches = [
        {
            'images': [make_rgb_image(0), make_rgb_image(16)],
            'image_identifiers': ['other-0', 'other-1'],
        },
        {
            'images': [make_rgb_image(28), make_rgb_image(40)],
            'image_identifiers': ['other-2', 'other-3'],
        },
    ]
    return TinyBatchLoader(batches), None


def build_fixture(task_type: str):
    if task_type == 'classification':
        return build_classification_batches()
    if task_type == 'object_detection':
        return build_detection_batches()
    if task_type == 'semantic_segmentation':
        return build_segmentation_batches()
    if task_type == 'other':
        return build_other_batches()
    raise ValueError(f'Unsupported task type: {task_type}')


def summarize_loader(task_type: str):
    try:
        from deepchecks.vision import VisionData
    except ImportError as exc:  # pragma: no cover - depends on optional runtime packages
        raise SystemExit(
            'deepchecks.vision requires torch and torchvision. Install the vision extra and a compatible torch build.'
        ) from exc

    loader, label_map = build_fixture(task_type)
    kwargs = {
        'batch_loader': loader,
        'task_type': task_type,
        'dataset_name': 'vision-smoke',
        'reshuffle_data': False,
    }
    if label_map is not None:
        kwargs['label_map'] = label_map

    try:
        vision_data = VisionData(**kwargs)
    except Exception as exc:  # pragma: no cover - smoke helper should stay readable if validation changes
        raise SystemExit(f'VisionData construction failed for task_type={task_type}: {exc}') from exc

    try:
        first_batch = next(iter(vision_data))
    except Exception as exc:  # pragma: no cover
        raise SystemExit(f'Iteration over VisionData failed for task_type={task_type}: {exc}') from exc

    first_image = np.asarray(first_batch['images'][0])
    summary = {
        'task_type': vision_data.task_type.value,
        'loader_batches': len(loader),
        'batch_keys': sorted(first_batch.keys()),
        'image_shape': list(first_image.shape),
        'image_dtype': str(first_image.dtype),
        'image_min': int(first_image.min()),
        'image_max': int(first_image.max()),
        'has_images': vision_data.has_images,
        'has_labels': vision_data.has_labels,
        'has_predictions': vision_data.has_predictions,
        'num_classes': vision_data.num_classes,
        'image_identifiers': list(first_batch.get('image_identifiers', [])),
    }

    if 'labels' in first_batch:
        first_label = first_batch['labels'][0]
        if isinstance(first_label, np.ndarray):
            summary['label_shape'] = list(first_label.shape)
            summary['label_dtype'] = str(first_label.dtype)
        else:
            summary['label_type'] = type(first_label).__name__
            summary['label_value'] = first_label if isinstance(first_label, (int, str, float)) else str(first_label)

    if 'predictions' in first_batch:
        first_prediction = np.asarray(first_batch['predictions'][0])
        summary['prediction_shape'] = list(first_prediction.shape)
        summary['prediction_dtype'] = str(first_prediction.dtype)

    print(json.dumps(summary, indent=2, sort_keys=True, default=str))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Build a tiny in-memory Deepchecks VisionData object.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--task-type',
        default='classification',
        choices=['classification', 'object_detection', 'semantic_segmentation', 'other'],
        help='Task type used to generate the tiny batch fixture.',
    )
    parser.add_argument(
        '--skip-run',
        action='store_true',
        help='Only build and summarize the local batch fixture; do not import Deepchecks or construct VisionData.',
    )
    return parser.parse_args()


def summarize_fixture(task_type: str):
    loader, label_map = build_fixture(task_type)
    first_batch = next(iter(loader))
    first_image = np.asarray(first_batch['images'][0])
    summary = {
        'task_type': task_type,
        'skip_run': True,
        'loader_batches': len(loader),
        'batch_keys': sorted(first_batch.keys()),
        'image_shape': list(first_image.shape),
        'image_dtype': str(first_image.dtype),
        'image_min': int(first_image.min()),
        'image_max': int(first_image.max()),
        'label_map_keys': sorted(label_map.keys()) if label_map else [],
    }
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))


def main() -> int:
    args = parse_args()
    if args.skip_run:
        summarize_fixture(args.task_type)
    else:
        summarize_loader(args.task_type)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
