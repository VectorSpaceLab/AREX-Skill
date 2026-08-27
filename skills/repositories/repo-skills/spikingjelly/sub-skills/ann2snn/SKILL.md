---
name: ann2snn
description: "ANN-to-SNN conversion workflows for CNNs and Transformers,
  including FX versus module conversion, rate coding, Transformer TD-equivalent
  paths, STA, SpikeZIP, Qwen2 calibration, and tiny synthetic validation
  patterns."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# ANN2SNN

Use this sub-skill when the request is about converting a trained ANN into a
SpikingJelly SNN, choosing between FX and module-tree conversion, calibrating
with synthetic batches, or validating time-axis readout semantics.

## Route here for

- `Converter` / `FXConverter` workflows that use `RateCodingRecipe`,
  `LocalThresholdBalancingRecipe`, `TransformerTDEquivalentRecipe`, or
  `STATransformerRecipe`.
- `ModuleConverter` workflows that use `SpikeZIPTFQANNRecipe` or
  `Qwen2SNNRecipe`.
- Calibration objects and replay contracts such as `Qwen2SNNCalibration`,
  `SignedQCFSSequenceEncoder`, and `ChannelVoltageScaler`.
- Questions about explicit time-dimension readout, cache continuation, or the
  difference between dense ANN logits and converted sequence outputs.

## Do not use for

- General SNN modeling, neuron/reset semantics, or step-mode basics; route to
  `core-snn`.
- Dataset acquisition, file layout, or calibration-data preparation; route to
  `datasets`.
- CuPy/Triton/FP8/backend profiling or kernel behavior; route to
  `performance-and-analysis`.

## What this skill owns

- CNN ANN-to-SNN conversion with rate coding and local threshold balancing.
- Transformer ANN-to-SNN conversion through TD-equivalent FX rewriting.
- STA conversion for Transformers, including calibration-driven spike encoders.
- SpikeZIP QANN-to-SNN module-tree conversion.
- Tiny Qwen2 calibration, conversion, replay, cache, and generation flows.
- Synthetic smoke patterns that validate the converter choice and readout rule
  without downloading data or checkpoints.

## Fast routing rules

1. If the model is a CNN or plain feedforward ANN, start with
   `RateCodingRecipe` or `LocalThresholdBalancingRecipe` on the FX path.
2. If the model is a Transformer and you want FX graph rewriting, use
   `TransformerTDEquivalentRecipe` for the lightweight TD baseline or
   `STATransformerRecipe` for calibrated STA conversion.
3. If the model is already SpikeZIP-compatible QANN, use `ModuleConverter`
   plus `SpikeZIPTFQANNRecipe`.
4. If the model is Hugging Face Qwen2, calibrate first with
   `calibrate_qwen2_snn`, then convert with `ModuleConverter` and
   `Qwen2SNNRecipe`.
5. For any step-mode or reset question, follow `core-snn` and keep this skill
   focused on conversion contracts.

## Bundled files

- `references/conversion-recipes.md`
- `references/troubleshooting.md`
- `scripts/ann2snn_tiny_smoke.py`

## Cross-links

- `../core-snn/` for `functional.set_step_mode`, `functional.reset_net`, and
  state-reset semantics.
- `../datasets/` for calibration-data sourcing and loader layout.
- `../performance-and-analysis/` for optional Triton or FP8 backend behavior.

## Evidence used

- Source: `spikingjelly/activation_based/ann2snn/*`
- Tutorials: `docs/source/tutorials/en/ann2snn.rst`,
  `docs/source/tutorials/en/ann2snn_transformer.rst`
- API docs: `docs/source/APIs/spikingjelly.activation_based.ann2snn.rst`,
  `docs/source/APIs/spikingjelly.activation_based.ann2snn.examples.rst`
- Tests: `test/activation_based/test_ann2snn.py`,
  `test/activation_based/test_ann2snn_operators.py`,
  `test/activation_based/test_ann2snn_qcfs.py`,
  `test/activation_based/test_ann2snn_transformer.py`,
  `test/activation_based/test_ann2snn_qwen2.py`
- Live signatures from the prepared inspection environment for the public
  converters, recipes, Qwen2 calibration objects, TD operators, and
  `estimate_delay_start`.

## Read this first

- Use the conversion recipes and signatures in the bundled references rather
  than the source checkout.
- Readout is explicit: the converted model usually returns a time sequence, and
  the caller decides when to sum or cache it.
- Qwen2 conversion is a module-tree path; it is not driven through the FX
  converter.
