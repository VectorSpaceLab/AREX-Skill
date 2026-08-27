---
name: openfold
description: "Route OpenFold protein-structure prediction, data preparation,
  training, installation, and programmatic API tasks to focused repo skill
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenFold Repo Skill

Use this repo skill when a task is about OpenFold: installing or validating its runtime, planning protein-structure inference, preparing FASTA/mmCIF/MSA inputs, training or fine-tuning models, using OpenFold Python APIs, debugging optional CUDA/TensorRT/DeepSpeed dependencies, or deciding which OpenFold workflow fits a protein modeling request.

## First Checks

1. Read `references/repo-provenance.md` when deciding whether this skill matches a current OpenFold checkout or should be refreshed.
2. Read `references/capability-map.md` for a compact route map from user tasks to sub-skills and bundled helpers.
3. Run `scripts/check_openfold_imports.py --json` in the target environment for a package import/config/extension check before deeper workflows.
4. Use `references/troubleshooting.md` for cross-cutting install/import/backend/data-asset triage, then route to the nearest sub-skill for workflow-specific recovery.

## Route by Task

| User task | Read next | Why |
| --- | --- | --- |
| Install OpenFold, plan parameters/databases, diagnose import/build/backend failures, or validate runtime readiness | `sub-skills/installation-assets/` | Owns environment setup, assets, optional dependencies, external binaries, and safe environment checks. |
| Build or validate monomer, multimer, SoloSeq, precomputed-alignment, custom-template, long-sequence, or threading inference commands | `sub-skills/inference/` | Owns `run_pretrained_openfold.py`, `thread_sequence.py`, inference flags, outputs, relaxation, and inference troubleshooting. |
| Prepare FASTA, MSA, mmCIF, precomputed alignment, alignment DB, duplicate-chain, cluster-file, or cache inputs | `sub-skills/data-preparation/` | Owns input file layouts, parser facts, alignment/cache validators, and data-prep troubleshooting. |
| Train or fine-tune OpenFold, configure validation/distillation, resume checkpoints, plan DeepSpeed, or construct distributed training commands | `sub-skills/training/` | Owns `train_openfold.py`, training prerequisites, DeepSpeed/distributed options, checkpoints, and training command builders. |
| Use OpenFold from Python, inspect config presets, instantiate model APIs, import/convert weights, or reason about acceleration internals | `sub-skills/model-apis/` | Owns verified/source-backed API signatures, config presets, weights/checkpoints, output objects, metrics, and optional acceleration APIs. |

## Installation Baseline

- Public package/distribution name: `openfold`.
- Source metadata version used for this skill: `2.2.0`.
- Documented production target: Linux, Python 3.10, PyTorch 2, CUDA-class GPU runtime for realistic inference/training.
- For a local checkout, install only after selecting a compatible PyTorch/CUDA runtime, then use `python -m pip install --no-build-isolation -e .` so `setup.py` can import the already-installed `torch` while building the OpenFold extension.
- OpenFold setup imports `torch` at build time and builds `attn_core_inplace_cuda` as a CUDA extension when CUDA/NVCC are available, otherwise as a CPU stub.
- Full inference/training usually requires large external parameters, sequence databases, template mmCIFs, HMMER/HHSuite/Kalign binaries, and GPU resources; do not run downloads, database searches, model inference, or training without explicit user approval.

Minimal package check:

```bash
python - <<'PY'
from openfold.config import model_config
from openfold.data.parsers import parse_fasta
cfg = model_config('model_1')
tags, seqs = parse_fasta('>query\nACD\n')
print('openfold config/parser ok', cfg.model.template.enabled, tags, seqs)
PY
```

For fuller diagnostics, use:

```bash
python scripts/check_openfold_imports.py --json
```

## Shared Rules

- Keep inference and training commands as dry-run plans until parameters, databases, hardware, external binaries, and output paths are confirmed.
- If `run_pretrained_openfold.py`, `train_openfold.py`, or model imports fail with `ModuleNotFoundError: attn_core_inplace_cuda`, repair/rebuild the OpenFold install before claiming model or CLI readiness.
- Use precomputed alignments to avoid database searches only after validating the alignment directory or alignment DB layout in `sub-skills/data-preparation/`.
- Route missing TensorRT, `cuda.cudart`, DeepSpeed, cuEquivariance, FlashAttention, OpenMM, PDBFixer, HMMER, HHSuite, or Kalign errors through `sub-skills/installation-assets/` first.
- Do not assume CPU-only execution is enough for full OpenFold training or production inference; CPU-only is mainly useful for import/config/data validation.

## Bundled Root Files

- `references/capability-map.md` maps capabilities to sub-skill owners and safe helpers.
- `references/troubleshooting.md` covers cross-cutting install/import/runtime failures.
- `references/repo-routing-metadata.json` is structured metadata consumed by DisCo import tooling.
- `scripts/check_openfold_imports.py` performs lightweight import/config/module availability checks without model execution.
