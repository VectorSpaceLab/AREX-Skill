# snnTorch workflow map

This reference maps common user intents to the owning sub-skill. Use it when you need a fast route decision before opening deeper API notes.

## Primary routes

| User intent | Start here | Why |
| --- | --- | --- |
| Build, combine, or debug spiking neuron layers | [`core-neurons`](../sub-skills/core-neurons/SKILL.md) | Covers stateful neurons, recurrent cells, time-major layers, BNTT, and GradedSpikes. |
| Turn tensors or labels into spikes, pick a surrogate gradient, or train with a loss | [`encoding-training`](../sub-skills/encoding-training/SKILL.md) | Covers spike encoders, losses, monitors, STDP, and legacy backprop wrappers. |
| Export a model to NIR or import a NIR graph back into snnTorch | [`nir-interoperability`](../sub-skills/nir-interoperability/SKILL.md) | Covers sequential and recurrent NIR round-trips plus known compatibility limits. |
| Plot spike rasters, counts, traces, or animations | [`plotting`](../sub-skills/plotting/SKILL.md) | Covers headless matplotlib usage and the `spikeplot` helpers. |
| Maintain legacy neuromorphic dataset code | [`spikevision`](../sub-skills/spikevision/SKILL.md) | Covers the deprecated `spikevision` dataset wrappers and local transform helpers. |

## Common combinations

- **Train a classifier**: `core-neurons` + `encoding-training` + `plotting`
- **Export a trained model**: `core-neurons` + `nir-interoperability`
- **Diagnose a training loop**: `encoding-training` first, then `core-neurons` if the problem is really a state or return-shape issue
- **Visualize recorded spikes**: `plotting` after you have a stable tensor shape from `core-neurons` or `encoding-training`
- **Handle old neuromorphic data**: `spikevision` only for compatibility or migration work; new pipelines should switch to Tonic

## Quick route hints

- If the prompt mentions `Leaky`, `Synaptic`, `RLeaky`, `SLSTM`, `StateLeaky`, or state tuples, go to `core-neurons`.
- If the prompt mentions `spikegen`, `surrogate`, `SF.ce_count_loss`, `SF.mse_count_loss`, `backprop.BPTT`, or `STDPLearner`, go to `encoding-training`.
- If the prompt mentions `export_to_nir`, `import_from_nir`, `NIRGraph`, or a type-inference error, go to `nir-interoperability`.
- If the prompt mentions `spikeplot.raster`, `spikeplot.spike_count`, `spikeplot.traces`, or `animator`, go to `plotting`.
- If the prompt mentions `NMNIST`, `DVSGesture`, `SHD`, or a deprecation warning from `snntorch.spikevision`, go to `spikevision`.

## Useful smoke checks

- [`scripts/stack_smoke.py`](../scripts/stack_smoke.py): broad import and optional CUDA probe.
- Sub-skill scripts under `sub-skills/*/scripts/`: synthetic, focused smokes that do not depend on the original checkout.
