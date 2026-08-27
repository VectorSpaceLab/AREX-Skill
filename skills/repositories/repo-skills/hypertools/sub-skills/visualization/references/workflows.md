# Visualization workflows

These are the bundled recipes this sub-skill should be able to drive without
reopening the source repository.

## 1) Static plot

Use when you need a plain figure with labels or color mapping.

```python
import numpy as np
import hypertools as hyp

def walk(n=90, d=2, seed=0):
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.standard_normal((n, d)), axis=0)

data = walk()
hue = np.linspace(0.0, 1.0, len(data))
labels = [f'pt-{i}' if i in {0, len(data)//2, len(data)-1} else None
          for i in range(len(data))]

fig = hyp.plot(data, fmt='-', hue=hue, labels=labels, colorbar=True,
               title='static smoke', backend='auto', show=False)
```

Validate:
- matplotlib: `fig.axes[0].lines` exists
- plotly: `fig.data` exists
- continuous hue + colorbar should preserve the mapping

## 2) Interactive plotly

Use when the caller wants the plotly renderer or a notebook-friendly render.

```python
with hyp.set_interactive_backend('plotly'):
    fig = hyp.plot(data, backend='auto', show=False)
```

Validate:
- returned figure module starts with `plotly`
- `backend='auto'` respects the backend preference context

## 3) Animation

Use `animate='spin'` for rotating 3-D views, `animate=True` / `'parallel'`
for sliding trajectories, `animate='serial'` for one dataset at a time, and
`animate='window'` for a moving fixed-length window.

```python
result = hyp.plot(data, animate='spin', duration=1, frame_rate=5,
                  backend='auto', show=False)
```

Validate:
- plotly: `len(result.frames) > 0`
- matplotlib: a `HyperAnimation` / `(fig, ani)` result is returned

## 4) Density and surface

Use when the visual question is "where is the cloud dense?" or "wrap the
cloud with a hull".

```python
import numpy as np
rng = np.random.default_rng(1)
blob_a = rng.standard_normal((120, 3)) * 0.6
blob_b = rng.standard_normal((120, 3)) * 0.6 + [3.5, 0, 0]

fig_density = hyp.plot([blob_a, blob_b], '.', density=True,
                       backend='auto', show=False)
fig_surface = hyp.plot([blob_a, blob_b], '.', surface=True,
                       backend='auto', show=False)
```

Validate:
- 2-D density: images / contour layers appear
- 3-D density: fog or volume / iso-surface layers appear
- surface: 2-D fill or 3-D mesh appears

## 5) MultiIndex rows

Use when a DataFrame index encodes nested groups and the plot should show leaf
traces plus per-level averages.

```python
import pandas as pd

df = ...  # row MultiIndex with at least 2 levels
fig = hyp.plot(df, fmt='.', legend=True, colorbar=True,
               backend='auto', show=False)
```

Validate:
- top-level labels drive the legend
- MultiIndex owns the color/linewidth/alpha layout
- `hue=` is ignored and `cluster=` / `n_clusters=` should fail

## 6) Streaming

Use for iterators, generators, or streaming datasets.

```python
def stream():
    rng = np.random.default_rng(4)
    p = np.zeros(3)
    while True:
        p = p + 0.05 * rng.standard_normal(3)
        yield p

fig = hyp.plot(stream(), stream_init=50, stream_chunk=20,
               stream_window=80, stream_max=150, show=False)
```

Validate:
- `fig.stream_info['n_samples']` matches the consumed count
- `fig.stream_info['truncated']` tells you whether the stream was capped
- `align` and `cluster` are not supported for streams

## 7) save_path

Use when the output must land on disk.

```python
from pathlib import Path
import tempfile

tmpdir = Path(tempfile.mkdtemp(prefix='hypertools-plot-'))

png = tmpdir / 'figure.png'
html = tmpdir / 'figure.html'

hyp.plot(data, backend='matplotlib', save_path=png, show=False)
hyp.plot(data, backend='plotly', save_path=html, show=False)
```

Validate:
- files exist and are non-empty
- `.html` keeps plotly interactivity
- plotly raster / video exports need Chrome or Chromium with kaleido
- `.mp4` / `.mov` / `.avi` / `.mkv` need ffmpeg when written by matplotlib

## 8) Forecast overlay

Use when the plot should show a dashed continuation of each trajectory.

```python
fig = hyp.plot(data, predict='GaussianProcess', t=10,
               backend='auto', show=False)
```

Validate:
- the forecast trace is added after the data trace(s)
- `predict=` is static-plot only in this release
- if the user wants a different model, route that choice to
  `../forecasting/SKILL.md`
