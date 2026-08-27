# Visualization troubleshooting

## Plotly backend import or fallback

**Symptom:** `The plotly backend requires plotly` or `set_interactive_backend('plotly')` warns and falls back.

**Fix:** install the interactive extra.

```bash
pip install "hypertools[interactive]"
```

**Check:**

```bash
python -c "import plotly, hypertools; print(plotly.__version__)"
```

## Plotly image / movie export fails

**Symptom:** saving plotly output to PNG / GIF / MP4 / MOV / AVI complains about
Chrome, Chromium, or kaleido.

**Fix:** install Chrome or Chromium, or use HTML export if you only need an
interactive file. For headless static export, plotly relies on kaleido.

```bash
plotly_get_chrome
```

If that is not available, install Chrome / Chromium with your system package
manager.

## FFmpeg missing

**Symptom:** saving matplotlib animations to video containers fails with an
ffmpeg error.

**Fix:** install `ffmpeg` and put it on `PATH`.

**Fallback:** use `.gif` or `.html` instead.

## save_path problems

**Symptom:** `save_path` raises `TypeError`, `ValueError`, or `PermissionError`.

**Likely cause / fix:**
- empty or non-string path -> pass a real string or path-like object
- path points to an existing directory -> use a filename instead
- missing parent directory -> create the directory first
- read-only target -> switch to a writable temp directory
- unsupported extension -> choose a supported export format

## Labels, hue, colorbar, and MultiIndex

**Symptom:** labels disappear, hue collapses unexpectedly, or the colorbar does
not look right.

**Likely cause / fix:**
- `labels` length must match the number of observations
- `hue` is positional, not index-based
- numeric 1-D hue is continuous, small-cardinality integer / boolean hue is
  categorical
- matrix hue blends colors per observation and may not support a colorbar
- `colorbar=True` needs a real color mapping
- `names` is per input dataset and cannot be combined with categorical hue
- row-MultiIndex expansion owns color / linewidth / alpha; `hue=` is ignored

## Density and surface

**Symptom:** `surface=` or `density=` raises for 1-D data, or a 2-D animated
surface does nothing.

**Likely cause / fix:**
- `surface` and `density` are for 2-D or 3-D plots only
- 1-D data needs `ndims=2` or `ndims=3`
- animated 2-D surfaces are a no-op in this release
- degenerate / collinear / coplanar inputs may warn and skip the overlay
- 3-D density iso-surfaces need the `hypertools[density3d]` extra / scikit-image;
  without it, expect a fog fallback or a warning

## Streaming parameters

**Symptom:** stream plots stop early, clamp badly, or reject the arguments.

**Likely cause / fix:**
- `stream_init`, `stream_chunk`, `stream_max`, and `stream_window` must be
  positive integers when provided
- a stream must yield numeric rows
- streamed trajectories need at least two features / channels
- `align` and `cluster` are not supported for streaming plots
- if the cloud drifts outside the head-fitted box, increase `stream_init`

## Backend import and interactive display

**Symptom:** a matplotlib interactive plot behaves strangely in scripts or
notebooks.

**Likely cause / fix:**
- `backend='plotly'` / `'matplotlib'` are renderer choices, not GUI backend names
- `mpl_backend` only matters for interactive matplotlib display
- `set_interactive_backend('auto')` restores backend auto-detection
- use `show=False` for smoke tests and batch export

## Forecast overlay

**Symptom:** `predict=` fails when combined with animation.

**Fix:** `predict=` is static-only in this release. Remove `animate` or make a
separate static overlay plot. If you need the model reused later, request
`return_model=True` and inspect `bundle['predict']`.
