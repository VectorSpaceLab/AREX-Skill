#!/usr/bin/env python3
"""Tiny HyperTools install smoke check.

Run this from any clean environment that has HyperTools installed. It checks
basic importability, published defaults, a tiny plot/reduce roundtrip, and a
simple save/load path without relying on the source checkout.
"""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd

try:
    import hypertools as hyp
    from hypertools.core.configurator import get_default_options
except Exception as exc:  # pragma: no cover - exercised in runtime envs
    raise SystemExit(f"unable to import hypertools: {exc}") from exc


def _check_defaults() -> None:
    defaults = get_default_options()
    assert defaults["reduce"], "published defaults did not load"
    assert defaults["plot"], "plot defaults did not load"


def _check_plot_and_reduce() -> None:
    rng = np.random.default_rng(0)
    x = np.cumsum(rng.standard_normal((48, 5)), axis=0)
    fig = hyp.plot(x, '.', reduce='PCA', ndims=2, show=False, backend='matplotlib')
    assert fig is not None
    reduced = np.asarray(hyp.reduce(x, 'PCA', ndims=2))
    assert reduced.shape == (48, 2)


def _check_roundtrip() -> None:
    frame = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    with tempfile.TemporaryDirectory(prefix='hypertools-install-smoke-') as tmp:
        path = Path(tmp) / 'frame.csv'
        hyp.save(frame, path)
        loaded = hyp.load(path)
        pd.testing.assert_frame_equal(loaded, frame)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expect-version', default=None,
                        help='optional exact hypertools version to require')
    args = parser.parse_args()

    if args.expect_version and hyp.__version__ != args.expect_version:
        raise SystemExit(
            f'version mismatch: expected {args.expect_version}, got {hyp.__version__}'
        )

    assert hasattr(hyp, 'plot') and hasattr(hyp, 'load') and hasattr(hyp, 'save')
    assert 'KMeans' in hyp.supported_models()

    _check_defaults()
    _check_plot_and_reduce()
    _check_roundtrip()

    print(f'install smoke ok: hypertools {hyp.__version__}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
