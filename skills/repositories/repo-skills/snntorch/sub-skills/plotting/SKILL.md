---
name: plotting
description: "Plot raster, spike-count, trace, and animation views for
  time-first snnTorch spike tensors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Plotting

Use this sub-skill when the task is to visualize spike tensors with `snntorch.spikeplot` helpers rather than to train, encode, load datasets, or exchange NIR graphs.

## Route here for

- Raster plots from time-first binary spike tensors with `spikeplot.raster`.
- Output-neuron spike-count panels and spike-count animations with `spikeplot.spike_count`.
- Membrane/current traces, optionally with spike overlays, using `spikeplot.traces`.
- Image-like spike-frame animations with `spikeplot.animator` in notebooks or scripts.
- Headless matplotlib setup for CI, SSH, and batch jobs.

## Do not handle here

- Training loops, losses, surrogate gradients, or `utils.reset`: route to `encoding-training`.
- Spike encoding from raw data with `spikegen`: route to `encoding-training`.
- NIR export/import: route to `nir-interoperability`.
- Dataset download/loading and legacy neuromorphic dataset wrappers: route to `spikevision`.
- Core neuron construction or state lifecycle beyond using recorded `spk_rec`/`mem_rec`: route to `core-neurons`.

## Operating workflow

1. Identify the recorded tensor: most `spikeplot` workflows use one sample with time as dimension 0, such as `[num_steps, num_outputs]` for spike counts/traces or `[num_steps, height, width]` for frame animations.
2. Normalize shapes before plotting. For classic rasters, prefer `[num_steps, num_neurons]`; flatten trailing spatial dimensions if needed. For minibatch recordings, index one sample first, for example `spk_rec[:, sample_idx].detach().cpu()`.
3. Choose the helper and exact arguments from [API reference](references/api-reference.md); use [workflows](references/workflows.md) for notebook and headless-script patterns.
4. For `spike_count`, pass a Python list/tuple/array of labels whose length matches the output dimension; do not pass a torch tensor as `labels`.
5. For servers or CI, set an Agg backend before importing `matplotlib.pyplot`, create explicit `fig, ax` objects, and close figures after rendering.
6. If plotting fails or animations do not save/display, use [troubleshooting](references/troubleshooting.md) before changing model or tensor semantics.

## Bundled script

- [`scripts/spikeplot_smoke.py`](scripts/spikeplot_smoke.py): headless Agg smoke that builds synthetic spike/trace tensors, exercises raster, spike-count, traces, and a lightweight animation object, and prints a pass summary.

Start with [workflows](references/workflows.md) for practical recipes and [API reference](references/api-reference.md) for live snnTorch 1.0.0 signatures.
