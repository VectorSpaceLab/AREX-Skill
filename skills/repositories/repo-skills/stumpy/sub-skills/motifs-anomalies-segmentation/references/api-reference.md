# Motifs / anomalies / segmentation API reference

This reference describes the STUMPY APIs owned by this sub-skill and the input forms they expect. It assumes ordinary profile computation has already happened elsewhere unless the API itself consumes raw series directly.

## Distance semantics

- A matrix profile value is the nearest-neighbor distance for one subsequence.
- Low profile values identify motif candidates: subsequences that have very similar nearest neighbors.
- High profile values identify discord / anomaly candidates: subsequences whose nearest neighbors are still far away.
- For z-normalized workflows, keep `normalize=True` consistently. For absolute / non-normalized workflows, compute the upstream profile with the matching non-normalized API and pass `normalize=False` downstream; `p` only matters in that non-normalized route.

## Motifs and query matching

### `motifs(T, P, ...)`

Signature shape:

```python
stumpy.motifs(
    T,
    P,
    min_neighbors=1,
    max_distance=None,
    cutoff=None,
    max_matches=10,
    max_motifs=1,
    atol=1e-8,
    normalize=True,
    p=2.0,
    T_subseq_isconstant=None,
)
```

Consumes:
- `T`: one raw 1-D time series.
- `P`: the 1-D matrix profile distance vector for `T`, usually `mp[:, 0]` or `mp.P_`.

Returns:
- `motif_distances`: rows of sorted distances for each motif representative and its matches.
- `motif_indices`: matching subsequence start indices; the first column is the self/trivial match for each motif.

Important details:
- Do not pass the full 4-column profile array as `P`.
- If the upstream profile was computed with top-k neighbors, summarize those k distances into one scalar per subsequence before calling `motifs`.
- `max_distance` may be a float or a callable that accepts one distance-profile array `D`.
- `cutoff` limits which low profile values are allowed to become motif representatives.
- `max_matches=None` asks for every match within `max_distance`; otherwise the result is capped.

### `match(Q, T, ...)`

Signature shape:

```python
stumpy.match(
    Q,
    T,
    M_T=None,
    Σ_T=None,
    max_distance=None,
    max_matches=None,
    atol=1e-8,
    query_idx=None,
    normalize=True,
    p=2.0,
    T_subseq_isfinite=None,
    T_subseq_isconstant=None,
    Q_subseq_isconstant=None,
)
```

Consumes:
- `Q`: a raw query sequence.
- `T`: the raw time series to scan.
- Optional precomputed sliding mean/std arrays (`M_T`, `Σ_T`) for `T` if you already have them.

Returns:
- A two-column array: distance then subsequence start index, sorted from closest to farthest.

Important details:
- Use `match` when you know the query; it does not require a full matrix profile.
- Use `query_idx` only when `Q` is a subsequence of the same `T`; leave it `None` for AB-join-style searches.
- `max_distance=None` defaults to a data-derived threshold that returns at least the closest match.
- `max_matches` caps the number of rows; use `None` when you need all rows that pass the threshold.

## Multidimensional motif handoff

### `mmotifs(T, P, I, ...)`

Signature shape:

```python
stumpy.mmotifs(
    T,
    P,
    I,
    min_neighbors=1,
    max_distance=None,
    cutoffs=None,
    max_matches=10,
    max_motifs=1,
    atol=1e-8,
    k=None,
    include=None,
    normalize=True,
    p=2.0,
    T_subseq_isconstant=None,
)
```

Consumes:
- Multidimensional raw series `T` with dimensions on rows and time on columns.
- Multidimensional profile distances `P` and indices `I` from `mstump` or `maamp`.

Returns:
- Motif distances and indices.
- `motif_subspaces`: selected dimensions for each motif.
- `motif_mdls`: MDL arrays used to choose subspace size when `k` is not fixed.

Routing note:
- This sub-skill can explain the handoff and output interpretation, but multidimensional profile computation, orientation checks, `include`, `k`, `subspace`, and `mdl` debugging belong to `multidimensional-profiles`.

## Consensus motifs across multiple series

### `ostinato(Ts, m, ...)`

Signature shape:

```python
stumpy.ostinato(Ts, m, normalize=True, p=2.0, Ts_subseq_isconstant=None)
```

Consumes:
- `Ts`: a Python list of raw 1-D time series.
- `m`: subsequence window size shared by the search.

Returns:
- `central_radius`: best consensus radius.
- `central_Ts_idx`: which series contains the central consensus motif.
- `central_subseq_idx`: motif start index inside that series.

Use when you need a motif conserved across all or most series in a set. Distributed and GPU variants are acceleration mechanics and route to `distributed-gpu-acceleration`.

## Similarity and summarization

### `mpdist(T_A, T_B, m, ...)`

Signature shape:

```python
stumpy.mpdist(
    T_A,
    T_B,
    m,
    percentage=0.05,
    k=None,
    normalize=True,
    p=2.0,
    T_A_subseq_isconstant=None,
    T_B_subseq_isconstant=None,
)
```

Consumes:
- Two raw 1-D series and a window size.

Returns:
- A scalar MPdist score. Lower means the two series share many similar subsequences, regardless of order.

Important details:
- `percentage` chooses the fraction of concatenated AB/BA profile values used to report the distance.
- `k` overrides `percentage` when you need an explicit order statistic.
- MPdist is a similarity measure, not a strict mathematical metric.

### `snippets(T, m, k, ...)`

Signature shape:

```python
stumpy.snippets(
    T,
    m,
    k,
    percentage=1.0,
    s=None,
    mpdist_percentage=0.05,
    mpdist_k=None,
    normalize=True,
    p=2.0,
    mpdist_T_subseq_isconstant=None,
)
```

Consumes:
- One raw 1-D series, a snippet window `m`, and the number of snippets `k`.

Returns a tuple:
1. top snippets,
2. snippet start indices,
3. MPdist profiles,
4. fractions of data represented,
5. profile areas,
6. regime slice table.

Important details:
- `m` must be no larger than half the series length.
- `s` overrides `percentage` when choosing the sub-subsequence length used by the MPdist profiles.
- `mpdist_percentage` / `mpdist_k` tune the MPdist subroutine.

## Chains

### `atsc(IL, IR, j)` and `allc(IL, IR)`

Consume:
- `IL`: left matrix profile index column, usually `mp[:, 2]` or `mp.left_I_`.
- `IR`: right matrix profile index column, usually `mp[:, 3]` or `mp.right_I_`.
- `j`: anchor index for `atsc` only.

Return:
- `atsc`: one anchored time-series chain as a 1-D integer array.
- `allc`: `(all_chain_set, longest_unanchored_chain)`.

Important details:
- Chains are temporally ordered motifs / evolving patterns.
- These functions are normalization-agnostic because the profile indices were already computed upstream.
- Passing profile distances instead of left/right indices will produce nonsensical chains.

## Semantic segmentation

### `fluss(I, L, n_regimes, ...)`

Signature shape:

```python
stumpy.fluss(I, L, n_regimes, excl_factor=5, custom_iac=None)
```

Consumes:
- `I`: nearest-neighbor matrix profile index vector, usually `mp[:, 1]` or `mp.I_`.
- `L`: approximate period / subsequence length used to manage edge effects.
- `n_regimes`: number of regimes, which is one more than the number of change points.

Returns:
- `cac`: corrected arc curve.
- `regime_locs`: estimated regime boundary indices.

Important details:
- FLUSS uses indices, not profile distances.
- `excl_factor` suppresses edge artifacts and enforces spacing around found regimes.

### `floss(mp, T, m, L, ...)`

Signature shape:

```python
stream = stumpy.floss(
    mp,
    T,
    m,
    L,
    excl_factor=5,
    n_iter=1000,
    n_samples=1000,
    custom_iac=None,
    normalize=True,
    p=2.0,
    T_subseq_isconstant_func=None,
)
stream.update(new_value)
```

Consumes:
- Full 4-column matrix profile `mp` from the initial window.
- Raw series `T` used to produce that profile.
- Matrix-profile window `m` and segmentation period `L`.

Exposes:
- `stream.cac_1d_`: updated one-dimensional corrected arc curve.
- `stream.P_`: updated profile distances.
- `stream.I_`: updated right profile indices.
- `stream.T_`: updated rolling series.

Routing note:
- FLOSS interpretation is here; long-lived online update-loop design belongs to `approximate-streaming-pan`.

## Shapelet and guided motif support

- Shapelet discovery is usually a profile-contrast workflow: compute a self-join profile for one class, compute an AB-join profile against another class, and rank peaks in `P_AB - P_self` as candidate class-specific shapelets.
- Candidate shapelets can be scored against each labeled sample with `stumpy.mass(shapelet, sample)`, using the minimum distance as a feature.
- Guided motif search can modify a profile before motif extraction with an annotation vector `AV` in `[0, 1]`: `corrected_P = P + (1 - AV) * np.nanmax(P)`. The annotation vector must have the same length as `P`.
