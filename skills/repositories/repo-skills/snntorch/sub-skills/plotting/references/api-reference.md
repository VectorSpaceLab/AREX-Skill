# snnTorch spikeplot API reference

Evidence was distilled from the public `snntorch.spikeplot` module, the generated `snntorch.spikeplot` docs page, and the `docs/examples/example_splt/` raster, spike-count, traces, and animation examples. Signatures below were checked against the installed snnTorch 1.0.0 API.

## Tensor conventions

| Workflow | Preferred input shape | Notes |
| --- | --- | --- |
| Raster | `[num_steps, num_neurons]` | Time is axis 0. If spikes are image-like (`[T, H, W]`), flatten trailing dimensions to `[T, H*W]` for a conventional time-vs-neuron raster. |
| Spike count | `[num_steps, num_outputs]` | Use one sample's output spikes, e.g. `spk_rec[:, sample_idx].detach().cpu()`. Labels must be list-like and match `num_outputs`. |
| Traces | `[num_steps, num_neurons]` | `data` holds membrane/current traces. Optional `spk` overlay must have the same shape. `dim[0] * dim[1]` should match the number of plotted neurons. |
| Animator | `[num_steps, height, width]` | Use one sample of image-like spike frames. `data[step]` is passed to `ax.imshow`. |

CPU notes: `raster`, `animator`, and `traces` move tensors to CPU internally. `spike_count` passes summed tensors through pandas, so pass a detached CPU tensor.

## `raster`

```python
snntorch.spikeplot.raster(data, ax, **kwargs)
```

| Argument | Meaning |
| --- | --- |
| `data` | Spike tensor. Use time-first `[T, N]` for a classic raster. 1-D input is treated as `[T, 1]`. |
| `ax` | Matplotlib axes that receives the scatter plot. |
| `**kwargs` | Forwarded to `matplotlib.axes.Axes.scatter`; common examples are `s`, `c`, and `marker`. |

Behavior:

- Draws nonzero coordinates from `torch.where(data.cpu())` with `ax.scatter(...)`.
- Returns the matplotlib `PathCollection` from `scatter`.
- Does not create a figure or labels for you; set titles, `xlabel`, `ylabel`, and save/display with matplotlib.

## `animator`

```python
snntorch.spikeplot.animator(data, fig, ax, num_steps=False, interval=40, cmap="plasma")
```

| Argument | Meaning |
| --- | --- |
| `data` | Time-first image-like tensor; each `data[step]` should be 2-D for `imshow`. |
| `fig` | Matplotlib figure used to build the animation. |
| `ax` | Matplotlib axes used for each frame. |
| `num_steps` | Number of frames. If `False`, uses `data.size()[0]`. |
| `interval` | Delay between frames in milliseconds. Default: `40`. |
| `cmap` | Matplotlib colormap passed to `imshow`. Default: `"plasma"`. |

Behavior:

- Moves `data` to CPU, hides axes with `plt.axis("off")`, and snapshots each frame.
- Returns a `matplotlib.animation.ArtistAnimation`.
- The animation object must stay referenced until it is displayed or saved.

## `spike_count`

```python
snntorch.spikeplot.spike_count(
    data,
    fig,
    ax,
    labels,
    num_steps=False,
    animate=False,
    interpolate=1,
    gridshader=True,
    interval=25,
    time_step=False,
)
```

| Argument | Meaning |
| --- | --- |
| `data` | CPU spike tensor for one sample, shape `[T, num_outputs]`. |
| `fig` | Matplotlib figure used for the plot or animation. |
| `ax` | Matplotlib axes receiving the horizontal count plot. |
| `labels` | Python list/tuple/array of output labels. Length should equal `num_outputs`; torch tensors are not accepted by pandas as an index here. |
| `num_steps` | Count/scan length. If `False`, uses `data.size()[0]`. |
| `animate` | If `False`, draws the final count plot in-place and returns `None`. If `True`, returns an `ArtistAnimation`. |
| `interpolate` | Animation interpolation factor; `1` means no extra frames, `5` means four inserted frames per step. |
| `gridshader` | Adds alternating background shading when `True`. |
| `interval` | Delay between animation frames in milliseconds. Default: `25`. |
| `time_step` | If provided, scales the x-axis from step indices to seconds and labels it `Time [s]`. |

Behavior:

- Counts spikes with `data[:idx].sum(dim=0)` and draws horizontal lines/dots for each label.
- Uses pandas internally to associate counts with `labels`; convert tensor labels with `.tolist()` first.
- For notebook animation, assign the returned animation to a variable, then display with IPython HTML helpers or save with a matplotlib writer.

## `traces`

```python
snntorch.spikeplot.traces(data, spk=None, dim=(3, 3), spk_height=5, titles=None)
```

| Argument | Meaning |
| --- | --- |
| `data` | Trace tensor such as membrane potential or synaptic current, shape `[T, N]`. |
| `spk` | Optional spike overlay tensor, same shape as `data`. When present, the plotted value is `data + spk_height * spk`. |
| `dim` | Subplot grid `(rows, cols)`. The product should match the number of plotted neurons. |
| `spk_height` | Height added for overlay spikes. Default: `5`. |
| `titles` | Optional list of subplot titles; titles are used where provided. |

Behavior:

- Uses `matplotlib.gridspec.GridSpec(*dim)` and creates one subplot per grid cell.
- Detaches tensors, moves them to CPU, converts to NumPy, then calls `ax.plot(data[:, i])`.
- Returns `None` and relies on the active matplotlib figure; create/select a figure before calling if the surrounding code manages multiple figures.
