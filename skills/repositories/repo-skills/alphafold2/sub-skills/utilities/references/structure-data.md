# Structure data and metric caveats

Read this before converting a model output into utility input. The package
contains more than one coordinate convention, and the utilities do not carry
an atom-order or residue-correspondence schema for you.

## Coordinate layouts and atom order

The README's model-facing coordinate examples use a flattened tensor
`(B, L * atoms, 3)`. The documented model choices include:

- `backbone`: three atoms per residue, displayed as C, C-alpha, N;
- `backbone-with-cbeta`: those three plus C-beta;
- `backbone-with-oxygen`, `backbone-with-cbeta-and-oxygen`, and `all`;
- a custom `(14,)` atom-selection vector.

The utility source uses a SidechainNet-like all-atom layout for several
functions:

- coordinates `(B, L, 14, 3)`;
- occupancy/cloud mask `(B, L, 14)`;
- flattened atom points `(B, L*14, 3)` and masks `(B, L*14)` when a graph or MDS
  operation is performed at atom level.

`scn_backbone_mask` marks the first three slots of each residue as N, CA, and C
in its own flattened layout. That is not the README's displayed model order.
Never reshape model output into a SidechainNet tensor unless the selected atom
count, residue-major order, atom order, and units are all explicitly known.
Keep an atom map and a mask with every coordinate tensor.

Coordinates in the README workflow are in Angstroms. The utility functions do
not convert units; a nanometer input silently changes distance thresholds and
metric meaning.

## Residues, atom slots, and padding

`constants.py` defines `NUM_COORDS_PER_RES=14`, `NUM_AMINO_ACIDS=21`, and
`DISTOGRAM_BUCKETS=37`. SidechainNet integer sequences conventionally use token
`20` as padding for `sidechain_container`; the utility vocabulary also maps a
padding character `_` to an empty atom cloud.

- A residue mask is normally `(B,L)`; an atom/cloud mask is `(B,L,14)`.
- Flatten a cloud mask to `(B,L*14)` only when the coordinate tensor is
  flattened in the same residue-major then atom-major order.
- Missing sidechain slots are not equivalent to real atoms at coordinate zero.
  Exclude them through the occupancy mask. Likewise, a padded residue must be
  removed from both rows and columns of a pairwise matrix.
- `sidechain_container` expects right-padding and removes padding from the tail
  of each sequence. Interior padding, inconsistent sequence lengths, or a
  `backbones` width that is not `L * atom_mask.sum()` is unsupported.

For `mat_input_to_masked`, `x` is `(B,N,D)` or `(N,D)`, `x_mask` is `(B,N)` or
`(N,)`, and an adjacency is either dense `(B,N,N)`/`(N,N)` or flattened
`(2,E)`. The result uses compact node numbering. Its `batch` output labels the
retained nodes, not the original padded positions. Do not use a residue mask
where a flattened atom mask is required.

## Distogram buckets and pair matrices

The README reports model distograms as `(B,L,L,37)`. The utility
`center_distogram_torch` expects the same final bucket axis but expects
nonnegative masses, not raw logits and not integer bucket IDs. Its default
threshold vector is evenly spaced from `2` through `20`; it derives central
representatives and uncertainty weights and zeroes the diagonal. It does not
know your residue padding mask.

For a safe conversion:

1. Apply the model's intended normalization to logits so each pair has
   nonnegative mass; do not pass logits directly.
2. Call `center_distogram_torch` and check for non-finite central values from
   zero-mass pairs.
3. Symmetrize the central matrix if the caller's pair predictions are not
   symmetric, and set its diagonal to zero.
4. Set weights to zero for every padded row and column and for the diagonal.
5. Use `MDScaling` only on a square, finite matrix and retain the real-point
   count for later slicing.

`get_bucketed_distance_matrix` is a different direction of conversion: it
starts from coordinates `(B,N,3)`, bucketizes pair distances using boundaries
from `2` through `20`, and fills masked pairs with `-100`. Its integer labels
are not input probabilities for `center_distogram_torch`.

## MDS, symmetry, and reflection

`MDScaling` consumes `(N,N)` or `(B,N,N)` distances and returns `(B,3,N)`.
Distance geometry is ambiguous up to translation, rotation, and reflection.
`fix_mirror=True` is a protein-specific phi-angle heuristic and requires
flattened N/CA/C masks that match the point axis. Use `fix_mirror=False` for a
generic point cloud, a residue-level matrix without atom masks, or a synthetic
fixture with no protein backbone semantics.

For padded data, zero weights involving padding rather than inserting a large
fake distance. MDS may still emit coordinates for zero-weight indices; exclude
them before alignment and metrics. Stress history diagnoses optimization and
is not a confidence score. A random symmetric matrix may not be Euclidean or
physically realizable, so finite coordinates and the expected shape are the
only appropriate assertions for a tiny synthetic smoke case.

## Alignment and metrics

`Kabsch` requires two corresponding unbatched `(3,N)` point sets in this
version's public wrapper. It centers both sets and rotates the first into the
second. It is not a sequence aligner and does not fix residue gaps, atom-order
mismatch, scale, or units. Select the intersection of target/prediction masks,
then preserve exactly the same point order.

`RMSD`, `GDT`, and `TMscore` accept `(3,N)` or `(B,3,N)` through their wrappers;
none performs alignment. GDT-TS uses `[1,2,4,8]` Å and GDT-HA uses `[0.5,1,2,4]` Å.
The package's TM-score is explicitly a simplified formula, not the official
TM-score/TM-align implementation. Do not use random-tensor scores or the
simplified score as evidence of a correct fold or a CASP-equivalent result.

`lddt_ca_torch` accepts matching `(B,L,14,3)` tensors plus `(B,L,14)` cloud
masks, selects atom slot `1` as C-alpha, and returns `(B,L)`. It does not align,
perform sequence matching, or reconcile missing residues. Use the intersection
of valid C-alpha residues and report the target, residue mapping, mask, units,
and reference radius (`r_0=15` by default) for meaningful evaluation.

## Scientific interpretation

A random synthetic tensor is useful for API, dtype, shape, finite-value, and
failure-path checks only. A tiny padded distance matrix can verify that masks
are applied and MDS returns the documented layout, but it cannot validate
protein geometry, bucket calibration, mirror orientation, LDDT, GDT, or TM-score
thresholds. Scientific claims require a justified target structure, consistent
residue/atom correspondence, known coordinate units, and an explicit treatment
of missing/padded atoms.
