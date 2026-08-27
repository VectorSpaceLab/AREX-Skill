---
name: embeddings
description: "Guides ESM, MSA Transformer, ProtTrans/ProtBERT, and precomputed
  sequence/MSA representations for Alphafold2, including projection, masks,
  caches, downloads, Apex, and OOM diagnosis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Embeddings

Use this sub-skill for `ESMEmbedWrapper`, `MSAEmbedWrapper`,
`ProtTranEmbedWrapper`, external sequence/MSA features, precomputed
representations, projection-width checks, or failures involving model assets,
`torch.hub`, Hugging Face, `transformers`, Apex, fused operations, caches, and
memory pressure.

## Route the task

- For exact wrapper signatures, tensor contracts, masks, projection rules, and
  `disable_token_embed`, read [API reference](references/api-reference.md).
- Before constructing any pretrained wrapper, read
  [External models](references/external-models.md). Construction can resolve
  code and large weights; never trigger that acquisition without approval.
- For missing assets, network/cache errors, source-shape defects, Apex/fused
  failures, width mismatch, or OOM, use
  [Troubleshooting](references/troubleshooting.md).
- For a safe CPU-default check, run
  [`embedding_input_smoke.py`](scripts/embedding_input_smoke.py). It creates a
  synthetic `(B, M, N, 1280)` tensor, checks the core projection, and consumes
  projected representations without constructing or downloading a pretrained
  model.

## Operating sequence

1. Decide between a live pretrained wrapper and already available
   representations. Prefer precomputed inputs when model source, weights,
   cache, network policy, fused kernels, or memory have not been approved and
   validated.
2. Validate `seq: (B, N)`, `msa: (B, M, N)`, boolean masks on the same residue
   axes, and the external feature width before allocating a model.
3. Match the external width to the correct projection: wrapper projections end
   at `Alphafold2.dim`; the core `embedd_project` accepts `num_embedds`
   channels (1280 by default) and also ends at `Alphafold2.dim`.
4. Review the 0.4.32 source limitations before relying on a wrapper or on the
   core argument spelled `embedds`. The README describes the intended workflow,
   but several wrapper/helper paths and the direct `embedds` branch drift from
   that description.
5. Run only a bounded, explicit device check. The pretrained wrapper paths are
   not offline merely because `alphafold2_pytorch` imports successfully.

## Boundaries

- General `Alphafold2` trunk construction, attention, and output contracts:
  [core-model](../core-model/SKILL.md).
- Coordinates, confidence, refinement, and recycling:
  [structure-and-recycling](../structure-and-recycling/SKILL.md).
- Metrics and unrelated utilities: [utilities](../utilities/SKILL.md).

A wrapper computes `seq_embed` and `msa_embed` and forwards them to the trunk.
The lower-level `embedds` argument is a different interface; in 0.4.32 its
branch is shadowed by MSA initialization. Do not describe a successful wrapper
or functional direct-`embedds` inference unless that exact path was validated.
