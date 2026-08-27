# Matching outputs

## Descriptor input contract

Most descriptor matchers operate on two descriptor tensors:

```python
desc1.shape == (N1, D)
desc2.shape == (N2, D)
```

`D` must match. Keep descriptors on the same device and dtype. Some matchers also accept or compute a distance matrix `dm` with shape `(N1, N2)`.

## Output contract

The basic matcher functions return a pair:

```python
dists, idxs = match_mnn(desc1, desc2)
```

| Output | Shape | Meaning |
| --- | --- | --- |
| `dists` | `(M, 1)` | Distance or score for each accepted match. Smaller is better for nearest-neighbor-style matchers. |
| `idxs` | `(M, 2)` | Long indices. Column 0 indexes `desc1`; column 1 indexes `desc2`. |

`0 <= M <= min(N1, N2)` for mutual matchers. One-way nearest-neighbor matching can return up to `N1` matches. Thresholded matchers can return `M == 0`.

## Common matchers

| Matcher | Behavior |
| --- | --- |
| `match_nn` | For each descriptor in `desc1`, returns its nearest descriptor in `desc2`. |
| `match_mnn` | Keeps only pairs that are mutual nearest neighbors. |
| `match_snn` | Uses a second-nearest-neighbor ratio threshold. |
| `match_smnn` | Combines ratio filtering and mutual nearest-neighbor filtering. |
| `match_fginn` | Uses first geometrically inconsistent nearest neighbors. |
| `match_adalam` | Applies AdaLAM geometric filtering; expects keypoint/LAF geometry in addition to descriptors. |

## Empty matches

An empty result is valid when there are no descriptors, only one candidate for a ratio matcher, or thresholds reject all pairs. Downstream code should branch on `idxs.numel() == 0` before indexing keypoint tensors.

## Geometry handoff

To build point correspondences after matching:

```python
pts1_matched = pts1[idxs[:, 0]]
pts2_matched = pts2[idxs[:, 1]]
```

Then hand off to the geometry route for homography, fundamental matrix, essential matrix, or pose estimation. Keep coordinate order `(x, y)` and pixel-space conventions explicit.
