#!/usr/bin/env python3
"""CPU-only synthetic smoke test for Torchreid feature extraction.

This helper intentionally avoids downloads by building a model with
pretrained=False, saving a local synthetic checkpoint, and then loading that
checkpoint through FeatureExtractor.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            'Run a synthetic CPU smoke test for Torchreid feature extraction, '
            'local checkpoint loading, and distance/rank helpers.'
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--model-name',
        default='osnet_x0_25',
        help='Torchreid model key to build for the smoke test.',
    )
    parser.add_argument(
        '--height',
        type=int,
        default=256,
        help='Synthetic image height used for the generated test inputs.',
    )
    parser.add_argument(
        '--width',
        type=int,
        default=128,
        help='Synthetic image width used for the generated test inputs.',
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=7,
        help='Seed used to make the synthetic inputs deterministic.',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print model-complexity details while constructing the extractor.',
    )
    return parser.parse_args()


def build_synthetic_image(height: int, width: int, seed: int):
    import numpy as np

    rng = np.random.default_rng(seed)
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[..., 0] = np.linspace(0, 255, width, dtype=np.uint8)[None, :]
    img[..., 1] = np.linspace(0, 255, height, dtype=np.uint8)[:, None]
    img[..., 2] = rng.integers(0, 256, size=(height, width), dtype=np.uint8)
    return img


def main() -> int:
    args = parse_args()

    import numpy as np
    import torch

    from torchreid.models import build_model
    from torchreid.metrics import compute_distance_matrix, evaluate_rank
    from torchreid.utils import FeatureExtractor

    with tempfile.TemporaryDirectory(prefix='torchreid-smoke-') as tmpdir:
        tmpdir_path = Path(tmpdir)
        checkpoint_path = tmpdir_path / 'synthetic_checkpoint.pth.tar'

        # Build a local model without any pretrained download path.
        model = build_model(
            name=args.model_name,
            num_classes=1,
            pretrained=False,
            use_gpu=False,
        )
        torch.save({'state_dict': model.state_dict()}, checkpoint_path)

        if args.verbose:
            extractor = FeatureExtractor(
                model_name=args.model_name,
                model_path=str(checkpoint_path),
                image_size=(args.height, args.width),
                device='cpu',
                verbose=True,
            )
        else:
            with contextlib.redirect_stdout(io.StringIO()):
                extractor = FeatureExtractor(
                    model_name=args.model_name,
                    model_path=str(checkpoint_path),
                    image_size=(args.height, args.width),
                    device='cpu',
                    verbose=False,
                )

        images = [
            build_synthetic_image(args.height, args.width, args.seed),
            build_synthetic_image(args.height, args.width, args.seed + 1),
        ]

        features = extractor(images)
        if not isinstance(features, torch.Tensor):
            raise TypeError('FeatureExtractor did not return a torch.Tensor')
        if features.dim() != 2:
            raise AssertionError(
                f'Expected a 2-D feature tensor, got shape {tuple(features.shape)}'
            )
        if features.size(0) != 2:
            raise AssertionError(
                f'Expected batch dimension 2, got {features.size(0)}'
            )

        distmat = compute_distance_matrix(features, features, metric='euclidean')
        if distmat.shape != (2, 2):
            raise AssertionError(
                f'Expected a 2x2 distance matrix, got {tuple(distmat.shape)}'
            )

        cmc, mAP = evaluate_rank(
            distmat.cpu().numpy(),
            q_pids=np.array([0, 1]),
            g_pids=np.array([0, 1]),
            q_camids=np.array([0, 1]),
            g_camids=np.array([1, 0]),
            max_rank=2,
            use_cython=False,
        )

        try:
            from torchreid.metrics.rank_cylib.rank_cy import evaluate_cy  # noqa: F401
            cython_available = True
        except Exception:
            cython_available = False

        summary = {
            'model_name': args.model_name,
            'checkpoint_created': True,
            'feature_shape': list(features.shape),
            'distance_shape': list(distmat.shape),
            'cmc_top1': float(cmc[0]),
            'mAP': float(mAP),
            'rank_cy_imported': cython_available,
        }
        print(json.dumps(summary, indent=2, sort_keys=True))

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
