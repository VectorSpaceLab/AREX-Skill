---
name: interpretation-and-visualization
description: "Guides braindecode Captum attribution, frequency gradients,
  channel topomaps, metrics, and headless visualization for electrophysiology
  models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Interpretation and visualization

Use this route for saliency or integrated-gradient maps, layer GradCAM,
frequency-domain amplitude gradients, topomaps, confusion/metric plots, or
model sanity checks.

## Workflow

1. Put the model in evaluation mode and confirm input shape `(batch, channels,
   time)`, target indices, device, and differentiability. Keep a cloned leaf
   tensor for attribution.
2. Use Captum wrappers for input-space methods and detach results before NumPy
   or plotting. Match target batch length and preserve channel/time axes.
3. Use `amplitude_gradients` for frequency analysis and interpret bins using the
   actual sampling rate and FFT convention. Validate with a tiny known filter
   before analyzing a large model.
4. For topomaps, require a montage or non-zero channel positions and a channel
   order matching the model input. Select a non-interactive plotting backend in
   headless jobs.
5. Save figures and arrays to explicit writable paths; do not use visualization
   as evidence of causal importance without stability checks.

Read [API reference](references/api-reference.md), [workflows](references/workflows.md),
and [troubleshooting](references/troubleshooting.md). Run the local
[interpretation smoke](scripts/smoke_interpretation.py) to check gradient and
frequency behavior without downloads or a display server. Captum is optional;
install the visualization extra only for Captum methods.
