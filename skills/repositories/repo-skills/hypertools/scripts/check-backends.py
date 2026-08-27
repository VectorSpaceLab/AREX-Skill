#!/usr/bin/env python3
"""Optional HyperTools backend smoke checks.

Use this helper when you want to verify optional runtime extras one at a time
without running the repo's full native test suite.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import tempfile
import threading
import time
import warnings
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import hypertools as hyp


def _module_name(obj) -> str:
    return type(obj).__module__


def _walk(n: int = 90, d: int = 3, seed: int = 0):
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.standard_normal((n, d)), axis=0)


def _blobs(seed: int = 1):
    rng = np.random.default_rng(seed)
    a = rng.standard_normal((120, 3)) * 0.6
    b = rng.standard_normal((120, 3)) * 0.6 + [3.5, 0, 0]
    return [a, b]


def _corpus():
    return [
        'cats purr on warm windowsills',
        'dogs fetch balls in the park',
        'astronomers track distant galaxies',
        'puppies learn sit stay and come',
    ]


def _check_plotly(require: bool) -> bool:
    if importlib.util.find_spec('plotly') is None:
        msg = 'plotly not installed'
        if require:
            raise SystemExit(msg)
        print(f'skip plotly: {msg}')
        return True
    with hyp.set_interactive_backend('plotly'):
        fig = hyp.plot(_walk(), backend='auto', show=False)
    assert _module_name(fig).startswith('plotly')
    print('ok plotly backend')
    return True


def _check_gensim(require: bool) -> bool:
    if importlib.util.find_spec('gensim') is None:
        msg = 'gensim not installed'
        if require:
            raise SystemExit(msg)
        print(f'skip gensim: {msg}')
        return True
    from hypertools.tools import text2mat

    mat = text2mat([
        _corpus(),
    ], vectorizer='Word2Vec', semantic=None, corpus=_corpus())[0]
    assert np.asarray(mat).shape == (4, 100)
    print('ok gensim text')
    return True


def _start_local_outlet(name: str, n_channels: int = 4):
    import pylsl

    info = pylsl.StreamInfo(name, 'EEG', n_channels, 100.0, 'float32',
                            f'hypertools-backend-smoke-{name}')
    outlet = pylsl.StreamOutlet(info)
    stop = threading.Event()

    def _push() -> None:
        i = 0
        while not stop.is_set():
            sample = [float(i) + 0.1 * c for c in range(n_channels)]
            outlet.push_sample(sample)
            i += 1
            time.sleep(0.01)

    thread = threading.Thread(target=_push, daemon=True)
    thread.start()
    return stop, thread


def _check_lsl(require: bool) -> bool:
    if importlib.util.find_spec('pylsl') is None:
        msg = 'pylsl not installed'
        if require:
            raise SystemExit(msg)
        print(f'skip lsl: {msg}')
        return True
    from hypertools.io.streaming import is_stream

    name = f'hypertools-backend-smoke-{time.time_ns()}'
    try:
        stop, thread = _start_local_outlet(name)
    except Exception as exc:
        if require:
            raise SystemExit(f'lsl outlet unavailable: {exc}') from exc
        print(f'skip lsl: outlet unavailable: {exc}')
        return True
    try:
        time.sleep(0.25)
        stream = hyp.io.lsl_stream(name=name, timeout=5.0)
        assert is_stream(stream)
        sample = next(stream)
        assert len(sample) == 4
        if hasattr(stream, 'close'):
            stream.close()
    except Exception as exc:
        if require:
            raise SystemExit(f'lsl smoke failed: {exc}') from exc
        print(f'skip lsl: smoke failed: {exc}')
        return True
    finally:
        stop.set()
        thread.join(timeout=5.0)
    print('ok lsl local smoke')
    return True


def _check_density3d(require: bool) -> bool:
    if importlib.util.find_spec('skimage') is None:
        msg = 'scikit-image not installed'
        if require:
            raise SystemExit(msg)
        print(f'skip density3d: {msg}')
        return True
    blobs = _blobs()
    density_fig = hyp.plot(blobs, '.', density=True, backend='matplotlib', show=False)
    surface_fig = hyp.plot(blobs, '.', surface=True, backend='matplotlib', show=False)
    assert density_fig.axes[0].collections
    assert surface_fig.axes[0].collections
    print('ok density3d')
    plt.close('all')
    return True


def _check_xlsx(require: bool) -> bool:
    if importlib.util.find_spec('openpyxl') is None:
        msg = 'openpyxl not installed'
        if require:
            raise SystemExit(msg)
        print(f'skip xlsx: {msg}')
        return True
    frame = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    with tempfile.TemporaryDirectory(prefix='hypertools-backend-smoke-') as tmp:
        path = Path(tmp) / 'frame.xlsx'
        hyp.save(frame, path)
        loaded = hyp.load(path)
        pd.testing.assert_frame_equal(loaded, frame)
    print('ok xlsx')
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all', action='store_true',
                        help='run every optional backend smoke')
    parser.add_argument('--plotly', action='store_true', help='check plotly rendering')
    parser.add_argument('--gensim', action='store_true', help='check gensim text wrappers')
    parser.add_argument('--lsl-local', action='store_true', help='check a local pylsl outlet/inlet')
    parser.add_argument('--density3d', action='store_true', help='check 3-D density and surface rendering')
    parser.add_argument('--xlsx', action='store_true', help='check xlsx save/load support')
    parser.add_argument('--require', action='store_true',
                        help='fail instead of skipping when an optional dependency is missing')
    args = parser.parse_args()

    selected = []
    flags = {
        'plotly': args.plotly,
        'gensim': args.gensim,
        'lsl_local': args.lsl_local,
        'density3d': args.density3d,
        'xlsx': args.xlsx,
    }
    if args.all or not any(flags.values()):
        selected = list(flags)
    else:
        selected = [name for name, enabled in flags.items() if enabled]

    checks = {
        'plotly': _check_plotly,
        'gensim': _check_gensim,
        'lsl_local': _check_lsl,
        'density3d': _check_density3d,
        'xlsx': _check_xlsx,
    }

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for name in selected:
            checks[name](args.require)

    print('backend smoke complete')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
