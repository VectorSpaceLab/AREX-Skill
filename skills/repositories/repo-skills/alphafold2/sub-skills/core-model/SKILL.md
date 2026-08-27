---
name: core-model
description: "Guide construction and execution of the verified Alphafold2
  sequence/MSA trunk and direct Evoformer API, including distogram and
  angle-logit prediction, masks, templates, extra MSA inputs, embeddings, and
  supported trunk configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Core model

Use this skill when the request is to build or run `alphafold2_pytorch.Alphafold2`, configure its Evoformer trunk, supply sequence/MSA/template features or masks, or diagnose core shape and output-routing errors.

## Route first

- Read [the API reference](references/api-reference.md) before choosing constructor or forward arguments.
- Use [the workflows](references/workflows.md) for small, CPU-safe synthetic calls and output inspection. The bundled [smoke helper](scripts/core_smoke.py) is deterministic, has no network or data-file step, and defaults to CPU.
- Route coordinate refinement, confidence, and recycling semantics to [structure-and-recycling](../structure-and-recycling/SKILL.md).
- Route pretrained ESM/MSA/ProtTrans wrappers and downloaded embedding models to [embeddings](../embeddings/SKILL.md).
- Route distance metrics, bucket utilities, and MDS to [utilities](../utilities/SKILL.md).
- For import, dimension, memory, or README/source-drift failures, use [troubleshooting](references/troubleshooting.md).

## Minimum safe recipe

1. Install distribution `alphafold2-pytorch==0.4.32` with its native scientific dependencies, then verify `import alphafold2_pytorch`.
2. Construct `Alphafold2(dim=16, depth=1, heads=1, dim_head=16)` and call `model.eval()` with `torch.no_grad()` for inference.
3. Pass `seq` as integer shape `(B, N)`, an optional integer `msa` shape `(B, M, N)`, and boolean `mask`/`msa_mask` with matching shapes. The inspected source asserts that MSA width equals primary-sequence width; do not follow the README examples that use different widths.
4. Read `ReturnValues.distance` for distogram logits. Set `predict_angles=True` to additionally read `theta_logits`, `phi_logits`, and `omega_logits`; the source returns an object, not the tuple shown in the README.
5. For already embedded pair/MSA representations, use the direct public `Evoformer` route in the API reference; it returns updated representations and does not produce distogram or angle logits itself.

The exact contracts, source/installed provenance, template and embedding dimensions, supported knobs, and drift warnings are in the linked references. Do not claim README-only flags such as `reversible`, `use_conv`, sparse/linear/Kronecker/compressed attention, or `custom_block_types` are constructor features at this version: they are absent from the inspected public signature.
