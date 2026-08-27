---
name: alphafold3-pytorch
description: "Use AlphaFold 3 PyTorch for protein and biomolecular
  structure-prediction workflows, heterogeneous molecule inputs,
  PDB/mmCIF/MSA/template preparation, bounded model inference, training
  configuration, and local CLI or Gradio operation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# AlphaFold 3 PyTorch

Use this skill when a task names `alphafold3-pytorch`, AlphaFold 3 in PyTorch,
protein/complex structure prediction, biomolecular diffusion, PDB/mmCIF inputs,
MSA/template features, or the package's `Alphafold3`/`Alphafold3Input` APIs.
This is operating guidance for the public package, not a claim that a
checkpoint, training dataset, or production-scale result is available.

## Start safely

1. Install the public distribution in an isolated environment:
   `python -m pip install alphafold3-pytorch`.
2. Confirm the package and its scientific dependencies import:
   `python -c "import torch, alphafold3_pytorch as af3; print(af3.Alphafold3)"`.
3. Run the read-only environment probe at
   [`scripts/check_environment.py`](scripts/check_environment.py) before using
   CUDA, optional encoders, MSA accelerators, or a CLI checkpoint.
4. Read [`references/package-overview.md`](references/package-overview.md) for
   verified API boundaries and choose exactly one focused route below.
5. Read [`references/troubleshooting.md`](references/troubleshooting.md) when
   an import, data dependency, shape, device, checkpoint, or output failure is
   involved.

The package has heavy runtime dependencies and production defaults. Begin with
small synthetic inputs and reduced model dimensions; do not start full
training, download PDB/AFDB data, or launch the interactive app as an
exploratory smoke test.

## Route by task

- **Model construction, forward/loss versus sampling, confidence, ranking,
  diffusion, checkpoint loading, or memory:** use
  [`model-inference`](sub-skills/model-inference/SKILL.md).
- **Proteins, RNA/DNA, ligands, ions, atom features, batching, serialization,
  missing atoms, or output structure conversion:** use
  [`input-representation`](sub-skills/input-representation/SKILL.md).
- **PDB/mmCIF parsing, MSA/templates, cropping, weighted sampling, or dataset
  curation:** use [`data-pipeline`](sub-skills/data-pipeline/SKILL.md).
- **Trainer, DataLoader, YAML/Pydantic configs, conductor phases, EMA,
  checkpoints, Fabric, or bounded training preflight:** use
  [`training-configuration`](sub-skills/training-configuration/SKILL.md).
- **Console commands, checkpoint-to-mmCIF planning, local Gradio UI, entity
  validation, or app cache/precision behavior:** use
  [`cli-serving`](sub-skills/cli-serving/SKILL.md).

When a request crosses routes, start here, then follow the owning sub-skill's
explicit sibling links. Keep data preparation separate from model execution so
large downloads and expensive inference are not accidentally triggered.

## Public contract

The primary public objects are `Alphafold3`, `Alphafold3Input`, `AtomInput`,
`BatchedAtomInput`, `PDBInput`, `PDBDataset`, `Trainer`, and the Pydantic/YAML
configuration factories. The two console entry points are
`alphafold3_pytorch` and `alphafold3_pytorch_app`. Exact signatures, defaults,
feature dimensions, return modes, and CLI flags live in the nearest references,
not in this router.

## Scope limits

- A real checkpoint is required for meaningful inference; this skill does not
  provide weights or validate biological quality by a tiny synthetic forward.
- CPU checks validate API/data correctness. CUDA is an optional stronger runtime
  path and must be probed explicitly; CPU evidence is not CUDA evidence.
- PDB/AFDB/CCD acquisition, filtering, clustering, Nim compilation, full
  training, and interactive server launch are intentionally bounded or
  reference-only. Follow the stop conditions in the focused route.
- Before refreshing this skill for a changed checkout, read
  [`references/repo-provenance.md`](references/repo-provenance.md) and compare
  its commit, package version, dirty state, and evidence paths.
