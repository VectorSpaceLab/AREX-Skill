#!/usr/bin/env python3
"""Tiny self-contained HyperTools visualization smoke helper.

The goal is to exercise the visualization surface without depending on any
external example files.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import tempfile
import warnings

import matplotlib
matplotlib.use("Agg")
os.environ.setdefault("HYPERTOOLS_BACKEND", "Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    import hypertools as hyp
except ModuleNotFoundError as exc:
    if exc.name != "hypertools":
        raise
    raise SystemExit(
        "This smoke helper requires HyperTools in the active Python "
        "environment. Install it with `pip install hypertools` or run from "
        "an environment where `import hypertools` succeeds."
    ) from exc

FEATURES = (
    "static",
    "interactive",
    "animate",
    "density-surface",
    "multiindex",
    "streaming",
    "save-path",
    "forecast-overlay",
)
BACKENDS = ("auto", "matplotlib", "plotly")


def walk(n=90, d=2, seed=0):
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.standard_normal((n, d)), axis=0)


def blobs_3d(seed=1):
    rng = np.random.default_rng(seed)
    a = rng.standard_normal((120, 3)) * 0.6
    b = rng.standard_normal((120, 3)) * 0.6 + [3.5, 0, 0]
    return [a, b]


def multiindex_df(seed=2):
    rng = np.random.default_rng(seed)
    rows = []
    tuples = []
    for group in ("A", "B"):
        for subject in ("s1", "s2"):
            pts = np.cumsum(rng.standard_normal((20, 3)), axis=0)
            rows.append(pts + (0 if group == "A" else 4))
            tuples.extend([(group, subject)] * len(pts))
    data = np.vstack(rows)
    index = pd.MultiIndex.from_tuples(tuples, names=["group", "subject"])
    return pd.DataFrame(data, index=index, columns=["x", "y", "z"])


def stream_rows(seed=3):
    rng = np.random.default_rng(seed)
    point = np.zeros(3)
    while True:
        point = point + 0.05 * rng.standard_normal(3)
        yield point.copy()


def normalize_animation_result(result):
    if isinstance(result, tuple) and len(result) == 2:
        return result
    fig = getattr(result, "figure", result)
    ani = getattr(result, "animation", None)
    return fig, ani


def module_name(obj):
    return type(obj).__module__


def run_static(backend):
    data = walk()
    hue = np.linspace(0.0, 1.0, len(data))
    labels = [f"pt-{i}" if i in {0, len(data) // 2, len(data) - 1}
              else None for i in range(len(data))]
    fig = hyp.plot(data, fmt='-', hue=hue, labels=labels, colorbar=True,
                   title='static smoke', backend=backend, show=False)
    if module_name(fig).startswith("plotly"):
        assert fig.data, "expected plotly traces"
    else:
        assert fig.axes and (fig.axes[0].lines or fig.axes[0].collections), \
            "expected matplotlib artists"
    print(f"static ok: {module_name(fig)}")
    plt.close('all')


def run_interactive(backend):
    data = walk(d=3, seed=1)
    with hyp.set_interactive_backend(backend):
        fig = hyp.plot(data, backend='auto', show=False)
    if backend == 'plotly':
        assert module_name(fig).startswith('plotly')
    elif backend == 'matplotlib':
        assert module_name(fig).startswith('matplotlib')
    print(f"interactive ok: {module_name(fig)}")
    plt.close('all')


def run_animate(backend):
    data = walk(d=3, seed=4)
    result = hyp.plot(data, animate='spin', duration=1, frame_rate=5,
                      backend=backend, show=False)
    fig, ani = normalize_animation_result(result)
    if module_name(fig).startswith('plotly'):
        assert len(fig.frames) > 0
        print(f"animate ok: plotly frames={len(fig.frames)}")
    else:
        assert ani is not None
        save_count = getattr(ani, '_save_count', None)
        print(f"animate ok: matplotlib save_count={save_count}")
    plt.close('all')


def run_density_surface(backend):
    data = blobs_3d()
    density_fig = hyp.plot(data, '.', density=True, backend=backend,
                           show=False)
    surface_fig = hyp.plot(data, '.', surface=True, backend=backend,
                           show=False)
    if module_name(density_fig).startswith('plotly'):
        assert density_fig.data
        assert surface_fig.data
    else:
        assert density_fig.axes[0].collections
        assert surface_fig.axes[0].collections
    print(f"density/surface ok: {module_name(density_fig)}")
    plt.close('all')


def run_multiindex(backend):
    df = multiindex_df()
    fig = hyp.plot(df, fmt='.', legend=True, colorbar=True, backend=backend,
                   show=False)
    if module_name(fig).startswith('plotly'):
        assert fig.data
    else:
        assert fig.axes[0].get_legend() is not None
    print(f"multiindex ok: {module_name(fig)}")
    plt.close('all')


def run_streaming(_backend):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        fig = hyp.plot(stream_rows(), stream_init=40, stream_chunk=20,
                       stream_window=30, stream_max=120, show=False)
    assert fig.stream_info['n_samples'] == 120
    assert fig.stream_info['truncated'] is True
    print("streaming ok: n_samples=120 truncated=True")
    plt.close('all')


def run_save_path(_backend):
    data = walk(d=3, seed=6)
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix='hypertools-plot-smoke-'))
    png = tmpdir / 'figure.png'
    html = tmpdir / 'figure.html'
    hyp.plot(data, backend='matplotlib', save_path=png, show=False)
    hyp.plot(data, backend='plotly', save_path=html, show=False)
    assert png.exists() and png.stat().st_size > 0
    assert html.exists() and html.stat().st_size > 0
    print(f"save-path ok: {png} {html}")
    plt.close('all')


def run_forecast_overlay(backend):
    data = walk(seed=7)
    fig = hyp.plot(data, predict='GaussianProcess', t=10,
                   backend=backend, show=False)
    if module_name(fig).startswith('plotly'):
        assert len(fig.data) >= 2
    else:
        assert len(fig.axes[0].lines) >= 2
    print(f"forecast ok: {module_name(fig)}")
    plt.close('all')


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', choices=BACKENDS, default='auto',
                        help='renderer preference for backend-aware cases')
    parser.add_argument('--feature', choices=FEATURES, required=True,
                        help='smoke scenario to run')
    return parser.parse_args()


def main():
    args = parse_args()
    runners = {
        'static': run_static,
        'interactive': run_interactive,
        'animate': run_animate,
        'density-surface': run_density_surface,
        'multiindex': run_multiindex,
        'streaming': run_streaming,
        'save-path': run_save_path,
        'forecast-overlay': run_forecast_overlay,
    }
    runners[args.feature](args.backend)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
