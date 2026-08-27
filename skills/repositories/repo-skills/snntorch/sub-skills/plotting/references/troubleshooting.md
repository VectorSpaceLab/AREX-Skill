# Spikeplot troubleshooting

## `ImportError: No module named matplotlib`

`snntorch.spikeplot` imports `matplotlib.pyplot` at module import time. Install matplotlib in the same Python environment as snnTorch before using this sub-skill. The base package metadata lists `numpy` and `pandas` as core requirements, while spikeplot workflows require matplotlib.

## Headless backend errors or blank windows

Symptoms include `cannot connect to display`, backend selection errors, or plots that hang on a server.

Fix:

1. Set `MPLBACKEND=Agg` in the shell, or call `matplotlib.use("Agg", force=True)` before importing `matplotlib.pyplot`.
2. Do not rely on `plt.show()` in CI/headless scripts.
3. Use `fig.savefig(...)` for persistent outputs and `plt.close(fig)` when done.

## `spike_count` fails with tensor labels

Observed failure pattern:

```text
TypeError: Index(...) must be called with a collection of some kind, tensor(...) was passed
```

Cause: `spike_count` builds a pandas `Series(..., index=labels)`. A torch tensor is not accepted as the label index in this path.

Fix:

```python
labels = [str(i) for i in range(spk_results.shape[1])]
# or, if labels started as a tensor:
labels = list(map(str, label_tensor.detach().cpu().tolist()))
splt.spike_count(spk_results.detach().cpu(), fig, ax, labels=labels)
```

Also ensure `len(labels) == spk_results.shape[1]`.

## Time dimension is not first

Most snnTorch plotting examples record time first. Common model output shape is `[num_steps, batch, num_outputs]`; image spike data may be `[num_steps, batch, channels, height, width]`.

Fix:

- For a class/output spike count: `spk_results = spk_rec[:, sample_idx].detach().cpu()` gives `[T, num_outputs]`.
- For an image-frame animation: `frame_sample = spike_data[:, sample_idx, channel_idx].detach().cpu()` gives `[T, H, W]`.
- For a raster from image-like spikes: `spk_2d = frame_sample.reshape(frame_sample.shape[0], -1)` gives `[T, H*W]`.

Do not pass `[batch, T, ...]` into these helpers unless you first transpose or index it into time-first form.

## `spike_count` receives a CUDA tensor

`raster`, `animator`, and `traces` move tensors to CPU internally, but `spike_count` passes sums through pandas. Passing CUDA tensors can fail or create confusing conversion errors.

Fix:

```python
spk_results = spk_results.detach().cpu()
splt.spike_count(spk_results, fig, ax, labels=labels)
```

## `spike_count` argument mismatch

Check these before debugging the model:

- `data` is 2-D `[num_steps, num_outputs]`, not a full minibatch.
- `labels` is a list/tuple/array, not a torch tensor.
- `len(labels)` equals `num_outputs`.
- `num_steps` is either omitted or matches the intended scan length.
- `animate=True` returns an animation object; `animate=False` draws in-place and returns `None`.

## Animation displays in notebooks but will not save

`animator` and `spike_count(..., animate=True)` return `matplotlib.animation.ArtistAnimation`. Display and saving are handled by matplotlib/IPython, not by snnTorch itself.

Fix:

- Keep the animation assigned to a variable until display/save completes: `anim = ...`.
- In notebooks, use `HTML(anim.to_html5_video())` or another supported IPython display path.
- For `anim.save("file.gif")` or `anim.save("file.mp4")`, confirm the relevant matplotlib writer is installed and configured. MP4 commonly needs an ffmpeg writer; GIF commonly needs a pillow-compatible writer.
- The public docs describe spikeplot as using matplotlib and celluloid-era animation workflows. The current module provides its own `Camera` helper, but notebook environments may still need the broader plotting/animation stack from the docs requirements.

## `traces` index errors or missing subplots

`traces` creates `dim[0] * dim[1]` subplots and indexes `data[:, i]` for each subplot.

Fix:

- Make `data.shape[1]` at least as large as `dim[0] * dim[1]`.
- Prefer exact matches, e.g. six traces with `dim=(2, 3)`.
- If overlaying spikes, ensure `spk.shape == data.shape`.
- Keep `titles` optional, but if provided, make it at least as long as the number of panels you want titled.

## Raster looks crowded or odd for image-like spikes

`raster` is a thin wrapper over `ax.scatter(*torch.where(data.cpu()), **kwargs)`. For classic rasters, pass a 2-D `[T, N]` tensor. If you pass a higher-rank tensor, additional nonzero coordinate arrays are forwarded to matplotlib, which is usually not the intended time-vs-neuron plot.

Fix:

```python
spk_2d = frame_sample.reshape(frame_sample.shape[0], -1)
splt.raster(spk_2d, ax, s=1.5, c="black")
```

## Missing `celluloid`

The inspected `snntorch.spikeplot` module defines its own `Camera` class and does not require direct `from celluloid import Camera` usage in the helper code. However, the public docs and docs requirements mention celluloid as part of the plotting/animation companion stack. If an older environment or notebook example imports `celluloid` directly, install it alongside matplotlib, then rerun the example.
