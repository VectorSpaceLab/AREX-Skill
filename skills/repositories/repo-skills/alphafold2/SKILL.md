---
name: alphafold2
description: "Guide alphafold2-pytorch protein sequence, MSA, distogram,
  angle-logit, coordinate-refinement, recycling, embedding, and
  structure-utility workflows with version-aware troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# alphafold2-pytorch

Use this skill when a task names `alphafold2-pytorch`, `alphafold2_pytorch`,
`Alphafold2`, `Evoformer`, protein sequence/MSA folding, distograms, angle
logits, residue coordinates, ESM/MSA/ProtTrans embeddings, recycling, MDS, or
protein-structure metrics.

This graph targets the unofficial PyTorch implementation at distribution
version `0.4.32`. It is not the official DeepMind AlphaFold2 implementation.
Its current source and README disagree in several places; prefer the verified
current API described by the linked sub-skills over older README recipes.

## Install and inspect

Install the public distribution, then verify the import before building a
model:

```bash
python -m pip install alphafold2-pytorch==0.4.32
python -c "import alphafold2_pytorch; print(alphafold2_pytorch.Alphafold2)"
```

Coordinate and utility paths also need the scientific and geometric
requirements declared by the distribution, including a mutually compatible
PyTorch/PyTorch3D pair, `invariant-point-attention`, `sidechainnet`,
`mdtraj`, `ProDy`, `mp-nerf`, and OpenMM where the selected helper imports it.
Use [the environment checker](scripts/check_environment.py) for a read-only
summary; use [cross-cutting troubleshooting](references/troubleshooting.md)
when dependency resolution selects an incompatible backend.

## Route by task

- **Core sequence/MSA trunk, Evoformer, distograms, angle logits, masks,
  templates, and current constructor/forward contracts:** read
  [core-model](sub-skills/core-model/SKILL.md).
- **Residue coordinates, invariant-point refinement, confidence, auxiliary
  returns, and recycling:** read
  [structure-and-recycling](sub-skills/structure-and-recycling/SKILL.md).
- **ESM, MSA Transformer, ProtTrans wrappers or safe precomputed
  representations:** read [embeddings](sub-skills/embeddings/SKILL.md).
- **Distogram-to-distance conversion, MDS, atom masks, sidechain layouts,
  Kabsch, LDDT, GDT, TM-score, and distance losses:** read
  [utilities](sub-skills/utilities/SKILL.md).

Start with the owning sub-skill, then follow its API reference and
troubleshooting file. Cross-links are deliberate: do not duplicate a sibling's
full API table in the root router.

## Operating constraints

- Use tiny synthetic tensors first. The model is quadratic in sequence length
  for several trunk operations, and untrained outputs are not scientific
  structure predictions.
- At this version, normal MSA input has shape `(B, M, N)` with the same residue
  width `N` as `seq`; masks should be boolean and on the same device.
- CPU is the default verification backend. CUDA is an optional acceleration
  path and must be checked on the actual host; a visible CUDA installation is
  not proof that a shared device has enough memory.
- Pretrained embedding wrappers may download code or weights and may require
  caches, network access, Hugging Face/torch.hub support, or fused operations.
  Do not trigger those side effects without explicit approval.
- Full training, multi-terabyte MSA acquisition, DeepSpeed sparse attention,
  PyRosetta relaxation, and notebook-scale experiments are intentionally not
  part of this runtime graph. See [limitations](references/limitations.md).

## Provenance and refresh

Read [repository provenance](references/repo-provenance.md) before treating
this graph as current for another checkout. Refresh it when the commit,
package version, public signatures, or evidence paths change. The generated
runtime graph is self-contained and does not require the source checkout to
remain available.
