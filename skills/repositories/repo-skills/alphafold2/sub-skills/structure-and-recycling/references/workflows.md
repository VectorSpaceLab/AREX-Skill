# Structure workflows

Use this reference for safe, small coordinate workflows. Every example is
intended for an already importable `alphafold2_pytorch` installation and uses
synthetic tensors only. It does not download checkpoints, MSA data, or
pretrained embeddings. Random weights and random/synthetic tokens prove API and
shape behavior only; they do not produce a meaningful structure.

## Tiny CPU coordinate and confidence pass

Start with the bundled helper from arbitrary current directories:

```bash
python /path/to/skills/disco/alphafold2/sub-skills/structure-and-recycling/scripts/coordinate_smoke.py
```

It defaults to CPU, uses `dim=32`, trunk `depth=1`, `heads=1`,
`dim_head=8`, `predict_coords=True`, and one IPA iteration. It asserts finite
coordinate and confidence outputs, then captures and reuses recyclables. It
performs no filesystem writes or network access. A CUDA probe is explicit:

```bash
python /path/to/skills/disco/alphafold2/sub-skills/structure-and-recycling/scripts/coordinate_smoke.py --device cuda
```

Use `--device cuda:0` for a selected device. A visible CUDA runtime is not
proof that this call will allocate on a shared host; preserve the helper's
failure report and fall back to CPU when allocation fails.

The direct Python shape contract is:

```python
import torch
from alphafold2_pytorch import Alphafold2

model = Alphafold2(
    dim=32,
    depth=1,
    heads=1,
    dim_head=8,
    predict_coords=True,
    structure_module_depth=1,
    structure_module_heads=1,
    structure_module_dim_head=1,  # accepted compatibility argument
).eval()

B, M, N = 1, 2, 4
seq = torch.tensor([[0, 4, 7, 12]], dtype=torch.long)
msa = torch.tensor([[[0, 4, 7, 12], [1, 5, 8, 13]]], dtype=torch.long)
mask = torch.ones(B, N, dtype=torch.bool)
msa_mask = torch.ones(B, M, N, dtype=torch.bool)

with torch.no_grad():
    coords, confidence = model(
        seq, msa, mask=mask, msa_mask=msa_mask,
        return_confidence=True,
    )

assert coords.shape == (B, N, 3)
assert confidence.shape == (B, N, 1)
assert torch.isfinite(coords).all()
assert torch.isfinite(confidence).all()
```

Keep all tensors and the model on one device. Supply `mask` even when using a
one-row fallback (`msa=None`). For a padded sequence, set false mask entries
and exclude their coordinates downstream; a finite value at a masked location
is not a valid predicted atom.

## Auxiliary logits plus recyclable capture

The second call shape is the useful way to obtain a `ReturnValues` object and a
recyclable snapshot:

```python
with torch.no_grad():
    coords_1, ret_1 = model(
        seq, msa, mask=mask, msa_mask=msa_mask,
        return_aux_logits=True,
        return_recyclables=True,
    )

recycle = ret_1.recyclables
assert recycle is not None
assert recycle.coords.shape == (B, N, 3)
assert recycle.single_msa_repr_row.shape[:2] == (B, N)
assert recycle.pairwise_repr.shape[:3] == (B, N, N)
assert all(
    not tensor.requires_grad
    for tensor in (
        recycle.coords,
        recycle.single_msa_repr_row,
        recycle.pairwise_repr,
    )
)

with torch.no_grad():
    coords_2, ret_2 = model(
        seq, msa, mask=mask, msa_mask=msa_mask,
        recyclables=recycle,
        return_aux_logits=True,
        return_recyclables=True,
    )

assert coords_2.shape == coords_1.shape
assert ret_2.recyclables is not None
```

The second call is a single explicit recycle injection. If more passes are
wanted, repeat deliberately and validate each newly returned object. Keep the
same model representation dimension, batch, residue length, device, masks, and
shape-compatible optional features. Do not mix snapshots from different model
instances merely because their sequence lengths match. Recycling is not a
quality guarantee for random weights or for a trained model without a
controlled evaluation.

## Confidence and return-mode probes

To check return routing without relying on tuple guesses:

```python
with torch.no_grad():
    coords, confidence = model(
        seq, msa, mask=mask, msa_mask=msa_mask,
        return_confidence=True,
    )
    coords_aux, ret = model(
        seq, msa, mask=mask, msa_mask=msa_mask,
        return_aux_logits=True,
        return_recyclables=True,
    )

assert coords_aux.shape == coords.shape
assert confidence.shape == (B, N, 1)
assert ret.distance.shape[:3] == (B, N, N)
assert ret.recyclables is not None
```

Do not combine `return_confidence=True` and `return_aux_logits=True` expecting a
three-item result: the implementation returns `(coords, ret)` because the
auxiliary branch has precedence. `return_recyclables=True` alone populates a
field on `ret`, but does not make a coordinate-only call return a tuple.
`return_trunk=True` also wins before structure refinement and returns
`ReturnValues`, not coordinates.

## Optional templates

Template arguments are precomputed feature tensors, not file paths. Configure
the model's feature widths to match the tensors:

```python
model = Alphafold2(
    dim=32, depth=1, heads=1, dim_head=8,
    templates_dim=8,
    templates_angles_feats_dim=6,
    predict_coords=True,
    structure_module_depth=1,
    structure_module_heads=1,
).eval()

templates_feats = torch.zeros(B, 1, N, N, 8)
templates_angles = torch.zeros(B, 1, N, 6)
templates_mask = torch.ones(B, 1, N, dtype=torch.bool)

with torch.no_grad():
    coords = model(
        seq, msa, mask=mask, msa_mask=msa_mask,
        templates_feats=templates_feats,
        templates_angles=templates_angles,
        templates_mask=templates_mask,
    )
assert coords.shape == (B, N, 3)
```

`templates_feats` requires `templates_mask`; `templates_angles` also requires
the same mask because its rows are appended to the MSA mask. The default widths
are `templates_dim=32` and `templates_angles_feats_dim=55` when model
constructor overrides are omitted. Use finite float features and boolean masks.
Do not pass README-era `templates_seq`, `templates_coors`, or
`templates_sidechains`; those are not current forward parameters.

## Optional extra MSA

The ordinary MSA path is the safest small workflow. If a task specifically
needs the current extra-MSA branch, use finite integer `extra_msa` and a boolean
`extra_msa_mask`, and conservatively make both the same shape as `msa`,
including its row count and residue width:

```python
extra_msa = torch.tensor(
    [[[0, 4, 7, 12], [1, 5, 8, 13]]], dtype=torch.long
)
extra_msa_mask = torch.ones_like(extra_msa, dtype=torch.bool)

with torch.no_grad():
    coords = model(
        seq, msa, mask=mask, msa_mask=msa_mask,
        extra_msa=extra_msa,
        extra_msa_mask=extra_msa_mask,
    )
```

The current source embeds `msa` inside the `extra_msa` branch instead of
`extra_msa`; the extra-MSA values are therefore not consumed by that line. A
different extra row count can make the extra mask incompatible with the tensor
that was embedded. This is a source defect and not evidence that the extra
alignment improves coordinates. Use the branch only for shape-compatible
compatibility probing and document the limitation in any experiment.

## Full refinement/data workflows are outside this safe route

A meaningful coordinate pipeline requires trained weights, biologically valid
sequence/MSA tokens, a feature-generation and template pipeline, sequence
length/memory planning, and an evaluation reference. This sub-skill does not
perform model downloads, large MSA acquisition, training, sidechain/atom
reconstruction, coordinate serialization, metric calculation, or benchmark
claims. Read [utilities](../../utilities/SKILL.md) for metrics and coordinate
post-processing, and [embeddings](../../embeddings/SKILL.md) for external
pretrained embedding wrappers.

The repository's refinement helper is only an unfinished sketch: external
PyRosetta integration is optional and its final relaxation routine is
unimplemented. Treat “refinement” here as the model's IPA coordinate pass, not
FastRelax or physically constrained structure optimization.
