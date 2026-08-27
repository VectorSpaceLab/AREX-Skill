# Structure troubleshooting

Use this page when a coordinate, confidence, template, extra-MSA, or recycle
call fails. Start with the bundled `scripts/coordinate_smoke.py` on CPU; it
separates import, allocation, shape, and finite-output failures without
network or checkpoint side effects.

## Import and optional structure dependencies

**Symptom:** importing `alphafold2_pytorch` fails with
`ModuleNotFoundError` for `pytorch3d` or `invariant_point_attention`, often
before any model is constructed.

**Cause:** `alphafold2_pytorch.alphafold2` imports
`pytorch3d.transforms` and `invariant_point_attention.IPABlock` at module
load. These are required for this package import and coordinate path; they are
not optional switches that can be bypassed by setting `predict_coords=False`.

**Recovery:** use the same interpreter for a small dependency probe:

```bash
python -c "import torch, pytorch3d, invariant_point_attention; print(torch.__version__)"
python -c "import alphafold2_pytorch; print('alphafold2 import ok')"
```

Install the package's compatible dependency set in an isolated environment,
then rerun the coordinate smoke. Do not blindly upgrade a compiled PyTorch3D
binary to repair an ABI or Torch mismatch; align the PyTorch and PyTorch3D
builds first. Import success alone is weaker than a finite CPU coordinate run.

## CUDA visibility, allocation, and shared memory

**Symptom:** `torch.cuda.is_available()` is true, but the helper fails on
`--device cuda` with an allocation error, `out of memory`, or a CUDA runtime
failure.

**Cause:** CUDA visibility only proves that the framework sees a runtime. It
does not reserve enough memory for the model, quadratic pair features, IPA
buffers, or `torch.cdist` during recycling. CUDA was not verified for this
skill because a shared device could not satisfy the tiny allocation.

**Recovery:**

1. Keep the error text and label the CUDA attempt unverified.
2. Run the same helper with its default `--device cpu`.
3. If diagnosing a real GPU, reduce `B`, `M`, `N`, trunk `depth`, and
   `structure_module_depth`, and select an explicitly available device.
4. Do not terminate or clear other users' processes on a shared host.
5. Do not claim GPU support from `torch.cuda.is_available()` alone.

The CPU route is the accepted deterministic fallback for this sub-skill. GPU
performance or numerical equivalence requires a separate successful allocation
and should be reported independently.

## Shape, mask, dtype, and device mismatches

Check these invariants before calling `forward`:

```text
seq              integer (B, N)
mask             boolean (B, N)
msa              integer (B, M, N)
msa_mask         boolean (B, M, N)
templates_feats  floating (B, T, N, N, templates_dim)
templates_angles floating (B, T, N, templates_angles_feats_dim)
templates_mask  boolean (B, T, N)
extra_msa        integer (B, M_extra, N), conservatively M_extra == M
extra_msa_mask  boolean with the conservative extra-MSA shape
recycle.coords  (B, N, 3)
recycle.single_msa_repr_row (B, N, dim)
recycle.pairwise_repr (B, N, N, dim)
```

Keep the model, tokens, feature tensors, masks, and recyclable fields on one
device. Use integer token tensors, boolean masks, and finite floating feature
values. The implementation explicitly asserts that `msa.shape[-1]` equals
`seq.shape[-1]`; fix the residue axis rather than padding only one input.

If `msa=None`, still pass `mask`: the no-MSA fallback derives a one-row MSA
mask by rearranging it. Template inputs require `templates_mask`; wrong feature
widths usually fail later at a linear layer, so compare the model's
`templates_dim` and `templates_angles_feats_dim` with the last tensor axes.

A long sequence can fail from quadratic pair-memory or recyclable `cdist`
allocation instead of a useful shape error. Shrink the synthetic fixture first,
then make a separate memory plan for the real sequence. For half-precision
inputs, the structure representation is converted to float32; do not assume
the returned coordinate dtype is restored by the source.

## Return-mode and recyclable surprises

- `predict_coords=False` returns `ReturnValues`, not coordinates.
- `return_trunk=True` returns `ReturnValues` even when coordinates are enabled.
- `return_confidence=True` returns `(coords, confidence)` only when the
  auxiliary branch is not selected; confidence has shape `(B, N, 1)`.
- `return_aux_logits=True` returns `(coords, ret)` and takes precedence over
  `return_confidence=True`.
- `return_recyclables=True` alone does not create a tuple. Pair it with
  `return_aux_logits=True` to read `ret.recyclables`.
- A recyclable snapshot is detached. It is tied to the original batch, length,
  representation dimension, and device; do not pass one from a different model
  dimension or move only one field.

If a second pass fails inside normalization, addition, `torch.cdist`, or device
dispatch, inspect every field of `Recyclables` before retrying. Require finite
values, `requires_grad == False`, exact leading dimensions, and matching
`dtype`/device. Reuse the same masks and feature shapes unless a deliberate
experiment validates the change.

`confidence` is the output of a learned linear head. It is not automatically a
calibrated pLDDT value or a coordinate metric; use the utilities route for
metrics and keep the residue mask for interpretation.

## Current source versus stale README options

**Symptom:** `TypeError: __init__() got an unexpected keyword argument` for
`atoms`, `structure_module_type`, `structure_module_dim`,
`structure_module_refinement_iters`, `structure_num_global_nodes`, or
`predict_real_value_distances`, or for forward names such as `templates_seq`,
`templates_coors`, or `templates_sidechains`.

**Cause:** those names occur in README-era coordinate/template descriptions but
are absent from the current constructor or forward signature.

**Recovery:** use the current names `predict_coords`,
`structure_module_depth`, `structure_module_heads`,
`structure_module_dim_head`, `templates_feats`, `templates_angles`, and
`templates_mask`. Verify with `inspect.signature(Alphafold2)` before adapting a
recipe from another release. Current coordinate shape is `(B, N, 3)`, not an
atom-expanded tensor; `IPABlock` is the active structure path, not a selectable
SE3/EN/EGNN mode; and real-value distance prediction is not a current flag.

## Extra MSA and template limitations

The current extra-MSA branch embeds the ordinary `msa` tensor inside the
branch rather than the `extra_msa` argument. If `extra_msa` has a different row
count, its mask can become incompatible with the embedded tensor. Use the
same-shape conservative recipe only for compatibility probing, and do not claim
that the extra values influenced a trained coordinate result.

Templates are already prepared model features. They are not paths to PDB files,
and passing raw coordinates in `templates_feats` does not activate an atom
builder. Wrong template widths or missing masks can surface as low-level
broadcast/linear-layer errors; validate all five axes before retrying.

## External refinement and full-data assumptions

Do not assume the model's coordinate output is physically relaxed, complete
with side chains, PDB-ready, or benchmarked. The external FastRelax sketch in
this release requires an optional PyRosetta installation and leaves its final
relaxation step unimplemented. Keep external relaxation out of the safe smoke.

Trained checkpoints, large MSA acquisition, template generation, pretrained
embedding downloads, atom reconstruction, serialization, and metric selection
are separate workflows. Route coordinate metrics/post-processing to
`utilities`, and external pretrained wrappers to `embeddings`; do not add
network access or hidden downloads to `coordinate_smoke.py`.
