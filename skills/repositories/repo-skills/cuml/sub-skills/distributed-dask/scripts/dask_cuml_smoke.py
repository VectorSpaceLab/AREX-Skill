#!/usr/bin/env python3
'''
Tiny cuML Dask smoke.

The script keeps import-time dependency checks separate from the actual
cluster smoke so it can fail cleanly when the Dask extras are missing.
'''
from __future__ import annotations

import argparse
import importlib
import sys


OPTIONAL_MODULES = [
    ('dask', 'dask'),
    ('dask.distributed', 'dask.distributed'),
    ('dask_cuda', 'dask_cuda'),
    ('dask_cudf', 'dask_cudf'),
    ('raft_dask', 'raft_dask'),
]


def _note_import(module_name: str, label: str, missing: list[str]) -> None:
    try:
        importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - import smoke only
        missing.append(f'{label}: {exc.__class__.__name__}: {exc}')


def _check_dependencies() -> list[str]:
    missing: list[str] = []
    for module_name, label in OPTIONAL_MODULES:
        _note_import(module_name, label, missing)

    try:
        import cuml.dask  # noqa: F401
    except Exception as exc:  # pragma: no cover - import smoke only
        missing.append(f'cuml.dask: {exc.__class__.__name__}: {exc}')

    return missing


def _check_cuda() -> int:
    import cupy as cp

    try:
        return cp.cuda.runtime.getDeviceCount()
    except Exception as exc:  # pragma: no cover - CUDA smoke only
        raise RuntimeError(f'CUDA unavailable: {exc}') from exc


def _build_cluster(device_limit: str):
    from dask.distributed import Client
    from dask_cuda import LocalCUDACluster

    kwargs = {'threads_per_worker': 1}
    if device_limit is not None:
        kwargs['device_memory_limit'] = device_limit

    cluster = LocalCUDACluster(**kwargs)
    client = Client(cluster)
    return cluster, client


def _run_smoke(client, n_samples: int, n_clusters: int):
    import cupy as cp
    from cuml.dask.cluster import KMeans
    from cuml.dask.datasets import make_blobs

    workers = list(client.scheduler_info()['workers'])
    n_workers = len(workers)
    if n_workers < 1:
        raise RuntimeError('no Dask workers started')

    n_parts = max(1, min(n_samples, n_workers * 2))
    X, y = make_blobs(
        n_samples=n_samples,
        n_features=8,
        centers=n_clusters,
        cluster_std=0.25,
        random_state=0,
        n_parts=n_parts,
        client=client,
    )

    model = KMeans(n_clusters=n_clusters, random_state=0, client=client)
    model.fit(X)
    labels = model.predict(X)

    labels_host = cp.asarray(labels.compute())
    unique_labels = int(cp.unique(labels_host).size)
    centers_shape = getattr(model.cluster_centers_, 'shape', None)
    return n_workers, n_parts, unique_labels, centers_shape


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Tiny cuML Dask smoke for LocalCUDACluster and KMeans.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--n-samples',
        type=int,
        default=128,
        help='Number of synthetic samples to generate.',
    )
    parser.add_argument(
        '--n-clusters',
        type=int,
        default=4,
        help='Number of clusters to generate and fit.',
    )
    parser.add_argument(
        '--device-limit',
        default='auto',
        help='Device memory limit forwarded to LocalCUDACluster.',
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.n_samples < args.n_clusters:
        print(
            'distributed-dask smoke skipped: n-samples must be >= n-clusters',
            file=sys.stderr,
        )
        return 2

    missing = _check_dependencies()
    if missing:
        print('distributed-dask smoke skipped: missing optional dependencies', file=sys.stderr)
        for item in missing:
            print(f' - {item}', file=sys.stderr)
        print('Install the version-matched Dask extras before retrying.', file=sys.stderr)
        return 2

    try:
        n_gpus = _check_cuda()
    except RuntimeError as exc:
        print(f'distributed-dask smoke skipped: {exc}', file=sys.stderr)
        return 2

    if n_gpus < 1:
        print('distributed-dask smoke skipped: no CUDA devices visible', file=sys.stderr)
        return 2

    cluster = None
    client = None
    try:
        cluster, client = _build_cluster(args.device_limit)
        n_workers, n_parts, unique_labels, centers_shape = _run_smoke(
            client, args.n_samples, args.n_clusters
        )
        print(
            'distributed-dask smoke passed: '
            f'workers={n_workers} '
            f'partitions={n_parts} '
            f'samples={args.n_samples} '
            f'clusters={args.n_clusters} '
            f'unique_labels={unique_labels} '
            f'cluster_centers_shape={centers_shape}'
        )
        return 0
    except Exception as exc:
        print(
            f'distributed-dask smoke failed: {exc.__class__.__name__}: {exc}',
            file=sys.stderr,
        )
        return 1
    finally:
        if client is not None:
            client.close()
        if cluster is not None:
            cluster.close()


if __name__ == '__main__':
    raise SystemExit(main())
