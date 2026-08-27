---
name: encoding-training
description: "Route spike encoding, surrogate gradients, training helpers,
  losses, monitors, quantization, STDP, and backprop-wrapper questions."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# encoding-training

Use this sub-skill for workflows that start with raw tensors or labels and end with spike-coded data, a training step, or output/gradient inspection.

## Ask this sub-skill about
- `spikegen` encodings: rate, latency, delta, and target coding
- surrogate gradients for neuron `spike_grad`
- loss and accuracy helpers in `snntorch.functional`
- `utils.reset`, `data_subset`, and `valid_split`
- backprop wrappers: `BPTT`, `TBPTT`, `RTRL`
- monitors for spikes, inputs, attributes, and gradients
- `functional.quant.state_quant`
- `functional.stdp_learner.STDPLearner`

## Route elsewhere
- neuron definitions and reset semantics in detail -> core-neurons
- NIR export/import -> nir-interoperability
- raster plots, animations, and spike histograms -> plotting
- legacy spikevision datasets -> spikevision

## Start here
1. `references/workflows.md`
2. `references/api-reference.md`
3. `references/troubleshooting.md`

## Bundled smoke helpers
- `scripts/spike_encoding_smoke.py`
- `scripts/synthetic_bptt_smoke.py`
- `scripts/shape_mismatch_diagnostic.py`
- `scripts/stdp_smoke.py`

## Import reminders
- Use `import snntorch.functional as SF` for accuracy, losses, regularization, and probes.
- Import quantization and STDP helpers from their submodules:
  `from snntorch.functional import quant`
  `from snntorch.functional.stdp_learner import STDPLearner`
- There is no standalone `SF.metrics` namespace in this release; use `SF.accuracy_rate` and `SF.accuracy_temporal`.
- `backprop` is a compatibility layer and emits a deprecation warning.
- Call `utils.reset(net)` between sequences unless a wrapper already does it.
- `STDPLearner.reset()` is not reliable in this release; create a fresh learner when you need a clean STDP episode.
