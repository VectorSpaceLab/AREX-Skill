---
name: visualization
description: "Plot, animate, and export HyperTools figures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Visualization

Use this sub-skill when the request is about plotting, rendering, animating,
or exporting HyperTools figures rather than choosing the analysis pipeline.

## Owns
- `hypertools.plot(...)` for static matplotlib plots, plotly renders, and
  animations
- `hypertools.set_interactive_backend(...)` plus `backend='auto'`,
  `'matplotlib'`, and `'plotly'`
- styling, `fmt`, markers, line styles, `palette`, `hue`, `legend`, `names`,
  `labels`, `colorbar`, `title`, and axis-label kwargs
- `surface`, `density`, and `save_path`
- row-MultiIndex plotting behavior in `hyp.plot`
- streaming plot parameters: `stream_init`, `stream_chunk`, `stream_max`,
  and `stream_window`
- `predict=` as a visual overlay only; model selection stays in
  `../forecasting/SKILL.md`
- `return_model=True` plot bundles when the caller wants the fitted plotting
  bundle back

## Route away
- Choose reduction / alignment / clustering / manipulation stages in
  `../pipeline/SKILL.md`
- Resolve loaders, save/load source details, and `hyp.io.lsl_stream` in
  `../io/SKILL.md`
- Choose forecast or imputation models in `../forecasting/SKILL.md`

## Read first
- `./references/plot-reference.md`
- `./references/workflows.md`
- `./references/troubleshooting.md`

## Quick smoke
Run:

```bash
python ./scripts/smoke_plot.py --feature static --backend auto
```

For streaming plots, remember that the backend is always matplotlib.
For animation, plotly returns a `Figure` with frames; matplotlib returns a
`HyperAnimation` or `(fig, ani)`-style result.
