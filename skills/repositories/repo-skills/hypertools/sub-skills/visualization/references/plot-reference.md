# Plot reference

## Core entry points

- `hypertools.plot.plot(...)` is the main plotting API.
- `hypertools.set_interactive_backend(...)` changes the default renderer or the
  matplotlib GUI backend used for interactive plots.

### Minimal patterns

```python
import hypertools as hyp
fig = hyp.plot(data, fmt='.', backend='auto', show=False)
```

```python
with hyp.set_interactive_backend('plotly'):
    fig = hyp.plot(data, backend='auto', show=False)
```

## Backend selection

- `backend='auto'` is the default. It resolves to plotly on Colab/Kaggle when
  plotly is importable, and matplotlib everywhere else.
- `backend='plotly'` renders an interactive plotly `Figure`.
- `backend='matplotlib'` renders the classic matplotlib figure path.
- `mpl_backend` only matters when a matplotlib GUI backend is needed for an
  interactive display.
- `set_interactive_backend('plotly'|'matplotlib'|'auto'|<mpl backend>)` sets a
  session-level preference. Use it when several plots should share the same
  renderer.

## Major plotting kwargs

| Area | Key kwargs |
| --- | --- |
| Data / stages | `x`, `ndims`, `reduce`, `align`, `cluster`, `manip`, `normalize`, `pipeline`, `resample` |
| Style | `fmt`, `marker(s)`, `linestyle(s)`, `linewidth`, `markersize`, `color(s)`, `palette`, `font`, `title`, `xlabel`, `ylabel`, `zlabel` |
| Grouping / color | `hue`, `color_reduce`, `names`, `legend`, `colorbar`, `labels`, `label_alpha` |
| Motion | `animate`, `duration`, `tail_duration`, `rotations`, `zoom`, `chemtrails`, `precog`, `bullettime`, `focused`, `frame_rate`, `morph_samples` |
| Overlays | `surface`, `density`, `predict`, `t` |
| Export / return | `save_path`, `show`, `return_model` |
| Streaming | `stream_init`, `stream_chunk`, `stream_max`, `stream_window` |

## Behavior notes

### Styling and text
- `fmt='.'`, `fmt='o-'`, and the rest of the matplotlib format grammar work on
  both backends.
- `labels` is per observation, or nested per dataset.
- `names` is per input dataset and is not the same thing as `labels`.
- `label_alpha` controls the label box opacity.
- `title`, `legend`, `labels`, `hue`, and `colorbar` share font resolution.

### Hue and colorbar
- String `hue` values group by category.
- Numeric 1-D `hue` values produce a continuous color map.
- Small-cardinality integer / boolean hues are treated as discrete groups.
- Matrix-valued `hue` blends colors per observation.
- `color_reduce` reduces wide hue matrices to RGB.
- `colorbar=True` needs a real color mapping.
- `colorbar` may be `True` or a dict with `label`, `ticks`, and `location`.

### Layout and output
- `return_model=True` returns a bundle containing `fig`, `xform_data`,
  `animation`, `pipeline`, `models`, and `predict` metadata.
- `predict=` overlays are static-plot only in this release.
- Streaming plots always render with matplotlib, even if a backend is passed.

## Output types to expect

- Static matplotlib: `matplotlib.figure.Figure`
- Static plotly: `plotly.graph_objects.Figure`
- Animated matplotlib: `HyperAnimation` or `(fig, ani)`-style output
- Animated plotly: plotly `Figure` with `frames`
- Streaming: matplotlib `Figure` with `fig.stream_info`

## Fast checks

- Matplotlib static: `fig.axes[0].lines`, `fig.axes[0].get_legend()`
- Plotly static: `fig.data`, `fig.layout`, `fig.frames`
- Streaming: `fig.stream_info['n_samples']`, `fig.stream_info['truncated']`
- Save/export: file exists and is non-empty

## Routing reminders

- If the request is really about stage choice or a fitted pipeline, route to
  `../pipeline/SKILL.md`.
- If the request is about where data comes from or how LSL streams are
  resolved, route to `../io/SKILL.md`.
- If the request is about which forecasting or imputation model to use for
  `predict=` or `impute=`, route to `../forecasting/SKILL.md`.
