# Utilities troubleshooting

Use this page after reading [api-reference.md](api-reference.md) and
[structure-data.md](structure-data.md). Diagnose import, dependency, input,
numerical, and interpretation failures separately; a successful tensor call is
not proof of a scientifically meaningful structure evaluation.

## Import and optional dependency failures

### `from alphafold2_pytorch.utils import ...` raises `ModuleNotFoundError`

**Symptom:** an error names `sidechainnet`, `mp_nerf`, `Bio`/BioPython,
`einops`, PyTorch, or another scientific package before a utility call runs.

**Cause and recovery:** `utils.py` imports SidechainNet vocabulary/build tables,
BioPython, einops, mp-nerf, torch, and constants at module import time. Install
and verify the package's compatible scientific dependency set rather than
patching one function in isolation. A CPU import is the safe baseline. CUDA is
optional for this utility route and a visible but OOM-blocked GPU is not an API
failure.

### SidechainNet/mp-nerf failures

`sidechainnet` is needed for module import, vocabulary, atom tables, cloud
masks, and normal SidechainNet layouts. `mp-nerf` is needed when
`sidechain_container` constructs missing atoms. Confirm the versions together
with PyTorch before retrying. Do not claim sidechain packing from a backbone
reshape alone.

### `clean_pdb` or `custom2pdb` cannot import `mdtraj`

`mdtraj` is imported lazily by those PDB helpers. It is not required by the
core tensor metric implementations once the utility module imports. Install it
only for PDB load/clean/write workflows, then check chain selection and atom
ordering before replacing coordinates. These helpers may read/write files and
`download_pdb` invokes an external network command; they are not part of the
bundled deterministic smoke check.

### ProDy or OpenMM confusion

`ProDy` appears in package metadata but is not directly imported by the
reviewed utility functions. `OpenMM` is discussed in README relaxation/data
material, not in the utility tensor path. Installing either does not replace
SidechainNet, mp-nerf, or MDTraj, and their presence does not validate a
force-field relaxation or coordinate metric.

## Shape, atom-order, and mask failures

### Invalid atom mask or coordinate shape

Before `lddt_ca_torch`, assert:

```python
assert true_coords.shape == pred_coords.shape
assert true_coords.ndim == 4 and true_coords.shape[-2:] == (14, 3)
assert cloud_mask.shape == true_coords.shape[:-1]
```

Before `sidechain_container`, assert `atom_mask.shape == (14,)`,
`atom_mask.bool().sum() > 0`, `backbones.shape[-1] == 3`, and
`backbones.shape[1] == L * atom_mask.bool().sum()`. A model tensor `(B,L*3,3)`
is not automatically a `(B,L,14,3)` SidechainNet tensor. Reshape only after
confirming selected atoms and order. A difficult padded case should contain
one fully padded residue and one residue missing a sidechain slot; compute
metrics on the shared valid atom/C-alpha mask, not on zero coordinates.

### Incorrect backbone masks for mirror fixing

`scn_backbone_mask` returns flattened masks `(B,L*n_aa)` (or the corresponding
unbatched shape) with N, CA, C in the first three slots per residue. Do not pass
a residue mask `(B,L)` as `N_mask` to `MDScaling`. Use `fix_mirror=False` for
non-protein synthetic points. With mirror fixing enabled, require enough
successive N/CA/C positions for the phi heuristic and ensure every mask agrees
with the matrix's `N` point axis.

### Padded pair matrices

`center_distogram_torch` does not receive a residue mask. After centralization,
set weights to zero for every padded row/column and diagonal. Keep the matrix
square, finite, and symmetric. MDS can still output a coordinate for each
padded index; slice real indices before Kabsch, GDT, TM-score, RMSD, or any
scientific comparison.

### `mat_input_to_masked` edge errors

- Use `x` `(N,D)` or `(B,N,D)` and a matching boolean `x_mask`.
- Supply `edges` as `(2,E)` or `edges_mat` with the same batch rank as `x`.
- `edge_mask` must refer to the same flattened edge representation.
- Validate that at least one edge remains and that node indices are in range.
- The current `edge_attr_mat`-only branch references `edge_attr` before it is
  assigned; flatten edge attributes and pass `edge_attr` instead.
- The source filters `edge_attr` by `edge_mask` but does not fully re-filter it
  after node compaction. Verify edge-attribute alignment yourself or omit edge
  attributes for a masking-only call.

Empty graphs, all-false node masks, and inconsistent edge/attribute lengths are
not supported happy paths. Diagnose them in the caller before invoking the
helper.

## Numerical and API issues

### Non-finite central distances or weights

A zero-mass distogram pair causes division by zero in
`center_distogram_torch`. Pass nonnegative, nonempty bin masses and then
`torch.isfinite`-check the result. Set invalid pair weights to zero; do not
interpret a filled `nan` as a distance observation. Raw logits can be negative
and are not valid bin masses.

### MDS is unstable or returns unexpected geometry

Check square/symmetric/finite distances, zero diagonal, and nonnegative
pairwise values. Symmetrize noisy estimates and use small CPU fixtures with
`iters=3..10` and `verbose=0`. Weight out padding rather than using arbitrary
large distances. Inspect stress history as an optimization diagnostic.

Use `eigen=True` only for an unweighted fast branch; weighted input falls back
to iterative behavior. `fix_mirror=True` is only for a flattened protein
backbone with valid N/CA/C masks. Coordinate recovery is inherently ambiguous
under translation, rotation, and reflection; a finite shape-correct result does
not establish the original structure.

### Kabsch or metrics fail on small/degenerate inputs

The public `Kabsch` wrapper in this version is for unbatched `(3,N)` inputs.
Use `(3,N)` for alignment, then add a batch dimension for `GDT`, `RMSD`, or
`TMscore` only if desired. Use at least three finite, non-collinear matched
points; one point or a collinear set is ill-conditioned. Kabsch does not fix
sequence gaps, atom permutation, scale, or unit mismatch.

For `GDT`, pass one weight per four cutoffs, for example
`weights=[1,1,1,1]`. The wrapper's `mode` controls cutoffs and overrides the
`cutoffs` argument. The implementation averages weighted fractions without
normalizing weights by their sum. `TMscore` is the package's simplified
length-normalized formula, not the official TM-score; random or very short
inputs are not authoritative.

### LDDT is all zeros or uninformative

Confirm that cloud masks include slot `1` only for real C-alpha atoms, that
both tensors use the same `(B,L,14,3)` layout, and that at least two valid
residues fall within the reference radius `r_0=15`. The function compares
local pairwise distances, does not align structures, and does not reconcile
missing residues. An identical matched structure is a useful sanity case;
random tensors are only an API smoke case.

## Interpretation and safety limits

Random synthetic coordinates, synthetic bucket masses, and tiny padded MDS
fixtures validate shapes, finite values, masking, and wrapper behavior only.
They do not calibrate distance buckets or establish fold quality. For real
claims, document the target source, residue mapping, atom order, units,
intersection mask, padding treatment, alignment choice, metric variant, and
whether the simplified TM-score is acceptable. Stop rather than silently
substituting a different atom layout or treating README drift as a verified
utility contract.
