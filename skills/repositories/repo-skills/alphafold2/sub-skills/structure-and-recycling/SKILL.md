---
name: structure-and-recycling
description: "Guide coordinate prediction, IPA structure refinement, confidence
  and recyclable outputs, and optional template or extra-MSA inputs that feed
  structure refinement in alphafold2-pytorch 0.4.32."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Structure and recycling

Use this sub-skill for residue-level coordinate prediction, invariant point
attention (IPA) refinement, confidence output, recycling between model passes,
or template/extra-MSA inputs that should feed the structure path. The operating
contract is the `alphafold2_pytorch.Alphafold2` API in distribution version
0.4.32.

## Route first

- Read [the API reference](references/api-reference.md) for verified structure
  flags, input shapes, return precedence, precision, and the exact
  `Recyclables` contract.
- Read [the workflows](references/workflows.md) for tiny coordinate,
  confidence, auxiliary-output, recycling, template, and extra-MSA recipes.
- Read [troubleshooting](references/troubleshooting.md) for missing structure
  dependencies, CUDA allocation failures, shape/device problems, stale README
  options, and unsupported external refinement assumptions.
- Run the bundled [coordinate smoke](scripts/coordinate_smoke.py) for a
  deterministic, download-free CPU check. Use its optional `--device` only
  after the requested backend can allocate memory.

## Operating rules

1. Construct `Alphafold2(..., predict_coords=True)`. Supply integer `seq` of
   shape `(B, N)`, boolean residue `mask` of shape `(B, N)`, and normally an
   integer `msa` of shape `(B, M, N)` with a matching boolean `msa_mask`.
   Omitting `msa` creates a one-row MSA from `seq`, but still requires `mask`.
2. At this version, coordinate output is exactly `(B, N, 3)`: one XYZ point
   per residue. Do not reinterpret it as backbone, side-chain, or all-atom
   coordinates.
3. `structure_module_depth` counts IPA refinement iterations and
   `structure_module_heads` is passed to `IPABlock`. Although accepted by the
   constructor, `structure_module_dim_head` is not forwarded to the current
   IPA block and is not a verified active width control.
4. Use `return_confidence=True` for `(coords, confidence)`, where confidence is
   raw learned-head output of shape `(B, N, 1)`. Use
   `return_aux_logits=True` for `(coords, ReturnValues)`. Auxiliary output wins
   if both flags are true, so confidence is then not returned separately.
5. Capture recycling state with both `return_aux_logits=True` and
   `return_recyclables=True`; then pass `ret.recyclables` into a compatible
   second call. Validate all three recyclable fields for shape, device,
   finiteness, and detachment first. Recycling is explicit per call and is not
   a guarantee of better coordinates.
6. Treat templates and extra MSA as feature tensors that feed the trunk before
   structure refinement, not as file paths or direct coordinate outputs. Follow
   the conservative current-version recipes because the extra-MSA branch has a
   documented implementation defect.
7. Reject stale README-only arguments including `atoms`,
   `structure_module_type`, `structure_module_dim`,
   `structure_module_refinement_iters`, and
   `predict_real_value_distances`. The current API does not expose selectable
   SE3/EN/EGNN structure modules or atom-expanded output.

Route core distogram/angle configuration to
[core-model](../core-model/SKILL.md), coordinate metrics and post-processing to
[utilities](../utilities/SKILL.md), and pretrained external wrappers to
[embeddings](../embeddings/SKILL.md). Full data acquisition, training,
checkpoint download, atom building, PDB production, and external relaxation
remain outside this sub-skill.
