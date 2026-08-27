---
name: keras-quantum-layers
description: "Route TensorFlow Quantum Keras-layer tasks for circuit wiring,
  readout, and trainable hybrid models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# keras-quantum-layers

Use this sub-skill when the user wants to build, call, or debug `tfq.layers`
models.

## Owns

- `AddCircuit` append/prepend wiring for batched circuit tensors.
- Readout layers: `Expectation`, `Sample`, `SampledExpectation`, `State`, `Unitary`.
- Trainable circuit layers: `PQC`, `ControlledPQC`, `NoisyPQC`, `NoisyControlledPQC`.
- Backend choice, shot/repetition handling, control-input wiring, and noisy-layer behavior.

## Read first

- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- The bundled references capture the layer contracts, small recipes, and
  failure modes that the notebook examples and source tests establish.

## Shared smoke helper

- Use `../../scripts/tfq_smoke_check.py` for a quick import plus tiny one-qubit
  layer sanity check.
- Whole-notebook execution is not the default runtime path here; use the
  distilled notebook recipes in `references/workflows.md` instead.

## Route away when

- The problem is about circuit tensor conversion, backend execution ops, or low-level op selection; use the tensor-ops-and-execution sub-skill.
- The problem is about differentiators, gradient plumbing, or optimizer loops; use the differentiation-and-optimizers sub-skill.
- The problem is about dataset loading or tutorial-scale execution; use the datasets-and-tutorials sub-skill.

## Fast prompt mapping

- "Append a helper circuit" -> `AddCircuit`.
- "Read expectation / sample / state / unitary outputs" -> the executor layers.
- "Build a variational quantum layer" -> `PQC`.
- "Drive a circuit from classical features" -> `ControlledPQC`.
- "Add noise and train" -> `NoisyPQC` or `NoisyControlledPQC`.
- "Noisy or sampled readout on a fixed circuit" -> `Expectation` or `SampledExpectation`.
- "Need a custom backend object" -> check the layer's accepted backend class before wiring it in.
