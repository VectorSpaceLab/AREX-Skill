# Workflows for motifs, anomalies, chains, snippets, shapelets, and segmentation

The examples below use tiny deterministic arrays and require no network or external data. Replace the synthetic series with user data only after the routing and column choices are correct.

## Shared synthetic series

This series has one repeated motif in the first half and a different repeated motif in the second half, so it supports both motif matching and a simple regime-change smoke path.

```python
import numpy as np
import stumpy

A = np.array([0.0, 1.0, 0.0, -1.0])
B = np.array([0.0, -1.0, 0.0, 1.0])
T = np.concatenate([A, A, A, B, B, B]).astype(np.float64)
m = 4
mp = stumpy.stump(T, m)
P = mp[:, 0].astype(float)
I = mp[:, 1].astype(int)
```

## 1. Motifs and query matches from a 1-D profile

Use this when you already have `T` and a 1-D profile `P`.

```python
motif_distances, motif_indices = stumpy.motifs(
    T,
    P,
    max_distance=0.1,
    cutoff=np.inf,
    max_matches=3,
    max_motifs=1,
)

Q = T[:m]
query_matches = stumpy.match(
    Q,
    T,
    max_distance=0.1,
    max_matches=3,
    query_idx=0,
)
```

Interpretation:
- `motif_indices[0]` gives the start indices of the representative motif and its closest matches.
- `query_matches` is sorted by distance and is the right API when the query is known ahead of time.
- `np.argmin(P)` is the lowest-distance motif candidate.
- `np.argmax(P)` is a high-distance discord / anomaly candidate.

If `P` came from a top-k profile, reduce it to one distance per subsequence before `motifs`, for example with a domain-specific mean or minimum over the top-k distance axis.

## 2. Discord / anomaly inspection

STUMPY does not need a separate discord object for the common static case. Inspect the profile peaks after profile computation:

```python
discord_idx = int(np.argmax(P))
discord_distance = float(P[discord_idx])
discord_subsequence = T[discord_idx : discord_idx + m]
nearest_neighbor_idx = int(I[discord_idx])
```

Use this only as a candidate-ranking step. Validate with domain context, nearby peaks, data gaps, constant subsequences, and the chosen `m`.

## 3. Consensus motif across several raw series

Use `ostinato` when the input is a list of raw 1-D series and the question is "what subsequence is conserved across this collection?"

```python
Ts = [T, T + 0.25, T - 0.25]
radius, series_idx, subseq_idx = stumpy.ostinato(Ts, m)
consensus = Ts[series_idx][subseq_idx : subseq_idx + m]
```

The result identifies the central consensus motif and its radius. To find each series' nearest occurrence to that consensus motif, run `stumpy.mass(consensus, each_series)` or `stumpy.match(consensus, each_series)`.

Do not pass multidimensional profile arrays to `ostinato`. If you already have multidimensional `P` and `I`, use the `mmotifs` handoff and route subspace decisions to `multidimensional-profiles`.

## 4. MPdist similarity and snippets

Use MPdist when two series may be similar even if matching subsequences occur in different orders.

```python
score_same = stumpy.mpdist(T[:12], T[:12], m=4)
score_different = stumpy.mpdist(T[:12], T[12:], m=4)
```

Use snippets when a long series needs a small set of representative subsequences and regime slices.

```python
snips, snip_idx, profiles, fractions, areas, regimes = stumpy.snippets(
    T,
    m=4,
    k=2,
)
```

Interpretation:
- Lower MPdist means more shared subsequences.
- `snip_idx` locates each representative snippet.
- `fractions` estimates how much of the series each snippet explains.
- `regimes` stores `[snippet_number, start, stop]` rows for the regions represented by each snippet.

## 5. Time-series chains

Use chains when the question is about a motif that evolves or drifts over time. Start from the left and right index columns, not the distance or nearest-neighbor index columns.

```python
IL = mp[:, 2].astype(int)
IR = mp[:, 3].astype(int)

anchored_chain = stumpy.atsc(IL, IR, j=0)
all_chain_set, longest_unanchored_chain = stumpy.allc(IL, IR)
```

Interpretation:
- `atsc` follows the chain starting from an anchor index `j`.
- `allc` returns all unique chains plus one longest unanchored chain.
- Chain results are meaningful only if the upstream profile's left and right nearest-neighbor columns match the normalization mode and window size you intend.

## 6. Static semantic segmentation with FLUSS

Use FLUSS for batch / static segmentation from nearest-neighbor index arcs.

```python
cac, regime_locations = stumpy.fluss(
    I,
    L=m,
    n_regimes=2,
    excl_factor=1,
)
```

Interpretation:
- `cac` is the corrected arc curve.
- Low `cac` locations are candidate regime boundaries.
- `n_regimes=2` asks for one boundary; generally, boundaries = `n_regimes - 1`.
- `L` should be near a natural period or motif length and is often close to `m`, but it is a segmentation parameter rather than a profile-computation parameter.

## 7. Online semantic segmentation with FLOSS

Use FLOSS when the series is updated one value at a time and you want the segmentation curve to update with it.

```python
stream = stumpy.floss(
    mp,
    T,
    m=m,
    L=m,
    excl_factor=1,
)
stream.update(0.5)
updated_cac = stream.cac_1d_
updated_profile = stream.P_
updated_indices = stream.I_
updated_series = stream.T_
```

FLOSS needs the full 4-column profile and the raw initial series. Designing a long-running stream loop, egress policy, and pan/online matrix-profile state belongs to `approximate-streaming-pan`.

## 8. Shapelet candidates from profile contrasts

Shapelet discovery is a profile-analysis workflow rather than a separate STUMPY shapelet API.

```python
class_a = np.concatenate([A, A, A, np.array([np.nan])])
class_b = np.concatenate([B, B, B, np.array([np.nan])])

P_self = stumpy.stump(class_a, m)[:, 0].astype(float)
P_cross = stumpy.stump(class_a, m, class_b, ignore_trivial=False)[:, 0].astype(float)

P_self[~np.isfinite(P_self)] = np.nan
P_cross[~np.isfinite(P_cross)] = np.nan
P_diff = P_cross - P_self
candidate_idx = np.argpartition(np.nan_to_num(P_diff, nan=-np.inf), -3)[-3:]
shapelet = class_a[candidate_idx[0] : candidate_idx[0] + m]
```

A good class-A shapelet candidate has low within-class distance (`P_self`) and high cross-class distance (`P_cross`), so peaks in `P_cross - P_self` are useful candidates. To turn a shapelet into a classifier feature, compute a distance profile against each sample and keep the minimum distance:

```python
D = stumpy.mass(shapelet, T)
feature_value = float(np.nanmin(D))
```

## 9. Guided motif search with an annotation vector

Use this when the best raw motif lands in a region that domain context says is undesirable but not invalid.

```python
annotation_vector = np.ones_like(P, dtype=float)
annotation_vector[8:12] = 0.0  # De-emphasize a region; length must match P
corrected_P = P + (1.0 - annotation_vector) * np.nanmax(P)
corrected_motif_idx = int(np.nanargmin(corrected_P))
```

Then either inspect `corrected_motif_idx` directly or pass `corrected_P` into `stumpy.motifs(T, corrected_P, ...)`. Keep the original `mp[:, 1]` for the nearest-neighbor locations unless you recompute the profile.

## 10. Scripted smoke check

The bundled smoke script runs the same no-network pattern and prints validation facts:

```bash
python scripts/motif_segmentation_smoke.py --mode both
python scripts/motif_segmentation_smoke.py --mode motif --max-distance 0.1
python scripts/motif_segmentation_smoke.py --mode fluss --L 4 --n-regimes 2 --excl-factor 1
```
