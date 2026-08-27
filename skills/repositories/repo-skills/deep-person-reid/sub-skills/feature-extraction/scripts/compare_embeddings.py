#!/usr/bin/env python3
"""Compare query and gallery image lists with Torchreid embeddings.

Each manifest line should contain:

    path

or:

    path pid camid

When every line supplies pid/camid labels, the helper also computes CMC/mAP.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Record:
    path: str
    pid: Optional[int]
    camid: Optional[int]
    line_no: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            'Extract Torchreid embeddings for query/gallery manifests, compute '
            'a distance matrix, and optionally evaluate rank metrics.'
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--model-name',
        required=True,
        help='Exact Torchreid model key to build.',
    )
    parser.add_argument(
        '--weights',
        required=True,
        help='Path to a local checkpoint. This helper never downloads weights.',
    )
    parser.add_argument(
        '--query-list',
        required=True,
        help='Text file listing query images, one per line.',
    )
    parser.add_argument(
        '--gallery-list',
        required=True,
        help='Text file listing gallery images, one per line.',
    )
    parser.add_argument(
        '--metric',
        default='euclidean',
        choices=('euclidean', 'cosine'),
        help='Distance metric used by compute_distance_matrix().',
    )
    parser.add_argument(
        '--device',
        default='cpu',
        help='Torch device string. Use cpu for the safest no-download path.',
    )
    parser.add_argument(
        '--height',
        type=int,
        default=256,
        help='Image height passed to FeatureExtractor.',
    )
    parser.add_argument(
        '--width',
        type=int,
        default=128,
        help='Image width passed to FeatureExtractor.',
    )
    parser.add_argument(
        '--max-rank',
        type=int,
        default=50,
        help='Maximum CMC rank to compute when labels are present.',
    )
    parser.add_argument(
        '--rerank',
        action='store_true',
        help='Apply CPU re-ranking before evaluation.',
    )
    parser.add_argument(
        '--output-json',
        help='Optional path to write the summary JSON.',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Ask FeatureExtractor to print model-complexity details.',
    )
    return parser.parse_args()


def load_manifest(path: str) -> list[Record]:
    manifest_path = Path(path).expanduser()
    if not manifest_path.is_file():
        raise SystemExit(f'No manifest found at {manifest_path}')

    records: list[Record] = []
    base_dir = manifest_path.parent

    for line_no, raw_line in enumerate(manifest_path.read_text().splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) not in (1, 3):
            raise SystemExit(
                f'{manifest_path}:{line_no}: expected "path" or "path pid camid", '
                f'got {line!r}'
            )

        img_path = Path(parts[0]).expanduser()
        if not img_path.is_absolute():
            img_path = (base_dir / img_path).resolve()
        else:
            img_path = img_path.resolve()

        pid = camid = None
        if len(parts) == 3:
            try:
                pid = int(parts[1])
                camid = int(parts[2])
            except ValueError as exc:
                raise SystemExit(
                    f'{manifest_path}:{line_no}: pid/camid must be integers'
                ) from exc

        records.append(Record(str(img_path), pid, camid, line_no))

    if not records:
        raise SystemExit(f'{manifest_path} does not contain any usable entries')

    return records


def label_mode(records: list[Record]) -> str:
    has_labels = [r.pid is not None and r.camid is not None for r in records]
    if all(has_labels):
        return 'all'
    if any(has_labels):
        return 'mixed'
    return 'none'


def labels_to_numpy(records: list[Record]):
    import numpy as np

    if label_mode(records) != 'all':
        return None
    pids = np.array([r.pid for r in records], dtype=int)
    camids = np.array([r.camid for r in records], dtype=int)
    return pids, camids


def ensure_local_weights(path: str) -> str:
    weight_path = Path(path).expanduser()
    if not weight_path.is_file():
        raise SystemExit(
            f'Local checkpoint not found: {weight_path}. '
            'Provide a verified file path to avoid downloads.'
        )
    return str(weight_path.resolve())


def main() -> int:
    args = parse_args()

    if args.device.startswith('cuda'):
        import torch

        if not torch.cuda.is_available():
            raise SystemExit(
                f'CUDA device {args.device!r} was requested, but torch.cuda.is_available() is False.'
            )

    weights = ensure_local_weights(args.weights)
    query_records = load_manifest(args.query_list)
    gallery_records = load_manifest(args.gallery_list)

    import torch

    from torchreid.metrics import compute_distance_matrix, evaluate_rank
    from torchreid.utils import FeatureExtractor, re_ranking

    query_paths = [r.path for r in query_records]
    gallery_paths = [r.path for r in gallery_records]

    extractor = FeatureExtractor(
        model_name=args.model_name,
        model_path=weights,
        image_size=(args.height, args.width),
        device=args.device,
        verbose=args.verbose,
    )

    features = extractor(query_paths + gallery_paths)
    if not isinstance(features, torch.Tensor):
        raise TypeError('FeatureExtractor did not return a torch.Tensor')

    num_query = len(query_paths)
    num_gallery = len(gallery_paths)
    q_feat = features[:num_query]
    g_feat = features[num_query:]

    q_g = compute_distance_matrix(q_feat, g_feat, metric=args.metric)
    distmat = q_g.cpu().numpy()
    reranked = False

    if args.rerank:
        q_q = compute_distance_matrix(q_feat, q_feat, metric=args.metric).cpu().numpy()
        g_g = compute_distance_matrix(g_feat, g_feat, metric=args.metric).cpu().numpy()
        distmat = re_ranking(distmat, q_q, g_g)
        reranked = True

    q_label_mode = label_mode(query_records)
    g_label_mode = label_mode(gallery_records)
    if q_label_mode == 'mixed' or g_label_mode == 'mixed':
        raise SystemExit(
            'Every line in each manifest must either include pid/camid labels or omit them entirely.'
        )
    if q_label_mode != g_label_mode:
        raise SystemExit(
            'Query and gallery manifests must use the same labeling mode. '
            'Provide pid/camid on every line of both files, or omit labels from both.'
        )

    summary = {
        'model_name': args.model_name,
        'weights': weights,
        'metric': args.metric,
        'reranked': reranked,
        'num_query': num_query,
        'num_gallery': num_gallery,
        'query_label_mode': q_label_mode,
        'gallery_label_mode': g_label_mode,
        'feature_shape': list(features.shape),
        'distance_shape': list(distmat.shape),
        'evaluation_ran': False,
    }

    q_labels = labels_to_numpy(query_records)
    g_labels = labels_to_numpy(gallery_records)
    if q_labels is not None and g_labels is not None:
        q_pids, q_camids = q_labels
        g_pids, g_camids = g_labels
        cmc, mAP = evaluate_rank(
            distmat,
            q_pids,
            g_pids,
            q_camids,
            g_camids,
            max_rank=args.max_rank,
            use_cython=True,
        )
        summary['evaluation_ran'] = True
        summary['mAP'] = float(mAP)
        summary['cmc_head'] = [float(x) for x in cmc[: min(5, len(cmc))]]

    if args.output_json:
        output_path = Path(args.output_json).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        summary['output_json'] = str(output_path)
        output_path.write_text(json.dumps(summary, indent=2, sort_keys=True))

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
