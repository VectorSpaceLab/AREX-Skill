# Spikeplot workflows

Use these recipes after a model or encoder has already produced recorded tensors. This sub-skill assumes plotting starts from tensors such as `spk_rec`, `mem_rec`, or a single image-like spike sample. The tutorial 5/6 and quickstart-style loops establish the expected record-then-plot flow.

## 1. Headless script setup

Set the backend before importing `matplotlib.pyplot` when running on CI, SSH sessions, batch jobs, or any host without a GUI display:

```python
import os
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
```

Then create explicit figures/axes and close them when done:

```python
fig, ax = plt.subplots(facecolor="w", figsize=(8, 4))
# call snntorch.spikeplot helper here
fig.savefig("plot.png", dpi=150, bbox_inches="tight")
plt.close(fig)
```

The bundled `scripts/spikeplot_smoke.py` uses this pattern and writes no persistent files by default.

## 2. Raster for time-vs-neuron spikes

Use `raster` when you want a scatter of nonzero spikes across time.

```python
import torch
import matplotlib.pyplot as plt
import snntorch.spikeplot as splt

# One sample, time first: [num_steps, num_neurons]
spk_sample = spk_rec[:, sample_idx].detach().cpu()
spk_2d = spk_sample.reshape(spk_sample.shape[0], -1)

fig, ax = plt.subplots(facecolor="w", figsize=(10, 5))
splt.raster(spk_2d, ax, s=1.5, c="black")
ax.set_title("Input or hidden-layer spikes")
ax.set_xlabel("Time step")
ax.set_ylabel("Neuron number")
```

Notes:

- Time must be axis 0.
- For image-like spikes, flatten trailing spatial dimensions before `raster` if you want a clean time-vs-pixel/neuron view.
- `raster` forwards style keywords directly to matplotlib `scatter`.

## 3. Spike-count panel for output spikes

Use `spike_count` for class/output-neuron count plots after a forward pass.

```python
import matplotlib.pyplot as plt
import snntorch.spikeplot as splt

# spk_rec from a model usually has shape [num_steps, batch, num_outputs].
spk_results = spk_rec[:, sample_idx].detach().cpu()
labels = [str(i) for i in range(spk_results.shape[1])]

fig, ax = plt.subplots(facecolor="w", figsize=(12, 7))
splt.spike_count(
    spk_results,
    fig,
    ax,
    labels=labels,
    num_steps=spk_results.shape[0],
    time_step=1e-3,
)
```

Notes:

- `labels` must be list-like; convert tensor labels with `.tolist()` or `list(map(str, tensor.tolist()))`.
- Use a CPU tensor. The docs examples detach and move to CPU before calling `spike_count`.
- `time_step` changes the x-axis label from steps to seconds.

## 4. Animated spike-count notebook view

In notebooks, keep the animation object in scope and display it explicitly:

```python
from IPython.display import HTML

fig, ax = plt.subplots(facecolor="w", figsize=(12, 7))
labels = [str(i) for i in range(spk_results.shape[1])]

anim = splt.spike_count(
    spk_results,
    fig,
    ax,
    labels=labels,
    animate=True,
    interpolate=4,
)
HTML(anim.to_html5_video())
# anim.save("spike_bar.mp4")  # requires an available matplotlib animation writer
```

Use smaller `num_steps` and lower `interpolate` values while iterating. If saving fails, check writer availability before changing spike data.

## 5. Trace grid with optional spike overlay

Use `traces` to inspect membrane potential or synaptic current traces. The optional `spk` overlay adds vertical spike markers by plotting `data + spk_height * spk`.

```python
import matplotlib.pyplot as plt
import snntorch.spikeplot as splt

# Time first: [num_steps, num_neurons]
trace_sample = mem_rec[:, sample_idx, :6].detach().cpu()
spike_overlay = spk_rec[:, sample_idx, :6].detach().cpu()

plt.figure(facecolor="w", figsize=(9, 5))
splt.traces(
    trace_sample,
    spk=spike_overlay,
    dim=(2, 3),
    spk_height=5,
    titles=[f"n{i}" for i in range(6)],
)
```

Notes:

- Choose `dim` so `rows * cols` equals the number of trace columns you want to plot.
- `data` and `spk` should have matching shapes when overlaying spikes.
- Non-square grids such as `(2, 3)` are fine when the neuron count matches.

## 6. Image-like spike-frame animation

Use `animator` for one sample of image-like spikes across time.

```python
from IPython.display import HTML
import matplotlib.pyplot as plt
import snntorch.spikeplot as splt

# Example source shape might be [num_steps, batch, channels, height, width].
frame_sample = spike_data[:, sample_idx, channel_idx].detach().cpu()

fig, ax = plt.subplots(facecolor="w")
anim = splt.animator(frame_sample, fig, ax, interval=40, cmap="plasma")
HTML(anim.to_html5_video())
# anim.save("spike_frames.gif")
```

Notes:

- `frame_sample` should be `[T, H, W]`; each time slice is passed to `imshow`.
- Saving GIF/MP4 files depends on matplotlib animation writers available in the environment.
- In non-notebook scripts, use `anim.save(...)` only after confirming a writer is installed, or treat successful construction of `ArtistAnimation` as the smoke check.

## 7. Run the bundled smoke

From the plotting sub-skill directory:

```bash
MPLBACKEND=Agg python scripts/spikeplot_smoke.py
```

Expected output includes `spikeplot smoke ok` and summary lines for raster, spike-count, traces, and animation construction.
