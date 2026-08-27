#!/usr/bin/env python3
"""Tiny CPU smoke for the HyperTools pipeline workflow.

Exercises manip -> normalize -> reduce -> align -> cluster plus fitted
pipeline reuse via `analyze(..., pipeline=...)`.
"""

from __future__ import annotations

import numpy as np

import hypertools as hyp


def _paired_subjects(seed: int, n_rows: int = 12, n_cols: int = 6):
    """Two small subject-like datasets with shared latent structure."""
    rng = np.random.default_rng(seed)
    latent = rng.normal(size=(n_rows, 3))
    proj_a = rng.normal(size=(3, n_cols))
    proj_b = rng.normal(size=(3, n_cols))
    noise_a = 0.05 * rng.normal(size=(n_rows, n_cols))
    noise_b = 0.05 * rng.normal(size=(n_rows, n_cols))
    return [latent @ proj_a + noise_a, latent @ proj_b + noise_b]


def main() -> int:
    train = _paired_subjects(0)
    held_out = _paired_subjects(1)

    result, pipeline = hyp.analyze(
        train,
        manip={'model': 'Smooth', 'kwargs': {'kernel_width': 5}},
        normalize='across',
        reduce='PCA',
        ndims=2,
        align={'model': 'HyperAlign', 'kwargs': {'n_iter': 2}},
        cluster={'model': 'GaussianMixture', 'kwargs': {
            'n_components': 2,
            'random_state': 0,
            'max_iter': 25,
        }},
        random_state=0,
        return_model=True,
        internal=True,
    )

    assert isinstance(pipeline, hyp.Pipeline)
    assert pipeline.is_fitted
    assert [name for name, _ in pipeline.steps] == [
        'manip', 'normalize', 'reduce', 'align', 'cluster'
    ]
    assert isinstance(result, list) and len(result) == 2
    assert all(np.asarray(piece).shape == (12, 2) for piece in result)

    cluster_probs = np.asarray(
        pipeline.named_steps['cluster'].transform(np.vstack(result))
    )
    assert cluster_probs.shape == (24, 2)
    assert np.allclose(cluster_probs.sum(axis=1), 1.0, atol=1e-6)

    reused, reused_pipeline = hyp.analyze(
        held_out,
        pipeline=pipeline,
        return_model=True,
        internal=True,
    )
    assert reused_pipeline is pipeline
    assert isinstance(reused, list) and len(reused) == 2
    assert all(np.asarray(piece).shape == (12, 2) for piece in reused)

    reused_probs = np.asarray(
        pipeline.named_steps['cluster'].transform(np.vstack(reused))
    )
    assert reused_probs.shape == (24, 2)
    assert np.allclose(reused_probs.sum(axis=1), 1.0, atol=1e-6)

    print(
        'pipeline smoke ok:',
        [np.asarray(piece).shape for piece in result],
        'reuse:',
        [np.asarray(piece).shape for piece in reused],
        'cluster_probs:',
        cluster_probs.shape,
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
