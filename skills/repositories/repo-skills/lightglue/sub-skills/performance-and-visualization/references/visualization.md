# LightGlue visualization helpers

The `viz2d` helpers work by mutating the current Matplotlib figure. The common
pattern is:

```python
from lightglue import viz2d

viz2d.plot_images([image0, image1], titles=["left", "right"])
viz2d.plot_matches(m_kpts0, m_kpts1, color="lime", lw=0.2)
viz2d.add_text(0, f'Stop after {matches01["stop"]} layers', fs=20)
viz2d.save_plot("matches.png", dpi=200)
```

For pruning overlays, color the keypoints with `viz2d.cm_prune(...)` and call
`plot_keypoints` after `plot_images`.

## API synopsis

| Helper | Signature | Use |
| --- | --- | --- |
| `plot_images` | `plot_images(imgs, titles=None, cmaps="gray", dpi=100, pad=0.5, adaptive=True)` | Draws a horizontal strip of images and prepares the active figure |
| `plot_keypoints` | `plot_keypoints(kpts, colors="lime", ps=4, axes=None, a=1.0)` | Overlays keypoints on the current images |
| `plot_matches` | `plot_matches(kpts0, kpts1, color=None, lw=1.5, ps=4, a=1.0, labels=None, axes=None)` | Connects corresponding points between the two image panels |
| `cm_prune` | `cm_prune(x_)` | Converts LightGlue prune-step indices into colors |
| `add_text` | `add_text(idx, text, pos=(0.01, 0.99), fs=15, color="w", lcolor="k", lwidth=2, ha="left", va="top")` | Adds outlined text to one subplot |
| `save_plot` | `save_plot(path, **kw)` | Saves the active figure tightly cropped, without white margins |

## Inputs and color conventions

- `plot_images` accepts NumPy arrays or PyTorch tensors in RGB or grayscale.
- `plot_keypoints` and `plot_matches` accept NumPy arrays or PyTorch tensors.
- If `color` is omitted in `plot_matches`, the matches are colored by source
  position using a 2D gradient.
- `cm_prune` is designed for the raw `prune0` / `prune1` arrays returned by
  LightGlue.
- Larger `prune` values mean the point survived longer during pruning.

## Headless and saved-plot guidance

- Use `save_plot` when you want a figure suitable for docs or papers.
- In headless sessions, do not rely on an interactive window.
- If you are writing your own script, set a non-interactive Matplotlib backend
  before importing `pyplot`, or use the benchmark script's `--no-show` and
  `--save` options.
- Call `save_plot` before `plt.close()`.

## Useful recipes

### Matches with a stop-layer label

```python
viz2d.plot_images([image0, image1])
viz2d.plot_matches(m_kpts0, m_kpts1, color="lime", lw=0.2, ps=3)
viz2d.add_text(0, f"Stopped after {matches01['stop']} layers")
```

### Pruning heatmap

```python
kpc0 = viz2d.cm_prune(matches01["prune0"])
kpc1 = viz2d.cm_prune(matches01["prune1"])
viz2d.plot_images([image0, image1])
viz2d.plot_keypoints([kpts0, kpts1], colors=[kpc0, kpc1], ps=8)
```

### Publication-style save

```python
viz2d.plot_images([image0, image1], adaptive=True)
viz2d.plot_matches(m_kpts0, m_kpts1, lw=0.15)
viz2d.save_plot("lightglue_matches.pdf")
```
