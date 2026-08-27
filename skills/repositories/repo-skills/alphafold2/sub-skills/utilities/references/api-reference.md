# Utility API reference

Use this page for the source-backed signatures and tensor contracts in
`alphafold2_pytorch.utils` 0.4.32. Native utility tests establish the practical
shapes listed below, but most assert only that calls complete or that a return
shape matches; they are not numerical or biological validation.

## Distograms and MDS

### `center_distogram_torch`

```python
center_distogram_torch(
    distogram,
    bins=DISTANCE_THRESHOLDS,
    min_t=1.0,
    center="mean",
    wide="std",
) -> tuple[torch.Tensor, torch.Tensor]
```

- Input: `distogram` `(B, N, N, K)`. The package defaults to `K=37` and
  `bins=torch.linspace(2, 20, steps=37)`.
- Supply nonnegative bin masses, normally probabilities from applying softmax
  to model logits. The function does not apply softmax and divides by total
  mass on each pair.
- `center="mean"` computes a weighted mean; `center="median"` selects a bin
  from cumulative mass. Other center strings leave `central` undefined in this
  version and should not be used.
- `wide="std"` and `wide="var"` control dispersion; another value uses zero
  dispersion. `min_t` is accepted but not used by this implementation.
- Return: central distance estimate and dispersion-derived weight, each
  `(B, N, N)`. The diagonal is zeroed in both. Pairs whose central estimate
  reaches the high-distance class receive zero weight. The helper does not
  know which residues are padded.
- Preserve the batch dimension. The median implementation uses an unqualified
  `squeeze()`, so singleton `B` or `N` dimensions can be dropped before the
  function expands `central` back; inspect shapes carefully for degenerate
  inputs.

### `MDScaling`

```python
MDScaling(pre_dist_mat, **kwargs)
```

Useful keyword arguments in the torch path are:

```python
weights=None, iters=10, tol=1e-5,
fix_mirror=True, N_mask=None, CA_mask=None, C_mask=None,
eigen=False, verbose=2, backend="auto"
```

- `backend="auto"` dispatches to torch for a tensor and NumPy otherwise.
  Explicit `"torch"` and `"numpy"` are also accepted.
- Input: square symmetric distances `(N, N)` or `(B, N, N)`. A single matrix
  is expanded to a batch. `weights` should match or broadcast to the pair
  matrix; make it symmetric and set diagonal/padded pairs to zero.
- Torch return: coordinates `(B, 3, N)` and time-first stress history
  `(steps, B)`. Early stopping changes `steps`; with `eigen=True` and no
  weights, the fast branch returns a zero history tensor with the source's
  internal history shape.
- `fix_mirror` is a boolean-like switch in the implementation even though the
  wrapper docstring calls it an iteration count. A true value runs one phi-based
  reflection choice and requires compatible flattened N/CA/C masks. It does
  not run multiple reconstructions or choose by minimum stress.
- `eigen=True` is fast only when `weights is None`. If weights are present, the
  source prints a fallback notice when verbose and continues iteratively.
- The NumPy path has no `eigen` parameter. Do not pass torch-only keywords when
  explicitly selecting NumPy.

`MDScaling` wraps lower-level `mdscaling_torch`, `mdscaling_numpy`,
`mds_torch`, and `mds_numpy`. Prefer the wrapper unless lower-level behavior is
specifically required.

### `get_bucketed_distance_matrix`

```python
get_bucketed_distance_matrix(
    coords, mask, num_buckets=37, ignore_index=-100
) -> torch.Tensor
```

For practical batched use, `coords` is `(B, N, 3)` and `mask` is boolean
`(B, N)`. It computes pair distances, bucketizes them against linear thresholds
from 2 to 20, and returns integer labels `(B, N, N)`. Any pair for which either
point is masked becomes `ignore_index`. This is a label builder; its output is
not the probability distogram consumed by `center_distogram_torch`.

## Masks, padding, and coordinate containers

### `scn_backbone_mask`

```python
scn_backbone_mask(scn_seq, boolean=True, n_aa=3)
```

- Input: sequence tensor of shape `(..., L)`. Only its shape/device are used.
- Output with `boolean=True`: `(N_mask, CA_mask, C_mask)`, each `(..., L*n_aa)`.
  Slots `0`, `1`, and `2` of every residue are N, CA, and C.
- `n_aa` must be at least `3`; `n_aa=4` leaves the fourth slot unselected.
- With `boolean=False`, the implementation returns `nonzero` index tensors for
  N, CA, and C; use the returned tuple position to identify each selector.

### `mat_input_to_masked`

```python
mat_input_to_masked(
    x,
    x_mask=None,
    edges_mat=None,
    edges=None,
    edge_mask=None,
    edge_attr_mat=None,
    edge_attr=None,
) -> tuple[x_masked, edge_index, edge_attr_masked, batch]
```

- `x`: unbatched `(N, D)` or batched `(B, N, D)` node features.
- `x_mask`: required for unbatched input in practice; use boolean `(N,)` or
  `(B, N)`. The source synthesizes an all-true mask only in its batched branch.
- Supply either dense adjacency `edges_mat` (`(N,N)` or `(B,N,N)`) or flattened
  indices `edges` `(2,E)`. Batched dense adjacency is flattened and offset by
  batch before node compaction.
- `edge_mask` indexes the flattened edge list. If omitted, every supplied edge
  is kept before node masking.
- Return: retained features `(N_kept,D)`, compacted edge indices `(2,E_kept)`,
  optional edge attributes, and node-to-batch labels `(N_kept,)`.
- Current defects/limits:
  - `edge_attr_mat` without flattened `edge_attr` references `edge_attr` before
    assignment; flatten attributes yourself and pass `edge_attr`.
  - Supplied `edge_attr` is filtered by `edge_mask`, but the implementation
    does not apply the later node-removal filter to it. After node masking,
    `edge_attr_masked` can therefore have a different length/order than the
    returned compact `edge_index`. Avoid edge attributes unless the caller
    prefilters edges to retained nodes and verifies alignment.
  - Missing edges, empty edge lists, and an all-false node mask are not handled
    as clean empty outputs. Validate them before calling.

### `sidechain_container`

```python
sidechain_container(
    seqs, backbones, atom_mask, cloud_mask=None, padding_tok=20
) -> torch.Tensor
```

- `seqs`: `(B,L)` SidechainNet integer sequences or an iterable of sequence
  strings. Tensor token `20` is treated as right-padding.
- `atom_mask`: boolean/integer `(14,)`, selecting which atom slots are already
  supplied. It must select at least one slot.
- `backbones`: `(B, L*n_selected, 3)`, where
  `n_selected = atom_mask.bool().sum()`. The second dimension must divide
  exactly by `n_selected` and agree with sequence length.
- Optional `cloud_mask`: `(B,L,14)`; output slots outside it are zeroed.
- Return: `(B,L,14,3)`. If all 14 slots are supplied, the function only
  reshapes and returns. Otherwise it invokes mp-nerf to construct missing
  slots and returns on the original device.
- The source comment says the batch path could be extended and is not tested;
  the native test uses a batch of two, but numerical sidechain validity is not
  asserted. The implementation expects right-padding because it removes a
  count of padding tokens from the sequence tail. Mixed/interior padding is
  unsupported.

## Loss and C-alpha LDDT

### `distmat_loss_torch`

```python
distmat_loss_torch(
    X=None,
    Y=None,
    X_mat=None,
    Y_mat=None,
    p=2,
    q=2,
    custom=None,
    distmat_mask=None,
    clamp=None,
) -> torch.Tensor
```

Provide one representation for each side: coordinates through `X` and `Y`, or
precomputed pair matrices through `X_mat` and `Y_mat`. Coordinate inputs are
unconditionally `squeeze()`d and passed to `torch.cdist`; the least ambiguous
contract is unbatched `(N, D)`. Pair matrices must have the same shape.

`p` is the point-distance norm. `q=2` returns mean squared pair-distance error;
`q=1` produces absolute error through the source's power transform.
`distmat_mask` is a boolean selector over pair entries. Although the docstring
mentions weights, the implementation uses it for boolean indexing, not
multiplication; pass a boolean mask. `custom`, if provided, is called on the
squeezed pair matrices and then averaged. `clamp=(min,max)` clamps coordinate
components before `cdist`, not computed pair distances. No alignment or atom
matching occurs.

### `lddt_ca_torch`

```python
lddt_ca_torch(
    true_coords, pred_coords, cloud_mask, r_0=15.0
) -> torch.Tensor
```

- Inputs: matching coordinates `(B,L,14,3)` and cloud mask `(B,L,14)`.
- The source selects slot `1` as C-alpha and uses the reference distance matrix
  to include pairs under `r_0`. It scores differences against thresholds
  `0.5`, `1`, `2`, and `4`.
- Return: per-residue tensor `(B,L)`; masked/padded residues remain zero.
- This implementation includes all reference pairs under `r_0` before manually
  subtracting the self term. Empty or single-C-alpha selections and duplicate
  zero-distance points are poor inputs. It does not align structures or match
  sequences/residues.

## Alignment and metrics

### `Kabsch`

```python
Kabsch(A, B, backend="auto") -> tuple[A_aligned, B_centered]
```

Inputs may be `(3,N)` or `(B,3,N)`; the decorator handles batches by calling
the lower-level implementation per item. The function centers both structures
and rotates `A` into `B`, returning both centered arrays/tensors with the input
shape. It removes translation and proper rotation, but not residue mismatch,
atom-order mismatch, scale, or reflection.

For torch, the lower-level signature is `kabsch_torch(X, Y, cpu=True)`. The
capitalized wrapper does not expose `cpu` because it accepts no extra keyword
arguments beyond the decorator's `backend` keyword.

### `GDT`

```python
GDT(
    A, B, *, mode="TS", cutoffs=[1, 2, 4, 8], weights=None,
    backend="auto"
) -> tensor_or_array
```

Inputs are `(3,N)` or `(B,3,N)` and output is one value per batch item.
`mode="HA"` (case-insensitive) forces cutoffs `[0.5,1,2,4]`; every other mode
forces `[1,2,4,8]`. Therefore the public `cutoffs` argument is present in the
signature but ignored by the wrapper. Align first when that is the intended
metric workflow.

When weights are supplied, pass one value per four cutoffs. The lower-level
calculation is `(fractions * weights).mean(-1)`: weights are not normalized by
their sum. A scalar is not the documented shape and can fail in the torch
implementation.

### `TMscore`

```python
TMscore(A, B, backend="auto") -> tensor_or_array
```

Inputs and batch output follow `GDT`. The repository explicitly warns that this
is not the official TM-score implementation. The source sets
`L=max(15,N)` and `d0 = 1.24 * cbrt(L - 15) - 1.8`, then averages
`1 / (1 + (distance / d0)**2)`. Treat it as the package's simplified metric,
not an authoritative CASP/TM-align result.

The public wrappers `RMSD(A, B, backend="auto")`, `GDT`, and `TMscore` do not
align their inputs. Call `Kabsch` first if optimal rigid alignment is part of
the evaluation contract.
