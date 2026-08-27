# Data Formats

## Pair manifest rows

The matcher reads one whitespace-delimited row per image pair.
For batch matching, use either:

- **Match-only row**: `image0 image1`
- **Evaluation row**: `image0 image1 rot0 rot1 K0[0..8] K1[0..8] T_0to1[0..15]`

The evaluation form has **38 tokens** total.
If `--eval` is set, every row must use that form.

### Field meanings

- `image0`, `image1`:
  Image paths. They are looked up under `--input_dir` unless already absolute.
- `rot0`, `rot1`:
  EXIF rotations encoded as integers `0..3`.
  - `0` = no rotation
  - `1` = 90° clockwise
  - `2` = 180° clockwise
  - `3` = 270° clockwise
- `K0`, `K1`:
  Flattened `3x3` intrinsics matrices in row-major order.
- `T_0to1`:
  Flattened `4x4` relative pose matrix in row-major order.

The bundled validator checks token counts, rotation ranges, numeric matrix entries, and optional image existence.

## Match output `.npz`

The matching stage writes `*_matches.npz` with these keys:

| Key | Shape | Meaning |
| --- | --- | --- |
| `keypoints0` | `(N0, 2)` | Detected keypoints in image0 |
| `keypoints1` | `(N1, 2)` | Detected keypoints in image1 |
| `matches` | `(N0,)` | Index of the matched keypoint in image1, or `-1` |
| `match_confidence` | `(N0,)` | Matching confidence for each keypoint in image0 |

`matches[i] = j` means keypoint `i` in image0 is matched to keypoint `j` in image1.
`-1` means unmatched.

## Evaluation output `.npz`

When `--eval` is enabled, the script also writes `*_evaluation.npz` with these keys:

| Key | Type | Meaning |
| --- | --- | --- |
| `error_t` | scalar | Translation pose error in degrees |
| `error_R` | scalar | Rotation pose error in degrees |
| `precision` | scalar | Fraction of matched pairs with epipolar error below the correctness threshold |
| `matching_score` | scalar | `num_correct / len(keypoints0)` |
| `num_correct` | scalar | Number of correct matches |
| `epipolar_errors` | array | Epipolar error per matched correspondence |

The summary table printed at the end uses:

- `pose_error = max(error_t, error_R)` per pair
- `AUC@5`, `AUC@10`, `AUC@20` from the pose error distribution
- `Prec` = mean `precision` over all pairs, multiplied by 100
- `MScore` = mean `matching_score` over all pairs, multiplied by 100

## Visualization outputs

The script writes visualization files beside the `.npz` files:

- `*_matches.png` or `*_matches.pdf`
- `*_evaluation.png` or `*_evaluation.pdf`

The file stem is based on the two image stems only.
Avoid duplicate basenames in one output directory, or use separate output directories to prevent collisions.

## Sample manifests

- `assets/scannet_sample_pairs_with_gt.txt` includes ground truth rows for evaluation.
- `assets/phototourism_sample_pairs.txt` is match-only and does not include ground truth rows.
