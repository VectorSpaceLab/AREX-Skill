---
name: model-apis
description: "Use OpenFold programmatic model APIs, config presets, weight
  imports, protein outputs, validation metrics, and acceleration internals."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenFold Model APIs

Use this sub-skill when a task needs OpenFold from Python: selecting `model_config` presets, constructing `AlphaFold`, preparing low-level `forward` inputs, importing or converting weights, writing PDB/ModelCIF outputs, computing validation metrics, reasoning about optional acceleration flags, or choosing focused maintainer tests.

## Route Quickly

- Read `references/api-reference.md` for source-backed Python entry points, model input/output caveats, structure-output helpers, validation metrics, and safe maintainer test selection.
- Read `references/config-presets.md` before choosing presets or combining precision, long-sequence, TensorRT, DeepSpeed, cuEquivariance, FlashAttention, or train-mode overrides.
- Read `references/weights-and-checkpoints.md` to classify JAX `.npz`, OpenFold `.pt`/`.ckpt`, older OpenFold v1, DeepSpeed checkpoint trees, and OpenFold-to-JAX conversion requests.
- Read `references/acceleration.md` for API-level acceleration switches, optional backend fallback, and hardware-sensitive test guidance.
- Read `references/troubleshooting.md` when imports, config validation, checkpoint keys/shapes, batch tensors, output conversion, metrics, or optional kernels fail.

## Bundled Safe Helpers

- Run `scripts/inspect_openfold_api.py --json` to inspect package version, import status, safe signatures, preset summaries, parser/config/protein availability, and optional backend availability without constructing a model.
- Run `scripts/validate_config_preset.py --preset model_1_ptm --json` to validate a preset and selected high-level overrides without instantiating `AlphaFold`, loading weights, compiling TensorRT engines, or running inference/training.
- Add `--package-root /path/to/openfold-or-checkout-root` to either helper when the OpenFold package is not installed but an explicit source/package root is available.

## Current Verification Caveat

OpenFold package metadata observed during skill creation reported version `2.2.0`. The current inspection environment could import package metadata, `openfold.config`, parser modules, and `openfold.np.protein`; imports that traverse model/CLI internals failed because `attn_core_inplace_cuda` was not importable. Treat the model, script-utils, and compiled-kernel sections here as source-backed API guidance until the compiled extension path is repaired and live imports are re-run.

## Boundaries

- Route public inference command construction, prediction outputs, relaxation CLI use, and user-facing `run_pretrained_openfold.py` flags to `../inference/`.
- Route training launchers, fine-tuning configs, DeepSpeed launcher setup, and training checkpoint resume behavior to `../training/`.
- Route FASTA/MSA/mmCIF parsing, feature layout creation, alignment databases, template caches, and data pipeline details to `../data-preparation/`.
- Route installation of PyTorch/CUDA/OpenMM/DeepSpeed/TensorRT/cuEquivariance/FlashAttention and compiled-extension repair to `../installation-assets/`.

## Minimal Workflow

1. Validate the intended preset and overrides with `scripts/validate_config_preset.py` before constructing `AlphaFold`.
2. Build low-level Python integrations only from processed feature tensors; do not pass raw FASTA, MSA, or mmCIF data directly to `AlphaFold.forward`.
3. Match checkpoint family to preset family before importing weights or planning conversion.
4. Convert prediction outputs with `openfold.np.protein` helpers and choose ModelCIF when PDB chain limits or metadata make PDB unsuitable.
5. Select native tests only after the runtime environment advertises the needed compiled kernels, optional backends, and safe fixtures.
