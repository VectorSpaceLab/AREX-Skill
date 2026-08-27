---
name: tensorflow-quantum
description: "Guide TensorFlow Quantum workflows for circuit tensors, Keras
  quantum layers, differentiators, datasets, and tutorial recipes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TensorFlow Quantum

Use this skill when a prompt is about the TensorFlow Quantum package or the public `tensorflow_quantum` module.

## Route here when the user asks about
- package install, import, version, or `TF_USE_LEGACY_KERAS` setup
- circuit tensor conversion, raw execution getters, noisy execution, or `tfq.math`
- `tfq.layers` model wiring, readout layers, or quantum-classical Keras models
- differentiators, gradient plumbing, or tiny optimizer loops
- dataset helpers, notebook-derived recipes, or tutorial-style examples

## Sub-skill map
- `sub-skills/tensor-ops-and-execution/SKILL.md` for `tfq.convert_to_tensor`, `tfq.from_tensor`, raw execution ops, `tfq.noise`, `tfq.math`, and quantum-concurrent op mode questions
- `sub-skills/keras-quantum-layers/SKILL.md` for `tfq.layers`, append/prepend wiring, PQC/ControlledPQC families, and noisy readout layers
- `sub-skills/differentiation-and-optimizers/SKILL.md` for `tfq.differentiators`, `tfq.optimizers`, and gradient/parameter-search workflows
- `sub-skills/datasets-and-tutorials/SKILL.md` for `tfq.datasets` helpers and the notebook-style recipe summaries

## Start here
- `references/installation-and-compatibility.md`
- `references/api-overview.md`
- `references/troubleshooting.md`
- `references/repo-provenance.md` when checking whether this skill still matches the checkout
- `scripts/tfq_smoke_check.py`

## Fast path
If the prompt is short and factual, answer from `references/api-overview.md`. If it asks for setup or compatibility, read `references/installation-and-compatibility.md` first. If it reports an error, use `references/troubleshooting.md` before changing the recipe.

## Minimal setup reminder
- TensorFlow Quantum supports Python 3.10-3.12.
- Set `TF_USE_LEGACY_KERAS=1` before importing TensorFlow or TFQ.
- Install the package first, then run `python scripts/tfq_smoke_check.py --quick`.
- Add `--layers`, `--datasets`, `--differentiators`, or `--math` when you need a slightly deeper smoke.

## Shared route rule
Do not force a low-level tensor or backend issue into a layers or dataset route. Use the owning sub-skill so the future agent gets the right reference and smoke path on the first try.
