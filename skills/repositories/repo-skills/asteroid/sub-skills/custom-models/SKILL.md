---
name: custom-models
description: "Build or debug Asteroid custom models, blocks, registries, DSP
  helpers, and tracing behavior."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Custom models and core APIs

Use this sub-skill when the user is building a new Asteroid architecture, extending a block, or debugging a low-level API rather than running a recipe or applying a pretrained model.

## Typical triggers

- custom `BaseModel` or `BaseEncoderMaskerDecoder` subclasses
- `asteroid.models.get(...)` or `register_model(...)`
- `asteroid.masknn`, `asteroid.dsp`, `asteroid.complex_nn`, or `asteroid.utils`
- filterbanks, encoders, decoders, mask networks, or normalization layers
- TorchScript / tracing / shape issues
- `register_norm(...)`, `register_optimizer(...)`, or `prepare_parser_from_dict(...)`

## What to do first

1. Identify the exact block or API family the user wants to extend.
2. Decide whether they need:
   - a built-in model family
   - a reusable block
   - a custom serialization contract
   - a tracing or shape-debugging pass
3. Check the expected input/output shape and the sample-rate contract before editing anything.

## Standard workflow

- Read `references/api-reference.md` for the model/block/registry surface.
- Read `references/jit-and-tracing.md` when TorchScript or `torch.jit.trace` is involved.
- Read `references/troubleshooting.md` when the issue looks like a shape, serialization, or registry mismatch.
- Use `scripts/smoke_building_blocks.py` to exercise representative blocks and utilities locally.

## Common task families

- new source-separation architectures
- custom encoders/decoders or filterbanks
- mask network experiments
- complex-number-aware layers
- batch or source-dimension shape debugging
- registry-based extension points for activations, norms, optimizers, or models

## Built-in model families worth recognizing

The repo exposes ready-to-use model families such as:

- ConvTasNet
- DPRNNTasNet
- DPTNet
- LSTMTasNet
- DeMask
- DCUNet
- DCCRNet
- SuDORMRFNet / SuDORMRFImprovedNet
- FasNetTAC
- XUMX

Those are often the right starting point when the user wants to modify an existing Asteroid model rather than write a fresh stack from scratch.

## Troubleshooting reminders

- `get_model_args()` should be able to reconstruct the model cleanly.
- `BaseModel.from_pretrained(...)` round-trips are a good shape/serialization smoke.
- `BaseEncoderMaskerDecoder` expects waveform-like tensors with time last.
- Complex-mask helpers and JIT helpers have their own shape rules.
- If a registry lookup fails, check whether the class was actually registered and whether the name collides with an existing symbol.

## Inputs to inspect

- desired input shape and output shape
- time axis, channel axis, and batch axis conventions
- whether the user needs a built-in family, a reusable block, or a registry extension point
- whether tracing or serialization must work in addition to eager execution

## Smoke sequence

1. Instantiate a tiny built-in model or block.
2. Run a forward pass on a tiny tensor.
3. Round-trip through `serialize()` / `from_pretrained()` if a model is involved.
4. Trace the same block if the request mentions JIT or export.
5. Confirm any registry or helper function the user cares about.

## What to avoid

- Do not hand-wave shape conventions.
- Do not treat a successful eager forward pass as proof of tracing correctness.
- Do not rely on the original repo checkout in runtime instructions.
- Do not blur custom-model work with recipe training unless the task truly spans both.

## Common model-building signals

- `filterbank`, `encoder`, `decoder`, or `masker` usually point to architecture assembly.
- `complex` and `beamforming` usually point to DSP or complex-valued helpers.
- `register_*` almost always means a registry extension point.
- `torch.jit` or `trace` means the tracing-safe path should be considered explicitly.

## Good questions to ask when unclear

- Is this a new model or a modification of an existing family?
- Which dimensions should be preserved in the output?
- Does the user need a round-trip serialization contract?
- Should the answer focus on eager execution, tracing, or both?
